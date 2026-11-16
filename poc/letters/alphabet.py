#!/usr/bin/env python3
"""The 39 symbols of the letter constellation: Mashtots' 36 letters, the two later arrivals (Օ, Ֆ) and the ligature և.

Every row carries what the scene and the analysis need: alphabet order, upper and lower case, numeral value, the classical
letter name, the sound in Eastern and in Western Armenian (IPA), the phonetic set it belongs to, and whether the 1920s-40s
spelling reform changed how it is used.

Grades
* order, case, numeral values: Established (Unicode block U+0531..U+0587, the additive numeral system; checked in ../../numerals/).
* names and IPA: Established in standard descriptions, but typed here by Claude. An Armenian reader should check every row
  before anything is published (the repo README asks the same for all Armenian text).
* "reform" flags: Claude's summary of the classical vs reformed spelling differences; Estimate until a reader checks.

No third-party imports, so mp_* modules, the notebook cells and the scene builder can all use it.
"""
from __future__ import annotations

import sys

# alphabet order, upper case; matches mp_common.MASHTOTS_36 + LATER_2
MASHTOTS_36 = "ԱԲԳԴԵԶԷԸԹԺԻԼԽԾԿՀՁՂՃՄՅՆՇՈՉՊՋՌՍՎՏՐՑՒՓՔ"
LATER_2 = "ՕՖ"
LIGATURE = "և"          # ե + ւ; a ligature in classical spelling (Western), a letter of its own in the reformed spelling (Eastern)

# (upper, classical name, Eastern IPA, Western IPA). Western shifts: the old voiced stops and affricates became aspirated,
# the old plain voiceless ones became voiced, so Western Պետրոս is "Bedros" and Eastern is "Petros".
_ROWS = [
    ("Ա", "այբ", "ɑ", "ɑ"),
    ("Բ", "բեն", "b", "pʰ"),
    ("Գ", "գիմ", "ɡ", "kʰ"),
    ("Դ", "դա", "d", "tʰ"),
    ("Ե", "եչ", "ɛ, jɛ-", "ɛ, jɛ-"),
    ("Զ", "զա", "z", "z"),
    ("Է", "է", "ɛ", "ɛ"),
    ("Ը", "ըթ", "ə", "ə"),
    ("Թ", "թօ", "tʰ", "tʰ"),
    ("Ժ", "ժէ", "ʒ", "ʒ"),
    ("Ի", "ինի", "i", "i"),
    ("Լ", "լիւն", "l", "l"),
    ("Խ", "խէ", "χ", "χ"),
    ("Ծ", "ծա", "ts", "dz"),
    ("Կ", "կեն", "k", "ɡ"),
    ("Հ", "հօ", "h", "h"),
    ("Ձ", "ձա", "dz", "tsʰ"),
    ("Ղ", "ղատ", "ʁ", "ʁ"),
    ("Ճ", "ճէ", "tʃ", "dʒ"),
    ("Մ", "մէն", "m", "m"),
    ("Յ", "յի", "j", "j, h-"),
    ("Ն", "նու", "n", "n"),
    ("Շ", "շա", "ʃ", "ʃ"),
    ("Ո", "ո", "vɔ-, ɔ", "vɔ-, ɔ"),
    ("Չ", "չա", "tʃʰ", "tʃʰ"),
    ("Պ", "պէ", "p", "b"),
    ("Ջ", "ջէ", "dʒ", "tʃʰ"),
    ("Ռ", "ռա", "r", "r"),
    ("Ս", "սէ", "s", "s"),
    ("Վ", "վեւ", "v", "v"),
    ("Տ", "տիւն", "t", "d"),
    ("Ր", "րէ", "ɾ", "ɾ"),
    ("Ց", "ցօ", "tsʰ", "tsʰ"),
    ("Ւ", "հիւն", "v (in ու: u)", "v (in ու: u)"),
    ("Փ", "փիւր", "pʰ", "pʰ"),
    ("Ք", "քէ", "kʰ", "kʰ"),
    ("Օ", "օ", "ɔ", "ɔ"),
    ("Ֆ", "ֆէ", "f", "f"),
]

