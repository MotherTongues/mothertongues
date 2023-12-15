import csv

from mothertongues.config.models import DataSource
from mothertongues.parsers import BaseTabularParser


class Parser(BaseTabularParser):
    def __init__(self, data_source: DataSource):
        super().__init__(data_source)
        self.resource = self.get_data()

    def get_data(self):
        with open(self.resource_path, encoding="utf8") as f:
            reader = csv.reader(f, delimiter="|")
            if self.manifest.skip_header:
                _ = next(reader)
            return list(reader)
