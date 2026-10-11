#!/usr/bin/env python3
"""A case folder and a mock URL as builder input (standard library only).

    python3 builder/build.py <case_folder> <mock_url>

combine(folder, out_md): every file of the folder, in path order, as one Markdown brief: a header with the file's
relative path, then its text. Markdown, text, CSV, JSON, YAML, HTML (tags removed) and e-mails (headers + text parts)
are read as text; PDFs through `pdftotext -layout` when it is installed; .docx/.xlsx/.pptx from their XML. A file that
cannot be converted (an image, a PDF without pdftotext) is listed with its path so the building agent reads it itself
(its Read tool opens PDFs and images).

fetch_openapi(mock_url, out_json): the tool API of the mock (<mock_url>/openapi.json), with servers[0].url set to the
mock URL, so every tool the builder makes calls the mock.
"""
import email
import email.policy
import html
import json
import pathlib
import re
import shutil
import subprocess
import urllib.request
import zipfile

TEXT = {".md", ".txt", ".csv", ".tsv", ".json", ".yaml", ".yml", ".xml", ".log", ".ini", ".toml", ".js", ".ts", ".py",
        ".sh", ".mmd", ".puml", ".dot", ".sql", ".http"}
SKIP_DIRS = {".git", "node_modules", "__MACOSX", ".wrangler"}


def _xml_text(data, para_tags=("w:p", "a:p")):
    s = data.decode("utf-8", errors="ignore")
    for t in para_tags:
        s = s.replace("</%s>" % t, "\n")
    s = re.sub(r"<w:tab/>", "\t", s)
    s = re.sub(r"<[^>]+>", "", s)
    return html.unescape(s)


def _office(p):
    with zipfile.ZipFile(p) as z:
        names = z.namelist()
        if p.suffix.lower() == ".docx":
            parts = [n for n in names if re.match(r"word/(document|header\d*|footer\d*|footnotes)\.xml$", n)]
        elif p.suffix.lower() == ".pptx":
            parts = sorted((n for n in names if re.match(r"ppt/slides/slide\d+\.xml$", n)), key=lambda n: int(re.findall(r"\d+", n)[0]))
        else:   # xlsx: the shared strings, then each sheet's inline values
            parts = [n for n in names if n == "xl/sharedStrings.xml"] + sorted(n for n in names if re.match(r"xl/worksheets/sheet\d+\.xml$", n))
        return "\n".join("[%s]\n%s" % (n, _xml_text(z.read(n), ("w:p", "a:p", "si", "row"))) for n in parts)


def _eml(p):
    msg = email.message_from_bytes(p.read_bytes(), policy=email.policy.default)
    head = "\n".join("%s: %s" % (h, msg[h]) for h in ("From", "To", "Cc", "Date", "Subject") if msg[h])
    body, attached = [], []
    for part in msg.walk():
        if part.is_multipart():
            continue
        fn = part.get_filename()
        if fn:
            attached.append(fn); continue
        if part.get_content_type() in ("text/plain", "text/html"):
            t = part.get_content()
            if part.get_content_type() == "text/html":
                t = html.unescape(re.sub(r"<[^>]+>", " ", t))
            body.append(t)
    return head + "\n\n" + "\n".join(body) + ("\n\n[attachments: %s]" % ", ".join(attached) if attached else "")


def to_text(p):
    """(text or None, note). None: not converted, the agent reads the file itself."""
    ext = p.suffix.lower()
    try:
        if ext in TEXT or ext == "":
            raw = p.read_bytes()
            if b"\x00" in raw[:2048]:
                return None, "binary file"
            return raw.decode("utf-8", errors="replace"), ""
        if ext in (".html", ".htm"):
            return html.unescape(re.sub(r"<[^>]+>", " ", p.read_text(errors="replace"))), "html, tags removed"
        if ext == ".eml":
            return _eml(p), "e-mail"
        if ext in (".docx", ".xlsx", ".pptx"):
            return _office(p), "%s converted from its XML" % ext
        if ext == ".pdf":
            if shutil.which("pdftotext"):
                r = subprocess.run(["pdftotext", "-layout", str(p), "-"], capture_output=True, text=True, timeout=60)
                if r.returncode == 0 and r.stdout.strip():
                    return r.stdout, "pdf converted with pdftotext (a drawing may lose its layout: read the PDF itself too)"
            return None, "pdf not converted (no pdftotext): read the PDF itself"
    except Exception as e:  # never stop the build on one unreadable file
        return None, "not converted (%s)" % (str(e)[:120],)
    return None, "not converted (%s): read the file itself" % (ext or "no extension")


def combine(folder, out_md):
    """Write the folder as one Markdown brief. Returns (path, number of files, [(relative path, note)] not converted)."""
    folder = pathlib.Path(folder).resolve()
    files = sorted(p for p in folder.rglob("*") if p.is_file() and not (set(p.relative_to(folder).parts) & SKIP_DIRS)
                   and not p.name.startswith("."))
    out, missing = [], []
    out.append("# Case folder: %s\n\nEvery file of the folder follows, in path order, each under a header with its path "
               "relative to the folder. The original files are in %s.\n" % (folder.name, folder))
    for p in files:
        rel = p.relative_to(folder).as_posix()
        text, note = to_text(p)
        out.append("\n\n" + "=" * 24 + " FILE: %s%s " % (rel, (" (%s)" % note) if note else "") + "=" * 24 + "\n")
        if text is None:
            out.append("[not converted: read %s with the Read tool]\n" % p)
            missing.append((rel, note))
        else:
            out.append(text.rstrip() + "\n")
    out_md = pathlib.Path(out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("".join(out))
    return str(out_md), len(files), missing


def fetch_openapi(mock_url, out_json, timeout=30):
    """<mock_url>/openapi.json -> out_json with servers[0].url = mock_url. Raises on any failure."""
    base = mock_url.rstrip("/")
    req = urllib.request.Request(base + "/openapi.json", headers={"User-Agent": "build-the-builder"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        api = json.loads(r.read().decode("utf-8"))
    if not isinstance(api, dict) or not api.get("paths"):
        raise ValueError("%s/openapi.json has no paths" % base)
    api["servers"] = [{"url": base}] + [s for s in (api.get("servers") or []) if isinstance(s, dict) and s.get("url", "").rstrip("/") != base]
    out_json = pathlib.Path(out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(api, indent=1, ensure_ascii=False))
    return str(out_json)


def slot_name(folder):
    """A slot name from a folder name: lower case, [a-z0-9-] only."""
    s = re.sub(r"[^a-z0-9]+", "-", pathlib.Path(folder).resolve().name.lower()).strip("-")
    return s or "case"
