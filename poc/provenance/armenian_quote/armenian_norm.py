"""armenian_norm: quote matching for Armenian script, stdlib only (Python 3.9+).

The article's FIND step ("is the quote in the source as an unbroken run of lowercase words, ignoring punctuation and spacing") breaks on Armenian in
four places, all measured in notes/music-mashtots.md:
  1. str.lower() leaves U+0587 (ech-yiwn, "և") alone while the classical spelling writes the same letters as two code points "եւ"; casefold and NFKC both turn it into "եւ".
  2. \\w+ cuts a word at the Armenian marks U+055B/055C/055E ("Ի՞նչ" -> "Ի", "նչ"; "ինչո՞ւ" -> "ինչո", "ւ"), though they sit on a vowel inside the word.
  3. U+055A (Armenian apostrophe, "կ՚ապրիք") is not \\w but U+02BC (the modifier apostrophe a model may emit) is \\w, so the same elision tokenises two ways.
  4. Western (classical, Mesrobian) and Eastern (reformed) spelling differ letter by letter; a model that "corrects" a Western quote into the reformed spelling copies the words, not the letters.

Three tiers come out of `find`:
  verified  the quote's words are an unbroken run in the source after the basic fold (NFKC + casefold, marks and punctuation ignored)
  reworded  they are a run only after the orthography fold (classical and reformed spelling mapped to one skeleton); `quote_orthography` / `source_orthography` say which is which
  check     no run, either way
and a LOCATE span (character offsets into the ORIGINAL source string, never into the folded text).

The orthography fold is many-to-one on purpose (a skeleton, applied to both sides); it is an Estimate that an Armenian reader should check (see ORTHO_RULES and EXCEPTIONS).
"""
import re
import unicodedata

# U+055B emphasis, U+055C exclamation, U+055E question, U+055F abbreviation: they stand on a vowel inside a word, so they are deleted, not treated as a break.
GLUE = "\u055B\u055C\u055E\u055F"
# apostrophes: always a break (kept equal to the UD treebanks, which split "կ՚" from the verb). U+02BC and U+02BB are \w, so they are listed by hand.
APOSTROPHES = "\u055A\u0027\u2018\u2019\u02BC\u02BB\u0060\u00B4"


def _is_wordchar(ch):
    if ch in APOSTROPHES:
        return False
    cat = unicodedata.category(ch)
    return cat[0] in "LMN"          # letters (U+0559 modifier ring is Lm), combining marks, numbers


class Token:
    __slots__ = ("start", "end", "raw", "basic", "skel")

    def __init__(self, start, end, raw, basic, skel):
        self.start, self.end, self.raw, self.basic, self.skel = start, end, raw, basic, skel

    def __repr__(self):
        return "Token(%d,%d,%r,%r,%r)" % (self.start, self.end, self.raw, self.basic, self.skel)


def basic_fold(word):
    """NFKC, casefold, NFKC again (the order Unicode gives for caseless matching), then the glue marks removed."""
    w = unicodedata.normalize("NFKC", unicodedata.normalize("NFKC", word).casefold())
    return "".join(c for c in w if c not in GLUE)


# --- orthography fold: classical (Mesrobian, Western) and reformed (Eastern) spelling to one skeleton -------------------------------------------
# Applied in this order, to a word already basic-folded. Each rule is (name, regex, replacement). Estimate: rules written from the repo's own marker list
# (poc/mp_data.py _CLASSICAL/_REFORMED) and the standard description of the 1922/1940 reform; an Armenian reader should check them.
ORTHO_RULES = [
    ("inner e->e",  re.compile("(?<=.)\u0567"), "\u0565"),                           # non-initial է -> ե   ամէն / ամեն, մէկ / մեկ (first, so the rules below see the ե it makes: Հրէաստան)
    ("iw->yu",      re.compile("\u056B\u0582"), "\u0575\u0578\u0582"),               # իւ -> յու   classical ութիւն / reformed ություն, ճիւղ / ճյուղ
    ("ea->ya",      re.compile("\u0565\u0561"), "\u0575\u0561"),                      # եա -> յա    կեանք / կյանք, ամերիկեան / ամերիկյան
    ("oy->uy",      re.compile("\u0578\u0575"), "\u0578\u0582\u0575"),               # ոյ -> ույ   գոյն / գույն
    ("yiwn->v",     re.compile("(?<!\u0578)\u0582"), "\u057E"),                       # ւ not after ո -> վ   աւ -> ավ, եւ -> եվ (reformed և is NFKC-folded to եւ first)
]
# NOT in the default fold, measured and left out (notes/music-mashtots.md E3): word-initial յ + vowel -> հ (Յակոբ / Հակոբ) merges distinct Western words (հետ "with" / յետ "back") for +0.4 points of overlap.
OPTIONAL_RULES = [
    ("initial y",   re.compile("^\u0575(?=[\u0561\u0565\u0567\u0568\u056B\u0578\u0585])"), "\u0570"),
]
# whole words whose reform is not rule-shaped (lexical); kept tiny and visible
EXCEPTIONS = {
    "իւր": "իր",                                             # իւր -> իր
    "աստուած": "աստված",  # աստուած -> աստված
}


def ortho_fold(basic_word, rules=None):
    if basic_word in EXCEPTIONS:
        basic_word = EXCEPTIONS[basic_word]
    for _, rx, rep in (ORTHO_RULES if rules is None else rules):
        basic_word = rx.sub(rep, basic_word)
    return basic_word


