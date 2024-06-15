import csv
import json
import re
from collections import defaultdict
from enum import Enum
from functools import partial
from pathlib import Path
from string import ascii_letters
from typing import (
    Annotated,
    Any,
    Callable,
    Dict,
    List,
    NamedTuple,
    Optional,
    Tuple,
    Union,
)
from unicodedata import normalize
from uuid import UUID

from pydantic import (  # type: ignore
    AnyHttpUrl,
    BaseModel,
    ConfigDict,
    Field,
    FilePath,
    HttpUrl,
    field_validator,
    model_validator,
    parse_obj_as,
)
from typing_extensions import TypedDict

from mothertongues import __file__ as mtd_dir
from mothertongues.exceptions import ConfigurationError, UnsupportedFiletypeError
from mothertongues.utils import string_to_callable

SCHEMA_DIR = Path(mtd_dir).parent / "schemas"


class BaseConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Audio(BaseConfig):
    model_config = ConfigDict(extra="allow")
    description: Optional[str] = None
    """The location of the description of the audio (including speaker)"""

    filename: str
    """The location of the audio filename. Path is prepended with ResourceManifest.audio_path"""


class Video(BaseConfig):
    model_config = ConfigDict(extra="allow")
    description: Optional[str] = None
    """The location of the description of the video"""

    filename: str
    """The location of the video filename. Path is prepended with ResourceManifest.video_path"""


class NormalizationEnum(str, Enum):
    nfc = "NFC"
    nfd = "NFD"
    nkfc = "NFKC"
    nkfd = "NKFD"
    none = "none"


class SearchAlgorithms(str, Enum):
    weighted_levenstein = "weighted_levenstein"
    liblevenstein_automata = "liblevenstein_automata"


WeightValue = Annotated[float, Field(ge=0.0, le=1.0)]


class WeightedLevensteinConfig(BaseConfig):
    insertionCost: WeightValue = 1.0
    deletionCost: WeightValue = 1.0
    insertionAtBeginningCost: WeightValue = 1.0
    deletionAtEndCost: WeightValue = 1.0
    substitutionCosts: Dict[str, Dict[str, WeightValue]] = {}
    substitutionCostsPath: Optional[FilePath] = None
    defaultSubstitutionCost: WeightValue = 1.0

    def _convert_list_to_sub_costs(self, data: List[Tuple[str, str, float]]):
        sub_costs: Dict[str, Dict[str, float]] = defaultdict(dict)
        for item in data:
            sub_costs[str(item[0])][str(item[1])] = float(item[2])
            sub_costs[str(item[1])][str(item[0])] = float(item[2])
        return sub_costs

    @model_validator(mode="before")
    @classmethod
    def convert_sub_costs(cls, values):
        if (
            "substitutionCostsPath" in values
            and values["substitutionCostsPath"] is not None
        ):
            v_path = Path(values["substitutionCostsPath"])
            assert v_path.exists(), f"{v_path} does not exist"
            data = None
            if v_path.suffix == ".json":
                with open(v_path, encoding="utf8") as f:
                    data = json.load(f)
            elif v_path.suffix == ".xlsx":
                with open(v_path, encoding="utf8") as f:
                    data = json.load(f)
            elif v_path.suffix.endswith("sv"):
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
            else:
                raise UnsupportedFiletypeError(
                    v_path,
                    f"The file {v_path} is not a supported filetype for weights or substitution costs. Supported filetypes include json, xlsx, csv, psv, and tsv. Please fix and try again.",
                )
            try:
                if data:
                    values["substitutionCosts"] = cls._convert_list_to_sub_costs(
                        cls, data
                    )
            except IndexError as e:
                raise IndexError(
                    f"The file at {v_path} is not formatted properly. For each entry you must have two characters and a number between 0.0 and 1.0. They must be separated by a supported delimiter. Please check your file again."
                ) from e
        return values


class StemmerEnum(str, Enum):
    snowball_english = "snowball_english"
    none = "none"


class RestrictedTransducer(BaseConfig):
    lower: bool = True
    unicode_normalization: NormalizationEnum = NormalizationEnum.nfc
    remove_punctuation: str = "[.,/#!$%^&?*';:{}=\\-_`~()]"
    remove_combining_characters: bool = True
    replace_rules: Optional[Dict[str, str]] = None

    def create_callable(self: "RestrictedTransducer") -> Callable:
        """Create a callable function from the Restricted Transducer configuration.
        It's restricted because the same functionality needs to be available on the client.

        Args:
            config (RestrictedTransducer): pre-defined acceptable transductions

        Returns:
            Callable: a callable that takes one argument (string) and returns the transduced string
        """
        callables = []
        if self.lower:
            callables.append(lambda x: x.lower())
        if self.remove_combining_characters:

            def remove_combining_characters(text: str):
                text = normalize("NFD", text)
                return re.sub(
                    r"[\u0300-\u036f]", "", text
                )  # TODO: test, and consider adding the other 4 unicode blocks

            callables.append(remove_combining_characters)
        if self.unicode_normalization != NormalizationEnum.none:
            callables.append(partial(normalize, self.unicode_normalization.value))
        if self.remove_punctuation:
            callables.append(partial(re.sub, re.compile(self.remove_punctuation), ""))
        if self.replace_rules:

            def replace(term):
                for inp, outp in self.replace_rules.items():
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


