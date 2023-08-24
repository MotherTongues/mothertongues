from jsf import JSF

from mothertongues.config.models import (
    DataSource,
    DictionaryEntry,
    LanguageConfiguration,
    MTDConfiguration,
    ResourceManifest,
)
from mothertongues.dictionary import MTDictionary
from mothertongues.tests.base_test_case import BasicTestCase
from mothertongues.utils import load_mtd_configuration


class ConfigurationTest(BasicTestCase):
    """Test appropriate Configuration
    TODO: Create configs that exhibits the following and assert that errors/warnings are raised
    """

    def setUp(self):
        super().setUp()
        language_config_path = self.data_dir / "config_data_search_algs.json"
        config = load_mtd_configuration(language_config_path)
        self.mtd_config = MTDConfiguration(**config)
        self.dictionary = MTDictionary(self.mtd_config)

    def test_data_source_is_parsable(self):
        pass

    def test_targets_are_valid(self):
        # check type based on file_type
        # check location exists
        pass

    def test_transducers(self):
        # check that input fields exist
        pass

    def test_no_file_config(self):
        """Create a dictionary without any files"""
        language_config = LanguageConfiguration(sorting_field="word")
        entry_schema = DictionaryEntry.schema()
        entry_faker = JSF(entry_schema)
        # generate fake data based on DictionaryEntry schema
        entries = [entry_faker.generate() for _ in range(100)]
        data = DataSource(manifest=ResourceManifest(), resource=entries)
        self.mtd_config = MTDConfiguration(config=language_config, data=data)
        self.dictionary = MTDictionary(self.mtd_config)
        self.assertEqual(len(self.dictionary) + len(self.dictionary.duplicates), 100)

    def test_lev_weights(self):
        self.assertEqual(
            self.mtd_config.config.l1_search_config.insertionAtBeginningCost, 1.0
        )
        self.assertEqual(
            self.mtd_config.config.l1_search_config.substitutionCosts["a"]["b"], 0.01
        )
        self.assertEqual(
            self.mtd_config.config.l1_search_config.substitutionCosts["a"]["e"], 0.02
        )
        self.assertEqual(
            self.mtd_config.config.l1_search_config.substitutionCosts["c"]["d"], 1.0
        )

    def test_paths(self):
        # img and audio
        pass

    def test_example_sentences_same_length(self):
        pass
