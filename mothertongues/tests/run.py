import os
import sys
from unittest import TestLoader, TestSuite, TextTestRunner

from loguru import logger

from mothertongues.tests.test_cli import CommandLineTest
from mothertongues.tests.test_configuration import ConfigurationTest
from mothertongues.tests.test_dictionary_data import DictionaryDataTest
from mothertongues.tests.test_exporter import DictionaryExporterTest
from mothertongues.tests.test_index import DictionaryIndexBuilderTest
from mothertongues.tests.test_parsers import DictionaryParserTest
from mothertongues.tests.test_sorter import SorterTest

LOADER = TestLoader()

INTEGRATION_TESTS = [LOADER.loadTestsFromTestCase(test) for test in [CommandLineTest]]

CONFIG_TESTS = [
    LOADER.loadTestsFromTestCase(test)
    for test in [
        ConfigurationTest,
    ]
]

DATA_TESTS = [
    LOADER.loadTestsFromTestCase(test)
    for test in [
        DictionaryDataTest,
    ]
]

PROCESSOR_TESTS = [
    LOADER.loadTestsFromTestCase(test)
    for test in [
        SorterTest,
        DictionaryParserTest,
        DictionaryExporterTest,
        DictionaryIndexBuilderTest,
    ]
]


def run_tests(suite: str, describe: bool = False) -> bool:
    """Run the test suite specified in suite.
    Args:
        suite: one of "all", "dev", etc specifying which suite to run
        describe: if True, list all the test cases instead of running them.
    Returns: Bool: True iff success
    """
    if suite == "all":
        test_suite = LOADER.discover(os.path.dirname(__file__))
    elif suite == "dev":
        test_suite = TestSuite(
            CONFIG_TESTS + DATA_TESTS + PROCESSOR_TESTS + INTEGRATION_TESTS
        )
    elif suite == "config":
        test_suite = TestSuite(CONFIG_TESTS)
    elif suite == "data":
        test_suite = TestSuite(DATA_TESTS)
    elif suite == "processors":
        test_suite = TestSuite(PROCESSOR_TESTS)
    elif suite == "integ":
        test_suite = TestSuite(INTEGRATION_TESTS)
    else:
        logger.error("Please specify a test suite to run: i.e. 'dev' or 'all'")
        return False

    runner = TextTestRunner(verbosity=3)
    return runner.run(test_suite).wasSuccessful()


if __name__ == "__main__":
    try:
        result = run_tests(sys.argv[1])
        if not result:
            logger.error("Some tests failed. Please see log above.")
            sys.exit(1)
    except IndexError:
        logger.error("Please specify a test suite to run: i.e. 'dev' or 'all'")
        sys.exit(1)
