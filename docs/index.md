---
comments: true
---

Overview
--------

### What is Mother Tongues Dictionaries?

Mother Tongues Dictionaries (MTD) is a tool developed to facilitate the
rapid, inexpensive development of digital dictionaries, with a
particular focus on language revitalization of Indigenous languages. For
a primer in understanding some of the motivations behind language
revitalization, see [this
chapter](http://oxfordre.com/linguistics/view/10.1093/acrefore/9780199384655.001.0001/acrefore-9780199384655-e-8)
of the Oxford Research Encyclopedia of Linguistics.

MTD is unique in a number of ways:

1.  Approximate search comes out of the box, and the algorithm can be easily customized. See [guides](guides/index.md)
2.  Free & open source. As of version 1.0 MTD is licensed by the MIT License.
3.  Multiple platforms. MTD has a number of front ends that it is compatible with, including for the Web, iOS and Android.


### MTD Structure

You can think of creating a Mother Tongues Dictionary as involving two
distinct parts:

1\. **MTD** - The tool documented here, which is essentially a data
processing tool. It is able to take data for one or more languages from
multiple different sources (spreadsheets, websites, plain text files
etc\...) and combine the data, sort it, index it, calculate scores for
search results, find duplicates, and then export it to a number of different formats.

2\. **MTD-UI** - A front-end tool for *visualizing* your dictionary.
Each front end tool must accept the Mother Tongues data format. The schema for this data can be found at ***

Making a Dictionary
-------------------

To make a dictionary from your data, you need to do the following three
things:

1.  Install mothertongues, see [installation](install.md).
2.  Write a valid Mother Tongues Language configuration file. See
    [guides](guides/index.md)
3.  Write valid Mother Tongues data resource configuration files. See
    [guides](guides/index.md)

Then, build with the command line:

```bash
mothertongues build-and-run <path_to_language_configuration>
```

And open your browser at `localhost:3636` to see your dictionary.

Exporting a Dictionary
----------------------

Finally, you can export your dictionaries to JSON to be used with an MTD frontend using the command line:

```bash
mothertongues export <path_to_language_configuration> <output_dir>
```
