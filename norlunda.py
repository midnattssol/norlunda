#!/usr/bin/env python3.10
# pylint: disable=logging-fstring-interpolation
"""do all Norlunda sound changes.

Algorithm:
https://docs.google.com/document/d/1dwiVkmrtuwR9xIhsP0T7e86MQiujY83cwITTNi-KU8I/edit?usp=sharing
"""
import re
import logging
import functools as ft
import unicodedata
import collections as col
import dataclasses as dc
import typing as t

Q, W, E, R, T = map(t.TypeVar, "QWERT")

# Notes for developers:
# This IPA representation transcribes overlong vowels as "ɔːː",
# long vowels as "ɔː", and short vowels as "ɔ".
VOWELS = "iyuɪʏʊeøɘɵɤoəɛœɜɞʌɔæɐaɶɑɒ"
STOPS = "pbtdʈɖcɟkɡqɢʡʔ"
CONSONANTS = "ɸβθðszɣjwlrmnŋpbvtdkɡxŋʷ"
APPROXIMANTS = "wjzl"
CONSONANTS_NAPPROX = "".join(sorted(set(CONSONANTS) - {*APPROXIMANTS}))


def do_changed(func: callable, val: T) -> (bool, T):
    result = func(val)
    return result != val, result


@dc.dataclass
class Change:
    string: str
    result: str
    description: str
    rule: t.List[int]

    def __post_init__(self):
        self.rule = tuple(self.rule)

    def __str__(self):
        indent = (len(self.rule) - 1) * 2 * " "
        return (
            indent
            + f"* r{'-'.join(map(str, self.rule))}"
            + f" ({self.description}) applies (`/{self.string}/` -> `/{self.result}/`)"
        )


