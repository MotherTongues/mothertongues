from string import ascii_letters
from typing import Union


def col2int(col: Union[str, int], base0: bool = False):
    if isinstance(col, int):
        # return if it's already an int
        return col
    try:
        # otherwise try a basic type cast
        return int(col)
    except ValueError:
        # otherwise convert letter to number (can also have columns AA for example)
        num = 0
        for c in col:
            if c in ascii_letters:
                num = num * 26 + (ord(c.upper()) - ord("A"))
        return num if base0 else num + 1
