import contextlib
import sys
from string import ascii_lowercase

from jsf import JSF
from loguru import logger
from pydantic import ValidationError

from mothertongues.config.models import (
    DataSource,
    DictionaryEntry,
    LanguageConfiguration,
    MTDConfiguration,
    ResourceManifest,
    WeightedLevensteinConfig,
)
from mothertongues.dictionary import MTDictionary
from mothertongues.exceptions import (
    ConfigurationError,
    ParserError,
    UnsupportedFiletypeError,
)
from mothertongues.tests.base_test_case import BasicTestCase
from mothertongues.utils import load_mtd_configuration, string_to_callable


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

    def test_string_to_callable_conversion(self):
        # Pass a Callable
        def test():
            return "this is a test"

        self.assertEqual(string_to_callable(test), test)
        # Pass a lambda function which doesn't work anymore due to security reasons
        with self.assertRaises(ValueError):
            string_to_callable("lambda x: x.lower()")
        with self.assertRaises(ValueError):
            string_to_callable("lambda could just be a word in a string")
        # Pass a dot notation import
        self.assertEqual(
            string_to_callable("mothertongues.utils.string_to_callable"),
            string_to_callable,
        )
        with self.assertRaises(ConfigurationError):
            string_to_callable("foo.module.does.not.exist")

    def test_config_does_not_raise_unexpected_errors(self):
        """Generate 1000 fake dictionaries based on the schemas alone.
        These won't work, but shouldn't raise unexpected errors either"""
        language_config_faker = JSF(LanguageConfiguration.schema())
        entry_faker = JSF(DictionaryEntry.schema())
        resource_schema = ResourceManifest.schema()
        try:
            # This is an annoying error related to the ordering of elements
            # in the schema https://github.com/ghandic/jsf/issues/80
            # since this is only for testing and random generation of the transducer
            # doesn't really matter, we can just delete the problematic keys.
            manifest_faker = JSF(resource_schema)
        except AttributeError:
            del resource_schema["$defs"]["ArbitraryFieldRestrictedTransducer"]
            del resource_schema["properties"]["transducers"]
            del resource_schema["$defs"]["ParserTargets"]["properties"]["video"]
            manifest_faker = JSF(resource_schema)
        logger.remove()
        logger.add(sys.stderr, level="INFO")
        for _ in range(1000):
            # Custom exceptions from mothertongues.exceptions are ok, as are NotImplementedErrors for configurations that try to use the Custom Parser Method
            # UnsupportedFiletypeError is OK and so are various pydantic ValidationErrors
            with contextlib.suppress(
                ConfigurationError,
                ParserError,
                NotImplementedError,
                UnsupportedFiletypeError,
                ValidationError,
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

    # region Lev Weight Tests
    def test_lev_weights_subCostsPath_does_not_exist(self):
        weights_config_path = self.data_dir / "doesnt_exist.psv"
        with self.assertRaises(ValidationError):
            WeightedLevensteinConfig(substitutionCostsPath=weights_config_path)

    def test_lev_weights_subCostsPath_unsupported_delimiter(self):
        weights_config_path = self.data_dir / "weights_bad_delimiter.psv"

        with self.assertRaises(IndexError):
            WeightedLevensteinConfig(substitutionCostsPath=weights_config_path)

    def test_lev_weights_num_too_big(self):
        weights_config_path = self.data_dir / "weights_num_too_big.csv"

        with self.assertRaises(ValueError):
            WeightedLevensteinConfig(substitutionCostsPath=weights_config_path)

    def test_lev_weights_subCostsPath_unsupported_filetype(self):
        """
        Test validates that nothing happens if weights filetype is unsupported.
        """
        weights_config_path = self.data_dir / "weights_unsupported_filetype.txt"

        with self.assertRaises(UnsupportedFiletypeError) as err:
            WeightedLevensteinConfig(substitutionCostsPath=weights_config_path)

        self.assertIn("Supported filetypes include", err.exception.msg)

    def test_lev_weights_happy_path(self):
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

    def test_lev_weights_sub_both_dirs(self):
        """
        Test validates that a single subsitution in a 'weights' file weights correctly in both directions
        """
        weights_config_path = self.data_dir / "weights2.psv"
        search_config = WeightedLevensteinConfig(
            substitutionCostsPath=weights_config_path
        )

        lang_config = LanguageConfiguration(l1_search_config=search_config)
        self.assertEqual(lang_config.l1_search_config.substitutionCosts["c"]["k"], 0.01)
        self.assertEqual(lang_config.l1_search_config.substitutionCosts["k"]["c"], 0.01)

    # endregion

    # region Alphabet Tests

    def test_alphabet(self):
        # Plain
        english_alphabet = list(ascii_lowercase)
        eng_lc = LanguageConfiguration(alphabet=english_alphabet)
        self.assertEqual(eng_lc.alphabet, list(ascii_lowercase))
        # JSON
        alphabet_json_path = self.data_dir / "alphabet.json"
        json_lc = LanguageConfiguration(alphabet=alphabet_json_path)
        self.assertEqual(json_lc.alphabet, list(ascii_lowercase) + ["æ", "ø", "å"])
        # TXT
        alphabet_text_path = self.data_dir / "alphabet.txt"
        txt_lc = LanguageConfiguration(alphabet=alphabet_text_path)
        self.assertEqual(txt_lc.alphabet, list(ascii_lowercase) + ["æ", "ø", "å"])
        # str(TXT)
        txt_string_lc = LanguageConfiguration(alphabet=str(alphabet_text_path))
        self.assertEqual(
            txt_string_lc.alphabet, list(ascii_lowercase) + ["æ", "ø", "å"]
        )
        # Missing File Error
        with self.assertRaises(FileNotFoundError):
            LanguageConfiguration(alphabet="path/to/foo/bar.json")
        # Bad File type
        with self.assertRaises(ValidationError):
            LanguageConfiguration(alphabet="path/to/foo/bar.xlsx")

    def test_alphabet_contains_numbers_strings(self):
        alphabet_json_path = self.data_dir / "alphabet_with_numbers_string.json"
        json_lc = LanguageConfiguration(alphabet=alphabet_json_path)

        self.assertEqual(json_lc.alphabet, list(ascii_lowercase) + ["1", "0"])

    def test_alphabet_contains_numbers_numeric(self):
        alphabet_json_path = self.data_dir / "alphabet_with_numbers_numeric.json"

        with self.assertRaises(ValidationError):
            LanguageConfiguration(alphabet=alphabet_json_path)

    def test_alphabet_contains_punctuation(self):
        alphabet_json_path = self.data_dir / "alphabet_with_punctuation.json"
        json_lc = LanguageConfiguration(alphabet=alphabet_json_path)

        self.assertEqual(json_lc.alphabet, list(ascii_lowercase) + ["!", "'", "´", "."])

    def test_alphabet_is_empty_txt(self):
        alphabet_text_path = self.data_dir / "alphabet_empty.txt"
        txt_lc = LanguageConfiguration(alphabet=alphabet_text_path)

        self.assertEqual(txt_lc.alphabet, [])

    def test_alphabet_is_empty_json(self):
        alphabet_json_path = self.data_dir / "alphabet_empty.json"
        json_lc = LanguageConfiguration(alphabet=alphabet_json_path)

        self.assertEqual(json_lc.alphabet, [])

    # endregion

    def test_build_identifier(self):
        # Default
        lc = LanguageConfiguration()
        self.assertGreater(int(lc.build), 1)
        # Constant
        lc = LanguageConfiguration(build="test")
        self.assertEqual(lc.build, "test")
        # Callable

        def test():
            return "bloop"

        lc = LanguageConfiguration(build=test)
        self.assertEqual(lc.build, "bloop")

    def test_paths(self):
        # img and audio
        pass

    def test_example_sentences_same_length(self):
        pass
