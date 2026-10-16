# Quick Start

This section is meant to get you set up with building your dictionary as quick as possible.

1. **Create a starter project**: `mothertongues new-project`
    - you will be asked to provide a file location
    - the project created will contain sample data that can be immediately used to see the dicitionary in action

2. **Build and run** your dictionary: `mothertongues build-and-run "<FileLocationYouProvided>/config.mtd.json"`.
    - Your dictionary will be available on your computer at http://localhost:3636
    - Press ctrl+c to exit the server from your terminal.
    - Add `--watch` to rebuild your dictionary and refresh the page automatically whenever you change your configuration or data.

    !!! note "Local Development"
        If you are customizing MTD code, and you want to see your changes deployed locally, you need to run the above commands within the `uv` environment that was automatically setup for you upon local installation.

        This can be done by prefixing all `mothertongues` commands with `uv run` (e.g. `uv run mothertongues new-project`) or by activating the environment directly (`source .venv/bin/activate`).

        Check out the [uv documentation](https://docs.astral.sh/uv/getting-started/features/#running-commands) for more details

    !!! note "Developing the UI"
        If you are working on the Mother Tongues UI itself, run `npm install` once in the `mothertongues-UI` submodule and then use `uv run mothertongues dev "<FileLocationYouProvided>/config.mtd.json"`.
        This serves the UI from its source with live reloading at http://localhost:3636, and rebuilds your dictionary whenever its configuration, its data or the mothertongues Python code changes, so there is no need to run `nx build` or clear your browser cache between changes.
        See [customizing the UI](../guides/build.md#customizing-the-ui) for the full guide.