def tokenize(text):
    """Tokens of `text` with offsets into the original string. A token is a run of word characters; glue marks stay inside a token (or beside it) and vanish from its keys;
    a run made only of glue marks yields no token."""
    out, i, n = [], 0, len(text)
    while i < n:
        if _is_wordchar(text[i]):
            j = i
            while j < n and (_is_wordchar(text[j]) or text[j] in GLUE):
                j += 1
            raw = text[i:j]
            b = basic_fold(raw)
            if b:
                out.append(Token(i, j, raw, b, ortho_fold(b)))
            i = j
        else:
            i += 1
    return out


# --- orthography label: which spelling is this text in -----------------------------------------------------------------------------------------
_CLASSICAL = [re.compile(p) for p in ("ութիւն", r"(?<![\w])եւ(?![\w])", "իւ", "եա", r"(?<=\w)է", "(?<!ու)ոյ")]       # mp_data.py:402, copied verbatim
_REFORMED = [re.compile(p) for p in ("ություն", "և", "յու", "ույ")]                                                  # mp_data.py:403


def orthography(text, strip_reform_ligature=False):
    """The repo's classical-vs-reformed marker score (mp_data.orthography), on the basic-folded words WITHOUT the ligature fold, so U+0587 still counts as a reformed marker
    unless `strip_reform_ligature` is set. Returns (label, score in -1..1)."""
    t = text.lower()[:4000]
    if strip_reform_ligature:
        t = t.replace("և", "եւ")
    c = sum(len(p.findall(t)) for p in _CLASSICAL)
    r = sum(len(p.findall(t)) for p in _REFORMED)
    score = (c - r) / (c + r + 1)
    return ("classical" if score >= 0.3 else "reformed" if score <= -0.3 else "unclear"), round(score, 3)


class Source:
    """A source text tokenised once: use it when many quotes are checked against one source (the ledger case)."""
    def __init__(self, text):
        self.text = text
        self.tokens = tokenize(text)
        self.basic = [t.basic for t in self.tokens]
        self.skel = [t.skel for t in self.tokens]
        self.orthography = orthography(text)[0]
        self._squash = {}

    def squashed(self, which):
        """(string of the keys run together, {offset where a token starts: its index}, {offset where a token ends: its index}); cached."""
        if which not in self._squash:
            keys = self.basic if which == "basic" else self.skel
            starts, ends, pos = {}, {}, 0
            for i, k in enumerate(keys):
                starts[pos] = i
                pos += len(k)
                ends[pos] = i
            self._squash[which] = ("".join(keys), starts, ends)
        return self._squash[which]


def _runs(hay, needle):
    """Start indices of `needle` (a list) inside `hay` (a list)."""
    if not needle:
        return []
    m, first = len(needle), needle[0]
    return [i for i in range(len(hay) - m + 1) if hay[i] == first and hay[i:i + m] == needle]


def find(quote, source, min_words=1):
    """FIND + LOCATE for one quote against one source (a str or a Source). Returns a dict:
       verdict    'verified' | 'reworded' | 'check'
       tier       'verbatim' | 'basic' | 'orthography' | 'spacing' | 'orthography+spacing' | None
       span       [start, end) in the source text (the first match), or None
       matches    how many times the run occurs (more than 1: the span is only the first, like the article's repeated-quote limit)
       n_words    words in the quote; a quote shorter than min_words is 'check' with reason 'too short'
       respelled  for tier 'orthography': [[quote word, source word], ...] (first 8), the words that were respelled
       quote_orthography, source_orthography   the repo's marker labels (a short quote often says 'unclear'; `respelled` is the evidence)"""
    src = source if isinstance(source, Source) else Source(source)
    qt = tokenize(quote)
    res = dict(verdict="check", tier=None, span=None, matches=0, n_words=len(qt), reason=None,
               quote_orthography=orthography(quote)[0], source_orthography=src.orthography)
    if len(qt) < max(1, min_words):
        res["reason"] = "too short" if qt else "no words"
        return res
    st = src.tokens
    hits = _runs(src.basic, [t.basic for t in qt])
    if hits:
        i = hits[0]
        verbatim = quote.strip() in src.text          # the same characters, not only the same folded words
        res.update(verdict="verified", tier="verbatim" if verbatim else "basic", span=[st[i].start, st[i + len(qt) - 1].end], matches=len(hits))
        return res
    hits = _runs(src.skel, [t.skel for t in qt])
    if hits:
        i = hits[0]
        diffs = [[q.raw, st[i + k].raw] for k, q in enumerate(qt) if q.basic != st[i + k].basic]
        res.update(verdict="reworded", tier="orthography", span=[st[i].start, st[i + len(qt) - 1].end], matches=len(hits), reason="spelling differs only by the classical/reformed fold",
                   respelled=diffs[:8])
        return res
    # last resort: the same letters with the spaces and apostrophes moved ("կ՚ապրիք" / "կապրիք", a mark split off a word), on whole-token boundaries only
    for which, tier, keys in (("basic", "spacing", [t.basic for t in qt]), ("skel", "orthography+spacing", [t.skel for t in qt])):
        big, starts, ends = src.squashed(which)
        needle, pos = "".join(keys), -1
        found = []
        while True:
            pos = big.find(needle, pos + 1)
            if pos < 0:
                break
            if pos in starts and pos + len(needle) in ends:
                found.append((starts[pos], ends[pos + len(needle)]))
        if found:
            i, j = found[0]
            res.update(verdict="reworded", tier=tier, span=[st[i].start, st[j].end], matches=len(found), reason="same letters; spaces or apostrophes differ" + (" and spelling differs by the fold" if which == "skel" else ""))
            return res
    res["reason"] = "no run of these words in the source"
    return res
