from pathlib import Path
from types import MethodType

import pandas as pd

from mothertongues.config.models import (
    DataSource,
    LanguageConfiguration,
    MTDConfiguration,
    ResourceManifest,
)
from mothertongues.dictionary import MTDictionary
from mothertongues.tests.base_test_case import BasicTestCase
from mothertongues.utils import load_mtd_configuration


def _custom_parser_method(self: MTDictionary, data_source: DataSource) -> pd.DataFrame:
    print(
        f"Testing accessing the dictionary config. Here is the build number: {self.config.config.build}"
    )
    return _custom_parser(data_source)


def _custom_parser(data_source: DataSource) -> pd.DataFrame:
    if not isinstance(data_source.resource, Path):
        raise TypeError("Sorry, this parser can only read from pathlib.Path's")
    with open(data_source.resource, encoding="utf8") as f:
        data = [x.strip() for x in f]
    records = []
    for line in data:
        row = line.split(" ")
        record = {
            "entryID": int(row[1][4:]),
            "definition": row[2][1:-1],
            "word": row[3][1:-1],
            "audio_description": row[4][1:-1],
            "audio_filename": row[5][1:-1],
            "theme": row[6][1:-1],
            "optional_Part_of_speech": row[7][1:-1],
        }
        records.append(record)
    return pd.DataFrame(records)


class DictionaryParserTest(BasicTestCase):
    """Test Dictionary Data Parsers"""

    def setUp(self):
        super().setUp()
        self.formats_supported = ["csv", "psv", "tsv", "xlsx"]
        self.reference_data = [
            {
                "entryID": 4,
                "definition": "goodbye",
                "word": "farvel",
                "audio_description_0": "",
                "audio_filename_0": "",
                "theme": "greetings",
                "optional_Part of Speech": "interjection",
                "compare_form": "farvel",
                "sort_form": "farvel",
            },
            {
                "entryID": 3,
                "definition": "hello",
                "word": "hej",
                "audio_description_0": "Aidan Pine",
                "audio_filename_0": "hej.mp3",
                "theme": "greetings",
                "optional_Part of Speech": "interjection",
                "compare_form": "hej",
                "sort_form": "hej",
            },
            {
                "entryID": 2,
                "definition": "word",
                "word": "ord",
                "audio_description_0": "Aidan Pine",
                "audio_filename_0": "ord.mp3",
                "theme": "abstract",
                "optional_Part of Speech": "noun",
                "compare_form": "ord",
                "sort_form": "ord",
            },
            {
                "entryID": 1,
                "definition": "tree",
                "word": "træ",
                "audio_description_0": "Aidan Pine",
                "audio_filename_0": "tree.mp3",
                "theme": "plants",
                "optional_Part of Speech": "noun",
                "compare_form": "tre",
                "sort_form": "træ",
            },
        ]

    def test_tabular_parsers(self):
        for format in self.formats_supported:
            language_config_path = self.data_dir / f"config_{format}.json"
            config = load_mtd_configuration(language_config_path)
            mtd_config = MTDConfiguration(**config)
            dictionary = MTDictionary(mtd_config)
            data = dictionary.data.to_dict(orient="records")
            self.assertEqual(data[0]["word"], "farvel")
            self.assertEqual(data[3]["word"], "træ")
            self.assertEqual(data, self.reference_data)

    def test_json_parser(self):
        pass

    def test_custom_parser(self):
        language_config_path = self.data_dir / "config_custom.json"
        config = load_mtd_configuration(language_config_path)
        mtd_config = MTDConfiguration(**config)
        # Will raise a NotImplementedError if initialize without custom parse function
        with self.assertRaises(NotImplementedError):
            dictionary = MTDictionary(mtd_config)
        dictionary = MTDictionary(mtd_config, custom_parse_method=_custom_parser)
        data = dictionary.data.to_dict(orient="records")
        self.assertEqual(data[0]["word"], "farvel")
        self.assertEqual(data[3]["word"], "træ")
        dictionary_no_init = MTDictionary(
            mtd_config, parse_data_on_initialization=False
        )
        dictionary_no_init.custom_parse_method = MethodType(
            _custom_parser_method, dictionary_no_init
        )
        dictionary_no_init.initialize()
        data_from_no_init = dictionary_no_init.data.to_dict(orient="records")
        self.assertEqual(data_from_no_init[0]["word"], "farvel")
        self.assertEqual(data_from_no_init[3]["word"], "træ")
        # self.assertEqual(data, self.reference_data)

    def test_no_parser(self):
        language_configuration = LanguageConfiguration()
        data = DataSource(manifest=ResourceManifest(), resource=self.reference_data)
        mtd_config = MTDConfiguration(config=language_configuration, data=[data])
        return MTDictionary(mtd_config)

    def test_misconfigured_parser_targets(self):
        pass

    def test_prepending_paths(self):
        language_configuration = LanguageConfiguration()
        data_plus_img = self.reference_data
        data_plus_img[0]["img"] = "test.jpg"
        data = DataSource(
            manifest=ResourceManifest(
                img_path="http://bar.foo//", audio_path="https://foo.bar"
            ),
            resource=data_plus_img,
        )
        mtd_config = MTDConfiguration(config=language_configuration, data=[data])
        dictionary = MTDictionary(mtd_config)
        data = dictionary.data.to_dict(orient="records")
        self.assertEqual(data[1]["audio_filename_0"], "https://foo.bar/hej.mp3")
        self.assertEqual(data[0]["img"], "http://bar.foo/test.jpg")
