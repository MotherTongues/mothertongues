import json
import os
from unittest import main
from unittest.mock import ANY, MagicMock, patch

from typer.testing import CliRunner

from mothertongues.cli import app, stop_process_tree
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

    def test_build_and_run_missingUI(self):
        with patch("mothertongues.cli.UI_DIR", self.tempdir / "ui"):
            for command, path in [
                ("build-and-run", self.data_dir / "config_data_check.json"),
                ("run", self.data_dir / "config_data_check.json"),
            ]:
                with capture_logs() as logs:
                    result = self.runner.invoke(app, [command, str(path)])
                self.assertEqual(result.exit_code, 1)
                self.assertIn("Mother Tongues UI was not found", logs[0])
                self.assertIn("pip install mothertongues", logs[0])

    def test_dev_missingUIRepo(self):
        with capture_logs() as logs:
            result = self.runner.invoke(
                app,
                [
                    "dev",
                    str(self.data_dir / "config_data_check.json"),
                    "--ui-repo",
                    str(self.tempdir / "mothertongues-UI"),
                ],
            )
        self.assertEqual(result.exit_code, 1)
        self.assertIn("npm install", logs[0])

    def make_ui_dir(self):
        ui_dir = self.tempdir / "ui"
        (ui_dir / "assets").mkdir(parents=True)
        return ui_dir

    def test_run(self):
        ui_dir = self.make_ui_dir()
        data = self.tempdir / "dictionary_data.json"
        data.write_text('{"data": []}', encoding="utf8")
        with (
            patch("mothertongues.cli.UI_DIR", ui_dir),
            patch("mothertongues.cli.serve") as mock_serve,
        ):
            result = self.runner.invoke(app, ["run", str(data), "--port", "4321"])
        self.assertEqual(result.exit_code, 0)
        mock_serve.assert_called_once_with(ui_dir, 4321)
        self.assertEqual(
            (ui_dir / "assets" / "dictionary_data.json").read_text(encoding="utf8"),
            '{"data": []}',
        )

    def test_build_and_run(self):
        ui_dir = self.make_ui_dir()
        config = self.data_dir / "config_data_check.json"
        with (
            patch("mothertongues.cli.UI_DIR", ui_dir),
            patch("mothertongues.cli.serve") as mock_serve,
        ):
            result = self.runner.invoke(app, ["build-and-run", str(config)])
        self.assertEqual(result.exit_code, 0)
        mock_serve.assert_called_once_with(ui_dir, 3636)
        with open(ui_dir / "assets" / "dictionary_data.json", encoding="utf8") as f:
            self.assertIn("data", json.load(f))

    def test_build_and_run_watch(self):
        ui_dir = self.make_ui_dir()
        config = self.data_dir / "config_data_check.json"
        with (
            patch("mothertongues.cli.UI_DIR", ui_dir),
            patch("mothertongues.cli.watch_and_serve") as mock_watch,
            patch("mothertongues.cli.serve") as mock_serve,
        ):
            result = self.runner.invoke(app, ["build-and-run", str(config), "--watch"])
        self.assertEqual(result.exit_code, 0)
        mock_watch.assert_called_once_with(config, 3636, ui_dir)
        mock_serve.assert_not_called()
        # Watch mode serves the data from memory instead of writing it into the UI
        self.assertFalse((ui_dir / "assets" / "dictionary_data.json").exists())

    def invoke_dev(self, ui_repo):
        return self.runner.invoke(
            app,
            [
                "dev",
                str(self.data_dir / "config_data_check.json"),
                "--ui-repo",
                str(ui_repo),
                "--port",
                "4321",
            ],
        )

    def test_dev_missingNpx(self):
        ui_repo = self.tempdir / "mothertongues-UI"
        (ui_repo / "node_modules").mkdir(parents=True)
        with patch("mothertongues.cli.shutil.which", return_value=None):
            with capture_logs() as logs:
                result = self.invoke_dev(ui_repo)
        self.assertEqual(result.exit_code, 1)
        self.assertIn("Could not find `npx`", logs[0])

    def test_dev(self):
        ui_repo = self.tempdir / "mothertongues-UI"
        (ui_repo / "node_modules").mkdir(parents=True)
        with (
            patch("mothertongues.cli.shutil.which", return_value="/bin/npx"),
            patch("mothertongues.cli.subprocess.Popen") as mock_popen,
            patch("mothertongues.cli.watch_and_serve") as mock_watch,
            patch("mothertongues.cli.stop_process_tree") as mock_stop,
        ):
            result = self.invoke_dev(ui_repo)
            self.assertEqual(result.exit_code, 0)
            command = mock_popen.call_args.args[0]
            self.assertEqual(command[:4], ["/bin/npx", "nx", "serve", "mtd-mobile-ui"])
            self.assertIn("--port=4321", command)
            kwargs = mock_popen.call_args.kwargs
            self.assertEqual(kwargs["cwd"], ui_repo)
            self.assertEqual(kwargs["env"]["MTD_DATA_PORT"], "4322")
            (_, data_port, ui_dir), watch_kwargs = mock_watch.call_args
            self.assertEqual((data_port, ui_dir), (4322, None))
            self.assertEqual(watch_kwargs["ignore"], [ui_repo])
            # nx is stopped when the watcher exits
            mock_stop.assert_called_once_with(mock_popen.return_value)

    def test_stop_process_tree_posix(self):
        process = MagicMock(pid=1234)
        with (
            patch("mothertongues.cli.IS_WINDOWS", False),
            patch("mothertongues.cli.os.killpg", create=True) as mock_killpg,
        ):
            stop_process_tree(process)
            mock_killpg.assert_called_once_with(1234, ANY)
            process.wait.assert_called_once()
            # ...even if nx has already exited
            mock_killpg.side_effect = ProcessLookupError
            stop_process_tree(process)

    def test_stop_process_tree_windows(self):
        process = MagicMock(pid=1234)
        with (
            patch("mothertongues.cli.IS_WINDOWS", True),
            patch("mothertongues.cli.subprocess.run") as mock_run,
        ):
            stop_process_tree(process)
        self.assertEqual(
            mock_run.call_args.args[0], ["taskkill", "/T", "/F", "/PID", "1234"]
        )
        process.wait.assert_called_once()

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


if __name__ == "__main__":
    main()
