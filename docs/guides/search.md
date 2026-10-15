---
comments: true
---

# Approximate Search
*This guide applies for all paths ([no-code](../nocode/install.md) and [advanced developer](../developer/prerequisites.md))*

## What is Approximate Search?

Approximate search isn't just a *nice* feature for dictionaries of
endangered languages - it's usually a requirement.

Computers, by default, perform very narrow searches. If a dictionary user searches for 'cat', you expect an entry for 'cat'. But what if you search for 'kat' or 'kaat'? If you are learner of a language, these are honest mistakes to make. Approximate search allows *close* searches to return results.

Often, it's
learners of languages that want to use dictionaries the most, and if
your dictionary doesn't allow approximate search, beginners might have
a hard time accessing entries in the dictionary.

Typical learner/user mistakes come from the following issues:

1. Learners have a hard time hearing the difference between sounds.
2. Learners don't often know how to spell the different sounds.
3. Some languages make it tricky to type, even if you can hear the difference and know how to spell the word.

!!! note
    See [this
    paper](http://roedoejet.github.io/cv/static/cv/pdfs/computel.pdf) for
    further discussion.

## How does it work?

Approximate search is partially achieved by trying to 'normalize' differences between the *query* (what the user types) and the data in your dictionary. How much you 'normalize' is up to you as the creator of your dictionary - too much and your users will get confusing results, too little and your algorithm won't return enough results.

All of the configuration for your search algorithm happens in the [MTD Configuration](prepare.md#mtd-configuration-file). You can configure the search differently for both L1 and L2 searches. The default configuration looks like this:

```json
{
    "config": {
        "L1": "YourLanguage",
        "L2": "English",
        "l1_search_strategy": "weighted_levenstein",
        "l2_search_strategy": "liblevenstein_automata",
        "l1_search_config": {
            "insertionCost": 1.0,
            "deletionCost": 1.0,
            "insertionAtBeginningCost": 1.0,
            "deletionAtEndCost": 1.0,
            "substitutionCosts": {},
            "defaultSubstitutionCost": 1.0
        },
        "l1_stemmer": "none",
        "l2_stemmer": "snowball_english",
        "l1_normalization_transducer": {
            "lower": true,
            "unicode_normalization": "NFC",
            "remove_punctuation": "[.,/#!$%^&?*';:{}=\\-_`~()]",
            "remove_combining_characters": true
        },
        "l2_normalization_transducer": {
            "lower": true,
            "unicode_normalization": "NFC",
            "remove_punctuation": "[.,/#!$%^&?*';:{}=\\-_`~()]",
            "remove_combining_characters": true
        },
    ...
```

The following sections will show you different ways you can configure approximate search.

## Index: Changing which fields get searched

An index determines which fields are scanned during search.

By default, the inverted index is created with terms from `word` for L1 and `definition` for L2. But you can index other fields as well. For example, if you'd like to see search results when 'cat' is in the example sentence, you might do the following:

```json hl_lines="6-13"
{
    "config": {
        "L1": "YourLanguage",
        "L2": "English",
        ...
        "l1_keys_to_index": [
            "word",
            "example_sentence",
            "my_custom_field"
        ],
        "l2_keys_to_index": [
            "definition"
        ],
    }
}
```

## Case
Case refers to whether uppercase and lowercase letters are considered the same.

To illustrate this, we probably (hopefully!) agree that if I type the word 'cat', I should get a result of 'cat' if it's in the dictionary. I should probably also get 'cat' as a result if I type 'Cat' or 'CAT' of 'cAt' - in other words, my search should be [case insensitive](#case).

The default configuration file already nomralizes case, by setting `"lower"` to `true`. If you would like to change that setting, adjust the value of `"lower"`:

```json hl_lines='3'
...
"l1_normalization_transducer": {
            "lower": true,
            "unicode_normalization": "NFC",
            "remove_punctuation": "[.,/#!$%^&?*';:{}=\\-_`~()]",
            "remove_combining_characters": true
        },
...
```

!!! note
    This example is for L1 normalization - you can configure this for your L2 langauge as well.

## Unicode Normalization

Unicode normalization is necessary for normalizing differences between 'composed' and 'decomposed' codepoints. See [this post](https://towardsdatascience.com/what-on-earth-is-unicode-normalization-56c005c55ad0) for more information!

```json hl_lines='4'
...
"l1_normalization_transducer": {
            "lower": true,
            "unicode_normalization": "NFC",
            "remove_punctuation": "[.,/#!$%^&?*';:{}=\\-_`~()]",
            "remove_combining_characters": true
        },
...
```

## Stemming

Stemming is all about normalizing words by turning them into the 'stem' (version of the word without affixes). So for example, searching for the word 'relate' would return results of 'relate', 'relates', 'relation', etc... in English. By default, we use the [English Snowball Stemmer](https://www.nltk.org/api/nltk.stem.snowball.html) for L2 and apply no stemming for L1.

```json hl_lines="6-7"
{
    "config": {
        "L1": "YourLanguage",
        "L2": "English",
    ...
        "l1_stemmer": "none",
        "l2_stemmer": "snowball_english",
    }
    ...
}
```

If you would to use other stemmers (for example, if the L2 is in Spanish, Arabic, etc.) - see these documents... TBD

## Punctuation

You might want to remove all punctuation from your search results. That means, for example, that `sunflower` would be returned, even if someone searches for `sun-flower`. By default, many punctuation marks will be removed. You can change which punctuation marks will be removed by modifying the following config value:

```json hl_lines='5'
...
"l1_normalization_transducer": {
            "lower": true,
            "unicode_normalization": "NFC",
            "remove_punctuation": "[.,/#!$%^&?*';:{}=\\-_`~()]",
            "remove_combining_characters": true
        },
