import json
from pathlib import Path

import typer
from loguru import logger

from mothertongues.config import SchemaTypes, get_schemas
from mothertongues.config.models import MTDConfiguration
from mothertongues.dictionary import MTDictionary
from mothertongues.utils import load_mtd_configuration

app = typer.Typer(rich_markup_mode="markdown")


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
        logger.info(
            f"Writing dictionary data file to {(output_directory / 'dictionary_data.json')}"
        )
        with open(output_directory / "dictionary_data.json", "w", encoding="utf8") as f:
            json.dump(output, f)
    else:
        config, data, l1_index, l2_index = dictionary.export(combine=False)
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
