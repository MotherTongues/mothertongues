from copy import deepcopy

from mothertongues.config.models import (
    CheckableParserTargetFieldNames,
    MTDConfiguration,
)
from mothertongues.dictionary import MTDictionary
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

    def test_missing_chars(self):
        self.assertIn("😀", self.dictionary.sorter.oovs)

    def test_duplicates(self):
        self.assertCountEqual(self.dictionary.duplicates, ["4", "6"])

    def test_missing_required_fields(self):
        self.assertCountEqual(["7", "6"], self.dictionary.missing_data)
        looser_config = deepcopy(self.mtd_config)
        looser_config.config.required_fields = [CheckableParserTargetFieldNames.theme]
        dictionary = MTDictionary(looser_config)
        self.assertCountEqual(["7", "5"], dictionary.missing_data)
