import csv
import json
import re
from collections import defaultdict
from enum import Enum
from functools import partial
from pathlib import Path
from string import ascii_letters
from typing import Callable, Dict, List, Optional, Tuple, Union
from unicodedata import normalize

from loguru import logger
from pydantic import (
    BaseModel,
    Extra,
    Field,
    FilePath,
    HttpUrl,
    ValidationError,
    root_validator,
    validator,
)

from mothertongues.exceptions import ConfigurationError
from mothertongues.utils import string_to_callable


class BaseConfig(BaseModel):
    class Config:
        extra = Extra.forbid


class Audio(BaseConfig):
    description: Optional[str]
    """The location of the description of the audio (including speaker)"""

    filename: str
    """The location of the audio filename. Path is prepended with ResourceManifest.audio_path"""


class NormalizationEnum(str, Enum):
    nfc = "NFC"
    nfd = "NFD"
    nkfc = "NFKC"
    nkfd = "NKFD"
    none = "none"


class SearchAlgorithms(str, Enum):
    weighted_levenstein = "weighted_levenstein"
    liblevenstein_automata = "liblevenstein_automata"


class WeightedLevensteinConfig(BaseConfig):
    insertionCost: float = 1.0
    deletionCost: float = 1.0
    insertionAtBeginningCost: float = 0.5
    deletionAtEndCost: float = 0.5
    substitutionCosts: Dict[str, Dict[str, float]] = {}
    substitutionCostsPath: Optional[FilePath] = None
    defaultSubstitutionCost: float = 1.0

    def _convert_list_to_sub_costs(self, data: List[Tuple[str, str, float]]):
        sub_costs: Dict[str, Dict[str, float]] = defaultdict(dict)
        for item in data:
            sub_costs[str(item[0])][str(item[1])] = float(item[2])
        return sub_costs

    @root_validator(pre=True)
    def convert_sub_costs(cls, values):
        if (
            "substitutionCostsPath" in values
            and values["substitutionCostsPath"] is not None
        ):
            v_path = Path(values["substitutionCostsPath"])
            assert v_path.exists(), f"{v_path} does not exist"
            if v_path.suffix == ".json":
                with open(v_path, encoding="utf8") as f:
                    data = json.load(f)
                values["substitutionCosts"] = cls._convert_list_to_sub_costs(cls, data)
            if v_path.suffix == ".xlsx":
                with open(v_path, encoding="utf8") as f:
                    data = json.load(f)
                values["substitutionCosts"] = cls._convert_list_to_sub_costs(cls, data)
            if v_path.suffix.endswith("sv"):
                delimiter = None
                if v_path.suffix == ".csv":
                    delimiter = ","
                elif v_path.suffix == ".psv":
                    delimiter = "|"
                elif v_path.suffix == ".tsv":
                    delimiter = "\t"
                assert (
                    delimiter is not None
                ), "Sorry, can only handle comma, tab or pipe separated values"
                with open(v_path, encoding="utf8") as f:
                    reader = csv.reader(f, delimiter=delimiter)
                    data = list(reader)
                    values["substitutionCosts"] = cls._convert_list_to_sub_costs(
                        cls, data
                    )
        return values


class StemmerEnum(str, Enum):
    snowball_english = "snowball_english"
    none = "none"


class RestrictedTransducer(BaseConfig):
    lower: bool = True
    unicode_normalization: NormalizationEnum = NormalizationEnum.nfc
    remove_punctuation: str = "[.,/#!$%^&?*';:{}=\\-_`~()]"
    replace_rules: Optional[List[Dict[str, str]]] = None


