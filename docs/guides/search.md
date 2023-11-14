---
comments: true
---

# Approximate Search
*This guide applies for all paths (no-code and advanced developer)*

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

You might want to remove all punctuation from your search results, in case you want to return a result for `"hello"` when someone searches for `h,ello`, for example.

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

What about if I type 'kat' though? We might not expect a user to type 'kat' unless they are a learner of English - but, if we expect a lot of learners of English to be using our dictionary, that might be appropriate!

The Mother Tongues approximate search algorithm works by calculating the edit distance between the query and the [terms in your inverted index](#which-keys-get-indexed). The edit distance is how many insertions, deletions, or subsitutions it takes to get from one string to another: `kat` and `cat` have an edit distance of `1.0` by default for example since the default cost for substitutions is `1.0`.

### A simple example

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

!!! important
    This will **only** work when our search strategy is set to "weighted_levenstein". The other search strategy is faster, but does not allow for weighted edit distance calculations.
