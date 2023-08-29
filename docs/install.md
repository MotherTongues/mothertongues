# Installation

*This page assumes you are comfortable with the [Command Line](https://en.wikipedia.org/wiki/Command-line_interface), and [Python](https://en.wikipedia.org/wiki/Python_(programming_language)). You must have all of these installed on your machine.*

## Recommended

The simplest way to install `mothertongues` is with pip:

```bash
pip install mothertongues
```

!!! tip

    If you are using [Visual Studio Code](https://code.visualstudio.com/), you can add the [schema to your for intellisense](https://code.visualstudio.com/docs/languages/json#:~:text=The%20association%20of%20a%20JSON,under%20the%20property%20json.schemas%20.)!

    ```json
    "json.schemas": [
            {
                "fileMatch": [
                    "config.mtd.json"
                ],
                "url": "https://raw.githubusercontent.com/MotherTongues/mothertongues/main/mothertongues/schemas/config.json"
            }
        ]
    ```

## Local Development

Alternatively you can clone and install from source (advanced). To install locally you will have to have Git, Python 3.8+, [poetry](https://python-poetry.org/docs/) and Node 16+ on your machine. You can then follow these steps:

```bash
# Clone repo and UI submodule
git clone https://github.com/MotherTongues/mothertongues.git --recursive
# Build the UI:
cd mothertongues/mothertongues-UI && npm install
# Build the Python Development version of the UI:
npx nx build mtd-mobile-ui --configuration=pydev
# Install the Python package:
cd .. && poetry install
```
