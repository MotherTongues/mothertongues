import time

import nltk

from pydantic import ValidationError

from mothertongues.config.models import (
    BM25Config,
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

    def test_bm25_config(self):
        # Defaults
        l1_index = self.dictionary.return_single_index("l1")
        self.assertEqual((l1_index.k1, l1_index.b, l1_index.epsilon), (1.5, 1.0, 0.25))
        # Configured values are passed to the scorer for the matching language only
        self.dictionary.config.config.l2_bm25_config = BM25Config(
            k1=1.2, b=0.5, epsilon=0.1
        )
        l1_index = self.dictionary.return_single_index("l1")
        l2_index = self.dictionary.return_single_index("l2")
        self.assertEqual((l1_index.k1, l1_index.b, l1_index.epsilon), (1.5, 1.0, 0.25))
        self.assertEqual((l2_index.k1, l2_index.b, l2_index.epsilon), (1.2, 0.5, 0.1))
        # Out of range values are rejected
        for bad_value in [{"b": 1.5}, {"b": -0.1}, {"k1": -1}, {"epsilon": -1}]:
            with self.assertRaises(ValidationError):
                BM25Config(**bad_value)

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
        # rank_bm25 uses b=0.75
        second_index.calculate_scores(b=0.75)
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
