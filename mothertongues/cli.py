import json
from pathlib import Path

import typer
from loguru import logger

from mothertongues.config.models import MTDConfiguration
from mothertongues.dictionary import MTDictionary
from mothertongues.utils import load_mtd_configuration

app = typer.Typer()


@app.command()
def hello(name: str):
    print(f"Hello {name}")


@app.command()
def export(
    language_config_path: Path = typer.Argument(
        default=None, exists=True, file_okay=True, dir_okay=False, readable=True
    ),
    output_directory: Path = typer.Argument(
        default=None, exists=True, file_okay=False, dir_okay=True
    ),
    single_file: bool = typer.Option(default=True),
):
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
