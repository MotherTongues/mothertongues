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

1.  Approximate search comes out of the box, and the algorithm can be customized for specific languages. See [guides](guides/search.md)
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

Mother Tongues Dictionaries are intentionally designed with different communities and users in mind. To that end, we offer different paths you can take to create your dictionary.

### Option 1: No-Code Option (Fastest)
If any of the following describe you, then the no-code path may be right for you:

- I'm not overly comfortable with coding
- I want my dictionary running as quickly as possible with the least effort
- I want to try out-of-the-box MTD "as-is" (in other words, you don't need to make major code customizations right now)

See docs here: [No Code Installation](nocode/install.md)

!!! Tip
    If you're not sure which option is right for you, start with Option 1.

    You can always switch to the more advanced option later if needed.

### Option 2: Advanced Developer Option
If any of the following describe you, then the advanced developer path may be right for you:

- I want to run the dictionary locally on my computer before deploying
- I want to heavily customize the MTD-UI
- I want to use the MTD tool without the MTD-UI
- I want to contribute to MTD source code

See docs here: [Advanced Developer Installation](developer/prerequisites.md)
