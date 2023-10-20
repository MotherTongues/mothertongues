# Quick Start

This section is meant to get you set up with building your dictionary as quick as possible.

1. **Create a starter project**: `mothertongues new-project`
    - you will be asked to provide a file location
    - the project created will contain sample data that can be immediately used to see the dicitionary in action

2. **Build and run** your dictionary: `mothertongues build-and-run "<FileLocationYouProvided>/config.mtd.json"`.
    - Your dictionary will be available on your computer at http://localhost:3636
    - Press ctrl+c to exit the server from your terminal.

    !!! Local-Development-Note
        If you are customizing MTD code, and you want to see your changes deployed locally, you need to run the above commands within the `poetry` environment that was automatically setup for you upon local installation.

        This is can be done by including `poetry run` before all `mothertongues` commands or by activating your poestry env (`poetry shell`)

        Check out [poetry documentation](https://python-poetry.org/docs/basic-usage/#using-your-virtual-environment) for more details