def create_restricted_transducer(config: RestrictedTransducer) -> Callable:
    """Create a callable function from the Restricted Transducer configuration.
       It's restricted because the same functionality needs to be available on the client.

    Args:
        config (RestrictedTransducer): pre-defined acceptable transductions

    Returns:
        Callable: a callable that takes one argument (string) and returns the transduced string
    """
    callables = []
    if config.lower:
        callables.append(lambda x: x.lower())
    if config.unicode_normalization != NormalizationEnum.none:
        callables.append(partial(normalize, config.unicode_normalization.value))
    if config.remove_punctuation:
        callables.append(partial(re.sub, re.compile(config.remove_punctuation), ""))
    if config.replace_rules:

        def replace(term):
            for inp, outp in config.replace_rules.items():
                term = re.sub(inp, outp, term)
            return term

        callables.append(replace)
    if not callables:
        callables.append(lambda x: x)

    def new_callable(text):
        for callable in callables:
            text = callable(text)
        return text

    return new_callable


class Transducer(BaseConfig):
    input_field: str
    """The fieldname to use as the input for the transducer"""

    output_field: str
    """The fieldname for the transducer to write its output to"""

    functions: List[Callable]

    @validator("functions", always=True, pre=True)
    def convert_callables(cls, v, values):
        funcs = []
        for func in v:
            func = string_to_callable(func)
            funcs.append(func)
        values["functions"] = funcs
        return funcs


class ParserEnum(Enum):
    json = "json"
    csv = "csv"
    psv = "psv"
    tsv = "tsv"
    xlsx = "xlsx"
    custom = "custom"
    none = "none"  # for when object is passed directly with no parser needed


class Contributor(BaseConfig):
    role: str
    """What is this contributors role?"""

    name: str
    """What is their name?"""


class CheckableParserTargetFieldNames(Enum):
    word = "word"
    definition = "definition"
    entryID = "entryID"
    theme = "theme"
    secondary_theme = "secondary_theme"
    img = "img"
    audio = "audio"
    definition_audio = "definition_audio"
    example_sentence = "example_sentence"
    example_sentence_definition = "example_sentence_definition"
    example_sentence_audio = "example_sentence_audio"
    example_sentence_definition_audio = "example_sentence_definition_audio"
    optional = "optional"


class ParserTargets(BaseConfig):
    """Your ParserTargets define how to parse your data into a list of DictionaryEntry objects"""

    word: str
    """The location of the words in your dictionary"""

    definition: str
    """The location of the definitions in your dictionary"""

    entryID: Optional[str]
    """The location of the unique IDs in your dictionary. If None, ID's will be automatically assigned."""

    theme: Optional[str]
    """The location of the main theme to group the entry under."""

    secondary_theme: Optional[str]
    """The location of the secondary theme to group the entry under."""

    img: Optional[str]
    """The location of the image path associated with the entry. Path is prepended with ResourceManifest.img_path"""

    # Dict is used in case of json listof parser syntax
    audio: Optional[Union[List[Audio], Dict]]
    """The location of the audio associated with the entry."""

    definition_audio: Optional[Union[List[Audio], Dict]]
    """The location of the audio associated with the definition of the entry."""

    example_sentence: Optional[Union[List[str], Dict]]
    """The location(s) of any example sentences associated with the entry"""

    example_sentence_definition: Optional[Union[List[str], Dict]]
    """The location(s) of any example sentence definitions associated with the entry"""

    example_sentence_audio: Optional[Union[List[Audio], Dict]]
    """The location of the audio associated with the example sentences of the entry."""

    example_sentence_definition_audio: Optional[Union[List[Audio], Dict]]
    """The location of the audio associated with the example sentence definitions of the entry."""

    optional: Optional[Dict[str, str]]
    """A list of information to optionally display"""

    # @root_validator
    # def check_example_sentence_fields_are_same_length(cls, values):
    #     # TODO: implement
    #     return values

    # @root_validator
    # def warn_that_functionality_is_limited_if_none(cls, v):
    #     # TODO: test
    #     if v is None:
    #         logger.warning(
    #             f"Your configuration didn't include a value for {v}, you may not have full functionality in your dictionary."
    #         )
    #     return v


