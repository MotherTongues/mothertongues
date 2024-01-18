from copy import deepcopy

from mothertongues.config.models import (
    CheckableParserTargetFieldNames,
    LanguageConfiguration,
    MTDConfiguration,
    ParserEnum,
    ParserTargets,
    ResourceManifest,
)
from mothertongues.dictionary import DataSource, MTDictionary
from mothertongues.tests.base_test_case import BasicTestCase
from mothertongues.tests.utils import capture_logs
from mothertongues.utils import load_mtd_configuration


class DictionaryDataTest(BasicTestCase):
    """Test Dictionary Data Checks"""

    def setUp(self):
        super().setUp()

    def read_data_check(self):
        language_config_path = self.data_dir / "config_data_check.json"
        config = load_mtd_configuration(language_config_path)
        self.mtd_config = MTDConfiguration(**config)
        self.dictionary = MTDictionary(self.mtd_config)

    def test_extra_fields(self):
        ds1 = DataSource(
            manifest=ResourceManifest(),
            resource=[
                {"word": "test1", "definition": "test1", "foo": "bar"},
                {"word": "test2", "definition": "test2", "bar": "foo"},
            ],
        )
        config = MTDConfiguration(
            config=LanguageConfiguration(sorting_field="word"), data=[ds1]
        )
        dictionary = MTDictionary(config)
        self.assertEqual(len(dictionary), 2)
        self.assertEqual(dictionary[0]["foo"], "bar")
        self.assertEqual(dictionary[1]["bar"], "foo")
        # Extra fields aren't guaranteed to be on every entry
        with self.assertRaises(KeyError):
            dictionary[0]["bar"]

    def test_no_data(self):
        empty_data = DataSource(manifest=ResourceManifest(), resource=[])
        config = MTDConfiguration(config=LanguageConfiguration(), data=empty_data)
        dictionary = MTDictionary(config)
        self.assertEqual(len(dictionary), 0)

    def test_validation_error(self):
        bad_data = DataSource(
            manifest=ResourceManifest(), resource=[{"word": "foo", "definition": 42}]
        )
        config = MTDConfiguration(
            config=LanguageConfiguration(sorting_field="word"), data=bad_data
        )
        with capture_logs("DEBUG") as logs:
            dictionary = MTDictionary(config)
            self.assertEqual(len(dictionary), 0)
        self.assertIn("validation error", "".join(logs))

    def test_validation_error_json(self):
        bad_data = DataSource(
            manifest=ResourceManifest(
                file_type=ParserEnum.json,
                targets=ParserTargets(
                    word="word",
                    definition="definition",
                ),
            ),
            resource=self.data_dir / "data_invalid.json",
        )
        config = MTDConfiguration(
            config=LanguageConfiguration(sorting_field="word"), data=bad_data
        )
        with capture_logs("DEBUG") as logs:
            dictionary = MTDictionary(config)
            self.assertEqual(len(dictionary), 0)
        self.assertIn("validation error", "".join(logs))

    def test_missing_definitions(self):
        empty_data = DataSource(
            manifest=ResourceManifest(),
            resource=[{"word": "test"}, {"word": "foo", "definition": "bar"}],
        )
        config = MTDConfiguration(
            config=LanguageConfiguration(sorting_field="word"), data=empty_data
        )
        dictionary = MTDictionary(config)
        self.assertEqual(len(dictionary), 1)

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

    def test_multiple_example_audio(self):
        dictionary = self.create_test_dictionary_from_config("config_csv_multi.json")
        self.assertEqual(len(dictionary), 1)
        entry = dictionary.data[0]
        self.assertEqual(
            entry,
            {
                "word": "træ",
                "definition": "tree",
                "entryID": "1",
                "theme": "plants",
                "secondary_theme": "",
                "img": "",
                "audio": [{"description": "Aidan Pine", "filename": "tree.mp3"}],
                "video": [
                    {"description": "Nolan Van Hell", "filename": "snowfall.mp4"}
                ],
                "definition_audio": [],
                "example_sentence": ["Har du røde øjne?"],
                "example_sentence_definition": ["Do you have red eyes?"],
                "example_sentence_audio": [
                    [
                        {"description": "Aidan Pine", "filename": "rode1.mp3"},
                        {"description": "Aidan Pine", "filename": "rode2.mp3"},
                    ]
                ],
                "example_sentence_definition_audio": [],
                "optional": {"Part of Speech": "noun"},
                "source": "words",
                "sort_form": "træ",
                "sorting_form": [19, 17, 26],
            },
        )

    def test_multiple_sentences(self):
        dictionary = self.create_test_dictionary_from_config("config_csv_multi.json")
        self.assertEqual(len(dictionary), 1)
        entry = dictionary.data[0]
        self.assertEqual(
            entry,
            {
                "word": "træ",
                "definition": "tree",
                "entryID": "1",
                "theme": "plants",
                "secondary_theme": "",
                "img": "",
                "audio": [{"description": "Aidan Pine", "filename": "tree.mp3"}],
                "video": [
                    {"description": "Nolan Van Hell", "filename": "snowfall.mp4"}
                ],
                "definition_audio": [],
                "example_sentence": ["Har du røde øjne?"],
                "example_sentence_definition": ["Do you have red eyes?"],
                "example_sentence_audio": [
                    [
                        {"description": "Aidan Pine", "filename": "rode1.mp3"},
                        {"description": "Aidan Pine", "filename": "rode2.mp3"},
                    ]
                ],
                "example_sentence_definition_audio": [],
                "optional": {"Part of Speech": "noun"},
                "source": "words",
                "sort_form": "træ",
                "sorting_form": [19, 17, 26],
            },
        )

    def test_missing_chars(self):
        self.read_data_check()
        self.assertIn("😀", self.dictionary.sorter.oovs)

    def test_duplicates(self):
        self.read_data_check()
        self.assertCountEqual(self.dictionary.duplicates, ["4", "6", "9"])

    def test_info(self):
        self.read_data_check()
        self.assertEqual(self.dictionary[0]["entryID"], "5")

    def test_minimal(self):
        dictionary = self.create_test_dictionary_from_config("config_minimal.json")
        self.assertEqual(dictionary.data[0]["entryID"], "words00")

    def create_test_dictionary_from_config(self, config):
        language_config_path = self.data_dir / config
        config = load_mtd_configuration(language_config_path)
        mtd_config = MTDConfiguration(**config)
        return MTDictionary(mtd_config)

    def test_missing_required_fields(self):
        self.read_data_check()
        self.assertCountEqual(["7", "6", "9"], self.dictionary.missing_data)
        looser_config = deepcopy(self.mtd_config)
        looser_config.config.required_fields = [CheckableParserTargetFieldNames.theme]
        dictionary = MTDictionary(looser_config)
        self.assertCountEqual(["7", "5", "9"], dictionary.missing_data)
