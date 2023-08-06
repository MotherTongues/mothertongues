from typing import Tuple

from openpyxl import load_workbook
from openpyxl.cell.cell import Cell
from openpyxl.utils.exceptions import InvalidFileException

from mothertongues.config.models import DataSource
from mothertongues.exceptions import ParserError, UnsupportedFiletypeError
from mothertongues.parsers import BaseTabularParser
from mothertongues.parsers.utils import col2int


class Parser(BaseTabularParser):
    def __init__(self, data_source: DataSource):
        self.resource_path = data_source.resource
        self.manifest = data_source.manifest
        try:
            work_book = load_workbook(self.resource_path, data_only=True)
        except InvalidFileException:
            raise UnsupportedFiletypeError(self.resource_path)
        if self.manifest.sheet_name is not None:
            try:
                work_sheet = work_book[self.manifest.sheet_name]
            except KeyError as e:
                raise ParserError(
                    f"{self.manifest.sheet_name} does not exist in the workbook at {self.resource_path}"
                ) from e
        else:
            work_sheet = work_book.active
        min_row = 2 if self.manifest.skip_header else 1
        self.resource = work_sheet.iter_rows(min_row=min_row)

    def parse_fn(self, entry: Tuple[Cell, ...], col: str) -> str:
        """Given a tuple of OpenPyxl cells, return the value of the cell matching the column value for col"""
        for c in entry:
            if c.column in [col, col2int(col)]:
                if isinstance(c.value, float):
                    return str(int(c.value)) if c.value.is_integer() else str(c.value)
                else:
                    return c.value if c.value is not None else ""
        return ""
