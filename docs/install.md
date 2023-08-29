# Installation

*This page assumes you are comfortable with the [Command Line](https://en.wikipedia.org/wiki/Command-line_interface), and [Python](https://en.wikipedia.org/wiki/Python_(programming_language)). You must have all of these installed on your machine.*

## Recommended

The simplest way to install `mothertongues` is with pip:

```bash
pip install mothertongues
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
