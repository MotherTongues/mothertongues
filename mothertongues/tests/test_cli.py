import json

from typer.testing import CliRunner

from mothertongues.cli import app
from mothertongues.config.models import (
    DictionaryEntryExportFormat,
    MTDConfiguration,
    MTDExportFormat,
)
from mothertongues.tests.base_test_case import BasicTestCase


class CommandLineTest(BasicTestCase):
    """Test the command line"""

    def setUp(self):
        super().setUp()
        self.runner = CliRunner()

    def test_app_basic(self):
        result = self.runner.invoke(app, ["--help"])
        self.assertIn("https://docs.mothertongues.org/", result.stdout)
        self.assertEqual(result.exit_code, 0)

    def test_schema(self):
        result = self.runner.invoke(
            app, ["schema", "main", str(self.tempdir / "schema.json")]
        )
        self.assertEqual(result.exit_code, 0)
        with open(self.tempdir / "schema.json", encoding="utf8") as f:
            data = json.load(f)
        self.assertDictEqual(data, MTDExportFormat.schema())
        result = self.runner.invoke(
            app, ["schema", "config", str(self.tempdir / "schema.json")]
        )
        self.assertEqual(result.exit_code, 0)
        with open(self.tempdir / "schema.json", encoding="utf8") as f:
            data = json.load(f)
        self.assertDictEqual(data, MTDConfiguration.schema())
        result = self.runner.invoke(
            app, ["schema", "entry", str(self.tempdir / "schema.json")]
        )
        self.assertEqual(result.exit_code, 0)
        with open(self.tempdir / "schema.json", encoding="utf8") as f:
            data = json.load(f)
        self.assertDictEqual(data, DictionaryEntryExportFormat.schema())

    def test_export(self):
        result = self.runner.invoke(
            app,
            [
                "export",
                str(self.data_dir / "config_data_check.json"),
                str(self.tempdir),
            ],
        )
        self.assertEqual(result.exit_code, 0)
        self.assertIn("words9", result.stdout)
        self.assertIn("words7", result.stdout)
        self.assertIn("words4", result.stdout)
        self.assertIn("words6", result.stdout)
        self.assertIn("😀", result.stdout)
        self.assertIn(
            "Your dictionary for Danish and English has 6 entries.", result.stdout
        )
        with open(self.tempdir / "dictionary_data.json", encoding="utf8") as f:
            data = json.load(f)
        self.assertTrue(MTDExportFormat.validate(data))
