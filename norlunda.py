#!/usr/bin/env python3.10
"""Apply all Norlunda sound changes."""
import re
import typing as t
import dataclasses as dc
import collections as col
import unicodedata
import functools as ft
import unidecode


# Notes for developers:
# This IPA representation transcribes overlong vowels as "ɔːː",
# long vowels as "ɔː", and short vowels as "ɔ".


# print("a" + )
# print("ɑ̃"[1].encode("utf-8"))
# k = unicodedata.normalize("NFC", "ɑ̃").encode("utf-8")
# print(k)
# exit()
# Word = col.namedtuple("Word", ("syllables", "is_strong"))
# Syllable = col.namedtuple("Syllable", ("sounds", "is_stressed"))

# BUG: they appear to be correct but contain special characters
VOWELS = "iyɨʉɯuɪʏʊeøɘɵɤoe̞ø̞əɤ̞o̞ɛœɜɞʌɔæɐaɶäɑɒ"
STOPS = "pbp̪b̪t̼d̼t̪d̪tdʈɖcɟkɡqɢʡʔ"


def soundchanges(root_ipa, is_strong=True, is_verb=True):
    """Apply all Norlunda sound changes."""
    # root_ipa = _pgm_root_to_ipa(word)
    root_ipa = unidecode.unidecode(root_ipa)
    root_ipa = vowel_weakening(root_ipa, is_strong)
    root_ipa = a_umlaut(root_ipa)
    root_ipa = i_umlaut(root_ipa)
    if is_verb:
        root_ipa = infinitive_merger(root_ipa)
    root_ipa = stem_merger(root_ipa)
    root_ipa = r_umlaut(root_ipa)
    root_ipa = syllable_reduction(root_ipa)
    root_ipa = consonant_shortening(root_ipa)
    root_ipa = fricative_shift(root_ipa)
    root_ipa = vowel_shelving(root_ipa)
    return root_ipa


def consonant_shortening(word):
    word = re.sub(rf"e([^{VOWELS}.])(\.?)(\.?\1)+", r"æ\1\2", word)
    word = re.sub(rf"u([^{VOWELS}.])(\.?)(\.?\1)+", r"o\1\2", word)
    word = re.sub(rf"([^{VOWELS}.])(\.?)(\.?\1)+", r"\1\2", word)
    return word


def fricative_shift(word):
    # b after a vowel becomes v
    # b after a consonant becomes f
    word = re.sub(rf"([{VOWELS}]ː*\.?)b", r"\1v", word)
    word = re.sub(rf"([^{VOWELS}.]\.?)b", r"\1f", word)

    # h following a vowel or approximate, and not preceding a consonant.
    # lengthens a preceding short vowel and the h is dropped.
    word = re.sub(rf"([{VOWELS}]ː*\.?)([wjl]*\.?)h(\.?[{VOWELS}])", r"\1ː\2\3", word)
    word = re.sub(rf"([{VOWELS}]ː*\.?)h(\.?[^{VOWELS}.])", r"\1k\2", word)

    # þ becomes d
    word = re.sub("þ", "d", word)

    # sk becomes sh before a vowel and after a stop consonant
    word = re.sub(rf"([{STOPS}]\.?)sk(\.?[{VOWELS}])", r"\1sh\2", word)

    # t following an approximate becomes ts (i.e. z)
    word = re.sub("([wjz])t", "ts", word)

    # initial w before a consonant is dropped
    word = re.sub(rf"^w[^.{VOWELS}]", r"", word)

    # w any other case becomes v
    word = re.sub("w", "v", word)

    # initial h before a consonant is dropped and the following vowel is raised
    # - e becomes i
    # - o becomes u
    word = re.sub(f"h([^{VOWELS}]+?)e", "\1i", word)
    word = re.sub(f"h([^{VOWELS}]+?)o", "\1u", word)
    word = re.sub(f"h([^{VOWELS}])", "\1", word)
    return word


# print(fricative_shift("leːben"))
# print(fricative_shift("þonor"))


def vowel_shelving(word):
    # ā becomes /ɑɪ/
    # æ becomes /eː/ when preceding r
    # ǣ becomes /æ/ or /ɑɪ/ when terminal
    # ai becomes /ɛ/ when preceding r
    word = re.sub(r"aː", r"ɑɪ", word)
    word = re.sub(r"æ(\.?r)", r"eː\1", word)
    word = re.sub(r"æː$", r"æ", word)
    word = re.sub(r"ai(\.?r)", r"ɛ\1", word)

    # au becomes /oː/
    # e becomes /ɛ/
    # ē becomes /eː/
    # i becomes /ɪ/
    word = re.sub(r"au", r"oː", word)
    word = re.sub(r"e(?=[^ː])", r"ɛ", word)

    # ī becomes /iː/
    # semantic difference is lost between o and ō
    # u becomes /ʊ/
    # ū becomes /uː/
    # eo becomes /ɑu/
    # iu becomes /eː/
    word = re.sub(r"ɪː", r"iː", word)
    word = re.sub(r"i(?=[^ː])", r"ɪ", word)
    word = re.sub(r"oː", r"o", word)
    word = re.sub(r"u(?=[^ː])", r"ʊ", word)
    word = re.sub(r"eo", r"au", word)
    word = re.sub(r"iu", r"eː", word)

    return word


