from mothertongues.dictionary import MTDictionary
from mothertongues.tests.base_test_case import BasicTestCase
from mothertongues.utils import load_mtd_configuration


class DictionaryExporterTest(BasicTestCase):
    """Test Dictionary Exporting"""

    def setUp(self):
        super().setUp()
        language_config_path = self.data_dir / "config_json.json"
        config = load_mtd_configuration(language_config_path)
        self.dictionary = MTDictionary(**config)

    def test_export_data(self):
        output = self.dictionary.export().model_dump()
        self.assertIn("config", output)
        self.assertIn("l1_index", output)
        self.assertIn("l2_index", output)
        self.assertIn("data", output)
        self.assertEqual(output["data"][3]["word"], "træ")
