from mothertongues.config.models import (
    DataSource,
    LanguageConfiguration,
    MTDConfiguration,
    ResourceManifest,
)
from mothertongues.dictionary import MTDictionary
from mothertongues.tests.base_test_case import BasicTestCase
from mothertongues.utils import load_mtd_configuration


class DictionaryExporterTest(BasicTestCase):
    """Test Dictionary Exporting"""

    def setUp(self):
        super().setUp()
        language_config_path = self.data_dir / "config_json.json"
        config = load_mtd_configuration(language_config_path)
        self.mtd_config = MTDConfiguration(**config)
        self.dictionary = MTDictionary(self.mtd_config)

    def test_empty_export(self):
        empty_data = DataSource(manifest=ResourceManifest(), resource=[])
        config = MTDConfiguration(config=LanguageConfiguration(), data=empty_data)
        dictionary = MTDictionary(config)
        output = dictionary.export().model_dump()
        self.assertIn("config", output)
        self.assertIn("l1_index", output)
        self.assertIn("l2_index", output)
        self.assertIn("data", output)
        self.assertEqual(len(output["data"]), 0)

    def test_export_data(self):
        output = self.dictionary.export().model_dump()
        self.assertIn("config", output)
        self.assertIn("l1_index", output)
        self.assertIn("l2_index", output)
        self.assertIn("data", output)
        self.assertEqual(output["data"][3]["word"], "træ")
