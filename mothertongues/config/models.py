from enum import Enum
from string import ascii_letters
from typing import Callable, List, Union

from loguru import logger
from pandas import DataFrame
from pydantic import BaseModel, Extra, FilePath, HttpUrl, root_validator, validator


class BaseConfig(BaseModel):
    class Config:
        extra = Extra.forbid


class Audio(BaseConfig):
    speaker: Union[None, str] = None
    """The location of the speaker of the audio"""

    filename: str
    """The location of the audio filename. Path is prepended with ResourceManifest.audio_path"""


class Transducer(BaseConfig):
    input_field: str
    """The fieldname to use as the input for the transducer"""

    output_field: str
    """The fieldname for the transducer to write its output to"""

    functions: List[Callable]


class ParserEnum(Enum):
    json = "json"
    csv = "csv"
    psv = "psv"
    tsv = "tsv"
    xlsx = "xlsx"


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

    audio: Union[Audio, None] = None
    """The location of the audio associated with the entry."""

    definition_audio: Union[Audio, None] = None
    """The location of the audio associated with the definition of the entry."""

    example_sentence: Union[List[str], None]
    """The location(s) of any example sentences associated with the entry"""

    example_sentence_definition: Union[List[str], None]
    """The location(s) of any example sentences associated with the entry"""

    example_sentence_audio: Union[List[Union[Audio, None]], None] = None
    """The location of the audio associated with the example sentences of the entry."""

    example_sentence_definition_audio: Union[List[Union[Audio, None]], None] = None
    """The location of the audio associated with the example sentence definitions of the entry."""

    @root_validator
    def check_example_sentence_fields_are_same_length(cls, values):
        return values

    @validator()
    def warn_that_functionality_is_limited_if_none(cls, v):
        if v is None:
            logger.warning(
                f"Your configuration didn't include a value for {v}, you may not have full functionality in your dictionary."
            )
        return v


class ResourceManifest(BaseConfig):
    file_type: Union[None, ParserEnum] = None
    """The type of file to parse. None if data is passed as object"""

    name: str = "YourData"
    """The name/source of your dataset"""

    display_field: str = "word"
    """The fieldname to display"""

    compare_field: str = "compare_form"
    """The fieldname to pass to the approximate search algorithm"""

    sorting_field: str = "sort_form"
    """The fieldname to pass to the sorting algorithm"""

    skip_header: bool = False
    """TODO: change this to just allow any kwargs to pass to pandas.read_*. Whether to skip the header when parsing. Applies to spreadsheet formats"""

    transducers: List[Transducer]
    """A list of Transducers to apply to your data"""

    audio_path: Union[HttpUrl, None] = None
    """This is a path to your audio files that will be pre-pended to each audio path"""

    img_path: Union[HttpUrl, None] = None
    """This is a path to your image files that will be pre-pended to each image path"""

    targets: ParserTargets

    @validator("audio_path", "img_path")
    def check_paths_are_pingable(cls, v):
        return v

    @validator()
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

    alphabet: Union[List[str], str] = list(ascii_letters)
    """The Symbols/Letters present in Your Dictionary"""

    L1_compare_transducer_name: str
    """TODO: what is this"""

    optional_field_name: str
    """TODO: what is this"""

    credits: Union[List[Contributor], None] = None
    """Add a list of contributors to this project"""

    build: str
    """The build identifier for your dictionary build"""

    @validator()
    def warn_that_functionality_is_limited_if_none(cls, v):
        if v is None:
            logger.warning(
                f"Your configuration didn't include a value for {v}, you may not have full functionality in your dictionary."
            )
        return v


class DataSource(BaseConfig):
    manifest: ResourceManifest
    """The manifest describing how to parse your data"""

    data: Union[FilePath, List[dict]]
    """The data or a path to the data"""

    @validator("data")
    def check_data_is_parsable(cls, v):
        return v

    @root_validator
    def data_is_valid(cls, values):
        """Validates:
        - Data is parsable
        - ParserTargets are of the valid type given file_type
        - ParserTargets exist in data"""
        return values


class MTDConfiguration(BaseConfig):
    config: LanguageConfiguration
    """The Configuration for your Language"""

    data: List[Union[FilePath, DataSource]]
    """The list of data sources for your dictionary"""


class MTDictionary(BaseConfig):
    config: MTDConfiguration
    """The Configuration for your Dictionary"""

    data: DataFrame
    """Your Dictionary Data as a Pandas Dataframe"""

    def __init__(self, **data):
        """Create Data Frame from Config"""
        # TODO: parse data
        # TODO: transduce
        # TODO: sort
        super().__init__(**data)

    def __len__(self):
        return len(self.data.index)

    def __getitem__(self, position):
        return self.data.iloc[[position]]

    @validator("data")
    def check_duplicates(cls, v):
        return v

    @validator("data")
    def check_missing_chars(cls, v):
        return v

    @validator("data")
    def check_missing_data(cls, v):
        return v
