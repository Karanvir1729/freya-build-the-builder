#!/usr/bin/env python3
"""Check a deployed mock against every answer in the bank's test-customer file (status + body).
    python3 mock/verify.py <mock_url> <test-customers.json> [mock/services.json]"""
import json, sys, urllib.request, urllib.error, concurrent.futures as cf

def post(url, body, tries=4):
    import time
    for i in range(tries):
        req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                st, raw = r.status, r.read()
        except urllib.error.HTTPError as e:
            st, raw = e.code, e.read()
        try:
            return st, json.loads(raw or b"null")
        except ValueError:          # not JSON: Cloudflare's own error page (e.g. 1042 right after a deploy): retry
            time.sleep(2)
    return st, raw.decode(errors="replace")[:120]

def main(base, tc_path, svc_path="mock/services.json"):
    tc, svcs = json.load(open(tc_path)), json.load(open(svc_path))
    jobs = []
    for cu in tc["customers"]:
        for name, v in cu["services"].items():
            s = svcs[name]
            def add(path_keys, x):
                data = {}
                if s["customer"].endswith(".customerNo"):
                    data["customerNo"] = cu["customerNo"]
                else:
                    data["cardNumber"] = path_keys[0]
                if s.get("week"):
                    data["newStatementWeek"] = path_keys[-1]
                for f in s.get("required") or []:   # other required fields: any non-empty value
                    data.setdefault(f, {"intAddressInfoType": "E", "currencyType": "TL", "statementDay": 5}.get(f, "x"))
                jobs.append((name, path_keys, base.rstrip("/") + s["path"], {"data": data, "call": {"ani": "0", "lang": "tr"}}, x))
            def walk(x, keys):
                if isinstance(x, dict) and "http" in x:
                    add(keys, x); return
                for k, sub in x.items():
                    walk(sub, keys + [k])
            walk(v, [])
    bad = 0
    with cf.ThreadPoolExecutor(16) as ex:
        res = list(ex.map(lambda j: (j, post(j[2], j[3])), jobs))
    for (name, keys, url, body, want), (st, got) in res:
        exp = want.get("response", want.get("yanit"))
        if st != want["http"] or got != exp:
            bad += 1
            if bad <= 10:
                print("MISMATCH", name, keys, "status", st, "want", want["http"], json.dumps(got, ensure_ascii=False)[:160])
    print("%d of %d answers match" % (len(res) - bad, len(res)))
    return bad

if __name__ == "__main__":
    sys.exit(1 if main(*sys.argv[1:]) else 0)
