.. _configuration:

Configuration
=============

mothertongues Configuration
-----------------

Every dictionary will have one and only one MTD Configuration.


.. autopydantic_settings:: mothertongues.config.models.MTDConfiguration
    :settings-show-json: True
    :settings-show-config-member: False
    :settings-show-config-summary: False
    :settings-show-validator-members: True
    :settings-show-validator-summary: True
    :field-list-validators: True


LanguageConfiguration
---------------------

Every dictionary will have one and only one LanguageConfiguration.

.. autopydantic_settings:: mothertongues.config.models.LanguageConfiguration
    :settings-show-json: True
    :settings-show-config-member: False
    :settings-show-config-summary: False
    :settings-show-validator-members: True
    :settings-show-validator-summary: True
    :field-list-validators: True


DataSource
----------

Every dictionary will have one or more DataSources, which lets us build dictionaries from multiple data sources.

.. autopydantic_settings:: mothertongues.config.models.DataSource
    :settings-show-json: True
    :settings-show-config-member: False
    :settings-show-config-summary: False
    :settings-show-validator-members: True
    :settings-show-validator-summary: True
    :field-list-validators: True

Resource Manifest
~~~~~~~~~~~~~~~~~

Each DataSource will have a ResourceManifest describing how to parse and transform the data.

.. autopydantic_settings:: mothertongues.config.models.ResourceManifest
    :settings-show-json: True
    :settings-show-config-member: False
    :settings-show-config-summary: False
    :settings-show-validator-members: True
    :settings-show-validator-summary: True
    :field-list-validators: True

ParserTargets
~~~~~~~~~~~~~

The ParserTargets class defines which fields are present in your data and how they can be parsed.

.. autopydantic_settings:: mothertongues.config.models.ParserTargets
    :settings-show-json: True
    :settings-show-config-member: False
    :settings-show-config-summary: False
    :settings-show-validator-members: True
    :settings-show-validator-summary: True
    :field-list-validators: True
