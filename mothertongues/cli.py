import json
import shutil
import socketserver
from functools import partial
from http.server import SimpleHTTPRequestHandler
from pathlib import Path

import typer
from loguru import logger

from mothertongues.config import SchemaTypes, get_schemas
from mothertongues.config.models import MTDConfiguration
from mothertongues.dictionary import MTDictionary
from mothertongues.utils import load_mtd_configuration

app = typer.Typer(rich_markup_mode="markdown")


@app.command()
def run(
    dictionary_data: Path = typer.Argument(
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="The path to your generated dictionary data",
    ),
    port: int = 3636,
):
    """
    ## Run your dictionary in your browser\

    This is helpful for debugging, just run this command and your dictionary will be available at [http://localhost:3636](http://localhots:3636)
    You can exit the server by pressing ctrl+c.

    If you haven't generated your dictionary data yet, use the export command first or use the build-and-run command instead.
    """
    UI_DIR = Path(__file__).parent / "ui"
    shutil.copy(dictionary_data, UI_DIR / "assets" / "dictionary_data.json")
    Handler = partial(SimpleHTTPRequestHandler, directory=UI_DIR)
    logger.warning(
        "WARNING: This is a Development server and is not secure for production"
    )
    httpd = socketserver.TCPServer(("", port), Handler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()


@app.command()
def build_and_run(
    language_config_path: Path = typer.Argument(
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="The path to your dictionary's language configuration file.",
    ),
    port: int = 3636,
):
    """
    ## Build your dictionary and run it in your browser\

    This is helpful for debugging, just run this command and your dictionary will be available at [http://localhost:3636](http://localhots:3636)
    You can exit the server by pressing ctrl+c.
    """
    config = MTDConfiguration(**load_mtd_configuration(language_config_path))
    dictionary = MTDictionary(config)
    output = dictionary.export()
    UI_DIR = Path(__file__).parent / "ui"
    Handler = partial(SimpleHTTPRequestHandler, directory=UI_DIR)

    with open(UI_DIR / "assets" / "dictionary_data.json", "w", encoding="utf8") as f:
        json.dump(output, f)
    logger.warning(
        "WARNING: This is a Development server and is not secure for production"
    )
    httpd = socketserver.TCPServer(("", port), Handler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()


@app.command()
def schema(
    type: SchemaTypes = typer.Argument(
        default=SchemaTypes.main_format,
        help="The SchemaType to return, choose from the main format, or just the dictionary configuration, or the schema for each entry in the dictionary.",
    ),
    output: Path = typer.Argument(
        exists=False,
        file_okay=True,
        dir_okay=False,
        help="The file path to write the JSON schema",
    ),
):
    """
    ## Export the JSON Schema for various MotherTongues Dictionary data definitions\

    This is helpful when creating your own UI for use with MTD-generated data. Read more about it here: [https://docs.mothertongues.org/](https://docs.mothertongues.org/)

    """
    schema = get_schemas(type)
    with open(output, "w", encoding="utf8") as f:
        json.dump(schema, f)
    return schema


@app.command()
def export(
    language_config_path: Path = typer.Argument(
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="The path to your dictionary's language configuration file.",
    ),
    output_directory: Path = typer.Argument(
        exists=True,
        file_okay=False,
        dir_okay=True,
        help="The output directory to write to.",
    ),
    single_file: bool = typer.Option(
        default=True, help="Whether to export to a single file or separate files."
    ),
):
    """
    ## Export your dictionary for use in a MTD UI\

    You need to export your data to create the file necessary for the UI. Read more about it here: [https://docs.mothertongues.org/](https://docs.mothertongues.org/)
    """
    config = MTDConfiguration(**load_mtd_configuration(language_config_path))
    dictionary = MTDictionary(config)
    if single_file:
        output = dictionary.export()
        dictionary.print_info()
        logger.info(
            f"Writing dictionary data file to {(output_directory / 'dictionary_data.json')}"
        )
        with open(output_directory / "dictionary_data.json", "w", encoding="utf8") as f:
            json.dump(output, f)
    else:
        config, data, l1_index, l2_index = dictionary.export(combine=False)
        dictionary.print_info()
        logger.info(f"Writing config, data, and index files to {(output_directory)}")
        with open(output_directory / "config.json", "w", encoding="utf8") as f:
            json.dump(config, f)
        with open(output_directory / "data_hash.json", "w", encoding="utf8") as f:
            json.dump(data, f)
        with open(output_directory / "l1_index.json", "w", encoding="utf8") as f:
            json.dump(l1_index, f)
        with open(output_directory / "l2_index.json", "w", encoding="utf8") as f:
            json.dump(l2_index, f)


if __name__ == "__main__":
    app()
