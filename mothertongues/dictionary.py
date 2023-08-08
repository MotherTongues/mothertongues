from typing import Callable, List, Union
from urllib.parse import urljoin

from mothertongues.config.models import (
    CheckableParserTargetFieldNames,
    DataSource,
    DictionaryEntry,
    MTDConfiguration,
    ParserEnum,
    Transducer,
)
from mothertongues.exceptions import ConfigurationError, ParserError
from mothertongues.parsers import parse
from mothertongues.processors.index_builder import create_inverted_index
from mothertongues.processors.sorter import ArbSorter


class MTDictionary:
    config: MTDConfiguration
    """The Configuration for your Dictionary"""

    def __init__(
        self,
        config: MTDConfiguration,
        custom_parse_method: Union[Callable, None] = None,
        parse_data_on_initialization: bool = True,
        **kwargs,
    ):
        """Create Data Frame from Config"""
        if custom_parse_method is not None:
            setattr(self, "custom_parse_method", custom_parse_method)
        self.config = config
        self.data = None
        self.index = None
        if parse_data_on_initialization:
            self.initialize()
        super().__init__()

    def __repr__(self):
        return f"MTDictionary(L1={self.config.config.L1}, L2={self.config.config.L2}, n_entries={len(self.data)})"

    def __len__(self):
        return len(self.data)

    def __getitem__(self, position):
        return self.data[position]

    def initialize(self):
        # convert single DataSource to list
        if isinstance(self.config.data, DataSource):
            self.config.data = [self.config.data]
        for data_source in self.config.data:
            if data_source.manifest.file_type == ParserEnum.none:
                try:
                    data = data_source.resource
                except TypeError as e:
                    raise ParserError(
                        "Sorry, please try setting your parser to an appropriate value (ie 'csv' or 'json'), implement a custom parser, or pass valid data."
                    ) from e
            else:
                data = self.parse(data_source)
            # Prepend image and audio paths
            if (
                data_source.manifest.audio_path is not None
                and data_source.manifest.img_path is not None
            ):
                for entry in data:
                    if data_source.manifest.img_path and entry.get("img", None):
                        entry["img"] = urljoin(
                            data_source.manifest.img_path, entry["img"]
                        )
                    if data_source.manifest.audio_path and entry.get("audio", None):
                        for audio_i in range(len(entry["audio"])):
                            entry["audio"][audio_i]["filename"] = urljoin(
                                data_source.manifest.audio_path,
                                entry["audio"][audio_i]["filename"],
                            )
            # Transduce Data
            data = self.transduce(data, data_source.manifest.transducers)
            if self.data is None:
                self.data = data
            else:
                self.data += data
        # Sort
        if self.data is not None:
            self.sorter = ArbSorter(self.config.config.alphabet)
            try:
                self.data = self.sorter(self.data, self.config.config.sorting_field)
            except KeyError as e:
                raise ConfigurationError(
                    f"Sorry, the key '{self.config.config.sorting_field}' is not found in your data, please change the sorting_field to a field name that exists in your data. Your data fieldnames are: {self.data[0].keys()}"
                ) from e
            self.check_data()

    def custom_parse_method(self, data_source: DataSource) -> List[DictionaryEntry]:
        """Custom Parser for your data. This method is meant to be overridden by subclasses.
        To implement, you must parse the targets in self.parser_targets and return a list of DictionaryEntry objects.

        You can either implement by initializing the MTDictionary object with a custom parse function like so:

        >>> dictionary = MTDictionary(mtd_config: MTDConfiguration, custom_parse_method=custom_parser_function)

        Here, custom_parser_function has to be a function that takes a data_source as its only argument and return a list of DictionaryEntry of the parsed data:

        >>> def custom_parser_function(data_source: DataSource) -> List[DictionaryEntry]:
                ...parse the data...
                return list_of_entry_data

        Alternatively, if you need access to the configuration or other parts of the MTDictionary object in order to parse properly,
        you can define a method using MethodType.

        MTDictionary objects automatically parse on initialization by default though, so first create the MTDictionary and supress parsing on initialization:

        >>> dictionary_no_init = MTDictionary(
            mtd_config, parse_data_on_initialization=False
        )
        >>> dictionary_no_init.custom_parse_method = MethodType(
            custom_parser_method, dictionary_no_init
        )

        Where custom_parser_method is a function that takes two arguments and returns a list of DictionaryEntry:

        >>>  def custom_parser_method(self: MTDictionary, data_source: DataSource) -> List[DictionaryEntry]:
                ...do stuff with self...
                ...parse the data...
                return list_of_entry_data

        Then, don't forget to initialize the data:

        >>> dictionary_no_init.initialize()


        """
        raise NotImplementedError(
            "Your data was specified as 'custom' but the MTDictionary.custom_parse_method was not implemented. You must implement a custom parser for your data."
        )

    def transduce(self, data: List[dict], transducers: List[Transducer]) -> List[dict]:
        """Transduce the data in the dataframe using the transducers specified in the config"""
        for transducer in transducers:
            for fn in transducer.functions:
                for datum in data:
                    datum[transducer.output_field] = fn(datum[transducer.input_field])
        return data

    def parse(self, data_source: DataSource) -> List[dict]:
        """Parse the data in the file_path using the parser specified in the config"""
        # parse raw data
        if data_source.manifest.file_type == ParserEnum.custom:
            data = self.custom_parse_method(data_source)
        else:
            data = parse(data_source)
        return [x.dict() for x in data]

    def check_data(self):
        """
        Returns:
            _type_: _description_
        """
        # duplicates
        # missing chars
        self.missing_chars = self.sorter.oovs
        return True

    def export(self, combine=True, hash_data=True):
        config_export = self.config.config.dict(
            include={
                "L1": True,
                "L2": True,
                "alphabet": True,
                "build": True,
                "l1_stemmer": True,
                "l2_stemmer": True,
                "l1_normalization_transducer": True,
                "l2_normalization_transducer": True,
            }
        )
        if self.index is None:
            self.l1_index = create_inverted_index(self.data, self.config, "l1")
            self.l1_index.calculate_scores()
            self.l2_index = create_inverted_index(self.data, self.config, "l2")
            self.l2_index.calculate_scores()
        # TODO: transducers for the config should be built here
        # config_export['transducers'] =
        if hash_data:
            data = {
                entry[CheckableParserTargetFieldNames.entryID.value]: entry
                for entry in self.data
            }
        else:
            data = self.data
        if combine:
            return {
                "config": config_export,
                "data": data,
                "l1_index": self.l1_index.data,
                "l2_index": self.l2_index.data,
            }
        else:
            return config_export, data, self.l1_index.data, self.l2_index.data
