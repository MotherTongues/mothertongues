from pathlib import Path
from typing import List, Tuple
from unittest import main

from pydantic import ValidationError

from mothertongues.config.models import (
    DataSource,
    DictionaryEntry,
    LanguageConfiguration,
    MTDConfiguration,
    ParserEnum,
    ParserTargets,
    ResourceManifest,
)
from mothertongues.dictionary import MTDictionary
from mothertongues.exceptions import ConfigurationError
from mothertongues.tests.base_test_case import BasicTestCase
from mothertongues.utils import load_mtd_configuration


def _custom_parser(data_source: DataSource) -> Tuple[List[DictionaryEntry], List[dict]]:
    if not isinstance(data_source.resource, Path):
        raise TypeError("Sorry, this parser can only read from pathlib.Path's")
    with open(data_source.resource, encoding="utf8") as f:
        data = [x.strip() for x in f]
    records = []
    unparsable = []
    for line in data:
        row = line.split(" ")
        record = {
            "entryID": int(row[1][4:]),
            "definition": row[2][1:-1],
            "word": row[3][1:-1],
        }
        if row[4] != '""' and row[5] != '""':
            record["audio"] = [
                {
                    "description": f"{row[4][1:]} {row[5][:-1]}",
                    "filename": row[6][1:-1],
                }
            ]
            record["video"] = [
                {
                    "description": f"{row[7][1:]} {row[8]} {row[9][:-1]}",
                    "filename": row[10][1:-1],
                }
            ]
            record["theme"] = row[11][1:-1]
            record["optional"] = {"Part of Speech": row[12][1:-1]}
        else:
            record["audio"] = []
            record["video"] = []
            record["theme"] = row[8][1:-1]
            record["optional"] = {"Part of Speech": row[9][1:-1]}
        try:
            records.append(DictionaryEntry(**record))  # type: ignore
        except ValidationError:
            unparsable.append(record)
    return records, unparsable