# b after a vowel becomes v
# b after a consonant becomes f
# h following a vowel or approximate, and not preceding a consonant lengthens a preceding short vowel and the h is dropped
# h following a vowel before a consonant becomes k
# þ becomes d
# sk becomes sh before a vowel and after a stop consonant
# t following an approximate becomes ts (i.e. z)
# initial w before a consonant is dropped
# w any other case becomes v
# initial h before a consonant is dropped and the following vowel is raised
# e becomes i
# o becomes u

# print(consonant_shortening("soll"))
# print(consonant_shortening("sull"))
# print(consonant_shortening("sul"))
# exit()


def stem_merger(word):
    word = re.sub(rf"([{STOPS}])\.ja$", r"\1", word)
    word = re.sub(r"\.[aiu]z$", r"", word)
    word = re.sub(r"\.s$", r"", word)
    word = re.sub(r"\.j", r"i", word)
    word = re.sub(r"\.l", r"al", word)
    word = re.sub(r"\.r", r"or", word)
    word = re.sub(r"\.wj?", r"u", word)

    word = re.sub("æu$", "aː", word)
    word = re.sub("eu$", "eː", word)

    return word


# æw becomes ā
# ew becomes ē
#
# All terminal vowels (including -ja after stop consonants) are dropped. The suffixes -az, -iz, and -uz are dropped if they constitute their own syllable, as well as -s if it is being used as a grammatical marker. It may be necessary to look at descendant words to determine whether to treat -s as grammatical.
# Any remaining terminal approximates (j, l, r, w, and wj) become respectively i, al, or, u, and u. If a resulting u follows a vowel, it is absorbed such that…
# æw becomes ā
# ew becomes ē


def infinitive_merger(word):
    """Apply the infinitive merger.

    This is not perfect and uses the rule of thumb that
    if the word is made up of 3+ syllables, -(V)na is removed,
    and otherwise -na is removed.
    """
    syllables = re.split(r"\.", word)
    n_syllables = len(syllables)

    if n_syllables <= 2:
        word = re.sub(r"na$", r"an", word)
        return word

    word = re.sub(rf"([{VOWELS}j]+\.)*na$", r"an", word)
    return word


def vowel_weakening(word, is_strong):
    """Apply vowel weakening.

    - Overlong vowels become long.
    - Nasalized vowels de-nasalize.
    - Weak words (articles, conjunctions, prepositions) drop terminal vowels.
    """

    word = re.sub(r"\u0303", "", word)  # Removes the nasal diacritic.
    word = re.sub(r"ː+", "ː", word)  # Removes overlong vowels.
    if not is_strong:
        # Removes terminal vowels, as well as a potential
        # syllable break
        word = re.sub(rf"\.?([{VOWELS}]ː*)*", "", word)

    return word


def umlaut_factory(trigger, subs):
    def inner(root_ipa):
        syllables = re.split(r"\.", root_ipa)

        if len(syllables) == 1:
            return root_ipa

        # Skip the first one to align the syllables.
        syll_is_affected = map(trigger, syllables[1:])
        syll_is_affected = (*syll_is_affected, False)
        syll_is_affected = list(syll_is_affected)

        output = []
        for syllable, a_umlaut_triggered in zip(syllables, syll_is_affected):
            if not a_umlaut_triggered:
                output.append(syllable)
                continue

            # print(f"Triggered in {syllable!r}")
            for k, v in subs:
                syllable = re.sub(k, v, syllable)
            output.append(syllable)
        output = ".".join(output)
        return output

    return inner


# Note that the order of sound changes is important here.
# If the umlauts are rearranged, it might for example apply
# a -> e -> i for one syllable which is not supposed to happen.


a_umlaut = umlaut_factory(
    lambda x: re.match("[aoæ]", x),
    (
        ("ai", "æː"),
        ("au", "oː"),
        ("eu", "ɔː"),
        ("iu", "eo"),
        ("i", "e"),
        ("u", "o"),
    ),
)

i_umlaut = umlaut_factory(
    lambda x: re.match("[iɪj]", x),
    [("e", "i"), ("a", "e")],
)


def syllable_reduction(word):
    word = re.sub(r"aː?\.?w\.?eː?", r"aː", word)
    word = re.sub(r"eː?\.?w\.?eː?", r"oː", word)
    word = re.sub(r"eː?\.?w\.?oː?", r"oː", word)
    word = re.sub(r"eː?\.?w\.?uː?", r"uː", word)

    syllables = re.split(r"\.", word)

    if len(syllables) == 3:
        syllables[1] = re.sub(rf"h?[{VOWELS}]", r"", syllables[1])
    if len(syllables) == 2:
        syllables[1] = re.sub(r"h?[æeiu]", r"", syllables[1])

    word = ".".join(syllables)
    word = re.sub(r"gs", r"ks", word)
    return word


def r_umlaut(word):
    word = re.sub("æ(z|s$)", "er", word)
    word = re.sub("i(z|s$)", "er", word)
    word = re.sub("au(z|s$)", "or", word)
    word = re.sub("z", "r", word)
    word = re.sub(f"([{VOWELS}])s$", r"\1r", word)
    return word


# # Changes all instances of z (as well as terminal -s after a vowel) into r and centralizes preceding vowels.
# # æ becomes e
# # i becomes e
# # au becomes o
#
# # Example: bezi becomes beri
#
# # out = soundchanges("ˈɑi.trɔːː.nɑ̃")
# # out = soundchanges("full.az")
# # out = soundchanges("fell.iz")
# out = soundchanges("hab.ja.na")
# out = soundchanges("hau.zi.ja.nã")
# print(out)