@dc.dataclass
class NorlundaChanger:
    word: str
    is_verb: bool = True
    log: list = dc.field(default_factory=list)
    rule: list = dc.field(default_factory=list)
    _initial: str = None

    def __post_init__(self):
        self._initial = self.word

    def do(self, fn, description, *a, **kw):
        self.rule[-1] += 1
        prev = self.word
        result = fn(*a, **kw)
        if description and prev != result:
            self.log.append(Change(prev, result, description, self.rule))
        self.word = result
        return self

    def do_all(self):
        """do all Norlunda sound changes."""
        self.rule = [0]
        self.do_sub("remove stress markers", "'", "")
        self.do_sub("normalize length markers", ":", "ː")

        # monad = ChangeLoggerMonad(self.word, log_infinitive=self.is_verb)
        self.do(self.vowel_weakening, "weaken vowels")
        self.do(a_umlaut, "do a-umlaut", is_verb=self.is_verb, root_ipa=self.word)
        self.do(
            a_umlaut_approximants,
            "do a-umlaut for approximants",
            is_verb=self.is_verb,
            word=self.word,
        )
        self.do(i_umlaut, "do i-umlaut", is_verb=self.is_verb, root_ipa=self.word)

        if self.is_verb:
            self.do(self.infinitive_merger, "merge infinitives")

        self.do(self.stem_merger, "merge stems")
        self.do(r_umlaut, "do r-umlaut", word=self.word)
        self.do(syllable_reduction, "reduce syllables", word=self.word)
        self.do(self.consonant_shortening, "shorten consonants")
        self.do(self.fricative_shift, "shift fricatives")
        self.do(self.vowel_shelving, "shelf vowels")

        self.rule = None
        return self.word

    def print_log(self):
        self.log = sorted(self.log, key=lambda x: x.rule)
        return (
            f"# Log for word *{self._initial}*" + "\n\n" + "\n".join(map(str, self.log))
        )

    def consonant_shortening(self):
        """Remove long consonants."""
        self.rule.append(0)
        self.do_sub(
            "shorten long consonants and replace a preceding e with æ",
            rf"e([{CONSONANTS}])\1+",
            r"æ\1",
        )
        self.do_sub(
            "shorten long consonants and replace a preceding u with o",
            rf"u([{CONSONANTS}])\1+",
            r"o\1",
        )
        self.do_sub("shorten long consonants", rf"([{CONSONANTS}])\1+", r"\1")
        self.rule.pop()
        return self.word

    def do_sub(self, description, *a, **kw):
        func = lambda: re.sub(*a, self.word, **kw)
        return self.do(func, description)

    def fricative_shift(self):
        self.rule.append(0)
        self.do_sub("b after a vowel becomes v", rf"([{VOWELS}]ː*)b", r"\1v")
        self.do_sub("b after a consonant becomes f", rf"([{CONSONANTS}])b", r"\1f")

        # h following a vowel or approximant, and not preceding a consonant
        # lengthens a preceding short vowel and the h is dropped
        self.do_sub(
            "h following a vowel is dropped after optionally lengthening a preceding short vowel",
            rf"([{VOWELS}])ː*h([{VOWELS}$])",
            r"\1ː\2",
        )
        self.do_sub(
            "h following an approximant is dropped",
            rf"([{APPROXIMANTS}])h([{VOWELS}$])",
            r"\1\2",
        )

        self.do_sub(
            "h following a vowel before a consonant becomes k",
            rf"([{VOWELS}]ː*)h([{CONSONANTS.replace('w', '')}])",
            r"\1k\2",
        )
        self.do_sub("þ becomes d", "þ", "d")
        self.do_sub("sk becomes sh after a stop consonant", rf"([{STOPS}])sk", r"\1ʃ")
        self.do_sub("sk becomes sh before a vowel", rf"sk([{VOWELS}])", r"ʃ\1")
        self.do_sub(
            "t following an approximant becomes ts (i.e. z)",
            f"([{APPROXIMANTS}])t",
            r"\1ts",
        )
        self.do_sub(
            "initial w before a consonant is dropped", rf"^w([{CONSONANTS}])", r"\1"
        )
        self.do_sub("w any other case becomes v", "w", "v")
        self.do_sub(
            "initial h before a consonant is dropped and the following vowel is raised",
            rf"h([{CONSONANTS}]+?)e",
            r"\1i",
        )
        self.do_sub(
            "initial h before a consonant is dropped and the following vowel is raised",
            rf"h([{CONSONANTS}]+?)o",
            r"\1u",
        )
        self.do_sub(
            "initial h before a consonant is dropped", rf"h([{CONSONANTS}])", r"\1"
        )

        self.rule.pop()
        return self.word

    def vowel_shelving(self):
        self.rule.append(0)
        self.do_sub("ā becomes /ɑɪ/", r"aː", r"ɑɪ")
        self.do_sub("æ becomes /eː/ when preceding r", r"æ(r)", r"eː\1")
        self.do_sub("ǣ becomes /æ/ or /ɑɪ/ when terminal", r"æː$", r"æ")
        self.do_sub("ai becomes /ɛ/ when preceding r", r"ai(r)", r"ɛ\1")
        self.do_sub("au becomes /oː/", r"au", r"oː")
        self.do_sub("e becomes /ɛ/", r"e(?!ː)", r"ɛ")
        self.do_sub("ī becomes /iː/", r"ɪː", r"iː")
        self.do_sub("i becomes /ɪ/", r"i(?=[^ː])", r"ɪ")
        self.do_sub("u becomes /ʊ/", r"u(?=[^ː])", r"ʊ")
        self.do_sub("eo becomes /ɑu/", r"eo", r"au")
        self.do_sub("iu becomes /eː/", r"iu", r"eː")
        self.rule.pop()
        return self.word

    def stem_merger(self):
        self.rule.append(0)
        self.do_sub("drop terminal -ja after stops", rf"([{STOPS}])ja$", r"\1")
        self.do_sub("drop terminal -az/-iz/-uz", r"[aiu]z$", r"")
        # This should only be dropped if used as a grammatical marker,
        # which is pretty hard to guess.
        self.do_sub("drop terminal -s if not preceded by h", r"(?<!h)s$", r"")
        self.do_sub(
            "replace j with i if preceded by a non-approximant consonant",
            rf"([{CONSONANTS_NAPPROX}])j$",
            r"\1i",
        )
        self.do_sub(
            "replace j with al if preceded by a non-approximant consonant",
            rf"([{CONSONANTS_NAPPROX}])l+$",
            r"\1al",
        )
        self.do_sub(
            "replace j with or if preceded by a non-approximant consonant",
            rf"([{CONSONANTS_NAPPROX}])r$",
            r"\1or",
        )
        self.do_sub(
            "replace j with u if preceded by a non-approximant consonant",
            rf"([{CONSONANTS_NAPPROX}])wj?$",
            r"\1u",
        )
        self.do_sub("replace terminal æu with aː", "æu$", "aː")
        self.do_sub("replace terminal eu with eː", "eu$", "eː")

        self.rule.pop()
        return self.word

    def infinitive_merger(self):
        """do the infinitive merger.

        This is not perfect and uses the rule of thumb that
        if the self.word is made up of 3+ syllables, -(V)na is removed,
        and otherwise -na is removed.
        """
        self.word, infinitive = split_off_infinitive(self.word)
        if not infinitive:
            return self.word
        return self.word + "an"

    def vowel_weakening(self):
        """do vowel weakening.

        - Overlong vowels become long.
        - Nasalized vowels de-nasalize.
        - Weak self.words (articles, conjunctions, prepositions) drop terminal vowels.
        """
        self.rule.append(0)
        self.do_sub("remove the nasal diacritic.", r"\u0303", "")
        self.do_sub("remove overlong vowels", r"ː+", "ː")

        # Note that the order of sound changes is important here.
        # If the umlauts are rearranged, it might for example do
        # a -> e -> i for one syllable which is not supposed to happen.
        self.do_sub("umlaut ai -> æː", r"aː*iː*", r"æː")
        self.do_sub("umlaut au -> oː", r"aː*uː*", r"oː")
        self.do_sub("umlaut eu -> ɔː", r"eː*uː*", r"ɔː")
        self.do_sub("umlaut iu -> eː", r"iː*uː*", r"eː")

        n_syllables = len(split_syllables(self.word))

        # Removes terminal vowels.
        if n_syllables == 1:
            self.do_sub(
                "shorten terminal long vowels for monosyllabic words", r"ː$", ""
            )
        if n_syllables == 2:
            self.do_sub(
                "drop terminal long vowels for disyllabic words",
                rf"[{VOWELS}][{VOWELS}ː]?$",
                "",
            )

        self.rule.pop()
        return self.word


