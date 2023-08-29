import json
from contextlib import contextmanager
from datetime import datetime
from importlib import import_module
from pathlib import Path
from typing import Callable, Union

import joblib
from g2p import Mapping, Transducer
from g2p.mappings.utils import load_mapping_from_path
from loguru import logger

from mothertongues.exceptions import ConfigurationError


@contextmanager
def tqdm_joblib_context(tqdm_instance):
    """Context manager to make tqdm compatible with joblib.Parallel

    Runs the parallel jobs using joblib, but displays the nicer tqdm progress bar
    Only tested with tqdm.tqdm, but should also work with tqdm.notepad.tqdm and
    other variants

    Usage:
        with tqdm_joblib_context(tqdm(desc="my description", total=len(job_list))):
            joblib.Parallel(n_jobs=cpus)(delayed(fn)(item) for item in job_list)
    """

    class ParallelCallback(joblib.parallel.BatchCompletionCallBack):
        def __call__(self, out):
            tqdm_instance.update(n=self.batch_size)
            super().__call__(out)

    old_callback = joblib.parallel.BatchCompletionCallBack
    joblib.parallel.BatchCompletionCallBack = ParallelCallback
    try:
        yield
    finally:
        tqdm_instance.close()
        joblib.parallel.BatchCompletionCallBack = old_callback


def get_current_time():
    return str(int(datetime.now().timestamp()))


def resolve_relative_path(relative_path: Path, base_path: Path, check_exists=True):
    """Many paths in the configurations are potentially relative, so they need to be resolved.
    This function takes two paths and resolves the relative_path with respect to the base_path."""
    assert base_path.exists()
    if relative_path.is_absolute():
        return relative_path
    resolved_path = (base_path / relative_path).resolve()
    if check_exists and not resolved_path.exists():
        raise FileNotFoundError(
            f"Looked for path {relative_path} relative to {base_path} but it does not exist."
        )
    return resolved_path


def resolve_possible_path(possible_path, other_possible_type, base_path):
    """Helper function for returning a resolved path if it is the right type

    Args:
        possible_path (Any): possibly a path, possibly not
        other_possible_type (Any): This only works if there is only one other possible type. Check mothertongues.config.models
        base_path (Path): the base path to resolve the possible_path relative to

    Returns:
        Any: returns the original or a resolved path
    """
    return (
        possible_path
        if isinstance(possible_path, other_possible_type)
        else resolve_relative_path(Path(possible_path), base_path)
    )


def load_mtd_configuration(path: Path, base_path: Union[None, Path] = None):
    """Load a language configuration and resolve any relative paths.

    Args:
        path (Path): path to configuration file
        base_path (Union[None, Path]): the base path to resolve relative paths by. Defaults to path.
    """
    if base_path is None:
        base_path = path.parent
    config = load_json_from_path(path)
    if "data" not in config or "config" not in config:
        raise ConfigurationError(
            f"Your configuration file at {path} is malformed. It must have both a 'config' and 'data' key."
        )
    if "alphabet" in config["config"]:
        config["config"]["alphabet"] = resolve_possible_path(
            config["config"]["alphabet"], list, base_path
        )
    if "no_sort_characters" in config["config"]:
        config["config"]["no_sort_characters"] = resolve_possible_path(
            config["config"]["no_sort_characters"], list, base_path
        )
    if "l1_search_config" in config["config"] and (
        "substitutionCostsPath" in config["config"]["l1_search_config"]
        and config["config"]["l1_search_config"]["substitutionCostsPath"] is not None
    ):
        config["config"]["l1_search_config"][
            "substitutionCostsPath"
        ] = resolve_relative_path(
            Path(config["config"]["l1_search_config"]["substitutionCostsPath"]),
            base_path,
        )

    if "l2_search_config" in config["config"] and (
        "substitutionCostsPath" in config["config"]["l2_search_config"]
        and config["config"]["l2_search_config"]["substitutionCostsPath"] is not None
    ):
        config["config"]["l2_search_config"][
            "substitutionCostsPath"
        ] = resolve_relative_path(
            Path(config["config"]["l2_search_config"]["substitutionCostsPath"]),
            base_path,
        )

    for i in range(len(config["data"])):
        config["data"][i]["resource"] = resolve_possible_path(
            config["data"][i]["resource"], list, base_path
        )
        manifest = resolve_possible_path(config["data"][i]["manifest"], dict, base_path)
        if not isinstance(manifest, dict):
            config["data"][i]["manifest"] = load_manifest_configuration(manifest)
    return config


def load_manifest_configuration(path: Path, base_path: Union[None, Path] = None):
    """Load a resource manifest and resolve any relative paths.

    Args:
        path (Path): path to manifest
        base_path (Union[None, Path]): the base path to resolve relative paths by. Defaults to path.
    """
    if base_path is None:
        base_path = path.parent
    config = load_json_from_path(path)
    # for each transducer
    for t in range(len(config["transducers"])):
        # for each function belonging to that transducer
        for f in range(len(config["transducers"][t]["functions"])):
            fn = config["transducers"][t]["functions"][f]
            # if it's a string (and not already callable), it could be a lambda function
            # or it could be a function in dot notation, or it could be a path
            if isinstance(fn, str):
                # check if the path exists relative to the base_path. If it does, resolve it
                # as a path. This isn't 100% safe since the path might not exist, but in that case
                # the user should still get a warning and update the path defined in the configuration
                # TODO: make this less hacky
                fn_path = resolve_relative_path(Path(fn), base_path, False)
                if fn_path.exists():
                    config["transducers"][t]["functions"][f] = fn_path
    return config


def load_json_from_path(path: Path):
    with open(path, encoding="utf8") as f:
        return json.load(f)


def string_to_callable(string: Union[Callable, str]) -> Union[str, Callable]:
    """Convert a string to a callable.

    Callable strings can either be :

    - Callable, in which case they are returned
    - start with "lambda" in which case they are eval'ed
    - if they are a path to a yaml file, create a g2p mapping from them
    - dot notation import, like "mothertongues.utils.get_current_time"

    """
    if callable(string):
        return string
    path = Path(string)
    string = str(string)
    if string.startswith("lambda"):
        try:
            return eval(string)
        except SyntaxError as e:
            raise ValueError(
                f"Expected a callable, and was provided something that looked like a lambda function but was invalid: {type(string)}"
            ) from e
    elif path.is_file():
        try:
            # TODO: This should actually be updated in g2p
            mapping_data = load_mapping_from_path(path)
            mapping_data["mapping_path"] = mapping_data["mapping"]
            mapping_data["mapping"] = mapping_data["mapping_data"]
            transducer = Transducer(Mapping(**mapping_data))
            return lambda x: transducer(x).output_string
        except:  # noqa: E722 TODO: find exception
            raise ValueError("Expected file at to be loadable to g2p")
    elif string.endswith(".yaml") or string.endswith(".yml"):
        raise FileNotFoundError(
            f"File '{string}' looks like yaml but does not seem to exist. Please provide an absolute path or a path relative to your configuration file"
        )
    if "." not in string:
        logger.debug(
            f"String must be in the format <module>.<function>. If {string} is actually a string, you can ignore this."
        )
        return string
    module_name, function_name = string.rsplit(".", 1)
    try:
        module = import_module(module_name)
    except ImportError as e:
        raise ConfigurationError(
            f"Cannot import module '{module_name}' - this must be a valid Python module"
        ) from e
    try:
        function = getattr(module, function_name)
    except AttributeError as exc:
        raise ConfigurationError(
            f"Cannot find method '{function}' in module '{module}'"
        ) from exc
    return function
