from copy import deepcopy

from mothertongues.config.models import (
    CheckableParserTargetFieldNames,
    LanguageConfiguration,
    ResourceManifest,
)
from mothertongues.dictionary import DataSource, MTDictionary
from mothertongues.tests.base_test_case import BasicTestCase
from mothertongues.utils import load_mtd_configuration


class DictionaryDataTest(BasicTestCase):
    """Test Dictionary Data Checks"""

    def setUp(self):
        super().setUp()
        language_config_path = self.data_dir / "config_data_check.json"
        config = load_mtd_configuration(language_config_path)
        breakpoint()
        self.dictionary = MTDictionary(**config)

    def test_no_data(self):
        empty_data = DataSource(manifest=ResourceManifest(), resource=[])
        dictionary = MTDictionary(config=LanguageConfiguration(), data=empty_data)
        self.assertEqual(len(dictionary), 0)

    def test_missing_chars(self):
        self.assertIn("😀", self.dictionary.sorter.oovs)

    def test_duplicates(self):
        self.assertCountEqual(
            self.dictionary.duplicates, ["words4", "words6", "words9"]
        )

    def test_info(self):
        self.assertEqual(self.dictionary[0]["entryID"], "words5")

    def test_minimal(self):
        config_path = self.data_dir / "config_minimal.json"
        config = load_mtd_configuration(config_path)
        dictionary = MTDictionary(**config)
        self.assertEqual(dictionary.data[0]["entryID"], "words0")

    def test_missing_required_fields(self):
        self.assertCountEqual(
            ["words7", "words6", "words9"], self.dictionary.missing_data
        )
        looser_config = deepcopy(self.mtd_config)
        looser_config.config.required_fields = [CheckableParserTargetFieldNames.theme]
        dictionary = MTDictionary(looser_config)
        self.assertCountEqual(["words7", "words5", "words9"], dictionary.missing_data)
