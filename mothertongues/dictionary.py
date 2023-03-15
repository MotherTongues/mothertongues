from typing import List

import pandas as pd
from pydantic import BaseConfig, validator

from mothertongues.config.models import DataSource, MTDConfiguration, Transducer
from mothertongues.utils import extract_parser_targets


class MTDictionary(BaseConfig):
    config: MTDConfiguration
    """The Configuration for your Dictionary"""

    data: pd.DataFrame
    """Your Dictionary Data as a Pandas Dataframe"""

    def __init__(self, config: MTDConfiguration, **kwargs):
        """Create Data Frame from Config"""
        self.config = config
        self.data = None
        for data_source in self.config.data:
            # Parse Data
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
        super().__init__(**kwargs)

    def __len__(self):
        return len(self.data.index)

    def __getitem__(self, position):
        return self.data.iloc[[position]]

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

        parser_targets = extract_parser_targets(data_source.manifest.targets.dict())
        # parse raw data
        if data_source.manifest.file_type.value == "custom":
            return self.custom_parse_method(data_source)
        elif isinstance(data_source.resource, list):
            df = pd.DataFrame(data_source.resource)
            # assume parser targets are accurate if passing in raw data. # TODO: validate
        # TODO: refactor to drier code
        elif data_source.manifest.file_type.value == "csv":
            df = pd.read_csv(data_source.resource, header=None)
            df.rename(
                columns={int(v): k for k, v in parser_targets.items() if v is not None},
                inplace=True,
            )
        elif data_source.manifest.file_type.value == "psv":
            df = pd.read_csv(data_source.resource, delimiter="|", header=None)
            df.rename(
                columns={v: k for k, v in parser_targets.items() if v is not None},
                inplace=True,
            )
            # TODO: add test data
        elif data_source.manifest.file_type.value == "tsv":
            df = pd.read_csv(data_source.resource, delimiter="\t", header=None)
            df.rename(
                columns={v: k for k, v in parser_targets.items() if v is not None},
                inplace=True,
            )
            # TODO: add test data
        elif data_source.manifest.file_type.value == "xlsx":
            df = pd.read_excel(data_source.resource, header=None)
            # TODO: add test data and allow for A / B  C lettered columns
        elif data_source.manifest.file_type.value == "json":
            df = pd.read_json(data_source.resource)
            # TODO: decide if we're keeping this... maybe not...
        return df

    @validator("data")
    def check_duplicates(cls, v):
        return v

    @validator("data")
    def check_missing_chars(cls, v):
        return v

    @validator("data")
    def check_missing_data(cls, v):
        return v