class DictionaryParserTest(BasicTestCase):
    """Test Dictionary Data Parsers"""

    def setUp(self):
        super().setUp()
        self.formats_supported = ["csv", "psv", "tsv", "xlsx"]
        self.raw_data = [
            {
                "entryID": 4,
                "definition": "goodbye",
                "word": "farvel",
                "audio": [],
                "video": [],
                "theme": "greetings",
                "optional": {"Part of Speech": "interjection"},
                "sort_form": "farvel",
            },
            {
                "entryID": 3,
                "definition": "hello",
                "word": "hej",
                "audio": [{"description": "Aidan Pine", "filename": "hej.mp3"}],
                "video": [
                    {"description": "Nolan Van Hell", "filename": "snowfall.mp4"}
                ],
                "theme": "greetings",
                "optional": {"Part of Speech": "interjection"},
                "sort_form": "hej",
            },
            {
                "entryID": 2,
                "definition": "word",
                "word": "ord",
                "audio": [{"description": "Aidan Pine", "filename": "ord.mp3"}],
                "video": [
                    {"description": "Nolan Van Hell", "filename": "snowfall.mp4"}
                ],
                "theme": "abstract",
                "optional": {"Part of Speech": "noun"},
                "sort_form": "ord",
            },
            {
                "entryID": 1,
                "definition": "tree",
                "word": "træ",
                "audio": [{"description": "Aidan Pine", "filename": "tree.mp3"}],
                "video": [
                    {"description": "Nolan Van Hell", "filename": "snowfall.mp4"}
                ],
                "theme": "plants",
                "optional": {"Part of Speech": "noun"},
                "sort_form": "træ",
            },
        ]
        self.parsed_data = [
            {
                "word": "farvel",
                "definition": "goodbye",
                "entryID": "4",
                "theme": "greetings",
                "secondary_theme": "",
                "img": "",
                "audio": [],
                "video": [],
                "definition_audio": [],
                "example_sentence": [],
                "example_sentence_definition": [],
                "example_sentence_audio": [],
                "example_sentence_definition_audio": [],
                "optional": {"Part of Speech": "interjection"},
                "source": "words",
                "sort_form": "farvel",
                "sorting_form": [5, 0, 17, 21, 4, 11],
            },
            {
                "word": "hej",
                "definition": "hello",
                "entryID": "3",
                "theme": "greetings",
                "secondary_theme": "",
                "img": "",
                "audio": [{"description": "Aidan Pine", "filename": "hej.mp3"}],
                "video": [
                    {"description": "Nolan Van Hell", "filename": "snowfall.mp4"}
                ],
                "definition_audio": [],
                "example_sentence": [],
                "example_sentence_definition": [],
                "example_sentence_audio": [],
                "example_sentence_definition_audio": [],
                "optional": {"Part of Speech": "interjection"},
                "source": "words",
                "sort_form": "hej",
                "sorting_form": [7, 4, 9],
            },
            {
                "word": "ord",
                "definition": "word",
                "entryID": "2",
                "theme": "abstract",
                "secondary_theme": "",
                "img": "",
                "audio": [{"description": "Aidan Pine", "filename": "ord.mp3"}],
                "video": [
                    {"description": "Nolan Van Hell", "filename": "snowfall.mp4"}
                ],
                "definition_audio": [],
                "example_sentence": [],
                "example_sentence_definition": [],
                "example_sentence_audio": [],
                "example_sentence_definition_audio": [],
                "optional": {"Part of Speech": "noun"},
                "source": "words",
                "sort_form": "ord",
                "sorting_form": [14, 17, 3],
            },
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
                "example_sentence": [
                    "Har du røde øjne?",
                    "Døde røde rødøjede rådne røgede ørreder.",
                ],
                "example_sentence_definition": [
                    "Do you have red eyes?",
                    "Dead, red, red-eyed, rotten, smoked trout.",
                ],
                "example_sentence_audio": [
                    [
                        {"description": "AP", "filename": "ap_sent1.mp3"},
                        {"description": "AR", "filename": "ar_sent1.mp3"},
                    ],
                    [
                        {"description": "AP", "filename": "ap_sent2.mp3"},
                        {"description": "AR", "filename": "ar_sent2.mp3"},
                    ],
                ],
                "example_sentence_definition_audio": [],
                "optional": {"Part of Speech": "noun"},
                "source": "words",
                "sort_form": "træ",
                "sorting_form": [19, 17, 26],
            },
        ]
        self.parsed_data = [DictionaryEntry(**x).model_dump() for x in self.parsed_data]

    def test_json_parser(self):
        language_config_path = self.data_dir / "config_json.json"
        config = load_mtd_configuration(language_config_path)
        mtd_config = MTDConfiguration(**config)
        dictionary = MTDictionary(mtd_config)
        self.maxDiff = None
        self.assertEqual(dictionary.data[0]["word"], "farvel")
        self.assertEqual(dictionary.data[3]["word"], "træ")
        self.assertEqual(len(dictionary.data[3]["example_sentence"]), 2)
        self.assertEqual(len(dictionary.data[3]["example_sentence_audio"]), 2)
        self.assertEqual(len(dictionary.data[3]["example_sentence_audio"][0]), 2)
        self.assertCountEqual(dictionary.data, self.parsed_data)

    def test_basic_tabular_parsers(self):
        for format in [ParserEnum.csv, ParserEnum.tsv, ParserEnum.psv, ParserEnum.xlsx]:
            language_config_path = self.data_dir / f"config_{format.name}.json"
            config = load_mtd_configuration(language_config_path)
            mtd_config = MTDConfiguration(**config)
            dictionary = MTDictionary(mtd_config)
            self.maxDiff = None
            self.assertEqual(dictionary.data[0]["word"], "farvel")
            self.assertEqual(dictionary.data[3]["word"], "træ")
            data = self._correct_data(dictionary.data)
            self.assertCountEqual(data, self.parsed_data)
            mtd_config.data[0].manifest.skip_header = True
            dictionary = MTDictionary(mtd_config)
            self.assertEqual(len(dictionary.data), len(self.parsed_data) - 1)

    def test_xlsx_specifics(self):
        language_config_path = self.data_dir / "config_xlsx.json"
        config = load_mtd_configuration(language_config_path)
        mtd_config = MTDConfiguration(**config)
        # select another sheet
        mtd_config.data[0].manifest.sheet_name = "Skip"
        # skip header
        mtd_config.data[0].manifest.skip_header = True
        # test absent cell
        mtd_config.data[0].manifest.targets.secondary_theme = "ZZZZZZ"
        dictionary = MTDictionary(mtd_config)
        self.assertEqual(dictionary.data[0]["word"], "farvel")
        self.assertEqual(dictionary.data[3]["word"], "træ")
        data = self._correct_data(dictionary.data)
        self.assertCountEqual(data, self.parsed_data)

    def _test_parser_but_no_targets(self):
        """test missing TODO:"""
        data = DataSource(
            manifest=ResourceManifest(
                file_type="csv", targets=ParserTargets(word="2", definition="1")
            ),
            resource=self.data_dir / "data_check.csv",
        )
        looser_config = LanguageConfiguration()
        mtd_config = MTDConfiguration(config=looser_config, data=[data])
        with self.assertRaises(ConfigurationError):
            MTDictionary(mtd_config)

    def test_custom_parser(self):  # sourcery skip: extract-duplicate-method
        language_config_path = self.data_dir / "config_custom.json"
        config = load_mtd_configuration(language_config_path)
        mtd_config = MTDConfiguration(**config)
        # Will raise a NotImplementedError if initialize without custom parse function
        with self.assertRaises(NotImplementedError):
            dictionary = MTDictionary(mtd_config)
        dictionary = MTDictionary(mtd_config, custom_parse_method=_custom_parser)
        data = dictionary.data
        self.maxDiff = None
        self.assertEqual(data[0]["word"], "farvel")
        self.assertEqual(data[3]["word"], "træ")

        class CustomParserDictionary(MTDictionary):
            def custom_parse_method(
                self, data_source: DataSource
            ) -> Tuple[List[DictionaryEntry], List[dict]]:
                print(
                    f"Testing accessing the dictionary config. Here is the build number: {self.config.config.build}"
                )
                return _custom_parser(data_source)

        dictionary_no_init = CustomParserDictionary(
            mtd_config, parse_data_on_initialization=False
        )
        dictionary_no_init.initialize()
        data_from_no_init = dictionary_no_init.data
        self.assertEqual(data_from_no_init[0]["word"], "farvel")
        self.assertEqual(data_from_no_init[3]["word"], "træ")
        data = self._correct_data(data)
        self.assertCountEqual(data, self.parsed_data)

    def _correct_data(self, data):
        # add example sentences because it's not in all the data formats
        data[3]["example_sentence"] = self.parsed_data[3]["example_sentence"]
        data[3]["example_sentence_definition"] = self.parsed_data[3][
            "example_sentence_definition"
        ]
        data[3]["example_sentence_audio"] = self.parsed_data[3][
            "example_sentence_audio"
        ]
        return data

    def test_unparsable_data(self):
        """This is a stub for a test that should check how many items are unparsable in a given DataSource's Resource
        I need to think more about how to notify the user about this as well
        """
        pass

    def test_no_parser(self):
        data = DataSource(manifest=ResourceManifest(), resource=self.raw_data)
        self.assertEqual(data.resource[0]["word"], "farvel")
        self.assertEqual(data.resource[3]["word"], "træ")

    def test_misconfigured_parser(self):
        with self.assertRaises(ConfigurationError):
            DataSource(
                manifest=ResourceManifest(file_type=ParserEnum.csv),
                resource=self.data_dir / "data_check.csv",
            )

    def test_prepending_paths(self):
        language_configuration = LanguageConfiguration()
        data_plus_img = self.parsed_data
        data_plus_img[0]["img"] = "test.jpg"
        data = DataSource(
            manifest=ResourceManifest(
                img_path="http://bar.foo//",
                audio_path="https://foo.bar",
                video_path="https://foobar.bar",
            ),
            resource=data_plus_img,
        )
        mtd_config = MTDConfiguration(config=language_configuration, data=[data])
        dictionary = MTDictionary(mtd_config)
        data = dictionary.data
        self.assertEqual(data[1]["audio"][0]["filename"], "https://foo.bar/hej.mp3")
        self.assertEqual(data[0]["img"], "http://bar.foo/test.jpg")
        self.assertEqual(
            data[1]["video"][0]["filename"], "https://foobar.bar/snowfall.mp4"
        )


if __name__ == "__main__":
    main()
