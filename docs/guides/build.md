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

This guide assumes that you have worked through the steps to create a valid [Language Configuration file](#mtd-language-configuration-file) and [Data Resource Configuration files](#mtd-data-resource-configuration-file) for each unique source of data. It also assumes you have a directory
structure similar to the one [described in this guide](#file-structure).

Then run:

`mothertongues build-and-run <path_to_mtd.config.json>`

And your dictionary will be served at [http://localhost:3636](http://localhost:3636)

## Exporting your data

First, you need to export the dictionary data required by any MTD UI.

1.  Change directories to your [MTD folder](prepare.md#project-folder-structure).
2.  Then, build the dictionary using the `mothertongues export` command to create
    necessary data:

`mothertongues export <path_to_mtd.config.json> <output_folder>`


This will create a file called `dictionary_data.json` which is the file you will need to transfer to your MTD UI.

**TODO: @Aidan**, this the above casually mentioned "tranfer to your MTD UI". Is that the next section? (mobile development)? Or is there something else missing here?

## Mobile/UI Development -- this section needs work!!!

Here are the steps for creating a mobile dictionary on your machine.

!!! note
    You only need to do this if you intend to customize the code for the UI, otherwise you can just follow the steps for [running on your machine]() or [exporting your data]() and [publishing to GitHub]()

1. Fork the repository in GitHub

2. Follow the [local installation instructions](../install.md#local-development)

3. Change into the UI directory:

    `cd mothertongues-UI`

4. Install dependencies:

    `npm install`

5. Move your [exported data](#exporting-your-data) to `mothertongues-UI/packages/mtd-mobile-ui/src/assets/dictionary_data.json`

6. Serve your dictionary:

    `npx nx serve mtd-mobile-ui`
