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
        index.calculate_scores()
        for term in index.data:
            for posting in index.data[term]:
                self.assertGreater(index.data[term][posting]["score"]["total"], 0.0)

    def test_score_brown_corpus(self):
        nltk.download("brown")
        corpus = [
            {"entryID": i, "test": " ".join(sent)}
            for i, sent in enumerate(nltk.corpus.brown.sents()[:1000])
        ]
        index = create_inverted_index(corpus, self.dictionary.config, "l2")
        index.keys_to_index = ["test"]
        index.calculate_scores()
        get_top_1 = index._scorers["test"].get_top_n(["zurich"], corpus, n=1)
        self.assertEqual(get_top_1[0]["entryID"], 684)
