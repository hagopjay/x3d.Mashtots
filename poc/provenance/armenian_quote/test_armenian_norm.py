"""Tests for armenian_norm. Stdlib + pytest. The corpus test runs only when ARM_UD_DIR points at a folder holding hyw_armtdp-ud-dev.conllu (UD Western Armenian ArmTDP, CC BY-SA 4.0, not shipped)."""
import os, random, re, sys, unicodedata
import pytest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import armenian_norm as A

LIG = "\u0587"          # ech-yiwn
APOS = "\u055A"         # \u055A


def keys(s, which="basic"):
    return [getattr(t, which) for t in A.tokenize(s)]


# ---- the Unicode facts the design rests on (measured with Python 3.13, Unicode 15.1; a failure here means the platform changed) ----------------------
def test_unicode_facts():
    assert LIG.lower() == LIG                                  # lower() leaves the ligature alone
    assert LIG.casefold() == "եւ" == unicodedata.normalize("NFKC", LIG)
    assert unicodedata.normalize("NFC", LIG) == LIG != "եւ"   # NFC does not unify them
    assert LIG.upper() == "ԵՒ" and LIG.upper().lower() == "եւ" != LIG   # upper then lower does not round-trip
    assert all(chr(c).lower() == chr(c + 48) and chr(c + 48).upper() == chr(c) for c in range(0x531, 0x557))   # the 38 capitals are a plain +48
    for mark in "\u055A\u055B\u055C\u055D\u055E\u055F\u0589\u058A":
        assert not re.match(r"\w", mark)                      # all Armenian punctuation is a break for \w+
    assert re.match(r"\w", "\u0559") and re.match(r"\w", "\u02BC")   # but the modifier ring and the modifier apostrophe are word characters
    assert re.findall(r"\w+", "ինչո\u055Eւ") == ["ինչո", "ւ"]    # the regex cuts a word at its question mark


# ---- tokenizer -----------------------------------------------------------------------------------------------------------------------------------------
def test_ligature_and_case_fold_to_one_key():
    assert keys("Բար" + LIG) == keys("ԲԱՐԵՒ") == keys("բարեւ") == ["բարեւ"]


def test_marks_on_vowels_do_not_split_words():
    assert keys("Ի\u055Eնչ") == keys("Ինչ") == ["ինչ"]
    assert keys("ինչո\u055Eւ") == keys("ինչու") == ["ինչու"]
    assert keys("թե\u055B տղա") == ["թե", "տղա"]


def test_apostrophes_are_one_break():
    ref = ["կ", "ապրիք"]
    for sep in (APOS, "'", "\u2019", "\u02BC", " "):
        assert keys("կ" + sep + "ապրիք") == ref


def test_offsets_point_into_the_original_string():
    s = "  Ի\u055Eնչ   է, կ" + APOS + "ապրիք  "
    for t in A.tokenize(s):
        assert s[t.start:t.end] == t.raw
    assert [t.raw for t in A.tokenize(s)] == ["Ի\u055Eնչ", "է", "կ", "ապրիք"]


# ---- the orthography fold --------------------------------------------------------------------------------------------------------------------------------
# classical (Western) / reformed (Eastern) pairs written by Claude from the repo's marker list and the standard description: ESTIMATE, to be checked by an Armenian reader
PAIRS = [("ամէն", "ամեն"), ("մէկ", "մեկ"), ("սէր", "սեր"), ("կեանք", "կյանք"), ("ամերիկեան", "ամերիկյան"), ("գոյն", "գույն"), ("իշխանութիւն", "իշխանություն"),
         ("ճիւղ", "ճյուղ"), ("աւետարան", "ավետարան"), ("աւելի", "ավելի"), ("եւ", "եվ"), ("եւ", LIG), ("երեւան", "երև" + "ան"), ("բարեւ", "բար" + LIG),
         ("իւր", "իր"), ("աստուած", "աստված"), ("հրէաստան", "հրեաստան"), ("արարողութիւնը", "արարողությունը"), ("հարիւր", "հարյուր"), ("լաւ", "լավ")]


@pytest.mark.parametrize("classical,reformed", PAIRS)
def test_classical_and_reformed_share_a_skeleton(classical, reformed):
    assert keys(classical, "skel") == keys(reformed, "skel")


def test_fold_is_idempotent_on_pairs_and_marker_words():
    for a, b in PAIRS:
        for w in (a, b, a.upper()):
            k = A.basic_fold(w)
            assert A.ortho_fold(A.ortho_fold(k)) == A.ortho_fold(k)


def test_documented_misses_stay_documented():
    # these are NOT merged by the default fold (see OPTIONAL_RULES and the notes); if someone makes them merge, they must also look at the false merges
    assert keys("Յակոբ", "skel") != keys("Հակոբ", "skel")
    assert keys("հետ", "skel") != keys("յետ", "skel")                 # two Western words that the optional initial-յ rule would merge
    assert keys("ուզեր", "skel") == keys("ուզէր", "skel")             # a real collision: Western -եր (present) and -էր (past) fold together; hence 'reworded', never 'verified'