class DictionaryEntry(BaseModel):
    """There is a DictionaryEntry created for each entry in your dictionary.
    It intentionally shares the same data structure as the ParserTargets,
    but allows for extra fields.
    """

    word: str
    """The words in your dictionary"""

    definition: str
    """The definitions in your dictionary"""

    entryID: Optional[str]
    """The unique IDs for entries in your dictionary. If None, ID's will be automatically assigned."""

    theme: Optional[str] = ""
    """The main theme to group the entry under."""

    secondary_theme: Optional[str] = ""
    """The secondary theme to group the entry under."""

    img: Optional[str] = ""
    """The image path associated with the entry. Path is prepended with ResourceManifest.img_path"""

    audio: Optional[List[Audio]] = []
    """The audio associated with the entry."""

    definition_audio: Optional[List[Audio]] = []
    """The audio associated with the definition of the entry."""

    example_sentence: Optional[List[str]] = []
    """The example sentences associated with the entry"""

    example_sentence_definition: Optional[List[str]] = []
    """The example sentence definitions associated with the entry"""

    example_sentence_audio: Optional[List[Audio]] = []
    """The audio associated with the example sentences of the entry."""

    example_sentence_definition_audio: Optional[List[Audio]] = []
    """The audio associated with the example sentence definitions of the entry."""

    optional: Optional[Dict[str, str]] = {}
    """A list of information to optionally display"""

    class Config:
        extra = Extra.allow


class ResourceManifest(BaseConfig):
    file_type: ParserEnum = ParserEnum.none
    """The type of parser to use to parse the resource"""

    name: str = "YourData"
    """The name/source of your dataset"""

    skip_header: bool = False
    """Whether to skip the header when parsing. Applies to spreadsheet formats"""

    transducers: List[Transducer] = []
    """A list of Transducers to apply to your data"""

    audio_path: Optional[HttpUrl]
    """This is a path to your audio files that will be pre-pended to each audio path"""

    img_path: Optional[HttpUrl]
    """This is a path to your image files that will be pre-pended to each image path"""

    targets: Optional[ParserTargets]
    """The ParserTargets for parsing the resource. They are optional if providing a custom parser method"""

    sheet_name: Optional[str]
    """The sheet name; only used for xlsx parsers since workbooks can have multiple sheets"""

    json_parser_entrypoint: Optional[str]
    """The entrypoint for parsing json; only used with json parsers when the json is nested and you only want to parse something further down in the tree"""

    @root_validator(pre=True)
    def targets_none_only_if_custom_parser(cls, values):
        targets, file_type = values.get("targets"), values.get("file_type")

        if targets is None and file_type not in [
            ParserEnum.none,
            ParserEnum.custom,
            ParserEnum.none.value,
            ParserEnum.custom.value,
            None,
        ]:
            raise ConfigurationError(
                "Targets cannot be None if the parser is not using a custom parser."
            )
        return values

    @validator("audio_path", "img_path")
    def check_paths_are_pingable(cls, v):
        return v

    @root_validator
    def warn_that_functionality_is_limited_if_none(cls, v):
        if v is None:
            logger.warning(
                f"Your configuration didn't include a value for {v}, you may not have full functionality in your dictionary."
            )
        return v


