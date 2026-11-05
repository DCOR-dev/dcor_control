import pathlib
import re
import types

from dcor_control import backup


def test_delete_old_backups(tmp_path):
    regex = re.compile(r"^backup_(.*)_test\.txt$")
    paths = []
    for ii in range(10):
        path = tmp_path / f"backup_2026-01-{ii + 10}_test.txt"
        path.touch()
        paths.append(path)
    other = tmp_path / "other.txt"
    other.touch()
    backup.delete_old_backups(backup_root=tmp_path,
                              latest_backup=paths[-1],
                              regex=regex,
                              num=3)
    # only the three newest backups are kept
    assert sorted(tmp_path.glob("backup_*")) == paths[-3:]
    assert other.exists()


def test_gpg_encrypt(monkeypatch, tmp_path):
    calls = []

    def check_output(cmd, shell):
        calls.append(cmd)
        path_out.write_text("encrypted")

    monkeypatch.setattr(backup.sp, "check_output", check_output)
    path_in = tmp_path / "data.tar"
    path_in.write_text("data")
    path_out = tmp_path / "encrypted" / "data.tar.gpg"
    backup.gpg_encrypt(path_in, path_out, key_id="ABCDEF")
    cmd, = calls
    assert "--recipient 'ABCDEF'" in cmd
    assert path_out.parent.stat().st_mode & 0o777 == 0o700
    assert path_out.stat().st_mode & 0o777 == 0o400


def test_db_backup(monkeypatch, tmp_path):
    calls = []

    def check_output(cmd, shell):
        calls.append(cmd)
        # pg_dump writes the backup file
        path = cmd.split(" > ")[1].rstrip('"')
        pathlib.Path(path).write_text("database")

    monkeypatch.setattr(backup.pwd, "getpwnam",
                        lambda name: types.SimpleNamespace(pw_uid=1234))
    monkeypatch.setattr(backup.os, "chown", lambda *args: None)
    monkeypatch.setattr(backup.sp, "check_output", check_output)
    old = tmp_path / "database" / \
        "backup_db_ckan_default_2020-01-01_00-00-00_dcor-control.pgc"
    old.parent.mkdir()
    old.touch()
    path = backup.db_backup(path=tmp_path)
    assert path.parent == tmp_path / "database"
    assert path.read_text() == "database"
    assert path.stat().st_mode & 0o777 == 0o400
    assert "pg_dump --format=custom -d ckan_default" in calls[0]
    # less than 20 backups, so the old one is kept
    assert old.exists()
