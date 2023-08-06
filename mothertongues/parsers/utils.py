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


def extract_parser_targets(targets: dict):
    """Given some nested Parser Targets, create a flat dictionary of their contents

    Args:
        targets (ParserTargets): all the parser targets

    Returns:
        dict: a flat dictionary with the parser targets, enumerated for lists
    """
    target_dict = {}
    for k, v in targets.items():
        if isinstance(v, list):
            for i, item in enumerate(v):
                for v_k, v_j in item.items():
                    target_dict[f"{k}_{v_k}_{i}"] = v_j
        elif isinstance(v, dict):
            for v_key, v_val in v.items():
                target_dict[f"{k}_{v_key}"] = v_val
        else:
            target_dict[k] = v
    return target_dict