class ArbitraryFieldRestrictedTransducer(RestrictedTransducer):
    input_field: str
    """The fieldname to use as the input for the transducer"""

    output_field: str
    """The fieldname for the transducer to write its output to"""


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
    video = "video"
    definition_audio = "definition_audio"
    example_sentence = "example_sentence"
    example_sentence_definition = "example_sentence_definition"
    example_sentence_audio = "example_sentence_audio"
    example_sentence_definition_audio = "example_sentence_definition_audio"
    optional = "optional"


class ParserTargets(BaseConfig):
    """Your ParserTargets define how to parse your data into a list of DictionaryEntry objects"""

    model_config = ConfigDict(extra="allow")

    word: str
    """The location of the words in your dictionary"""

    definition: str
    """The location of the definitions in your dictionary"""

    entryID: Optional[str] = None
    """The location of the unique IDs in your dictionary. If None, ID's will be automatically assigned."""

    theme: Optional[str] = None
    """The location of the main theme to group the entry under."""

    secondary_theme: Optional[str] = None
    """The location of the secondary theme to group the entry under."""

    img: Optional[str] = None
    """The location of the image path associated with the entry. Path is prepended with ResourceManifest.img_path"""

    source: Optional[str] = ""
    """The location of the source of the entry. Note that this can be applied on each DataSource in manifest instead"""

    # Dict is used in case of json listof parser syntax
    audio: Optional[Union[List[Audio], Dict]] = None
    """The location of the audio associated with the entry."""

    # Dict is used in case of json listof parser syntax
    video: Optional[Union[List[Video], Dict]] = None
    """The location of the video associated with the entry."""

    # Dict is used in case of json listof parser syntax
    definition_audio: Optional[Union[List[Audio], Dict]] = None
    """The location of the audio associated with the definition of the entry."""

    # Dict is used in case of json listof parser syntax
    example_sentence: Optional[Union[List[str], Dict]] = None
    """The location(s) of any example sentences associated with the entry"""

    # Dict is used in case of json listof parser syntax
    example_sentence_definition: Optional[Union[List[str], Dict]] = None
    """The location(s) of any example sentence definitions associated with the entry"""

    # Dict is used in case of json listof parser syntax
    example_sentence_audio: Optional[Union[List[Union[List[Audio], Dict]], Dict]] = None
    """The location of the audio associated with the example sentences of the entry."""

    # Dict is used in case of json listof parser syntax
    example_sentence_definition_audio: Optional[
        Union[List[Union[List[Audio], Dict]], Dict]
    ] = None
    """The location of the audio associated with the example sentence definitions of the entry."""

    optional: Optional[Dict[str, str]] = None
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

    model_config = ConfigDict(extra="allow")

    word: str
    """The words in your dictionary"""

    definition: str
    """The definitions in your dictionary"""

    entryID: Optional[Union[str, int, UUID]] = None
    """The unique IDs for entries in your dictionary. If None, ID's will be automatically assigned."""

    theme: Optional[str] = ""
    """The main theme to group the entry under."""

    secondary_theme: Optional[str] = ""
    """The secondary theme to group the entry under."""

    img: Optional[str] = ""
    """The image path associated with the entry. Path is prepended with ResourceManifest.img_path"""

    audio: Optional[List[Audio]] = []
    """The audio associated with the entry."""

    video: Optional[List[Video]] = []
    """The video associated with the entry."""

    definition_audio: Optional[List[Audio]] = []
    """The audio associated with the definition of the entry."""

    example_sentence: Optional[List[str]] = []
    """The example sentences associated with the entry"""

    example_sentence_definition: Optional[List[str]] = []
    """The example sentence definitions associated with the entry"""

    example_sentence_audio: Optional[List[List[Audio]]] = []
    """The audio associated with the example sentences of the entry."""

    example_sentence_definition_audio: Optional[List[List[Audio]]] = []
    """The audio associated with the example sentence definitions of the entry."""

    optional: Optional[Dict[str, str]] = {}
    """A list of information to optionally display"""

    source: Optional[str] = ""
    """The source of the entry"""

    @model_validator(mode="after")
    def entryID_to_str(self) -> "DictionaryEntry":
        if self.entryID is not None:
            self.entryID = str(self.entryID)
        return self


