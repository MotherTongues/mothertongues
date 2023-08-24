import json
import re
from pathlib import Path
from typing import List, Union, no_type_check


class ArbSorter(object):
    """Sort entries based on alphabet. Inspired by Lingweenie: https://lingweenie.org/conlang/sort.html
       with adaptations for OOV and ignorable characters.

    Given a sequence of letters (arbitrary-length Unicode strings), convert each into a numerical code.
    Then, convert any string to be sorted into its numerical equivalent and sort on that.

    Examples:
        Here is an example of a sorter.

        >>> sorter = ArbSorter(['a', 'b', 'c'])
        >>> sorter.word_as_values('abc')
        [0, 1, 2]
        >>> sorter.values_as_word([0, 1, 2])
        'abc'

    Args:
        order (list[str]): The order to sort by.
    """

    @no_type_check
    def __init__(self, order: Union[List[str], Path], ignorable=None):
        self.order = order
        if isinstance(order, Path):
            if self.order.suffix.endswith("json"):
                with open(self.order, encoding="utf8") as f:
                    self.order = json.load(f)
            else:
                with open(self.order, encoding="utf8") as f:
                    self.order = [x.strip() for x in f]
        self.ignorable = [] if ignorable is None else ignorable
        split_order = [re.escape(x) for x in sorted(self.order, key=len, reverse=True)]
        self.splitter = re.compile(f'({"|".join(split_order)})', re.UNICODE)
        self.oovs: List[str] = []
        # Next, collect weights for the ordering.
        self.char_to_ord_lookup = {self.order[i]: i for i in range(len(self.order))}
        self.ord_to_char_lookup = {v: k for k, v in self.char_to_ord_lookup.items()}
        self.oov_start = 10000

    # Turns a word into a list of ints representing the new
    # lexicographic ordering.  Python, helpfully, allows one to
    # sort ordered collections of all types, including lists.
    def word_as_values(self, word):
        """Turn word into values"""
        # ignore empty strings
        word = [x for x in self.splitter.split(word) if x]
        values = []
        for char in word:
            if char in self.ignorable:
                continue
            if char in self.char_to_ord_lookup:
                values.append(self.char_to_ord_lookup[char])
            else:
                # OOV (can be multiple OOVs strung together)
                for oov in char:
                    if oov in self.ignorable:
                        continue
                    oov_index = self.oov_start + ord(oov)
                    self.char_to_ord_lookup[oov] = oov_index
                    self.ord_to_char_lookup[oov_index] = oov
                    self.oovs.append(oov)
                    values.append(oov_index)
        return values

    def values_as_word(self, values):
        """Turn values into word"""
        return "".join([self.ord_to_char_lookup[v] for v in values])

    def return_sorted_data(self, item_list, target, sort_key="sorting_form"):
        """Return sorted list based on item's (word's) sorting_form"""
        sorted_list = []
        for item in item_list:
            item[sort_key] = self.word_as_values(item[target])
            sorted_list.append(item)
        return sorted(sorted_list, key=lambda x: x[sort_key])

    def __call__(self, item_list, target, sort_key="sorting_form"):
        """Return sorted list based on item's (word's) sorting_form"""
        return self.return_sorted_data(item_list, target, sort_key)