...
```

## Removing Combining Characters

Sometimes it's convenient to just remove all accents/diacritics. For example, in French, we would possibly want to normalize "e" with "è", "é", and "ê". There is a convenience configuration in mothertongues that, if set to true, will temporarily apply NFD Unicode normalization and remove all codepoints in the [Combining Diacritical Marks](https://en.wikipedia.org/wiki/Combining_Diacritical_Marks) Unicode code block.

```json hl_lines='6'
...
"l1_normalization_transducer": {
            "lower": true,
            "unicode_normalization": "NFC",
            "remove_punctuation": "[.,/#!$%^&?*';:{}=\\-_`~()]",
            "remove_combining_characters": true
        },
...
```

## Adding weights

What about if I type 'kat' though? We might not expect a user to type 'kat' unless they are a learner of English - but, if we expect a lot of learners to be using our dictionary, that might be appropriate!

The Mother Tongues approximate search algorithm works by calculating the edit distance between the query and the [terms in your inverted index](#which-keys-get-indexed). The edit distance is how many insertions, deletions, or subsitutions it takes to get from one string to another: `kat` and `cat` have an edit distance of `1.0` by default for example since the default cost for substitutions is `1.0`.

The greater the distance, the more different the word. So a word the has a `1.0` distance is more different than a word that has a `0.5` distance. MTD gives you the option to edit distances to make search results more helpful for learners. Check out the example below!


### A simple distance example

Maybe we want to include information that `kat` is a bit closer to `cat` than `mat`. To do that, we will *weight* the substitution between `k` and `c` differently in our algorithm. We can do this by providing custom substitution costs:

```json hl_lines="1 7-11"
"l1_search_strategy": "weighted_levenstein",
"l1_search_config": {
    "insertionCost": 1,
    "deletionCost": 1,
    "insertionAtBeginningCost": 1,
    "deletionAtEndCost": 1,
    "substitutionCosts": {
        "c": {
            "k": 0.5
        }
    },
    "defaultSubstitutionCost": 1
},
...
```

That way `k` and `c` get a `0.5` distance. Whereas `c` and all other letters will get the `1.0` weight specified in the `defaultSubstitutionCost` value.

### A complex distance example

If you would like to provide many weights, you have the option of creating a separate "weights" file to read from. Your config would look like this:

```json hl_lines="1 7-11"
"l1_search_strategy": "weighted_levenstein",
"l1_search_config": {
    "insertionCost": 1,
    "deletionCost": 1,
    "insertionAtBeginningCost": 1,
    "deletionAtEndCost": 1,
    "substitutionCostsPath": "filepath_to_my_weights.csv",
    "defaultSubstitutionCost": 1
},
...
```

A sample `weights.csv`` file might be:

```
c,k,0.5
c,s,0.75
c,t,0.9
```

The *weights* file can be one of several formats

- .json
- .xslx
- .csv using a delimiter of `,`
- .psv using a delimter of `|`
- .tsv using a tab delimiter



!!! important
    This will **only** work when our search strategy is set to "weighted_levenstein". The other search strategy is faster, but does not allow for weighted edit distance calculations.

## Ranking results (Advanced)

When more than one entry matches a search, Mother Tongues has to decide which ones to show first. It does this in two steps:

1. **Edit distance first.** Results are sorted by how close they are to what the user typed (see [Adding weights](#adding-weights)). An entry containing `cat` will always rank above an entry that only contains `kat` when the user searches for `cat`.
2. **Then a relevance score.** Results that are *equally* close to the query (for example, every entry containing the word `cat`) are then sorted by a relevance score calculated with [BM25](https://en.wikipedia.org/wiki/Okapi_BM25).

The one exception is when the search only looks for exact matches; in that case, results are sorted by the relevance score alone.

This means that the settings below only change the order of results that are equally close to the query. They will not help if your search is returning too many or too few results - for that, see the other sections of this guide.

You can configure the relevance score separately for L1 and L2 searches. The default configuration looks like this:

```json hl_lines="6-15"
{
    "config": {
        "L1": "YourLanguage",
        "L2": "English",
        ...
        "l1_bm25_config": {
            "k1": 1.5,
            "b": 1.0,
            "epsilon": 0.25
        },
        "l2_bm25_config": {
            "k1": 1.5,
            "b": 1.0,
            "epsilon": 0.25
        },
    }
}
```

The defaults should work well for most dictionaries. If you do want to change them, here is what each setting does:

**`b` - field length (between 0 and 1, default 1).** Controls whether a match in a short field counts for more than the same match in a long field. When searching for `cat`, you probably want an entry whose definition is just "cat" to rank above one whose definition is "a small domesticated mammal, often kept as a pet, related to the wild cat". At `1`, short fields are strongly favoured; at `0`, length is ignored.

**`k1` - repetition (0 or more, default 1.5).** Controls how much a word appearing several times in the same field adds to its score. Each repeat adds less than the one before, and `k1` controls how quickly that levels off. At `0`, only whether the word appears matters, not how often; higher values let repeats keep counting. Words, and most definitions, are too short for words to repeat, so this mainly matters if you've [indexed](#index-changing-which-fields-get-searched) longer fields like `example_sentence`.

**`epsilon` - very common words (0 or more, default 0.25).** Words that appear in many entries are given less weight than rare ones. For a word that appears in more than half of the entries, such as "to" in a dictionary where verbs are defined "to run", "to eat", and so on, the formula would give it a negative weight. Instead, its weight is set to `epsilon` × the average weight of all words, so it still counts for a little. At `0`, these words add nothing to the score.

!!! note
    These settings are used when your dictionary data is built, so you will need to rebuild your dictionary (for example with `mothertongues build-and-run` or `mothertongues export`) to see their effect.