class DictionaryEntryExportFormat(BaseModel):
    """There is a DictionaryEntry created for each entry in your dictionary.
    It intentionally shares the same data structure as the ParserTargets,
    but allows for extra fields. This is the same as DictionaryEntry except with
    some specifications for the output format (for example every exported entry will have)
    a value for entryID, and a sorting_form).
    """

    model_config = ConfigDict(extra="allow")

    word: str
    """The words in your dictionary"""

    definition: str
    """The definitions in your dictionary"""

    entryID: str
    """The unique IDs for entries in your dictionary. If None, ID's will be automatically assigned."""

    sorting_form: List[int]
    """The form used to sort entries"""

    theme: Optional[str] = ""
    """The main theme to group the entry under."""

    secondary_theme: Optional[str] = ""
    """The secondary theme to group the entry under."""

    img: Optional[str] = ""
    """The image path associated with the entry. Path is prepended with ResourceManifest.img_path"""

    audio: Optional[List[Audio]] = []
    """The audio associated with the entry."""

    video: Optional[List[Video]] = []
    """The video associated with the entry."""

    definition_audio: Optional[List[Audio]] = []
    """The audio associated with the definition of the entry."""

    example_sentence: Optional[List[str]] = []
    """The example sentences associated with the entry"""

    example_sentence_definition: Optional[List[str]] = []
    """The example sentence definitions associated with the entry"""

    example_sentence_audio: Optional[List[List[Audio]]] = []
    """The audio associated with the example sentences of the entry."""

    example_sentence_definition_audio: Optional[List[List[Audio]]] = []
    """The audio associated with the example sentence definitions of the entry."""

    optional: Optional[Dict[str, str]] = {}
    """A list of information to optionally display"""

    source: Optional[str] = ""
    """The source of the entry"""
    model_config = ConfigDict(extra="allow")


class ResourceManifest(BaseConfig):
    file_type: ParserEnum = ParserEnum.none
    """The type of parser to use to parse the resource"""

    name: str = "YourData"
    """The name/source of your dataset"""

    skip_header: bool = False
    """Whether to skip the header when parsing. Applies to spreadsheet formats"""

    transducers: List[ArbitraryFieldRestrictedTransducer] = []
    """A list of Transducers to apply to your data"""

    audio_path: Optional[HttpUrl] = None
    """This is a path to your audio files that will be pre-pended to each audio path"""

    video_path: Optional[HttpUrl] = None
    """This is a path to your video files that will be pre-pended to each video path"""

    img_path: Optional[HttpUrl] = None
    """This is a path to your image files that will be pre-pended to each image path"""

    targets: Optional[ParserTargets] = None
    """The ParserTargets for parsing the resource. They are optional if providing a custom parser method"""

    sheet_name: Optional[str] = None
    """The sheet name; only used for xlsx parsers since workbooks can have multiple sheets"""

    json_parser_entrypoint: Optional[str] = None
    """The entrypoint for parsing json; only used with json parsers when the json is nested and you only want to parse something further down in the tree"""

    @model_validator(mode="before")
    @classmethod
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

    @field_validator("audio_path", "img_path")
    @classmethod
    def check_paths_are_pingable(cls, v):
        return v


class LanguageConfigurationExportFormat(BaseModel):
    L1: str
    """The Language of Your Dictionary"""

    L2: str
    """The Other Language of Your Dictionary"""

    l1_search_strategy: SearchAlgorithms

    l2_search_strategy: SearchAlgorithms

    l1_search_config: Optional[WeightedLevensteinConfig] = None

    l2_search_config: Optional[WeightedLevensteinConfig] = None

    l1_stemmer: StemmerEnum

    l2_stemmer: StemmerEnum

    l1_normalization_transducer: RestrictedTransducer
    """The transducer for creating the 'normalized' form for l1"""

    l2_normalization_transducer: RestrictedTransducer
    """The transducer for creating the 'normalized' form for l2"""

    alphabet: List[str]
    """The Symbols/Letters present in Your Dictionary"""

    optional_field_name: str
    """The display name for the optional field"""

    credits: Optional[List[Contributor]] = None
    """Add a list of contributors to this project"""

    aboutPageImg: Optional[AnyHttpUrl] = parse_obj_as(
        AnyHttpUrl, "https://placehold.co/600x400"
    )
    """The path to an image for the about page"""

    aboutPageDescription: Optional[
        str
    ] = "Please change this text to describe your dictionary in a bit more detail."
    """A description of your dictionary project to go in the about page"""

    build: str
    """The build identifier for your dictionary build"""

    model_config = ConfigDict(extra="ignore")

    def export(self):
        return self.model_dump(
            mode="json",
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
                "aboutPageDescription": True,
                "aboutPageImg": True,
            },
        )


