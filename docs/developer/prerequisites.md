---
comments: true
---

# Prerequisites and Local Installation

*These guides assume you are comfortable with the [Command Line](https://en.wikipedia.org/wiki/Command-line_interface), [Git](https://en.wikipedia.org/wiki/Git) and [Python](https://en.wikipedia.org/wiki/Python_(programming_language)). You must have all of these installed on your machine. You are also strongly encouraged to have a [GitHub](https://github.com) account.*

This document outlines everything you need installed on your machine in order to pursue the "advanced" dictionary creation path.

There are a lot of guides for the "advanced" path and some of them are quite involved. Before each guide, there is a little paragraph (like the one above) that discusses the knowledge that you're assumed to have before attempting the guide, please take note of that! Remember that if you don't know one or more of the pre-requisite skills, the internet is a wonderful place with lots of resources for learning.

Operating System
------------------
Mother Tongues dictionaries can be created on any operating system (Mac, Windows, Linux, etc.)

We have made our best effort to ensure that all documentation found here works cross-platform.

That said, Mother Tongues is primary developed on MacOS and recieves most extensive testing on that operating system. If you find something that does not work for you, please modify actions according to your operating system - and feel free to let us know! (or [contribute](Contributing.md)!)

Prerequisites
------------------------
Before setting up Mother Tongues, you need the following installed on your machine

-  [Git](https://git-scm.com/downloads)
- [Python 3.11+](https://www.python.org/downloads/)
- [uv](https://docs.astral.sh/uv/getting-started/installation/) - python package/env manager
- [Node JS 22+](https://nodejs.org/en/download) - required for the UI

Installing Mother Tongues
----------------------------
You might want to clone and install mothertongues locally instead of through pip if you wish to customize the UI. To do so, run all of the following commands, in order. The UI must be built before installing the Python package, otherwise commands like `mothertongues build-and-run` will not be able to show your dictionary.

```bash
# Clone repo and UI submodule
git clone https://github.com/MotherTongues/mothertongues.git --recursive

# Install the UI's dependencies:
cd mothertongues/mothertongues-UI && npm install

# Build the Python Development version of the UI:
npx nx build mtd-mobile-ui --configuration=pydev

# Install the Python package:
cd .. && uv sync --all-groups
```

If you already cloned the repo without `--recursive`, run `git submodule update --init` from the `mothertongues` folder before building the UI. If you update the UI submodule later, re-run the build command above.
