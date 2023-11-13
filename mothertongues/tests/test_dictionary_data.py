from copy import deepcopy
from unittest import main

from mothertongues.config.models import (
    CheckableParserTargetFieldNames,
    LanguageConfiguration,
    MTDConfiguration,
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
        self.mtd_config = MTDConfiguration(**config)
        self.dictionary = MTDictionary(self.mtd_config)

    def test_no_data(self):
        empty_data = DataSource(manifest=ResourceManifest(), resource=[])
        config = MTDConfiguration(config=LanguageConfiguration(), data=empty_data)
        dictionary = MTDictionary(config)
        self.assertEqual(len(dictionary), 0)

    def test_multiple_sources(self):
        ds1 = DataSource(
            manifest=ResourceManifest(),
            resource=[{"word": "test1", "definition": "test1"}],
        )
        ds2 = DataSource(
            manifest=ResourceManifest(),
            resource=[
                {"word": "test2", "definition": "test2"},
                {"word": "test3", "definition": "test3", "source": "test3"},
            ],
        )
        config = MTDConfiguration(
            config=LanguageConfiguration(sorting_field="word"), data=[ds1, ds2]
        )
        dictionary = MTDictionary(config)
        self.assertEqual(len(dictionary), 3)
        # The first entry from the first data source (default source label of 'YourData')
        self.assertEqual(dictionary.data[0]["entryID"], "YourData00")
        # The first entry from the second data source (default source label of 'YourData')
        self.assertEqual(dictionary.data[1]["entryID"], "YourData10")
        # The second entry from the second data source (entry override of source label 'test3')
        self.assertEqual(dictionary.data[2]["entryID"], "test311")

    def test_missing_chars(self):
        self.assertIn("😀", self.dictionary.sorter.oovs)

    def test_duplicates(self):
        self.assertCountEqual(self.dictionary.duplicates, ["4", "6", "9"])

    def test_info(self):
        self.assertEqual(self.dictionary[0]["entryID"], "5")

    def test_minimal(self):
        config_path = self.data_dir / "config_minimal.json"
        config = load_mtd_configuration(config_path)
        mtd_config = MTDConfiguration(**config)
        dictionary = MTDictionary(mtd_config)
        self.assertEqual(dictionary.data[0]["entryID"], "words00")

    def test_missing_required_fields(self):
        self.assertCountEqual(["7", "6", "9"], self.dictionary.missing_data)
        looser_config = deepcopy(self.mtd_config)
        looser_config.config.required_fields = [CheckableParserTargetFieldNames.theme]
        dictionary = MTDictionary(looser_config)
        self.assertCountEqual(["7", "5", "9"], dictionary.missing_data)


if __name__ == "__main__":
    main()