class LanguageConfiguration(BaseConfig):
    L1: str = "YourLanguage"
    """The Language of Your Dictionary"""

    L2: str = "English"
    """The Other Language of Your Dictionary"""

    l1_search_strategy: SearchAlgorithms = SearchAlgorithms.weighted_levenstein

    l2_search_strategy: SearchAlgorithms = SearchAlgorithms.liblevenstein_automata

    l1_search_config: Optional[WeightedLevensteinConfig] = Field(
        default_factory=WeightedLevensteinConfig
    )

    l2_search_config: Optional[WeightedLevensteinConfig]

    l1_keys_to_index: List[str] = [CheckableParserTargetFieldNames.word.value]

    l2_keys_to_index: List[str] = [CheckableParserTargetFieldNames.definition.value]

    l1_stemmer: StemmerEnum = StemmerEnum.none

    l2_stemmer: StemmerEnum = StemmerEnum.snowball_english

    l1_normalization_transducer: RestrictedTransducer = Field(
        default_factory=RestrictedTransducer
    )
    """The transducer for creating the 'normalized' form for l1"""

    l2_normalization_transducer: RestrictedTransducer = Field(
        default_factory=RestrictedTransducer
    )
    """The transducer for creating the 'normalized' form for l2"""

    alphabet: Union[List[str], FilePath] = list(ascii_letters)
    """The Symbols/Letters present in Your Dictionary"""

    duplicate_fields_subset: List[CheckableParserTargetFieldNames] = [
        CheckableParserTargetFieldNames.word,
        CheckableParserTargetFieldNames.entryID,
    ]
    """The subset of fields to consider when removing duplicates"""

    required_fields: List[CheckableParserTargetFieldNames] = [
        CheckableParserTargetFieldNames.word,
        CheckableParserTargetFieldNames.definition,
    ]
    """The name of required truthy fields"""

    display_field: str = "word"
    """The fieldname to display"""

    compare_field: str = "compare_form"
    """The fieldname to pass to the approximate search algorithm"""

    sorting_field: str = "sort_form"
    """The fieldname to pass to the sorting algorithm"""

    optional_field_name: str = "Optional Field"
    """The display name for the optional field"""

    credits: Optional[List[Contributor]] = None
    """Add a list of contributors to this project"""

    build: str = "mothertongues.utils.get_current_time"
    """The build identifier for your dictionary build"""

    @root_validator
    def warn_that_functionality_is_limited_if_none(cls, v):
        if v is None:
            logger.warning(
                f"Your configuration didn't include a value for {v}, you may not have full functionality in your dictionary."
            )
        return v

    @validator("build", always=True, pre=True)
    def convert_callable_build(cls, v, values):
        """Take the build argument (string) and if it's in dot notation,
           convert it to a callable and call it.

        Args:
            v (_type_): the build value
            values (_type_): all values

        Returns:
            string: the called value of the build function (if it's not a function, just return the string)
        """
        v = string_to_callable(v)
        if callable(v):
            v = v()
            values["build"] = v
        return v

    @validator("alphabet")
    def load_alphabet(cls, v, values):
        """Load the alphabet

        Args:
            v (_type_): _description_
            values (_type_): _description_

        Returns:
            list[str]: The alphabet as a list
        """
        if isinstance(v, Path):
            if v.suffix.endswith("json"):
                with open(v, encoding="utf8") as f:
                    return json.load(f)
            if v.suffix.endswith("txt"):
                with open(v, encoding="utf8") as f:
                    return [x.strip() for x in f]
            raise ValidationError(
                "If providing a file with your alphabet, it must be either 'json' or 'txt'."
            )
        return v


class DataSource(BaseConfig):
    manifest: ResourceManifest
    """The manifest describing how to parse your data"""

    resource: Union[FilePath, List[dict], List[DictionaryEntry]]
    """The data or a path to the data"""

    @validator("resource")
    def check_data_is_parsable(cls, v):
        return v

    @root_validator
    def data_is_valid(cls, values):
        """Validates:
        - Data is parsable
        - ParserTargets are of the valid type given file_type
        - ParserTargets exist in data"""
        if (
            values
            and "resource" in values
            and isinstance(values["resource"], Path)
            and not values["resource"].exists()
        ):
            raise  # TODO: what should this raise?

        return values


class MTDConfiguration(BaseConfig):
    config: LanguageConfiguration
    """The Configuration for your Language"""

    data: Union[DataSource, List[DataSource]]
    """The data sources for your dictionary"""
