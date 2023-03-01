#!/usr/bin/env python3.10
# pylint: disable=logging-fstring-interpolation
"""Make sure the sound changer gives the expected results for different outputs."""
import norlunda as nl
import collections as col
import logging
import json
import regex as re


def parse_json_with_comments(data, **kwargs):
    data = re.sub(r"\s*#.*?\n", "", data)
    return json.loads(data, **kwargs)


NorlundaTestCase = col.namedtuple(
    "NorlundaTestCase", ("pgm_root", "norlunda", "english", "is_verb")
)

with open("test_cases.cson", "r", encoding="utf-8") as file:
    contents = parse_json_with_comments(file.read())
    contents = [
        NorlundaTestCase(
            nl.pgm_root_to_ipa(i["proto-germanic"]),
            i["norlunda"],
            i["english"],
            i.get("is_verb", True),
        )
        for i in contents
    ]


def test_strong_words():
    success = 0
    for i in contents:
        changer = nl.NorlundaChanger(i.pgm_root, i.is_verb)
        result = changer.apply_all()

        if nl.romanized(result) == nl.romanized(i.norlunda):
            success += 1
            logging.info(f"- *{i.pgm_root}* -> *{result}* was a success")
            continue

        logging.info("\n")
        for line in changer.print_log().splitlines():
            logging.info(line)

        logging.info(
            f"\nExpected `/{(i.norlunda)}/`, got "
            f"`/{(result)}/` (*{nl.romanized(i.norlunda)}* and *{nl.romanized(result)}*)"
        )
        logging.info("---\n")

    logging.info(f"Result: {success}/{len(contents)} words successful")


if __name__ == "__main__":
    logging.basicConfig(format="%(message)s", level=logging.DEBUG, force=True)
    test_strong_words()
