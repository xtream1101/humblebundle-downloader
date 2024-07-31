import pytest
from humblebundle_downloader.cli import parse_args


def test_old_action_format():
    with pytest.raises(DeprecationWarning):
        _ = parse_args(["download", "-l", "some_path", "-c", "fake_cookie"])


def test_no_action():
    args = parse_args(["-l", "some_path", "-c", "fake_cookie"])
    assert args.library_path == "some_path"
    assert args.cookie_file == "fake_cookie"


def test_no_args():
    with pytest.raises(SystemExit) as ex:
        parse_args([])
    assert ex.value.code == 2
