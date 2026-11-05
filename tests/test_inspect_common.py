import os
import pwd
import grp

from dcor_control.inspect import common


def test_check_permission_create_directory(tmp_path):
    path = tmp_path / "a" / "b"
    assert common.check_permission(path, mode_dir=0o750, autocorrect=True)
    assert path.is_dir()
    assert path.stat().st_mode & 0o777 == 0o750


def test_check_permission_create_directory_declined(monkeypatch, tmp_path):
    monkeypatch.setattr("builtins.input", lambda prompt: "n")
    path = tmp_path / "a"
    assert common.check_permission(path, mode_dir=0o750) == 0
    assert not path.exists()


def test_check_permission_mode(tmp_path):
    pdir = tmp_path / "dir"
    pdir.mkdir()
    pfile = pdir / "file.txt"
    pfile.write_text("hello")
    os.chmod(pdir, 0o700)
    os.chmod(pfile, 0o600)
    # recursive check corrects both directory and file
    assert common.check_permission(pdir, mode_dir=0o755, mode_file=0o644,
                                   recursive=True, autocorrect=True) == 2
    assert pdir.stat().st_mode & 0o777 == 0o755
    assert pfile.stat().st_mode & 0o777 == 0o644
    # nothing to do anymore
    assert common.check_permission(pdir, mode_dir=0o755, mode_file=0o644,
                                   recursive=True, autocorrect=True) == 0


def test_check_permission_mode_ask(monkeypatch, tmp_path):
    pfile = tmp_path / "file.txt"
    pfile.write_text("hello")
    os.chmod(pfile, 0o600)
    monkeypatch.setattr("builtins.input", lambda prompt: "n")
    assert common.check_permission(pfile, mode_file=0o644) == 0
    assert pfile.stat().st_mode & 0o777 == 0o600
    monkeypatch.setattr("builtins.input", lambda prompt: "y")
    assert common.check_permission(pfile, mode_file=0o644) == 1
    assert pfile.stat().st_mode & 0o777 == 0o644


def test_check_permission_owner(monkeypatch, tmp_path):
    pfile = tmp_path / "file.txt"
    pfile.write_text("hello")
    user = pwd.getpwuid(os.getuid()).pw_name
    group = grp.getgrgid(os.getgid()).gr_name
    # owner is correct
    assert common.check_permission(pfile, user=user, group=group) == 0
    # owner is wrong (pretend another uid), but user declines
    chown_calls = []
    monkeypatch.setattr(os, "chown",
                        lambda *args: chown_calls.append(args))
    monkeypatch.setattr(pwd, "getpwnam", lambda name: pwd.struct_passwd(
        ("other", "x", 12345, 12345, "", "/", "/bin/sh")))
    monkeypatch.setattr(grp, "getgrnam", lambda name: grp.struct_group(
        ("other", "x", 12345, [])))
    monkeypatch.setattr("builtins.input", lambda prompt: "n")
    assert common.check_permission(pfile, user="other") == 0
    assert not chown_calls
    assert common.check_permission(pfile, user="other",
                                   autocorrect=True) == 1
    assert chown_calls == [(pfile, 12345, 12345)]


def test_recursive_update_dict():
    d = {"a": 1, "b": {"c": 2, "d": 3}}
    u = {"b": {"c": 4, "e": {"f": 5}}, "g": 6}
    assert common.recursive_update_dict(d, u) == {
        "a": 1, "b": {"c": 4, "d": 3, "e": {"f": 5}}, "g": 6}
