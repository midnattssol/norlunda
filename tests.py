#!/usr/bin/env python3.10
"""Make sure the sound changer gives the expected results for different outputs."""
import unittest
import norlunda as nl

STRONG = {"argijaną": "ergan"}  # to ruin

# ergan; from PGmc. *argijaną “to ruin”
class TestNorlundaSoundChanger(unittest.TestCase):
    def test_strong_words(self):
        for pgm_root, norlunda_word in STRONG.items():
            self.assertEqual(nl.soundchanges(pgm_root), norlunda_word)


if __name__ == "__main__":
    unittest.main()
