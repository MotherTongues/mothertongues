import json
import os

from typer.testing import CliRunner

from mothertongues.cli import app
from mothertongues.config.models import (
    DictionaryEntryExportFormat,
    MTDConfiguration,
    MTDExportFormat,
)
from mothertongues.tests.base_test_case import BasicTestCase
from mothertongues.tests.utils import capture_logs


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

    # region Export Tests
    def test_export_help(self):
        result = self.runner.invoke(
            app,
            ["export", "--help"],
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Export your dictionary for use in a MTD UI", result.stdout)

    def test_export_missingConfigFileArg(self):
        result = self.runner.invoke(
            app,
            ["export"],
        )

        self.assertEqual(result.exit_code, 2)
        self.assertIn("Missing argument 'LANGUAGE_CONFIG_PATH'", result.stdout)

    def test_export_configFileDoesNotExist(self):
        result = self.runner.invoke(
            app,
            ["export", str(self.data_dir / "does_not_exist.json"), str(self.tempdir)],
        )
        self.assertEqual(result.exit_code, 2)
        self.assertIn("Invalid value for 'LANGUAGE_CONFIG_PATH'", result.stdout)
        self.assertIn("does not exist", result.stdout)

    def test_export_missingOutputDirArg(self):
        result = self.runner.invoke(
            app,
            ["export", str(self.data_dir / "config_data_check.json")],
        )

        self.assertEqual(result.exit_code, 2)
        self.assertIn("Missing argument 'OUTPUT_DIRECTORY'", result.stdout)

    def test_export_outputDirDoesNotExist(self):
        result = self.runner.invoke(
            app,
            [
                "export",
                str(self.data_dir / "config_data_check.json"),
                "nonexistant_output_dir",
            ],
        )
        self.assertEqual(result.exit_code, 2)
        self.assertIn("Invalid value for 'OUTPUT_DIRECTORY'", result.stdout)
        self.assertIn("does not exist", result.stdout)

    def test_export_config_empty(self):
        with capture_logs() as logs:
            result = self.runner.invoke(
                app,
                [
                    "export",
                    str(self.data_dir / "config_empty.json"),
                    str(self.tempdir),
                ],
            )

        self.assertEqual(result.exit_code, 1)
        self.assertIn("'data' value in your json config is empty", logs[0])

    def test_export_validate_happyPath(self):
        result = self.runner.invoke(
            app,
            [
                "export",
                str(self.data_dir / "config_data_check.json"),
                str(self.tempdir),
            ],
        )
        self.assertEqual(result.exit_code, 0)
        self.assertIn("9", result.stdout)
        self.assertIn("7", result.stdout)
        self.assertIn("4", result.stdout)
        self.assertIn("6", result.stdout)
        self.assertIn("😀", result.stdout)
        self.assertIn(
            "Your dictionary for Danish and English has 6 entries.", result.stdout
        )
        with open(self.tempdir / "dictionary_data.json", encoding="utf8") as f:
            data = json.load(f)
        self.assertTrue(MTDExportFormat.validate(data))

    # endregion

    # region New-project Tests
    def test_new_project_help(self):
        result = self.runner.invoke(
            app,
            ["new-project", "--help"],
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Create a start project", result.stdout)

    # def test_new_project_noArgs(self):
    #     result = self.runner.invoke(
    #         app,
    #         [
    #             "new-project",
    #         ],
    #     )

    #     self.assertEqual(result.exit_code, 0)

    def test_new_project_outputDir(self):
        result = self.runner.invoke(
            app,
            ["new-project", "--outdir", str(self.tempdir)],
        )

        self.assertEqual(result.exit_code, 0)

        # Assert that all expected files are created
        self.assertTrue(os.path.exists(os.path.join(self.tempdir, "data.xlsx")))
        self.assertTrue(os.path.exists(os.path.join(self.tempdir, "config.mtd.json")))

    def test_new_project_duplicateDataFile_noOverwrite(self):
        # Arrange
        path_dupe_file = os.path.join(self.tempdir, "data.xlsx")
        with open(path_dupe_file, "w"):
            pass

        # Act
        with capture_logs() as logs:
            result = self.runner.invoke(
                app,
                ["new-project", "--outdir", str(self.tempdir)],
            )

        # Assert
        self.assertEqual(result.exit_code, 1)
        self.assertIn("Tried to generate sample data", logs[0])
        self.assertIn("already exists", logs[0])
        self.assertIn("re-run with the --overwrite", logs[0])

    def test_new_project_duplicateDataFile_withOverwrite(self):
        # Arrange
        path_dupe_file = os.path.join(self.tempdir, "data.xlsx")
        with open(path_dupe_file, "w"):
            pass

        # Act
        result = self.runner.invoke(
            app,
            ["new-project", "--outdir", str(self.tempdir), "--overwrite"],
        )

        # Assert
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(os.path.exists(os.path.join(self.tempdir, "data.xlsx")))
        self.assertTrue(os.path.exists(os.path.join(self.tempdir, "config.mtd.json")))

    def test_new_project_duplicateConfigFile_noOverwrite(self):
        # Arrange
        path_dupe_file = os.path.join(self.tempdir, "config.mtd.json")
        with open(path_dupe_file, "w"):
            pass

        # Act
        with capture_logs() as logs:
            result = self.runner.invoke(
                app,
                ["new-project", "--outdir", str(self.tempdir)],
            )

        # Assert
        self.assertEqual(result.exit_code, 1)
        self.assertIn("Tried to generate configuration file", logs[0])
        self.assertIn("already exists", logs[0])
        self.assertIn("re-run with the --overwrite", logs[0])

    def test_new_project_duplicateConfigFile_withOverwrite(self):
        # Arrange
        path_dupe_file = os.path.join(self.tempdir, "config.mtd.json")
        with open(path_dupe_file, "w"):
            pass

        # Act
        result = self.runner.invoke(
            app,
            ["new-project", "--outdir", str(self.tempdir), "--overwrite"],
        )

        # Assert
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(os.path.exists(os.path.join(self.tempdir, "data.xlsx")))
        self.assertTrue(os.path.exists(os.path.join(self.tempdir, "config.mtd.json")))

    # endregion
