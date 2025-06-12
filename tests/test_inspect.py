import os
import pathlib
import shutil

from dcor_control import inspect


data_path = pathlib.Path(__file__).parent / "data"


def test_get_dcor_site_config_dir(tmp_path):
    act_dir = inspect.get_dcor_site_config_dir()
    if act_dir is not None:
        # Only test this if relevant (Not set when managed remotely)
        shutil.copy2(act_dir / "dcor_config.json",
                     tmp_path / "dcor_config.json")
        try:
            os.environ["DCOR_SITE_CONFIG_DIR"] = str(tmp_path)
            assert str(inspect.get_dcor_site_config_dir()) == str(tmp_path)
        except BaseException:
            raise
        finally:
            # cleanup
            os.environ.pop("DCOR_SITE_CONFIG_DIR")
