from collections import Counter
from typing import Callable, List, Union
from urllib.parse import urljoin

from rich import print
from rich.align import Align
from rich.console import Group
from rich.padding import Padding
from rich.panel import Panel
from rich.table import Table
from tqdm import tqdm

from mothertongues.config.models import (
    CheckableParserTargetFieldNames,
    DataSource,
    DictionaryEntry,
    MTDConfiguration,
    MTDExportFormat,
    ParserEnum,
    Transducer,
)
from mothertongues.exceptions import ConfigurationError
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
        self.missing_data: List[str] = []
        self.duplicates: List[str] = []
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
                data = data_source.resource
            else:
                data = self.parse(data_source)

            for i, entry in enumerate(data):
                if not isinstance(entry, DictionaryEntry):
                    entry = DictionaryEntry(**entry)
                # Add entryID if it was not provided.
                if entry.entryID is None:
                    entry.entryID = str(i)
                # Prepend image path
                if data_source.manifest.img_path and entry.img:
                    entry.img = urljoin(data_source.manifest.img_path, entry.img)
                # Prepend audio paths
                if data_source.manifest.audio_path and entry.audio:
                    for audio_i in range(len(entry.audio)):
                        entry.audio[audio_i].filename = urljoin(
                            data_source.manifest.audio_path,
                            entry.audio[audio_i].filename,
                        )
                # Add the source
                entry.source = data_source.manifest.name
                entry.entryID = entry.source + entry.entryID
                # Convert back to dict
                data[i] = entry.dict()

            # Transduce Data
            data = self.transduce(data, data_source.manifest.transducers)
            if self.data is None:
                self.data = data
            else:
                self.data += data
        # Sort
        if self.data is not None:
            self.sorter = ArbSorter(
                self.config.config.alphabet, self.config.config.no_sort_characters
            )
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
        return (
            self.custom_parse_method(data_source)
            if data_source.manifest.file_type == ParserEnum.custom
            else parse(data_source)
        )

    def check_data(self):
        """
        Returns:
            _type_: _description_
        """
        # find missing data and duplicates
        required_fields = [x.value for x in self.config.config.required_fields]
        duplicate_fields = {
            x.value: Counter() for x in self.config.config.duplicate_fields_subset
        }
        to_delete = []
        for i, entry in tqdm(
            enumerate(self.data),
            desc=f"Finding duplicates and entries that are missing fields for {', '.join(required_fields)}",
        ):
            truthy_fields = [bool(entry[field]) for field in required_fields]
            duplicate = False
            missing_fields = False
            for key, counter in duplicate_fields.items():
                counter.update([entry[key]])
                if counter[entry[key]] > 1:
                    self.duplicates.append(
                        entry[CheckableParserTargetFieldNames.entryID.value]
                    )
                    duplicate = True
                    break
            if not all(truthy_fields):
                self.missing_data.append(
                    entry[CheckableParserTargetFieldNames.entryID.value]
                )
                missing_fields = True
            if duplicate or missing_fields:
                to_delete.append(i)
        to_delete.sort(reverse=True)
        for item in to_delete:
            del self.data[item]
        self.duplicates = list(self.duplicates)
        self.missing_data = list(set(self.missing_data))
        # missing chars
        self.missing_chars = set(self.sorter.oovs)
        return True

    def print_info(self):
        if not self.data:
            print(
                Padding(
                    Panel(
                        "",
                        title="Nothing here, your dictionary is empty!",
                        subtitle="Please check your data and configurations.",
                    ),
                    (2, 4),
                )
            )
        n_entries = len(self.data)
        n_dupes = len(self.duplicates)
        n_missing = len(self.missing_data)
        n_oov_chars = len(self.missing_chars)
        dupe_ratio = n_dupes / n_entries
        colors = {"duplicates": "", "missing": "", "oov_chars": ""}
        warning = False
        severe_warning = False
        # provide warnings if too many duplicates
        if dupe_ratio > 0.05 or n_dupes > 100:
            warning = True
            colors["duplicates"] = "[yellow]"
            if dupe_ratio > 0.25 or n_dupes > 1000:
                severe_warning = True
                colors["duplicates"] = "[red]"
        # provide severe warnings if too many duplicates
        if n_missing > 0.05 or n_missing > 100:
            warning = True
            colors["missing"] = "[yellow]"
            if n_missing > 0.25 or n_missing > 1000:
                severe_warning = True
                colors["missing"] = "[red]"
        if n_oov_chars > 5:
            warning = True
            colors["oov_chars"] = "[yellow]"
            if n_oov_chars > 25:
                severe_warning = True
                colors["oov_chars"] = "[red]"
        title = "[green]Congratulations"
        subtitle = "Documentation:  [link=https://docs.mothertongues.org]https://docs.mothertongues.org[/link]"
        if warning:
            title = "[yellow]Congratulations - but your dictionary needs checking"
        if severe_warning:
            title = (
                "[red]Watch out! There are lots of possible errors in your dictionary"
            )
        basic = Padding(
            f"\nYour dictionary for {self.config.config.L1} and {self.config.config.L2} has {n_entries} entries.",
            (2, 2),
        )
        dupe_fields = ", ".join(
            [x.value for x in self.config.config.duplicate_fields_subset]
        )
        required_fields = ", ".join(
            [x.value for x in self.config.config.required_fields]
        )
        body = Align(basic, align="center")

        table = Table(title="Dictionary Information", show_lines=True)

        table.add_column("Description")
        table.add_column("Total")
        table.add_column("Examples")

        # Duplicates
        n_dupes_specs = (
            ", ".join(self.duplicates)[:300] + "..." if self.duplicates else "---"
        )
        table.add_row(
            f"Duplicate Entries\n\nThese entries had duplicate data in the following fields: {dupe_fields}",
            f"{colors['duplicates']}{n_dupes}",
            n_dupes_specs,
        )
        # Missing Data
        n_missing_specs = (
            ", ".join(self.missing_data)[:300] + "..." if self.missing_data else "---"
        )
        table.add_row(
            f"Missing Data\n\nThese entries had data missing in one of the following fields: {required_fields}",
            f"{colors['missing']}{n_missing}",
            n_missing_specs,
        )
        # Missing Characters
        n_oov_specs = ", ".join(self.missing_chars) if self.missing_chars else "---"
        table.add_row(
            "Unexpected Characters\n\nThese characters were not defined in your alphabet",
            f"{colors['oov_chars']}{n_oov_chars}",
            n_oov_specs,
        )
        print(
            Padding(
                Panel(
                    Group(body, Align(table, align="center")),
                    title=title,
                    subtitle=subtitle,
                ),
                (2, 4),
            )
        )

    def export(self):
        config_export = self.config.config.dict(
            include={
                "L1": True,
                "L2": True,
                "alphabet": True,
                "build": True,
                "l1_search_strategy": True,
                "l2_search_strategy": True,
                "l1_search_config": True,
                "l2_search_config": True,
                "l1_stemmer": True,
                "l2_stemmer": True,
                "l1_normalization_transducer": True,
                "l2_normalization_transducer": True,
                "optional_field_name": True,
            }
        )
        if self.index is None:
            self.l1_index = create_inverted_index(self.data, self.config, "l1")
            self.l1_index.build()
            self.l1_index.calculate_scores()
            self.l2_index = create_inverted_index(self.data, self.config, "l2")
            self.l2_index.build()
            self.l2_index.calculate_scores()
        return MTDExportFormat(
            config=config_export,
            sorted_data=self.data,
            l1_index=self.l1_index.data,
            l2_index=self.l2_index.data,
        )