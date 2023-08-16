from enum import Enum

from mothertongues.config.models import (
    DictionaryEntry,
    ExportLanguageConfiguration,
    MTDExportFormat,
)


class SchemaTypes(str, Enum):
    main_format = "main"
    config = "config"
    entry = "entry"


def get_schemas(type: SchemaTypes):
    if type == SchemaTypes.main_format:
        return MTDExportFormat.schema()
    if type == SchemaTypes.config:
        return ExportLanguageConfiguration.schema()
    if type == SchemaTypes.entry:
        return DictionaryEntry.schema()