# ===| Norlunda utilities |===


def romanized(root_ipa):
    """Transcribe Norlunda according to the romanization system."""
    root_ipa = re_sub_many(
        root_ipa,
        ("ɑi", "ei"),
        (r"ɑu", r"ou"),
        (r"[ɑɔ]", r"a"),
        (r"æː?", r"ae"),
        (r"ɛ", r"e"),
        (r"oː", r"o"),
        (r"(.)ː", r"\1\1"),
        (r"ː", r""),
        (r"ʊ", r"u"),
        (r"ts", r"z"),
        (r"ʃ", r"sh"),
        (r"ks", r"x"),
        (r"ŋ", r"ng"),
        (r"ɾ", "r"),
        (r"ɪ", "i"),
    )

    # The ɾ should not occur in the narrow transcription in this file,
    # but is included for completeness
    return root_ipa


def pgm_root_to_ipa(root_ipa):
    """Convert a Proto-Germanic root to IPA.

    This does not preserve nasalized vowels.
    """
    out = ""
    stack = col.deque(root_ipa.strip().lower().replace("ː", ":"))

    # Expand macrons, circumflexes, and ogoneks.
    functions = {
        r"macron": lambda x: x + "ː",
        r"circumflex": lambda x: x + "ːː",
        r"ogonek": lambda x: x,
    }

    while stack:
        character = stack.popleft()
        name = unicodedata.name(character)

        for fn_k, fn_v in functions.items():
            if (
                new_name := re.sub(f" (with|and) {fn_k}$", "", name, flags=re.I)
            ) != name:
                new_seq = unicodedata.lookup(new_name)
                new_seq = fn_v(new_seq)
                stack.extendleft(reversed(new_seq))
                break
        else:
            out += character

    return out


def split_grammatical_suffixes(word):
    v = filter(None, re.split("h?(az)$", word))
    return [*v, ""][:2]


def remove_infinitive_except_one_syllable(function):
    def inner(root_ipa):
        root_ipa, infinitive = split_off_infinitive(root_ipa)
        syllables = split_syllables(root_ipa)
        syllables = list(filter(None, syllables))

        infinitive = split_syllables(infinitive)
        if len(infinitive) > 1 and any(infinitive):
            i = next(filter(lambda x: x[1], enumerate(infinitive)))[0]
            syllables.append(infinitive[i])
            infinitive = "".join(infinitive[:i] + infinitive[i + 1 :])
        else:
            infinitive = infinitive[0]

        output = function("".join(syllables))

        if infinitive:
            output += infinitive
        return output

    return inner


