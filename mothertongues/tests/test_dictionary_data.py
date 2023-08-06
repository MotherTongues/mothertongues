from copy import deepcopy

from mothertongues.config.models import (
    CheckableParserTargetFieldNames,
    MTDConfiguration,
)
from mothertongues.dictionary import MTDictionary
from mothertongues.tests.base_test_case import BasicTestCase
from mothertongues.utils import load_mtd_configuration


class DictionaryDataTest(BasicTestCase):
    """Test Dictionary Data Checks
    TODO: Create data that exhibits the following and assert that errors/warnings are raised
    """

    def setUp(self):
        super().setUp()
        language_config_path = self.data_dir / "config_data_check.json"
        config = load_mtd_configuration(language_config_path)
        self.mtd_config = MTDConfiguration(**config)
        self.dictionary = MTDictionary(self.mtd_config)

    def test_missing_chars(self):
        self.assertIn("😀", self.dictionary.sorter.oovs)

    def _test_duplicates(self):
        # TODO: duplicates not currently implementd since refactor away from pandas
        self.assertEqual(self.dictionary.duplicates, ["", "farvel", "træ"])

    def _test_missing_required_fields(self):
        # TODO: these are automatically dropped in the parser with a warning. maybe that's enough
        # 9 & 6 dropped from duplicates
        self.assertEqual([7], self.dictionary.missing_data["entryID"].tolist())
        looser_config = deepcopy(self.mtd_config)
        looser_config.config.required_fields = [CheckableParserTargetFieldNames.theme]
        dictionary = MTDictionary(looser_config)
        self.assertEqual([7, 5], dictionary.missing_data["entryID"].tolist())
