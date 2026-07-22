import os
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    """Force-include mothertongues/ui only when it actually exists.

    It's built separately by the mothertongues-UI repo/submodule and is not
    tracked in this repo, so a plain `hatchling` force-include (which
    requires the source path to exist) would break local dev installs and
    the tests/docs CI workflows, none of which build the UI first.

    Set MTD_REQUIRE_UI_BUILD=1 (as the release publish workflow does) to make
    a missing UI a hard build failure instead of a silent omission.
    """

    def initialize(self, version, build_data):
        ui_dir = Path(self.root) / "mothertongues" / "ui"
        if ui_dir.is_dir():
            build_data.setdefault("force_include", {})[str(ui_dir)] = "mothertongues/ui"
        elif os.environ.get("MTD_REQUIRE_UI_BUILD"):
            raise FileNotFoundError(
                f"{ui_dir} does not exist. Build it first with "
                "`cd mothertongues-UI && npm install && "
                "npx nx build mtd-mobile-ui --configuration=pydev`."
            )
