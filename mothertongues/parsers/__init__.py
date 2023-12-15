import importlib
from typing import List, Tuple, Type, Union, no_type_check

from jsonpath_ng import jsonpath
from loguru import logger
from pydantic import ValidationError
from tqdm import tqdm

from mothertongues.config.models import DataSource, DictionaryEntry
from mothertongues.exceptions import UnsupportedFiletypeError


class BaseTabularParser:
    """
    Parse data for MTD.
    """

    def __init__(self, data_source: DataSource):
        self.resource_path = data_source.resource
        self.manifest = data_source.manifest
        self.parse_fn = lambda x, y: x[int(y)]

    def return_manifest_key_type(
        self, key: str, manifest: dict
    ) -> Union[Type[list], Type[dict], Type[str], Type[None]]:
        """Given a key in a nested dict, return the type of the corresponding value"""
        for k, v in manifest.items():
            if k == key:
                return type([]) if "listof" in v else type(v)
            elif isinstance(v, list):
                for item in v:
                    if (
                        isinstance(item, dict)
                        and self.return_manifest_key_type(key, item) is not None
                    ):
                        return self.return_manifest_key_type(key, item)
                return type(item)
            elif isinstance(v, dict):
                if type(self.return_manifest_key_type(key, v)) is not None:
                    return self.return_manifest_key_type(key, v)
        return type(None)

    def validate_type(self, k, v):
        """Some parsers like lxml and jsonpath_ng return lists when the data manifest does not specify a list, this corrects that."""
        if type(v) == list and len(v) == 1 and type(v[0]) == jsonpath.DatumInContext:
            v = v[0].value
        if (
            isinstance(v, list)
            and len(v) == 1
            and self.return_manifest_key_type(
                k, self.manifest.targets.model_dump(exclude_none=True)
            )
            != list
        ):
            return v[0]
        else:
            return v

    def fill_entry_template(
        self, entry_template: dict, entry, convert_function
    ) -> dict:
        """This recursive function hydrates the data according to the resource manifest. It is used by all parsers.

        Args:
            :param dict entry_template: The template for an entry. Keys are preserved, values are usually paths in the resource to data (JSONPath, XPath or Cell coordinates etc)
            :param any entry: The actual word/entry to extract some data from. This could be a row, or json dict or any piece of nested data from the data resource.
            :param function convert_function: A function that takes an entry and a path and returns the "filled in" object
        """
        new_lemma = {}
        for k, v in entry_template.items():
            if isinstance(v, dict):
                new_lemma[k] = self.fill_entry_template(v, entry, convert_function)
            elif isinstance(v, list):
                new_lemma[k] = []  # type: ignore
                for x in v:
                    values = self.fill_entry_template(
                        {k: x}, entry, convert_function
                    ).values()
                    for y in values:
                        # don't add dictionaries that only have empty values
                        if isinstance(y, dict) and not any(y.values()):
                            continue
                        new_lemma[k].append(y)  # type: ignore
            elif isinstance(v, str):
                if v == "":
                    new_lemma[k] = ""  # type: ignore
                    continue
                try:
                    new_lemma[k] = convert_function(entry, v.strip())
                except IndexError:
                    # TODO: maybe supress this with a verbose=False flag, or return the entries
                    # with missing data instead for review?
                    logger.warning(
                        f"Entry {entry} does not have a column '{k}'. Assigning null value."
                    )
                    new_lemma[k] = ""  # type: ignore
                    continue
        return new_lemma

    @no_type_check
    def resolve_targets(self) -> List[dict]:
        # not type checking because targets.dict() complains, but targets is only none with custom parser
        # also, self.resource is created by the classes that inherit the base parser.
        targets = self.manifest.targets.model_dump(exclude_none=True)
        return [
            self.fill_entry_template(targets, entry, self.parse_fn)
            for entry in tqdm(self.resource, desc="Parsing data")
        ]

    def parse(self) -> Tuple[List[dict], List[dict]]:
        data = self.resolve_targets()
        logger.debug("Resolved {n} targets", n=len(data))
        unparsable = []
        for i in reversed(range(len(data))):
            try:
                data[i] = DictionaryEntry(**data[i])  # type: ignore
            except ValidationError as err:
                logger.debug(
                    "Failed to create DictionaryEntry from data {data}: {err}",
                    data=data[i],
                    err=err,
                )
                unparsable.append(data[i])
                del data[i]
                continue
        return data, unparsable


def parse(data_source: DataSource):
    # load the right parser module or throw error if not supported.
    rel_module = f".{data_source.manifest.file_type.name}_parser"
    try:
        filetype_module = importlib.import_module(rel_module, "mothertongues.parsers")
    except ImportError as e:
        raise UnsupportedFiletypeError(data_source.manifest.file_type.name) from e
    logger.debug(
        "Parsing {resource} with {module}",
        resource=data_source.resource,
        module=filetype_module,
    )
    parser = filetype_module.Parser(data_source)
    return parser.parse()