class LanguageConfiguration(LanguageConfigurationExportFormat):
    L1: str = "YourLanguage"
    """The Language of Your Dictionary"""

    L2: str = "English"
    """The Other Language of Your Dictionary"""

    l1_search_strategy: SearchAlgorithms = SearchAlgorithms.weighted_levenstein

    l2_search_strategy: SearchAlgorithms = SearchAlgorithms.liblevenstein_automata

    l1_search_config: Optional[WeightedLevensteinConfig] = Field(
        default_factory=WeightedLevensteinConfig
    )

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

    alphabet: Union[List[str], FilePath] = list(ascii_letters)  # type: ignore
    """The Symbols/Letters present in Your Dictionary"""

    no_sort_characters: Union[List[str], FilePath] = []
    """Symbols/letters in your data that should be ignored by the sorting algorithm"""

    sorting_field: str = "sort_form"
    """The fieldname to pass to the sorting algorithm"""

    optional_field_name: str = "Optional Field"
    """The display name for the optional field"""

    credits: Optional[List[Contributor]] = None
    """Add a list of contributors to this project"""

    aboutPageImg: Optional[AnyHttpUrl] = parse_obj_as(
        AnyHttpUrl, "https://placehold.co/600x400"
    )
    """The path to an image for the about page"""

    aboutPageDescription: Optional[
        str
    ] = "Please change this text to describe your dictionary in a bit more detail."
    """A description of your dictionary project to go in the about page"""

    build: str = Field(
        default="mothertongues.utils.get_current_time", validate_default=True
    )
    """The build identifier for your dictionary build"""

    l1_keys_to_index: List[str] = [CheckableParserTargetFieldNames.word.value]

    l2_keys_to_index: List[str] = [CheckableParserTargetFieldNames.definition.value]

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

    @field_validator("alphabet", mode="before")
    @classmethod
    def load_alphabet(cls, alphabet: Any):
        """Load the alphabet

        Args:
            v (_type_): _description_
            values (_type_): _description_

        Returns:
            list[str]: The alphabet as a list
        """
        if isinstance(alphabet, str):
            alphabet = Path(alphabet)
        if isinstance(alphabet, Path):
            if alphabet.suffix.endswith("json"):
                with open(alphabet, encoding="utf8") as f:
                    return json.load(f)
            if alphabet.suffix.endswith("txt"):
                with open(alphabet, encoding="utf8") as f:
                    return [x.strip() for x in f]
            raise ValueError(
                f"If providing a file ({alphabet}) with your alphabet, it must be either 'json' or 'txt'."
            )
        return alphabet

    @field_validator("build", mode="before")
    @classmethod
    def convert_callable_build(cls, build: Any):
        """Take the build argument (string) and if it's in dot notation,
        convert it to a callable and call it.

        Args:
            v (_type_): the build value
            values (_type_): all values

        Returns:
            string: the called value of the build function (if it's not a function, just return the string)
        """
        build = string_to_callable(build)
        return build() if callable(build) else build

    model_config = ConfigDict(extra="forbid")


class DataSource(BaseConfig):
    manifest: ResourceManifest
    """The manifest describing how to parse your data"""

    resource: Union[FilePath, List[dict], List[DictionaryEntry]]
    """The data or a path to the data"""

    @field_validator("resource")
    @classmethod
    def check_data_is_parsable(cls, v):
        return v

    @model_validator(mode="after")
    def data_is_valid(self) -> "DataSource":
        """Validates:
        - Data is parsable
        - ParserTargets are of the valid type given file_type
        - ParserTargets exist in data"""
        if self.manifest.file_type == ParserEnum.none and isinstance(
            self.resource, Path
        ):
            raise ConfigurationError(
                "You cannot provide a path to your data if the parser is set 'none', instead you must pass the raw, parsed data."
            )
        if self.manifest.file_type in [
            ParserEnum.csv,
            ParserEnum.psv,
            ParserEnum.tsv,
            ParserEnum.xlsx,
            ParserEnum.json,
        ] and not isinstance(self.resource, Path):
            raise ConfigurationError(
                f"Your parser was set to {self.manifest.file_type} but you provided raw data, instead you must pass a list to your file or change your parser type."
            )
        return self


class Location(NamedTuple):
    entryIndex: str
    positionIndex: int


class MTDConfiguration(BaseConfig):
    config: LanguageConfiguration
    """The Configuration for your Language"""

    data: Union[DataSource, List[DataSource]]
    """The data sources for your dictionary"""


PostingData = TypedDict(
    "PostingData", {"location": List[Location], "score": Dict[str, float]}
)
IndexType = Dict[str, Dict[str, PostingData]]


class MTDExportFormat(BaseConfig):
    config: LanguageConfigurationExportFormat
    data: List[DictionaryEntryExportFormat]
    l1_index: IndexType
    l2_index: IndexType
