from mothertongues.config.models import MTDConfiguration
from mothertongues.dictionary import MTDictionary
from mothertongues.tests.base_test_case import BasicTestCase
from mothertongues.utils import load_mtd_configuration


class DictionaryParserTest(BasicTestCase):
    """Test Dictionary Data Parsers"""

    def setUp(self):
        super().setUp()
        self.formats_supported = ["csv", "psv", "tsv", "xlsx"]

    def test_dictionary_parsers(self):
        for format in self.formats_supported:
            language_config_path = self.data_dir / f"config_{format}.json"
            config = load_mtd_configuration(language_config_path)
            mtd_config = MTDConfiguration(**config)
            dictionary = MTDictionary(mtd_config)
            data = dictionary.data.to_dict(orient="records")
            self.assertEqual(data[0]["word"], "farvel")
            self.assertEqual(data[3]["word"], "træ")
