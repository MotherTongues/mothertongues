# Running Unit Tests Locally

All contributions to MotherTongues must pass unit tests before merging.
To run unit tests locally, do the following.

# MotherTongues Unit Tests

Unit tests for the MotherTongue repo are found in `/mothertongues/tests/`

Test runner is found in `run.py` script.

## Run Tests

### Run all tests
If poetry is active, run

    python run.py dev

If not in poetry, run

    poetry run python run.py dev

### Run specific tests

You can run individual test files like so:

    poetry run python -m unittest test_cli.py

You can also run individual tests by providing the path to the test method

    poetry run python -m unittest test_sorter.SorterTest.test_sort_formats

# MotherTongues-UI Unit Tests

Front end tests are run using `nx` within the *mothertongues-UI* directory

    cd mothertongues-UI
    npx nx test mtd-mobile-ui

!!! Note
    The above command assumes you have already installed the mtd-mobile-ui package. If not, first run `npm install` command
