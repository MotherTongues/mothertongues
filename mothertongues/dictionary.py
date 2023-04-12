from typing import Callable, List, Union

import pandas as pd
from pydantic import BaseConfig

from mothertongues.config.models import (
    DataSource,
    MTDConfiguration,
    ParserEnum,
    Transducer,
)
from mothertongues.utils import col2int, extract_parser_targets


class MTDictionary(BaseConfig):
    config: MTDConfiguration
    """The Configuration for your Dictionary"""

    def __init__(
        self,
        config: MTDConfiguration,
        custom_parse_method: Union[Callable, None] = None,
        parse_data_on_initialization: bool = True,
        **kwargs
    ):
        """Create Data Frame from Config"""
        if custom_parse_method is not None:
            setattr(self, "custom_parse_method", custom_parse_method)
        self.config = config
        self.data = None
        if parse_data_on_initialization:
            self.initialize()
        super().__init__()

    def __len__(self):
        return len(self.data.index)

    def __getitem__(self, position):
        return self.data.iloc[[position]]

    def initialize(self):
        # convert single DataSource to list
        if isinstance(self.config.data, DataSource):
            self.config.data = [self.config.data]
        for data_source in self.config.data:
            # Parse Data
            if data_source.manifest.file_type == ParserEnum.none:
                df = pd.DataFrame(data_source.resource)
            else:
                df = self.parse(data_source)
            # Transduce Data
            df = self.transduce(df, data_source.manifest.transducers)
            if self.data is None:
                self.data = df
            else:
                self.data.join(df)
        # Sort
        if self.data is not None:
            self.data.sort_values(by=self.config.config.sorting_field, inplace=True)
        self.check_data()

    def custom_parse_method(self, data_source: DataSource) -> pd.DataFrame:
        """Custom Parser for your data. This method is meant to be overridden by subclasses.
        To implement, you must parse the targets in self.parser_targets and return a pandas dataframe.

        TODO: this should be configurable in the config"""
        raise NotImplementedError(
            "Your data was specified as 'custom' but the MTDictionary.custom_parse_method was not implemented. You must implement a custom parser for your data."
        )

    def transduce(
        self, df: pd.DataFrame, transducers: List[Transducer]
    ) -> pd.DataFrame:
        """Transduce the data in the dataframe using the transducers specified in the config"""
        for transducer in transducers:
            for fn in transducer.functions:
                df[transducer.output_field] = df[transducer.input_field].apply(fn)
        return df

    def parse(self, data_source: DataSource) -> pd.DataFrame:
        """Parse the data in the file_path using the parser specified in the config"""
        # parse raw data
        if data_source.manifest.file_type == ParserEnum.custom:
            return self.custom_parse_method(data_source)
        if data_source.manifest.targets is not None:
            parser_targets = extract_parser_targets(data_source.manifest.targets.dict())
        else:
            parser_targets = None
        if isinstance(data_source.resource, list):
            df = pd.DataFrame(data_source.resource)
            # assume parser targets are accurate if passing in raw data. # TODO: validate
        elif data_source.manifest.file_type == ParserEnum.json:
            df = pd.read_json(data_source.resource)
            # TODO: decide if we're keeping this... maybe not...
        elif data_source.manifest.file_type == ParserEnum.xlsx:
            # For some reason pandas doesn't seem to read data in as utf8 for excel
            with open(data_source.resource, "rb") as f:
                df = pd.read_excel(f, header=None)
        else:
            delimiter = ","
            if data_source.manifest.file_type == ParserEnum.psv:
                delimiter = "|"
            elif data_source.manifest.file_type == ParserEnum.tsv:
                delimiter = "\t"
            df = pd.read_csv(
                data_source.resource, delimiter=delimiter, encoding="utf8", header=None
            )
        if parser_targets is not None and data_source.manifest.file_type in [
            ParserEnum.csv,
            ParserEnum.psv,
            ParserEnum.tsv,
            ParserEnum.xlsx,
        ]:
            # rename columns given parser targets
            df = df.rename(
                columns={
                    col2int(v): k for k, v in parser_targets.items() if v is not None
                }
            )
        df = df.fillna("")
        return df

    def check_data(self):
        """Can't implement with Pydantic validators. TODO: maybe this shouldn't be a pydantic config then...


        Returns:
            _type_: _description_
        """
        # duplicates
        # missing chars
        # missing data
        # typechecking
        # TODO: Implement this
        return True


# TODO: turn this into docs
# from types import MethodType

# def custom_parser(self: MTDictionary, data_source: DataSource):
#     return self.config

# dictionary = MTDictionary()
# dictionary.custom_parse_method = MethodType(custom_parser, dictionary)
