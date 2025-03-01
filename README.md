# Mother Tongues Dictionaries (MTD)

:speech_balloon: This repo is a near-complete re-write of the [legacy mothertongues](https://github.com/roedoejet/mothertongues) code and is set to replace it. For a list of improvements see [this section](#improvements). For legacy documentation, please go [here](https://mothertongues.github.io/mothertongues-docs/) :speech_balloon:

[![codecov](https://codecov.io/gh/MotherTongues/mothertongues/branch/main/graph/badge.svg?token=7JUKAAHZDV)](https://codecov.io/gh/MotherTongues/mothertongues)
[![Documentation Status](https://img.shields.io/badge/-docs-blue)](https://docs.mothertongues.org)
[![Build Status](https://github.com/MotherTongues/mothertongues/actions/workflows/tests.yml/badge.svg)](https://github.com/MotherTongues/mothertongues/actions)
[![PyPI package](https://img.shields.io/pypi/v/mothertongues.svg)](https://pypi.org/project/mothertongues/)
[![license](https://img.shields.io/badge/Licence-MIT-green)](LICENSE)
[![standard-readme compliant](https://img.shields.io/badge/readme%20style-standard-brightgreen.svg?style=flat-square)](https://github.com/RichardLitt/standard-readme)

MTD is an open-source tool that allow language communities and developers to quickly and inexpensively make their dictionary data digitally accessible. MTD is a tool that parses and prepares your data for being used with an [MTD User Interface](https://github.com/MotherTongues/mothertongues-UI).

Please visit the [website](https://www.mothertongues.org) or [docs](https://docs.mothertongues.org) for more information.

## Table of Contents

- [Background](#background)
- [Install](#install)
- [Usage](#usage)
- [Contributing](#contributing)
- [Acknowledgements](#acknowledgements)
- [License](#license)

## Background

This project started as just a single dictionary for Gitxsan - a language spoken in Northern British Columbia, but it became quickly apparent that many communities also had the same problem. That is, they had some dictionary data but all of the options for sharing that data online were prohibitively expensive. MTD aims to make it easier to create online digital dictionary resources.

**Note** - Just because you _can_ make an online dictionary does _not_ mean you _should_. Before making a dictionary, you must have clear consent from the language community in order to publish a dictionary. For some background on why this is important, please read sections 1 and 2.1 [here](http://oxfordre.com/linguistics/view/10.1093/acrefore/9780199384655.001.0001/acrefore-9780199384655-e-8)

## Install

It is recommended to install mothertongues using pip. The package name is `mothertongues`, and as of version 1.0.x it is imported with `import mothertongues`. The CLI can be run using `mothertongues --help`.

```
pip install mothertongues
```

### Quick Start

If you just want to try something out you can use the mothertongues command line to create a configuration and some sample data:

1. `poetry run python3 cli.py new-project`
2. Then run your dictionary: `poetry run python3 cli.py build-and-run <YourDictionaryConfigDirPath>/config.mtd.json`

### Local Install

To install locally you will have to have Git, Python 3.8+, [poetry](https://python-poetry.org/docs/#installing-with-the-official-installer) and Node 16+ on your machine. You can then follow these steps:

1. Clone repo and UI submodule `git clone https://github.com/MotherTongues/mothertongues.git --recursive`
2. Build the UI: `cd mothertongues/mothertongues-UI && npm install`
3. Build the Python Development version of the UI: `npx nx build mtd-mobile-ui --configuration=pydev`
4. Install the Python package: `cd .. && poetry install`

## Usage

In order to create a Mother Tongues Dictionary you will need at least two things:

- A configuration file for your language/dictionary
- A configuration file for each source of data

You can find out more about how to create these files against the MTD configuration schema by visiting the [guides](https://docs.mothertongues.org/docs/mtd-guides)

Once you have those files, you can either create a dictionary using the command line interface.

The basic workflow for creating a dictionary is as follows:

1. Fork and clone the [mtd-starter](https://github.com/MotherTongues/mtd-starter)
2. [Edit and prepare](https://docs.mothertongues.org/docs/mtd-guides-prepare) the repo using your own data
3. [Export your data](https://docs.mothertongues.org/docs/mtd-guides-ui#exporting-your-data) to a format readable by the Mother Tongues User Interfaces
4. Add your exported data (`dictionary_data.json`) from step 3 and then [publish](https://docs.mothertongues.org/docs/mtd-guides-publishing) your dictionary! 🎉


## Improvements

There are a variety of improvements from the legacy mothertongues library. Here are a few of them:

- The CLI now builds an inverted index over any of your dictionary entry keys and search is conducted on the terms of that index.
- Results are now ranked by a combination of Edit Distance and [OkapiBM25](https://en.wikipedia.org/wiki/Okapi_BM25) meaning you're likely to get better results. We sort results by first sorting them based on edit distance - for results with the same edit distance, we then sort them based on their OkapiBM25 score.
- We use strongly typed configurations to reduce errors when building your dictionary
- We support two search algorithms out-of-the-box: an unweighted Levenstein search over [Levenstein automata](http://blog.notdot.net/2010/07/Damn-Cool-Algorithms-Levenshtein-Automata#:~:text=The%20basic%20insight%20behind%20Levenshtein,distance%20of%20a%20target%20word.) (very fast) or a quadratic weighted Levenstein search over the terms of the index (flexible and slower, but still pretty fast).
- The search algorithm is now optimized for multi-term searches
- There is a unified normalization strategy between the UI and CLI that allows for performing case normalization, Unicode normalization, removal of punctuation (customizable), arbitrary replace rules, and removal of combining diacritics/accents.
- There is a built in web-server in the CLI for quickly spinning up a development version of your app `mothertongues build-and-run <path_to_language_config>`
- There is an API that serves the MTD JSON schemas and validates your configuration files and dictionary data.
- The sorter is improved to be able to handle Out of Vocabulary (OOV) characters
- Parsing JSON is many times faster thanks to @dhdaines


## Contributing

If something is not working, or you'd like to see another feature added, feel free to dive in! We please ask that you read the [contributing guidelines](Contributing.md) before submitting any pull requests. [Open an issue](https://github.com/MotherTongues/mothertongues/issues/new) or submit PRs. Help writing and clarifying documentation is also very welcome.

This repo follows the [Contributor Covenant](http://contributor-covenant.org/version/1/3/0/) Code of Conduct.

## Acknowledgements

Thank you to both Patrick Littell & Mark Turin for their contributions, guidance and support as well as institutional support from the [First Peoples' Cultural Council](http://www.fpcc.ca/) and SSHRC Insight Grant 435-2016-1694, ‘Enhancing Lexical Resources for BC First Nations Languages’.

Thank you to all other contributors for support with improving MotherTongues, finding bugs and writing documentation.

### Contributors

This project exists thanks to all the people who contribute.

[@dhdaines](https://github.com/dhdaines).
[@littell](https://github.com/littell).
[@markturin](https://github.com/markturin).
[@eddieantonio](https://github.com/eddieantonio).
[@kavonjon](https://github.com/kavonjon).

## License

[MIT © Aidan Pine.](LICENSE)
