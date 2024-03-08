from mothertongues.config.models import DataSource
from mothertongues.parsers import BaseTabularParser


class Parser(BaseTabularParser):
    def __init__(self, data_source: DataSource):
        super().__init__(data_source)
        self.resource = self.get_data()

    def get_data(self):
        return self.read_xsv(delimiter="\t")
