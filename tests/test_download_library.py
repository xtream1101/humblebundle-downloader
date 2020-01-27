from humblebundle_downloader.download_library import DownloadLibrary


def test_include_logic_has_values():
    dl = DownloadLibrary(
        'fake_cookie_path',
        'fake_library_path',
        ext_include=['pdf', 'EPub'],
    )
    assert dl._should_download_file_type('pdf') is True
    assert dl._should_download_file_type('df') is False
    assert dl._should_download_file_type('ePub') is True
    assert dl._should_download_file_type('mobi') is False


def test_include_logic_empty():
    dl = DownloadLibrary(
        'fake_cookie_path',
        'fake_library_path',
        ext_include=[],
    )
    assert dl._should_download_file_type('pdf') is True
    assert dl._should_download_file_type('df') is True
    assert dl._should_download_file_type('EPub') is True
    assert dl._should_download_file_type('mobi') is True


def test_exclude_logic_has_values():
    dl = DownloadLibrary(
        'fake_cookie_path',
        'fake_library_path',
        ext_exclude=['pdf', 'EPub'],
    )
    assert dl._should_download_file_type('pdf') is False
    assert dl._should_download_file_type('df') is True
    assert dl._should_download_file_type('ePub') is False
    assert dl._should_download_file_type('mobi') is True


def test_exclude_logic_empty():
    dl = DownloadLibrary(
        'fake_cookie_path',
        'fake_library_path',
        ext_exclude=[],
    )
    assert dl._should_download_file_type('pdf') is True
    assert dl._should_download_file_type('df') is True
    assert dl._should_download_file_type('EPub') is True
    assert dl._should_download_file_type('mobi') is True
