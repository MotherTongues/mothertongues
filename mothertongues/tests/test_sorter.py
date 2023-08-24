from string import ascii_lowercase
from unittest import main

from mothertongues.config.models import (
    DataSource,
    DictionaryEntry,
    LanguageConfiguration,
    MTDConfiguration,
    ResourceManifest,
)
from mothertongues.dictionary import MTDictionary
from mothertongues.processors.sorter import ArbSorter
from mothertongues.tests.base_test_case import BasicTestCase


class SorterTest(BasicTestCase):
    def setUp(self):
        super().setUp()
        self.english_alphabet = list(ascii_lowercase)
        self.danish_alphabet = self.english_alphabet + ["æ", "ø", "å"]
        self.alphabet_json_path = self.data_dir / "alphabet.json"
        self.alphabet_text_path = self.data_dir / "alphabet.txt"

    def list_to_sorting_form(self, lex_list, key="word"):
        """turn list of strings into list of dicts with sorting forms"""
        return [{key: v} for v in lex_list]

    def test_sort_in_dictionary(self):
        """When you create a dictionary the data should be sorted."""
        # language_config_path = self.data_dir / "config_sorter.json"
        # config = load_mtd_configuration(language_config_path)
        language_config = LanguageConfiguration(
            no_sort_characters=["4", "7"], sorting_field="word"
        )
        entries = [
            DictionaryEntry(word="7test", definition="test1"),
            DictionaryEntry(word="4best", definition="test2"),
        ]
        data = DataSource(manifest=ResourceManifest(), resource=entries)
        self.mtd_config = MTDConfiguration(config=language_config, data=data)
        self.dictionary = MTDictionary(self.mtd_config)
        self.assertEqual(self.dictionary.data[0]["word"], "4best")
        self.assertEqual(self.dictionary.data[1]["word"], "7test")

    def test_sort_formats(self):
        """Sort from json, text and list formats"""
        sorter = ArbSorter(self.danish_alphabet)
        json_sorter = ArbSorter(self.alphabet_json_path)
        txt_sorter = ArbSorter(self.alphabet_text_path)
        lexicon = [{"word": "råd"}, {"word": "ūįrød"}]
        sorter(lexicon, "word")
        json_sorter(lexicon, "word")
        txt_sorter(lexicon, "word")
        self.assertEqual(sorter.values_as_word([10363, 10303, 17, 27, 3]), "ūįrød")
        self.assertEqual(json_sorter.values_as_word([10363, 10303, 17, 27, 3]), "ūįrød")
        self.assertEqual(txt_sorter.values_as_word([10363, 10303, 17, 27, 3]), "ūįrød")

    def test_sort_ignorables(self):
        """Sort ignorable characters"""
        sorter = ArbSorter(self.danish_alphabet, ignorable=["ū"])
        lexicon = self.list_to_sorting_form(["råd", "ūįrød"])
        lexicon_sorted = [
            {"word": "råd", "sorting_form": [17, 28, 3]},
            {"word": "ūįrød", "sorting_form": [10303, 17, 27, 3]},
        ]
        self.assertEqual(sorter(lexicon, "word"), lexicon_sorted)
        self.assertEqual(sorter.values_as_word([10303, 17, 27, 3]), "įrød")

    def test_sort_oov_characters(self):
        """Sort oov characters at the end"""
        sorter = ArbSorter(self.danish_alphabet)
        lexicon = self.list_to_sorting_form(["råd", "ūįrød"])
        lexicon_sorted = [
            {"word": "råd", "sorting_form": [17, 28, 3]},
            {"word": "ūįrød", "sorting_form": [10363, 10303, 17, 27, 3]},
        ]
        self.assertEqual(sorter(lexicon, "word"), lexicon_sorted)
        self.assertEqual(sorter.values_as_word([10363, 10303, 17, 27, 3]), "ūįrød")
        self.assertEqual(
            sorter.values_as_word([10363, 10303, 10303, 17, 27, 3]), "ūįįrød"
        )

    def test_sort_unicode(self):
        """Sort non-ascii characters."""
        sorter = ArbSorter(self.danish_alphabet)
        lexicon = self.list_to_sorting_form(["æbleskiver", "hund", "råd", "rød"])
        lexicon_sorted = [
            {"word": "hund", "sorting_form": [7, 20, 13, 3]},
            {"word": "rød", "sorting_form": [17, 27, 3]},
            {"word": "råd", "sorting_form": [17, 28, 3]},
            {
                "word": "æbleskiver",
                "sorting_form": [26, 1, 11, 4, 18, 10, 8, 21, 4, 17],
            },
        ]
        self.assertEqual(sorter(lexicon, "word"), lexicon_sorted)

    def test_sort_unicode_df(self):
        """Sort non-ascii characters in DataFrame."""
        sorter = ArbSorter(self.danish_alphabet)
        lexicon = self.list_to_sorting_form(["æbleskiver", "hund", "råd", "rød"])
        lexicon_sorted = sorted(
            [
                {
                    "word": "æbleskiver",
                    "sorting_form": [26, 1, 11, 4, 18, 10, 8, 21, 4, 17],
                },
                {"word": "hund", "sorting_form": [7, 20, 13, 3]},
                {"word": "råd", "sorting_form": [17, 28, 3]},
                {"word": "rød", "sorting_form": [17, 27, 3]},
            ],
            key=lambda x: x["sorting_form"],
        )
        self.assertEquals(lexicon_sorted, sorter(lexicon, "word"))

    def test_digraph_sorting(self):
        """Sort digraphs"""
        sorter = ArbSorter(["a", "b", "aa", "c"])
        lexicon = self.list_to_sorting_form(["aba", "aaba", "caba", "baca"])
        lexicon_sorted = [
            {"word": "aba", "sorting_form": [0, 1, 0]},
            {"word": "baca", "sorting_form": [1, 0, 3, 0]},
            {"word": "aaba", "sorting_form": [2, 1, 0]},
            {"word": "caba", "sorting_form": [3, 0, 1, 0]},
        ]
        self.assertEqual(lexicon_sorted, sorter(lexicon, "word"))


if __name__ == "__main__":
    main()