def split_off_infinitive(word: str) -> [str, str]:
    """Get the infinitive suffix.

    The splitting syllable marker, if it exists,
    will always be with the suffix.
    """
    syllables = split_syllables(word)
    if match := re.search(rf"([{VOWELS}j]+)*na$", word):
        return word[: -len(match.group())], match.group()
    return word, ""


def split_syllables(word):
    out = word
    if re.match(rf"[{VOWELS}]", out):
        out = re.sub(f"(([{VOWELS}]ː*)+)", r".\1", out)
    else:
        out = re.sub(f"(([{VOWELS}]ː*)+)", r"\1.", out)
    out = out.strip(".")
    out = out.split(".")

    if len(out) < 2:
        return out

    if not re.search(f"[{VOWELS}]", out[-1]):
        val = out.pop()
        out[-1] += val

    return out


def re_sub_many(word: str, *regexes: [[str, str]]) -> str:
    """do a sequence of regexes to a word."""
    return ft.reduce(lambda left, right: re.sub(*right, left), regexes, word)


# ===| Sound changes |===


def a_umlaut_approximants(word, is_verb=True):
    infinitive = ""
    if is_verb:
        word, infinitive = split_off_infinitive(word)
    word = re.sub(r"i([jlrw])", r"e\1", word)
    word = re.sub(r"u([jlrw])", r"o\1", word)
    return word + infinitive


def umlaut_factory(name, trigger, subs):
    def inner(root_ipa):
        root_ipa, suffixes = split_grammatical_suffixes(root_ipa)
        # The items to consider are the root,
        # as well as the start of the infinitive prefix.
        syllables = split_syllables(root_ipa)
        syllables = list(filter(None, syllables))

        if len(syllables) == 1:
            return root_ipa

        # Shift the window one step so the syllable trigger
        # the one before it.
        syll_is_affected = map(trigger, syllables[1:])
        syll_is_affected = (*syll_is_affected, False)

        output = []
        for syllable, umlaut_triggered in zip(syllables, syll_is_affected):
            if not umlaut_triggered:
                output.append(syllable)
                continue
            for pattern, repl in subs:
                syllable = re.sub(pattern, repl, syllable)
            output.append(syllable)
        output = "".join(output)
        return output + suffixes

    def inner_(root_ipa, is_verb):
        # is_verb = root_ipa.endswith("an")
        if is_verb:
            return remove_infinitive_except_one_syllable(inner)(root_ipa)
        return inner(root_ipa)

    inner_.__name__ = name
    return inner_


a_umlaut = umlaut_factory(
    "a_umlaut",
    lambda x: re.match(f"[^{VOWELS}j]*[aoæ]", x),
    (
        (r"i(?![aoæ])", r"e"),
        (r"u(?![aoæ])", r"o"),
    ),
)


i_umlaut = umlaut_factory(
    "i_umlaut",
    lambda x: re.match(f"[^{VOWELS}j]*[iɪj]", x),
    [
        (r"e(?![yui])", r"i"),
        (r"a(?![yui])", r"e"),
    ],
)


def syllable_reduction(word):
    word = re.sub(r"aː*weː*", r"aː", word)
    word = re.sub(r"eː*w[eo]ː*", r"oː", word)
    word = re.sub(r"eː*wuː*", r"uː", word)

    syllables = split_syllables(word)

    if len(syllables) == 3:
        middle = syllables.pop(1)
        middle = re.sub(rf"h?[{VOWELS}]ː*", r"", middle)
        syllables[0] += middle
    elif len(syllables) == 2:
        syllables[1] = re.sub(r"h?[æeiu]ː*", r"", syllables[1])

    word = "".join(filter(None, syllables))
    word = re.sub(r"gs", r"ks", word)
    return word


def r_umlaut(word):
    word = re.sub("æ(z|s$)", "er", word)
    word = re.sub("i(z|s$)", "er", word)
    word = re.sub("ai(z|s$)", "eːr", word)
    word = re.sub("au(z|s$)", "or", word)
    word = re.sub("z", "r", word)
    word = re.sub(f"([{VOWELS}]ː*)s$", r"\1r", word)
    return word
