import time

import nltk

from mothertongues.config.models import (
    CheckableParserTargetFieldNames,
    MTDConfiguration,
)
from mothertongues.dictionary import MTDictionary
from mothertongues.processors.index_builder import InvertedIndex, create_inverted_index
from mothertongues.tests.base_test_case import BasicTestCase
from mothertongues.utils import load_mtd_configuration


class DictionaryIndexBuilderTest(BasicTestCase):
    """Test Building Dictionary Index"""

    def setUp(self):
        super().setUp()
        language_config_path = self.data_dir / "config_json.json"
        config = load_mtd_configuration(language_config_path)
        self.mtd_config = MTDConfiguration(**config)
        self.dictionary = MTDictionary(self.mtd_config)

    def test_build_index(self):
        index = create_inverted_index(
            self.dictionary.data, self.dictionary.config, "l1"
        )
        index.keys_to_index = [
            CheckableParserTargetFieldNames.definition.value,
            CheckableParserTargetFieldNames.word.value,
        ]
        index.build()
        # assert that it finds a single word and definition for each entry
        self.assertEqual(len(index.data), len(self.dictionary.data) * 2)
        index.keys_to_index = [
            CheckableParserTargetFieldNames.definition.value,
            CheckableParserTargetFieldNames.word.value,
            "example_sentence",
        ]
        index.build()
        self.assertEqual(
            self.dictionary.data[-1]["example_sentence"][0].split()[2], "røde"
        )
        self.assertIn(["example_sentence[0]", 2], index.data["røde"]["1"]["location"])

    def test_score(self):
        index = InvertedIndex(
            self.dictionary.data,
            keys_to_index=[
                CheckableParserTargetFieldNames.definition.value,
                CheckableParserTargetFieldNames.word.value,
                "example_sentence",
            ],
        )
        index.build()
        index.calculate_scores()
        for term in index.data:
            for posting in index.data[term]:
                self.assertGreaterEqual(
                    index.data[term][posting]["score"]["total"], 0.0
                )

    def test_score_brown_corpus(self):
        nltk.download("brown")
        corpus = [
            {"entryID": i, "test": " ".join(sent)}
            for i, sent in enumerate(nltk.corpus.brown.sents()[:1000])
        ]
        index = create_inverted_index(corpus, self.dictionary.config, "l2")
        index.keys_to_index = ["test"]
        second_index = create_inverted_index(corpus, self.dictionary.config, "l2")
        second_index.keys_to_index = ["test"]
        second_index.build()
        second_index.calculate_scores()
        index.build()
        index._legacy_calculate_scores()
        self.assertEqual(second_index.k1, index._scorers["test"].k1)
        self.assertEqual(second_index.b, index._scorers["test"].b)
        self.assertEqual(
            second_index.IDFS["test"]["light"], index._scorers["test"].idf["light"]
        )
        self.assertEqual(
            index.data["centuri"][926]["score"]["total"],
            second_index.data["centuri"][926]["score"]["total"],
        )
        get_top_1 = index._scorers["test"].get_top_n(["zurich"], corpus, n=1)
        self.assertEqual(get_top_1[0]["entryID"], 684)

    def test_speed(self):
        """Should be able to index and score a ten-thousand entry dictionary in < 15 seconds
        Even on a slower ci/cd test machine.
        """
        nltk.download("brown")
        corpus = [
            {"entryID": i, "test": " ".join(sent)}
            for i, sent in enumerate(nltk.corpus.brown.sents()[:10000])
        ]
        index = create_inverted_index(corpus, self.dictionary.config, "l2")
        index.keys_to_index = ["test"]
        t1 = time.perf_counter()
        index.build()
        index.calculate_scores()
        t2 = time.perf_counter()
        self.assertLess(t2 - t1, 20)