# ---- find: FIND, COMPARE-by-tier and LOCATE ------------------------------------------------------------------------------------------------------------
SRC = "Դուք քարանձաւային դարաշրջանի մէջ կ" + APOS + "ապրիք,- ըսաւ Հայաստանէն Հալէպ այցի եկած նախկին հալէպահայ մը:"


def test_verbatim_and_basic():
    r = A.find("մէջ կ" + APOS + "ապրիք", SRC)
    assert (r["verdict"], r["tier"]) == ("verified", "verbatim") and SRC[slice(*r["span"])] == "մէջ կ" + APOS + "ապրիք"
    r = A.find("ՄԷՋ  կ'ապրիք", SRC)
    assert (r["verdict"], r["tier"]) == ("verified", "basic") and SRC[slice(*r["span"])] == "մէջ կ" + APOS + "ապրիք"


def test_ligature_is_verified_not_reworded():
    src = "Բարեւ ձեզ եւ ողջոյն"
    assert A.find("ձեզ " + LIG + " ողջոյն", src)["verdict"] == "verified"
    assert A.find("ձեզ եւ ողջոյն", "Բարև ձեզ " + LIG + " ողջոյն")["verdict"] == "verified"


def test_reformed_quote_of_a_classical_source_is_reworded_with_orthography_labels():
    q = "քարանձավային դարաշրջանի մեջ կ" + APOS + "ապրիք"
    r = A.find(q, SRC)
    assert (r["verdict"], r["tier"]) == ("reworded", "orthography")
    assert SRC[slice(*r["span"])] == "քարանձաւային դարաշրջանի մէջ կ" + APOS + "ապրիք"
    assert r["source_orthography"] == "classical"
    assert r["respelled"] == [["քարանձավային", "քարանձաւային"], ["մեջ", "մէջ"]]               # which words were respelled, quote word first


def test_spacing_tier():
    r = A.find("կապրիք ըսաւ", SRC)
    assert (r["verdict"], r["tier"]) == ("reworded", "spacing") and SRC[slice(*r["span"])] == "կ" + APOS + "ապրիք,- ըսաւ"
    r = A.find("կապրիք ըսավ", SRC)
    assert (r["verdict"], r["tier"]) == ("reworded", "orthography+spacing")
    assert A.find("ապրի", SRC)["verdict"] == "check"                      # a word cut in half is not a quote of the word
    assert A.find("րիք", SRC)["verdict"] == "check"                       # nor is the tail of a word (the squashed match must start on a token start too)


def test_check_and_edges():
    assert A.find("քարանձաւային դարաշրջանի կ" + APOS + "ապրիք", SRC)["verdict"] == "check"     # words dropped in the middle: not a run
    assert A.find("", SRC)["reason"] == "no words" and A.find("   \u0589 ", SRC)["verdict"] == "check"
    assert A.find("մէջ", SRC, min_words=2)["reason"] == "too short"
    r = A.find("ու", "ու և ու եւ ու")
    assert r["matches"] == 3 and r["span"] == [0, 2]                            # repeated quote: first occurrence, and the count says it was ambiguous


def test_source_object_is_reusable_and_equal():
    S = A.Source(SRC)
    assert A.find("կ" + APOS + "ապրիք ըսաւ", S) == A.find("կ" + APOS + "ապրիք ըսաւ", SRC)


# ---- real text (skipped when the treebank is absent) ----------------------------------------------------------------------------------------------------------
UD = os.environ.get("ARM_UD_DIR")


@pytest.mark.skipif(not UD or not os.path.exists(os.path.join(UD or "", "hyw_armtdp-ud-dev.conllu")), reason="ARM_UD_DIR not set")
def test_real_western_text_windows():
    sents = [l.split("=", 1)[1].strip() for l in open(os.path.join(UD, "hyw_armtdp-ud-dev.conllu"), encoding="utf-8") if l.startswith("# text =")]
    pages = ["\n".join(sents[i:i + 20]) for i in range(0, len(sents) - 19, 20)]
    rnd, n_ok, n = random.Random(1), 0, 0
    for _ in range(300):
        p = rnd.choice(pages)
        S = A.Source(p)
        if len(S.tokens) < 10:
            continue
        i = rnd.randint(0, len(S.tokens) - 6)
        q = p[S.tokens[i].start:S.tokens[i + 4].end]
        r = A.find(q.upper().replace("եւ", LIG), S)             # shouted, ligature typed
        n += 1
        n_ok += r["verdict"] == "verified" and r["span"][0] <= S.tokens[i].start
        assert [t.basic for t in A.tokenize(p[r["span"][0]:r["span"][1]])] == [t.basic for t in A.tokenize(q)]
    assert n > 250 and n_ok == n
