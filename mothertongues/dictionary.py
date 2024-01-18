from collections import Counter
from typing import Any, Callable, List, Tuple, Union
from urllib.parse import urljoin

from loguru import logger
from pydantic import ValidationError
from rich import print
from rich.align import Align
from rich.console import Group
from rich.padding import Padding
from rich.panel import Panel
from rich.table import Table
from tqdm import tqdm

from mothertongues.config.models import (
    ArbitraryFieldRestrictedTransducer,
    CheckableParserTargetFieldNames,
    DataSource,
    DictionaryEntry,
    MTDConfiguration,
    MTDExportFormat,
    ParserEnum,
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
        sort_data: bool = True,
        apply_transducers: bool = True,
        **kwargs,
    ):
        """Create Data Frame from Config"""
        if custom_parse_method is not None:
            setattr(self, "custom_parse_method", custom_parse_method)
        self.config = config
        self.missing_data: List[str] = []
        self.duplicates: List[str] = []
        self.unparsable_entries: int = 0
        self.data = None
        self.l1_index = None
        self.l2_index = None
        self.sort_data = sort_data
        self.apply_transducers = apply_transducers
        if parse_data_on_initialization:
            self.initialize()
        super().__init__()

    def __repr__(self):
        n_entries = len(self.data) if self.data else 0
        return f"MTDictionary(L1={self.config.config.L1}, L2={self.config.config.L2}, n_entries={n_entries})"

    def __len__(self):
        return len(self.data)

    def __getitem__(self, position):
        return self.data[position]

    def initialize(self):
        # convert single DataSource to list
        if isinstance(self.config.data, DataSource):
            self.config.data = [self.config.data]
        # Process all data sources
        for i, data_source in enumerate(self.config.data):
            logger.debug(
                "Parsing data source {resource}", resource=data_source.resource
            )
            if data_source.manifest.file_type == ParserEnum.none:
                data = data_source.resource
            else:
                data, unparsable = self.parse(data_source)
                self.unparsable_entries += len(unparsable)
                if unparsable:
                    logger.debug(
                        f"Tried parsing {data_source.resource} but there were {len(unparsable)} unparsable entries."
                    )
            logger.debug("Found {n} entries", n=len(data))
            # create new list so that we only append valid
            # DictionaryEntry objects
            initialized_data = []
            for j, entry in enumerate(data):
                if not isinstance(entry, DictionaryEntry):
                    try:
                        entry = DictionaryEntry(**entry)
                    except ValidationError as err:
                        logger.debug(
                            "Failed to create DictionaryEntry from data {data}: {err}",
                            data=entry,
                            err=err,
                        )
                        self.missing_data.append(
                            entry.get(
                                CheckableParserTargetFieldNames.entryID.value,
                                "NoIDFound",
                            )
                        )
                        continue

                # Prepend media paths
                self.prepend_media_paths(data_source, entry)

                # Add the source
                if not entry.source:
                    entry.source = data_source.manifest.name
                # Add entryID if it was not provided.
                # Add data source and entry index
                if entry.entryID is None:
                    entry.entryID = entry.source + str(i) + str(j)
                # Convert back to dict
                initialized_data.append(entry.model_dump())

            # Transduce Data
            if self.apply_transducers:
                data = self.transduce(
                    initialized_data, data_source.manifest.transducers
                )
            if self.data is None:
                self.data = initialized_data
            else:
                self.data += initialized_data
        # Sort
        if self.sort_data and self.data is not None:
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

    @staticmethod
    def prepend_media_paths(data_source, entry):
        # Prepend image path
        if data_source.manifest.img_path and entry.img:
            entry.img = urljoin(str(data_source.manifest.img_path), str(entry.img))
        # Prepend audio paths
        if data_source.manifest.audio_path and entry.audio:
            for audio_i in range(len(entry.audio)):
                entry.audio[audio_i].filename = urljoin(
                    str(data_source.manifest.audio_path),
                    str(entry.audio[audio_i].filename),
                )
        # Prepend video paths
        if data_source.manifest.video_path and entry.video:
            for video_i in range(len(entry.video)):
                entry.video[video_i].filename = urljoin(
                    str(data_source.manifest.video_path),
                    str(entry.video[video_i].filename),
                )

    def custom_parse_method(
        self, data_source: DataSource
    ) -> Tuple[List[DictionaryEntry], List[Any]]:
        """Custom Parser for your data. This method is meant to be overridden by subclasses.
        To implement, you must parse the targets in self.parser_targets and return a list of DictionaryEntry objects and a list of unparsable objects (i.e. objects that failed being parsed into a DictionaryEntry).

        You can either implement by initializing the MTDictionary object with a custom parse function like so:

        >>> dictionary = MTDictionary(mtd_config: MTDConfiguration, custom_parse_method=custom_parser_function)

        Here, custom_parser_function has to be a function that takes a data_source as its only argument and return a list of DictionaryEntry of the parsed data:

        >>> def custom_parser_function(data_source: DataSource) -> Tuple[List[DictionaryEntry], List[Any]]:
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

        >>>  def custom_parser_method(self: MTDictionary, data_source: DataSource) -> Tuple[List[DictionaryEntry], List[Any]]:
                ...do stuff with self...
                ...parse the data...
                return list_of_entry_data, list_of_unparsable_objects

        Then, don't forget to initialize the data:

        >>> dictionary_no_init.initialize()


        """
        raise NotImplementedError(
            "Your data was specified as 'custom' but the MTDictionary.custom_parse_method was not implemented. You must implement a custom parser for your data."
        )

    def transduce(
        self, data: List[dict], transducers: List[ArbitraryFieldRestrictedTransducer]
    ) -> List[dict]:
        """Transduce the data in the dataframe using the transducers specified in the config"""
        for transducer in transducers:
            transducer_function = transducer.create_callable()
            for datum in data:
                datum[transducer.output_field] = transducer_function(
                    datum[transducer.input_field]
                )
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
        n_entries = len(self.data)
        n_dupes = len(self.duplicates)
        n_missing = len(self.missing_data)
        n_oov_chars = len(self.missing_chars)
        n_missing_ratio = n_missing / n_entries
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
        if n_missing_ratio > 0.05 or n_missing > 100:
            warning = True
            colors["missing"] = "[yellow]"
            if n_missing_ratio > 0.25 or n_missing > 1000:
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

    def build_indices(self):
        self.l1_index = self.return_single_index("l1")
        self.l2_index = self.return_single_index("l2")

    def return_single_index(self, lang: str):
        if lang not in ["l1", "l2"]:
            raise ValueError("Sorry we can only build indices for either 'l1' or 'l2'")
        result = create_inverted_index(self.data, self.config, lang)
        if self.data:
            result.build()
            result.calculate_scores()
        else:
            logger.debug(
                "Sorry your dictionary does not have any entries so we cannot build the index for it."
            )
        return result

    def export(self):
        config_export = self.config.config.export()
        if self.l1_index is None:
            self.l1_index = self.return_single_index("l1")
        if self.l2_index is None:
            self.l2_index = self.return_single_index("l2")
        return MTDExportFormat(
            config=config_export,
            data=self.data,
            l1_index=self.l1_index.data,
            l2_index=self.l2_index.data,
        )
