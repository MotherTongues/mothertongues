---
comments: true
---

# Building & Publishing your Dictionary

*These guides assume you are comfortable with the [Command Line](https://en.wikipedia.org/wiki/Command-line_interface) and [NPM](https://en.wikipedia.org/wiki/Npm_(software)).*

## Seeing your dictionary in action (i.e. Local Development)

!!! important
    This guide assumes you have worked through all the steps in [preparing your data](prepare.md).

Once you have properly configured your dictionary data, you can let `mothertongues` put it all together!

This will parse all of the data according to your specifications, combine all of your sources of data, sort your data according to your alphabet, create an [inverted index](https://en.wikipedia.org/wiki/Inverted_index) for improved performance, [calculate BM25 scores for ranking search results](https://en.wikipedia.org/wiki/Okapi_BM25), and generate the code necessary for your approximate search to work.

This guide assumes that you have worked through the steps to create a valid [MTD Configuration file](prepare.md#mtd-configuration-file) for your dictionary, with each of your sources of data listed under its `data` key. It also assumes you have a directory
structure similar to the one [described in this guide](prepare.md#project-folder-structure).

Then run:

`mothertongues build-and-run <path_to_config.mtd.json>`

And your dictionary will be served at [http://localhost:3636](http://localhost:3636)

If you add `--watch` (`mothertongues build-and-run <path_to_config.mtd.json> --watch`), your dictionary is rebuilt and the page in your browser refreshes automatically whenever you save a change to your configuration or data files.

## Exporting your data

First, you need to export the dictionary data required by any MTD UI.

1.  Change directories to your [MTD folder](prepare.md#project-folder-structure).
2.  Then, build the dictionary using the `mothertongues export` command to create
    necessary data:

`mothertongues export <path_to_config.mtd.json> <output_folder>`


This will create a file called `dictionary_data.json` which is the file you will need to transfer to your MTD UI in the next section.


## Customizing the UI

*This advanced guide assumes some experience with web development. The UI is an [Angular](https://angular.dev) and [Ionic](https://ionicframework.com) app found in the `mothertongues-UI` folder.*

!!! note
    You only need this guide if you want to change the code of the UI itself. To see changes to your dictionary's data or configuration as you make them, `mothertongues build-and-run <path_to_config.mtd.json> --watch` is all you need (see [above](#seeing-your-dictionary-in-action-ie-local-development)). To put your dictionary online, see [exporting your data](#exporting-your-data) or [publishing to GitHub](../nocode/install.md).

### Setting up

You need a copy of the `mothertongues` source code, including the `mothertongues-UI` submodule, and Node 22 or newer. If you don't have these yet, follow the steps for [installing Mother Tongues locally](../developer/prerequisites.md#installing-mother-tongues).

Then install the UI's dependencies. You only need to do this once, and again whenever the UI's `package.json` changes:

```bash
cd mothertongues-UI
npm install
cd ..
```

### Running the UI in development mode

From the `mothertongues` folder, run:

```bash
uv run mothertongues dev <path_to_config.mtd.json>
```

Wait until you see `Compiled successfully`, then open [http://localhost:3636](http://localhost:3636). From then on, any changes you save are picked up automatically:

| When you change...                                 | What happens                                                     |
| -------------------------------------------------- | ---------------------------------------------------------------- |
| UI code in `mothertongues-UI`                      | Only the changed code is recompiled, and the page reloads        |
| Your configuration or data files                   | Your dictionary is rebuilt, and the page reloads                 |
| The `mothertongues` Python code                    | The Python server restarts, rebuilds your dictionary, and the page reloads |

There's no need to run `nx build` or clear your browser's cache between changes. Press ctrl+c to stop.

Options:

- `--port <number>`: serve the UI on a different port (the default is 3636). Your dictionary data is served on the port after it (3637 by default), so both ports need to be free.
- `--ui-repo <path>`: use a copy of `mothertongues-UI` somewhere other than the `mothertongues-UI` folder.

??? info "How it works"
    `mothertongues dev` starts the Angular development server (`npx nx serve mtd-mobile-ui --configuration=pydev`), which compiles the UI in memory. It also starts a small Python server that builds your dictionary and serves `dictionary_data.json`. The Angular server forwards requests for the data to the Python server, which restarts whenever your configuration, data or the Python code changes.

### Publishing your customized UI

Development mode only runs on your computer. To put your customized dictionary online, build a production version of the site and upload it to any static web host, such as [GitHub Pages](https://pages.github.com), Netlify or your own server.

1. **Build the site.** From the `mothertongues-UI` folder, run:

    ```bash
    npx nx build mtd-mobile-ui --configuration=production --base-href=/<path>/
    ```

    The `--base-href` is the path your site will live at. For GitHub Pages, that's usually your repository's name, e.g. `--base-href=/my-dictionary/` for a site at `https://<YourGitHubUserName>.github.io/my-dictionary/`. For a site at the root of its own domain, use `--base-href=/`.

    The site is written to `dist/packages/mtd-mobile-ui`.

2. **Add your dictionary data.** The build contains sample data, so replace it with your own:

    ```bash
    uv run mothertongues export <path_to_config.mtd.json> dist/packages/mtd-mobile-ui/assets/
    ```

    If your dictionary has audio or images, copy them into `dist/packages/mtd-mobile-ui` too, at the paths your data refers to. For example, an audio path of `assets/audio/word.mp3` means the file goes in `dist/packages/mtd-mobile-ui/assets/audio/word.mp3`.

3. **Let pages reload correctly.** The site uses paths like `/my-dictionary/browse`, which only exist inside the app. Static hosts return a "not found" page if someone refreshes or follows a link straight to one of them. On GitHub Pages, fix this by copying `index.html` to `404.html`:

    ```bash
    cp dist/packages/mtd-mobile-ui/index.html dist/packages/mtd-mobile-ui/404.html
    ```

    Other hosts have their own setting for this, usually called a "rewrite" or "single-page app" fallback to `index.html`.

4. **Upload** everything in `dist/packages/mtd-mobile-ui` to your host.

!!! tip "Publishing automatically with GitHub Actions"
    The [mtd-starter](https://github.com/MotherTongues/mtd-starter) template already builds and publishes a dictionary to GitHub Pages every time you push (see [publishing to GitHub](../nocode/install.md)). To publish your customized UI instead of the default one:

    1. Push your changes to your own fork of [mothertongues-UI](https://github.com/MotherTongues/mothertongues-UI).
    2. In your copy of `.github/workflows/build.yaml`, change the "Check out mothertongues" step to `submodules: false`. Then add a step after it that checks out your fork into the UI folder:

        ```yaml
        - name: Check out my UI
          uses: actions/checkout@v7
          with:
            repository: <YourGitHubUserName>/mothertongues-UI
            path: mothertongues/mothertongues-UI
        ```

    3. Change `--base-href=/mtd-starter/` in the "Build" step to your repository's name.

### Troubleshooting

- **"Could not find an installed mothertongues-UI repository"**: the UI's dependencies aren't installed. Run `npm install` in `mothertongues-UI`. If that folder is empty, run `git submodule update --init` from the `mothertongues` folder first.
- **"Could not find `npx`"**: Node isn't installed, or isn't on your `PATH`. Install [Node 22 or newer](https://nodejs.org/en/download).
- **The port is already in use**: another server (perhaps another `mothertongues` command) is still running. Stop it, or choose other ports with `--port`.
- **"Could not build your dictionary"**: there's an error in your configuration or data. The UI keeps running, and your dictionary is rebuilt as soon as you save a fix.
