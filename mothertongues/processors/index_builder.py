from collections import defaultdict
from typing import Callable, Dict, List, Union

from jsonpath_ng import jsonpath
from jsonpath_ng import parse as json_parse
from loguru import logger
from nltk.stem.snowball import SnowballStemmer
from rank_bm25 import BM25Okapi
from tqdm import tqdm

from mothertongues.config.models import (
    CheckableParserTargetFieldNames,
    MTDConfiguration,
    StemmerEnum,
    create_restricted_transducer,
)

SNOWBALL_STEMMER = SnowballStemmer("english")

DEFAULT_STEMMER = SNOWBALL_STEMMER.stem


class InvertedIndex:
    """An inverted index class for efficiently storing dictionary terms for lookup.
    The structure is ...
    """

    def __init__(
        self,
        raw_data: List[dict],
        normalization_function: Union[Callable, None] = None,
        stemmer_function: Union[Callable, None] = None,
        keys_to_index: List[str] = [
            CheckableParserTargetFieldNames.word.value,
        ],
    ):
        self.normalization_function = normalization_function
        self.stemmer_function = stemmer_function
        self.data: Dict[
            str, Dict[str, Dict[str, Union[int, List[Union[str, int]]]]]
        ] = {}
        self._scorers: Dict[str, BM25Okapi] = {}
        self._path_cache: Dict[str, jsonpath.Fields] = {
            CheckableParserTargetFieldNames.entryID.value: json_parse(
                CheckableParserTargetFieldNames.entryID.value
            )
        }
        self.keys_to_index = keys_to_index
        self.raw_data = sorted(
            raw_data,
            key=lambda x: int(x[CheckableParserTargetFieldNames.entryID.value]),
        )

    def load(self, data):
        self.data = data

    def clear(self):
        self.data = {}
        self.raw_data = []

    def _calculate_score(self, scorer, doc_ids, key, term):
        scores = scorer.get_scores([term])
        for posting, score in zip(doc_ids, scores):
            if not score:
                continue
            assert (
                posting in self.data[term]
            ), f"posting {posting} received a score of {score} but is not found in the index for term {term}"
            if "score" not in self.data[term][posting]:
                self.data[term][posting]["score"] = defaultdict(float)
            self.data[term][posting]["score"][key] += score

    def calculate_scores(self):
        if not self.data:
            logger.info("Building index before calculating scores")
            self.build()
        for key in self.keys_to_index:
            if key not in self._path_cache:
                self._path_cache[key] = json_parse(key)
            jsonpath_expr = self._path_cache[key]
            # parse all the json paths for the target key
            parsed_corpus = [
                (
                    entry[CheckableParserTargetFieldNames.entryID.value],
                    jsonpath_expr.find(entry)[0].value,
                )
                for entry in self.raw_data
            ]
            # if the parsed item is a list, we have to separate each element and maintain the reference to the document ID
            if isinstance(parsed_corpus[0][1], list):
                corpus = []
                for value in parsed_corpus:
                    if value[1]:
                        corpus.extend((value[0], item) for item in value[1])
                    else:
                        corpus.append((value[0], ""))
            else:
                corpus = parsed_corpus
            # create a flat list of the document ids
            doc_ids = [item[0] for item in corpus]
            # create a parallel list of the tokenized corpus
            tokenized_corpus = [self._process_terms(item[1]) for item in corpus]
            # create the scorer based on the tokenized corpus
            scorer = BM25Okapi(tokenized_corpus)
            self._scorers[key] = scorer
            # for each term in the index, calculate the score of the term with respect to the posting
            # and add it.
            for term in tqdm(self.data, desc="Calculating scores"):
                self._calculate_score(
                    scorer,
                    doc_ids,
                    key,
                    term,
                )

        for term in tqdm(self.data, desc="Combining scores"):
            for posting in self.data[term]:
                self.data[term][posting]["score"]["total"] = sum(
                    self.data[term][posting]["score"].values()
                )

    def _add_index(self, term, doc_id, key, location_index):
        # if it's in the Index already
        if term in self.data:
            # if the posting is there already push the location
            if doc_id in self.data[term]:
                self.data[term][doc_id]["location"].append([key, location_index])
            else:
                # else add the posting and a location (for highlighting)
                self.data[term][doc_id] = {"location": [[key, location_index]]}
        else:
            self.data[term] = {doc_id: {"location": [[key, location_index]]}}

    def _process_terms(self, entry_data: str):
        # normalize value
        if self.normalization_function is not None:
            entry_data = self.normalization_function(entry_data)
        # split on whitespace
        terms = entry_data.split()
        # apply stemmer
        if self.stemmer_function is not None:
            terms = [self.stemmer_function(term) for term in terms]
        return terms

    def build(self):
        for entry in tqdm(self.raw_data, desc="Building index"):
            doc_id = (
                self._path_cache[CheckableParserTargetFieldNames.entryID.value]
                .find(entry)[0]
                .value
            )
            for key in self.keys_to_index:
                # get the value based on the 'key' (maybe target/jsonpath of some sort)
                if key not in self._path_cache:
                    self._path_cache[key] = json_parse(key)
                jsonpath_expr = self._path_cache[key]
                # find the json path value
                if value := jsonpath_expr.find(entry) or "":
                    # only take the first match as there shouldn't be any more
                    # for jsonpaths on the mtd data structure
                    value = value[0].value
                    # convert strings to list for looping
                    if not isinstance(value, list):
                        value = [value]
                        key_indices = [""]
                    else:
                        key_indices = [f"[{x}]" for x in range(len(value))]
                    for i, value_item in enumerate(value):
                        value_item_key = key + key_indices[i]
                        terms = self._process_terms(value_item)
                        # for term in normalize/stemmed/split value, add it to the index
                        for j, term in enumerate(terms):
                            self._add_index(term, doc_id, value_item_key, j)
        return self.data


def create_inverted_index(data: List[dict], config: MTDConfiguration, l1_or_l2: str):
    if l1_or_l2.lower() == "l1":
        stemmer_fn = (
            DEFAULT_STEMMER
            if config.config.l1_stemmer == StemmerEnum.snowball_english
            else None
        )
        return InvertedIndex(
            data,
            create_restricted_transducer(config.config.l1_normalization_transducer),
            stemmer_function=stemmer_fn,
            keys_to_index=config.config.l1_keys_to_index,
        )
    elif l1_or_l2.lower() == "l2":
        stemmer_fn = (
            DEFAULT_STEMMER
            if config.config.l2_stemmer == StemmerEnum.snowball_english
            else None
        )
        return InvertedIndex(
            data,
            create_restricted_transducer(config.config.l2_normalization_transducer),
            stemmer_function=stemmer_fn,
            keys_to_index=config.config.l2_keys_to_index,
        )
    raise ValueError(f"Expected 'l1' or 'l2', but got {l1_or_l2}")