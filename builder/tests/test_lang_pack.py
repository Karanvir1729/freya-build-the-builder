"""Table test of freyalib.lang_code('tr'): the language-pack helpers a code node pastes in (parse the caller's
number/ordinal/date words, say numbers/amounts/dates, match items). Execs the source as a code node would (one dict,
then separate globals/locals), checks no '{{'/'}}' and that compact_code keeps it compilable.

    python3 builder/tests/test_lang_pack.py
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import freyalib as fl  # noqa: E402

SRC = fl.lang_code("tr")
assert "{{" not in SRC and "}}" not in SRC
compile(fl.compact_code(SRC), "<lang>", "exec")

NOW = "2026-10-14T11:00:00+03:00"     # a Wednesday, local wall-clock time

CASES = [
    ("words_to_int", ("iki bin yüz kırk",), 2140),
    ("words_to_int", ("on iki bin",), 12000),
    ("words_to_int", ("bin",), 1000),
    ("words_to_int", ("yüz",), 100),
    ("words_to_int", ("beş yüz elli lira",), 550),
    ("words_to_int", ("12.000 TL",), 12000),
    ("words_to_int", ("12 bin",), 12000),
    ("words_to_int", ("üç milyon iki yüz bin",), 3200000),
    ("words_to_int", ("ödeyebileceğim tutar dört yüz yirmi beş",), 425),
    ("words_to_int", ("DÖRT",), 4),
    ("words_to_int", ("dort yuz",), 400),
    ("words_to_int", ("ikibinyüzkırk",), 2140),
    ("words_to_int", ("hiçbir fikrim yok",), None),
    ("words_to_int", ("",), None),
    ("words_to_int", (None,), None),
    ("spoken_digits", ("dört iki beş üç",), "4253"),
    ("spoken_digits", ("kırk iki elli üç",), "4253"),
    ("spoken_digits", ("4 2 5 3",), "4253"),
    ("spoken_digits", ("sıfır beş otuz iki",), "0532"),
    ("spoken_digits", ("dört yüz yirmi beş üç",), "4253"),
    ("spoken_digits", ("numaram 12 34",), "1234"),
    ("spoken_digits", ("bilmiyorum",), None),
    ("ordinal_in", ("üçüncü hafta", 4), 3),
    ("ordinal_in", ("3. hafta", 4), 3),
    ("ordinal_in", ("ilk seçenek", 3), 1),
    ("ordinal_in", ("ikinciyi istiyorum", 3), 2),
    ("ordinal_in", ("dördüncü", 4), 4),
    ("ordinal_in", ("dördüncü", 3), None),
    ("ordinal_in", ("sonuncu", 5), 5),
    ("ordinal_in", ("iki numara", 3), 2),
    ("ordinal_in", ("on ikinci", 12), 12),
    ("ordinal_in", ("hiçbiri", 3), None),
    ("say_number", (0,), "sıfır"),
    ("say_number", (1000,), "bin"),
    ("say_number", (2140,), "iki bin yüz kırk"),
    ("say_number", (12000,), "on iki bin"),
    ("say_number", (101001,), "yüz bir bin bir"),
    ("say_number", (1500000,), "bir milyon beş yüz bin"),
    ("say_number", ("x",), None),
    ("say_amount", (85.2, "EUR"), "seksen beş euro yirmi sent"),
    ("say_amount", (12000, "TL"), "on iki bin Türk Lirası"),
    ("say_amount", (420.5, "TRY"), "dört yüz yirmi Türk Lirası elli kuruş"),
    ("say_amount", (99.99, "USD"), "doksan dokuz dolar doksan dokuz sent"),
    ("say_amount", (1, "GBP"), "bir sterlin"),
    ("say_amount", (0.05, "GBP"), "sıfır sterlin beş peni"),
    ("say_amount", ("abc", "EUR"), None),
    ("say_date", ("2026-11-05",), "5 Kasım 2026"),
    ("say_date", ("05.11.2026",), "5 Kasım 2026"),
    ("say_date", ("2026-10-14T11:00:00+03:00",), "14 Ekim 2026"),
    ("say_date", ("2026-10-16", True), "16 Ekim 2026 Cuma"),
    ("say_date", ("yarın",), None),
    ("resolve_day", ("bugün", NOW), "2026-10-14"),
    ("resolve_day", ("yarın ödeyeceğim", NOW), "2026-10-15"),
    ("resolve_day", ("öbür gün", NOW), "2026-10-16"),
    ("resolve_day", ("ertesi gün", NOW), "2026-10-16"),
    ("resolve_day", ("dün ödedim", NOW), "2026-10-13"),
    ("resolve_day", ("cuma", NOW), "2026-10-16"),
    ("resolve_day", ("cumaya kadar", NOW), "2026-10-16"),
    ("resolve_day", ("cumartesi", NOW), "2026-10-17"),
    ("resolve_day", ("pazartesi", NOW), "2026-10-19"),
    ("resolve_day", ("çarşamba", NOW), "2026-10-21"),
    ("resolve_day", ("haftaya salı", NOW), "2026-10-20"),
    ("resolve_day", ("gelecek hafta cuma", NOW), "2026-10-23"),
    ("resolve_day", ("bu hafta cuma", NOW), "2026-10-16"),
    ("resolve_day", ("haftaya", NOW), "2026-10-21"),
    ("resolve_day", ("15 Ekim", NOW), "2026-10-15"),
    ("resolve_day", ("on beş ekimde", NOW), "2026-10-15"),
    ("resolve_day", ("5 Kasım 2026", NOW), "2026-11-05"),
    ("resolve_day", ("1 ekim", NOW), "2027-10-01"),
    ("resolve_day", ("20.10", NOW), "2026-10-20"),
    ("resolve_day", ("20/10/2026", NOW), "2026-10-20"),
    ("resolve_day", ("üç gün sonra", NOW), "2026-10-17"),
    ("resolve_day", ("iki hafta sonra", NOW), "2026-10-28"),
    ("resolve_day", ("ayın yirmisi", NOW), "2026-10-20"),
    ("resolve_day", ("ayın 10'u", NOW), "2026-11-10"),
    ("resolve_day", ("bugün", "2026-12-31T23:30:00-05:00"), "2026-12-31"),
    ("resolve_day", ("yarın", "2026-12-31T23:30:00-05:00"), "2027-01-01"),
    ("resolve_day", ("bilmiyorum", NOW), None),
    ("resolve_day", ("yarın", "bad"), None),
    ("yes_no", ("Evet, onaylıyorum.",), "yes"),
    ("yes_no", ("hayır istemiyorum",), "no"),
    ("yes_no", ("tamam değil",), "no"),
    ("yes_no", ("belki",), None),
]

ITEMS = [{"name": "Kredi Kartı", "digits": "4253"}, {"name": "Vadesiz Hesap", "digits": "TR12 0006 1234"},
         {"name": "İhtiyaç Kredisi", "digits": "7781"}]
MATCH = [
    ("kredi kartım", [0]),
    ("kartımın son dört hanesi dört iki beş üç", [0]),
    ("vadesiz hesabım", [1]),
    ("sonu bir iki otuz dört olan", [1]),
    ("ihtiyaç kredim", [2]),
    ("IHTIYAC KREDISI", [2]),
    ("kredi", [0, 2]),
    ("yetmiş yedi seksen bir", [2]),
    ("hiçbiri", []),
]


def run(env):
    bad = 0
    for fn, args, want in CASES:
        got = env[fn](*args)
        if got != want:
            bad += 1
            print("FAIL %s%r -> %r, want %r" % (fn, args, got, want))
    for text, want in MATCH:
        got = env["match_items"](text, ITEMS, "name", "digits")
        if got != want:
            bad += 1
            print("FAIL match_items(%r) -> %r, want %r" % (text, got, want))
    assert env["match_items"]("kart", None) == []
    assert env["match_items"]("kart", ["Kredi Kartı", "Hesap"]) == [0]
    return bad


g = {}
exec(SRC, g)
bad = run(g)
g2, l2 = {}, {}
exec(SRC, g2, l2)
bad += run(l2)
try:
    fl.lang_code("xx")
    raise SystemExit("lang_code('xx') must raise")
except ValueError:
    pass
n = 2 * (len(CASES) + len(MATCH))
print("lang pack: %d/%d cases pass" % (n - bad, n))
assert bad == 0