# the five three-way sets of stops and affricates, by place of articulation (Eastern: voiced, plain, aspirated)
TRIADS = {
    "lips": "ԲՊՓ",
    "back of the tongue": "ԳԿՔ",
    "teeth": "ԴՏԹ",
    "teeth, hissing": "ՁԾՑ",
    "palate, hushing": "ՋՃՉ",
}
# letters whose use differs between the classical (Western) and reformed (Eastern) spelling (Estimate; see the module note)
REFORM = {
    "Ւ": "classical իւ / աւ / եւ, reformed յու / օ / և",
    "Յ": "classical word-initial յ (Յակոբ), reformed հ (Հակոբ)",
    "Է": "classical է inside words, reformed ե",
    "Ե": "takes over from է in the reformed spelling",
    "Օ": "classical աւ, reformed օ",
    "Ո": "classical ո / ով, reformed վո- word-initially",
    "Վ": "reformed վ where classical writes ւ",
    LIGATURE: "classical ե + ւ written as one sign; a letter of its own in the reformed spelling",
}
LATIN_NAME = {"Ա": "ayb", "Բ": "ben", "Գ": "gim", "Դ": "da", "Ե": "yech", "Զ": "za", "Է": "e", "Ը": "et", "Թ": "to", "Ժ": "zhe",
              "Ի": "ini", "Լ": "lyun", "Խ": "khe", "Ծ": "tsa", "Կ": "ken", "Հ": "ho", "Ձ": "dza", "Ղ": "ghat", "Ճ": "che",
              "Մ": "men", "Յ": "hi", "Ն": "nu", "Շ": "sha", "Ո": "vo", "Չ": "cha", "Պ": "pe", "Ջ": "je", "Ռ": "ra", "Ս": "se",
              "Վ": "vev", "Տ": "tyun", "Ր": "re", "Ց": "tso", "Ւ": "hyun", "Փ": "pyur", "Ք": "ke", "Օ": "o", "Ֆ": "fe",
              LIGATURE: "yev"}


def lower(c):
    return c if c == LIGATURE else chr(ord(c) + 48)          # U+0531..0556 -> U+0561..0586


def numeral(i):
    return (i % 9 + 1) * 10 ** (i // 9) if i < 36 else None


def table():
    """39 dicts in alphabet order: the 36, then Օ, Ֆ, then և."""
    rows = []
    triad_of = {c: k for k, s in TRIADS.items() for c in s}
    for i, (up, name, e, w) in enumerate(_ROWS):
        rows.append(dict(index=i, upper=up, lower=lower(up), name=name, latin=LATIN_NAME[up], numeral=numeral(i),
                         group="mashtots" if i < 36 else "later", ipa_east=e, ipa_west=w, sound_differs=e != w,
                         triad=triad_of.get(up), reform=REFORM.get(up)))
    rows.append(dict(index=38, upper="ԵՒ", lower=LIGATURE, name="եւ", latin=LATIN_NAME[LIGATURE], numeral=None, group="ligature",
                     ipa_east="jɛv, ɛv", ipa_west="jɛv, ɛv", sound_differs=False, triad=None, reform=REFORM[LIGATURE],
                     parts=["Ե", "Ւ"]))
    return rows


def self_test():
    t = table()
    assert len(t) == 39, len(t)
    assert "".join(r["upper"] for r in t[:36]) == MASHTOTS_36
    assert "".join(r["upper"] for r in t[36:38]) == LATER_2
    assert [r["numeral"] for r in t[:9]] == list(range(1, 10)) and t[35]["numeral"] == 9000
    assert sum(r["numeral"] for r in t[:36]) == 49995                         # 45 x 1111, as in ../../numerals/README.md
    assert all(r["lower"] == chr(ord(r["upper"]) + 48) for r in t[:38])
    assert sum(len(s) for s in TRIADS.values()) == 15 and all(r["triad"] for r in t if r["upper"] in "".join(TRIADS.values()))
    # the Western shift swaps the first two members of every set and leaves the aspirate alone (the standard description)
    by = {r["upper"]: r for r in t[:38]}
    for s in TRIADS.values():
        assert by[s[2]]["ipa_east"] == by[s[2]]["ipa_west"], s
        assert by[s[0]]["ipa_west"] == by[s[2]]["ipa_west"], s                # Western voiced -> aspirated (merges with the third)
    print("alphabet self-test: 39 symbols, numerals sum 49,995, 5 sets of 3, Western shift consistent")


if __name__ == "__main__":
    self_test() if "--test" in sys.argv else print("\n".join(f"{r['index']:>2} {r['upper']} {r['lower']} {r['name']:<5} {r['numeral'] or '':>5} "
                                                          f"E {r['ipa_east']:<8} W {r['ipa_west']:<8} {r['triad'] or ''}" for r in table()))
