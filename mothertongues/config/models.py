from enum import Enum
from pathlib import Path
from string import ascii_letters
from typing import Callable, Dict, List, Union

from loguru import logger
from pydantic import BaseModel, Extra, FilePath, HttpUrl, root_validator, validator

from mothertongues.utils import string_to_callable


class BaseConfig(BaseModel):
    class Config:
        extra = Extra.forbid


class Audio(BaseConfig):
    description: Union[None, str] = None
    """The location of the description of the audio (including speaker)"""

    filename: str
    """The location of the audio filename. Path is prepended with ResourceManifest.audio_path"""


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
    xml = "xml"
    none = "none"  # for when object is passed directly with no parser needed


class Contributor(BaseConfig):
    role: str
    """What is this contributors role?"""

    name: str
    """What is their name?"""


class ParserTargets(BaseConfig):
    word: str
    """The location of the words in your dictionary"""

    definition: str
    """The location of the definitions in your dictionary"""

    entryID: Union[str, None] = None
    """The location of the unique IDs in your dictionary. If None, ID's will be automatically assigned."""

    theme: Union[str, None] = None
    """The location of the main theme to group the entry under."""

    secondary_theme: Union[str, None] = None
    """The location of the secondary theme to group the entry under."""

    img: Union[str, None] = None
    """The location of the image path associated with the entry. Path is prepended with ResourceManifest.img_path"""

    audio: Union[List[Audio], None] = None
    """The location of the audio associated with the entry."""

    definition_audio: Union[List[Audio], None] = None
    """The location of the audio associated with the definition of the entry."""

    example_sentence: Union[List[str], None] = None
    """The location(s) of any example sentences associated with the entry"""

    example_sentence_definition: Union[List[str], None] = None
    """The location(s) of any example sentences associated with the entry"""

    example_sentence_audio: Union[List[Union[Audio, None]], None] = None
    """The location of the audio associated with the example sentences of the entry."""

    example_sentence_definition_audio: Union[List[Union[Audio, None]], None] = None
    """The location of the audio associated with the example sentence definitions of the entry."""

    optional: Union[Dict[str, str], None] = None
    """A list of information to optionally display"""

    @root_validator
    def check_example_sentence_fields_are_same_length(cls, values):
        return values

    @root_validator
    def warn_that_functionality_is_limited_if_none(cls, v):
        if v is None:
            logger.warning(
                f"Your configuration didn't include a value for {v}, you may not have full functionality in your dictionary."
            )
        return v


class ResourceManifest(BaseConfig):
    file_type: ParserEnum = ParserEnum.none
    """The type of parser to use to parse the resource"""

    name: str = "YourData"
    """The name/source of your dataset"""

    skip_header: bool = False
    """TODO: change this to just allow any kwargs to pass to pandas.read_*. Whether to skip the header when parsing. Applies to spreadsheet formats"""

    transducers: List[Transducer] = []
    """A list of Transducers to apply to your data"""

    audio_path: Union[HttpUrl, None] = None
    """This is a path to your audio files that will be pre-pended to each audio path"""

    img_path: Union[HttpUrl, None] = None
    """This is a path to your image files that will be pre-pended to each image path"""

    targets: Union[ParserTargets, None] = None

    @validator("audio_path", "img_path")
    def check_paths_are_pingable(cls, v):
        return v

    @root_validator
    def targets_none_only_if_custom_parser(cls, v):
        if v["targets"] is None and not v["file_type"].custom:
            raise ValueError(
                "Targets cannot be None if the parser is not using a custom parser."
            )
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

    alphabet: Union[List[str], FilePath] = list(ascii_letters)
    """The Symbols/Letters present in Your Dictionary"""

    display_field: str = "word"
    """The fieldname to display"""

    compare_field: str = "compare_form"
    """The fieldname to pass to the approximate search algorithm"""

    sorting_field: str = "sort_form"
    """The fieldname to pass to the sorting algorithm"""

    optional_field_name: str = "Optional Field"
    """The display name for the optional field"""

    credits: Union[List[Contributor], None] = None
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


class DataSource(BaseConfig):
    manifest: ResourceManifest
    """The manifest describing how to parse your data"""

    resource: Union[FilePath, List[dict]]
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
