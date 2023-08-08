import json
from pathlib import Path

import typer

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
    single_file: bool = typer.Option(default=True),
):
    config = MTDConfiguration(**load_mtd_configuration(language_config_path))
    dictionary = MTDictionary(config)
    if single_file:
        output = dictionary.export()
        with open("dictionary_data.json", "w", encoding="utf8") as f:
            json.dump(output, f)
    else:
        config, data, l1_index, l2_index = dictionary.export(combine=False)
        with open("config.json", "w", encoding="utf8") as f:
            json.dump(config, f)
        with open("data_hash.json", "w", encoding="utf8") as f:
            json.dump(data, f)
        with open("l1_index.json", "w", encoding="utf8") as f:
            json.dump(l1_index, f)
        with open("l2_index.json", "w", encoding="utf8") as f:
            json.dump(l2_index, f)


if __name__ == "__main__":
    app()
