import contextlib

from jsf import JSF
from pydantic import error_wrappers

from mothertongues.config.models import (
    DataSource,
    DictionaryEntry,
    LanguageConfiguration,
    MTDConfiguration,
    ResourceManifest,
)
from mothertongues.dictionary import MTDictionary
from mothertongues.exceptions import (
    ConfigurationError,
    ParserError,
    UnsupportedFiletypeError,
)
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

    def test_config_does_not_raise_unexpected_errors(self):
        """Generate 1000 fake dictionaries based on the schemas alone.
        These won't work, but shouldn't raise unexpected errors either"""
        language_config_faker = JSF(LanguageConfiguration.schema())
        entry_faker = JSF(DictionaryEntry.schema())
        manifest_faker = JSF(ResourceManifest.schema())
        for _ in range(1000):
            # Custom exceptions from mothertongues.exceptions are ok, as are NotImplementedErrors for configurations that try to use the Custom Parser Method
            # UnsupportedFiletypeError is OK and so are various pydantic ValidationErrors
            with contextlib.suppress(
                ConfigurationError,
                ParserError,
                NotImplementedError,
                UnsupportedFiletypeError,
                error_wrappers.ValidationError,
            ):
                language_config = LanguageConfiguration(
                    **language_config_faker.generate()
                )
                manifest = ResourceManifest(**manifest_faker.generate())
                data = [DictionaryEntry(**entry_faker.generate()) for _ in range(50)]
                data_source = DataSource(manifest=manifest, resource=data)
                config = MTDConfiguration(config=language_config, data=data_source)
                MTDictionary(config)

    def _generate_fake_data(self):
        entry_schema = DictionaryEntry.schema()
        entry_faker = JSF(entry_schema)
        entries = [entry_faker.generate() for _ in range(1000)]
        for i, entry in enumerate(entries):
            entry["entryID"] = str(i)
        return DataSource(manifest=ResourceManifest(), resource=entries)

    def test_no_file_config(self):
        """Create a dictionary without any files and generated data"""
        language_config = LanguageConfiguration(sorting_field="word")
        # generate fake data based on DictionaryEntry schema
        fake_data_source1 = self._generate_fake_data()
        fake_data_source2 = self._generate_fake_data()
        self.mtd_config = MTDConfiguration(
            config=language_config, data=[fake_data_source1, fake_data_source2]
        )
        self.dictionary = MTDictionary(self.mtd_config)
        self.assertEqual(len(self.dictionary) + len(self.dictionary.duplicates), 2000)

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
