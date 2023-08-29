from enum import Enum

from mothertongues.config.models import (
    DictionaryEntryExportFormat,
    MTDConfiguration,
    MTDExportFormat,
    ResourceManifest,
)


class SchemaTypes(str, Enum):
    main_format = "main"
    config = "config"
    manifest = "manifest"
    entry = "entry"


def get_schemas(type: SchemaTypes, json=False):
    if type == SchemaTypes.main_format:
        return MTDExportFormat.schema_json() if json else MTDExportFormat.schema()
    if type == SchemaTypes.config:
        return MTDConfiguration.schema_json() if json else MTDConfiguration.schema()
    if type == SchemaTypes.manifest:
        return ResourceManifest.schema_json() if json else ResourceManifest.schema()
    if type == SchemaTypes.entry:
        return (
            DictionaryEntryExportFormat.schema_json()
            if json
            else DictionaryEntryExportFormat.schema()
        )
