import os
import sys
import pytest
import shutil
import time
from unittest.mock import patch, MagicMock, mock_open

# Add the src directory to the path to import the backup_tool module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from backup_tool import backup, config, network

# Fixture to mock os.path.exists
@pytest.fixture
def mock_os_path_exists():
    """Mocks os.path.exists."""
    with patch('os.path.exists') as mock_exists:
        # Default to True for paths unless specified otherwise in tests
        mock_exists.return_value = True
        yield mock_exists

# Fixture to mock os.path.isdir
@pytest.fixture
def mock_os_path_isdir():
    """Mocks os.path.isdir."""
    with patch('os.path.isdir') as mock_isdir:
        # Default to False (is a file) unless specified otherwise
        mock_isdir.return_value = False
        yield mock_isdir

# Fixture to mock os.stat
@pytest.fixture
def mock_os_stat():
    """Mocks os.stat to return a dummy file size."""
    with patch('os.stat') as mock_stat:
        mock_stat.return_value = MagicMock(st_size=1000) # Dummy file size
        yield mock_stat

# Fixture to mock os.makedirs
@pytest.fixture
def mock_os_makedirs():
    """Mocks os.makedirs."""
    with patch('os.makedirs') as mock_makedirs:
        yield mock_makedirs

# Fixture to mock shutil.copytree
@pytest.fixture
def mock_shutil_copytree():
    """Mocks shutil.copytree."""
    with patch('shutil.copytree') as mock_copytree:
        yield mock_copytree

# Fixture to mock shutil.copy2
@pytest.fixture
def mock_shutil_copy2():
    """Mocks shutil.copy2."""
    with patch('shutil.copy2') as mock_copy2:
        yield mock_copy2

# Fixture to mock the custom copy_with_progress
@pytest.fixture
def mock_copy_with_progress():
    """Mocks the custom copy_with_progress function."""
    with patch('backup_tool.backup.copy_with_progress') as mock_copy_progress:
        yield mock_copy_progress

# Fixture to mock network.connect_to_share
@pytest.fixture
def mock_network_connect():
    """Mocks network.connect_to_share."""
    with patch('backup_tool.network.connect_to_share') as mock_connect:
        mock_connect.return_value = "//mock_server/mock_share" # Return a dummy connected path
        yield mock_connect

# Fixture to mock network.disconnect_from_share
@pytest.fixture
def mock_network_disconnect():
    """Mocks network.disconnect_from_share."""
    with patch('backup_tool.network.disconnect_from_share') as mock_disconnect:
        yield mock_disconnect

# Fixture to mock os.uname
@pytest.fixture
def mock_os_uname():
    """Mocks os.uname."""
    with patch('os.uname') as mock_uname:
        mock_uname.return_value = MagicMock(nodename="mock_hostname")
        yield mock_uname

# Fixture to mock datetime.datetime.now
@pytest.fixture
def mock_datetime_now():
    """Mocks datetime.datetime.now."""
    with patch('datetime.datetime.now') as mock_now:
        mock_now.return_value = MagicMock()
        mock_now.return_value.strftime.return_value = "20231027_100000" # Consistent timestamp
        yield mock_now

# --- Test Cases for perform_backup ---

def test_perform_backup_success_files(mock_os_path_exists, mock_os_path_isdir, mock_os_stat, mock_os_makedirs, mock_copy_with_progress, mock_network_connect, mock_network_disconnect, mock_os_uname, mock_datetime_now):
    """Tests successful backup of files."""
    config_data = {
        "backup_sources": ["/fake/source1/file1.txt", "/fake/source2/file2.txt"],
        "backup_target": {
            "path": "//server/share",
            "type": "smb"
        },
        "schedule": {"daily": "02:00"}
    }
    mock_os_path_isdir.side_effect = lambda path: False # All sources are files

    backup.perform_backup(config_data)

    # Assert network connection and disconnection were called
    mock_network_connect.assert_called_once_with("//server/share", "smb", None)
    mock_network_disconnect.assert_called_once_with("//mock_server/mock_share", "smb")

    # Assert backup destination directory was created
    expected_backup_base = os.path.join("//mock_server/mock_share", "backups", "mock_hostname", "20231027_100000")
    mock_os_makedirs.assert_any_call(expected_backup_base, exist_ok=True)

    # Assert copy_with_progress was called for each file
    mock_copy_with_progress.assert_any_call("/fake/source1/file1.txt", os.path.join(expected_backup_base, "fake", "source1", "file1.txt"))
    mock_copy_with_progress.assert_any_call("/fake/source2/file2.txt", os.path.join(expected_backup_base, "fake", "source2", "file2.txt"))
    assert mock_copy_with_progress.call_count == 2 # Ensure it was called exactly twice

def test_perform_backup_success_directories(mock_os_path_exists, mock_os_path_isdir, mock_os_makedirs, mock_shutil_copytree, mock_network_connect, mock_network_disconnect, mock_os_uname, mock_datetime_now):
    """Tests successful backup of directories."""
    config_data = {
        "backup_sources": ["/fake/source1/dir1", "/fake/source2/dir2"],
        "backup_target": {
            "path": "//server/share",
            "type": "smb"
        },
        "schedule": {"daily": "02:00"}
    }
    mock_os_path_isdir.side_effect = lambda path: True # All sources are directories

    backup.perform_backup(config_data)

    # Assert network connection and disconnection were called
    mock_network_connect.assert_called_once_with("//server/share", "smb", None)
    mock_network_disconnect.assert_called_once_with("//mock_server/mock_share", "smb")

    # Assert backup destination directory was created
    expected_backup_base = os.path.join("//mock_server/mock_share", "backups", "mock_hostname", "20231027_100000")
    mock_os_makedirs.assert_any_call(expected_backup_base, exist_ok=True)

    # Assert shutil.copytree was called for each directory
    mock_shutil_copytree.assert_any_call("/fake/source1/dir1", os.path.join(expected_backup_base, "fake", "source1", "dir1"), dirs_exist_ok=True)
    mock_shutil_copytree.assert_any_call("/fake/source2/dir2", os.path.join(expected_backup_base, "fake", "source2", "dir2"), dirs_exist_ok=True)
    assert mock_shutil_copytree.call_count == 2 # Ensure it was called exactly twice

def test_perform_backup_source_not_found(mock_os_path_exists, mock_network_connect, mock_network_disconnect, mock_os_uname, mock_datetime_now):
    """Tests backup when a source is not found."""
    config_data = {
        "backup_sources": ["/fake/existing_source", "/fake/non_existent_source"],
        "backup_target": {
            "path": "//server/share",
            "type": "smb"
        },
        "schedule": {"daily": "02:00"}
    }
    # Configure mock_os_path_exists to return False for the non-existent source
    mock_os_path_exists.side_effect = lambda path: path == "/fake/existing_source"

    # Mock copy_with_progress and shutil.copytree to ensure they are not called for the missing source
    with patch('backup_tool.backup.copy_with_progress') as mock_copy_progress, \
         patch('shutil.copytree') as mock_copytree:

        backup.perform_backup(config_data)

        # Assert network connection and disconnection were called
        mock_network_connect.assert_called_once_with("//server/share", "smb", None)
        mock_network_disconnect.assert_called_once_with("//mock_server/mock_share", "smb")

        # Assert that copy was only attempted for the existing source
        mock_copy_progress.assert_called_once() # Assuming existing source is a file
        mock_copy_progress.assert_any_call("/fake/existing_source", ...) # Check if called with the existing source
        mock_copytree.assert_not_called() # Assuming existing source is a file

def test_perform_backup_network_error(mock_network_connect, mock_network_disconnect):
    """Tests backup when a network error occurs during connection."""
    config_data = {
        "backup_sources": ["/fake/source1"],
        "backup_target": {
            "path": "//server/share",
            "type": "smb"
        },
        "schedule": {"daily": "02:00"}
    }
    mock_network_connect.side_effect = network.NetworkError("Connection failed")

    with pytest.raises(network.NetworkError, match="Connection failed"):
        backup.perform_backup(config_data)

    # Assert network connection was called, but disconnection was not (as connection failed)
    mock_network_connect.assert_called_once_with("//server/share", "smb", None)
    mock_network_disconnect.assert_not_called()

def test_perform_backup_backup_error_during_copy(mock_os_path_exists, mock_os_path_isdir, mock_os_stat, mock_os_makedirs, mock_copy_with_progress, mock_network_connect, mock_network_disconnect, mock_os_uname, mock_datetime_now):
    """Tests backup when a BackupError occurs during file copying."""
    config_data = {
        "backup_sources": ["/fake/source1/file1.txt", "/fake/source2/file2.txt"],
        "backup_target": {
            "path": "//server/share",
            "type": "smb"
        },
        "schedule": {"daily": "02:00"}
    }
    mock_os_path_isdir.side_effect = lambda path: False # All sources are files
    # Make the first copy_with_progress call raise a BackupError
    mock_copy_with_progress.side_effect = [backup.BackupError("Copy failed"), None]

    backup.perform_backup(config_data) # Should not raise an exception, but log the error

    # Assert network connection and disconnection were called
    mock_network_connect.assert_called_once_with("//server/share", "smb", None)
    mock_network_disconnect.assert_called_once_with("//mock_server/mock_share", "smb")

    # Assert copy_with_progress was called for both files (continues after error)
    mock_copy_with_progress.assert_any_call("/fake/source1/file1.txt", ...)
    mock_copy_with_progress.assert_any_call("/fake/source2/file2.txt", ...)
    assert mock_copy_with_progress.call_count == 2

def test_perform_backup_config_error(mock_network_connect, mock_network_disconnect):
    """Tests backup when a ConfigError occurs."""
    # Missing backup_sources
    config_data = {
        "backup_target": {
            "path": "//server/share",
            "type": "smb"
        },
        "schedule": {"daily": "02:00"}
    }

    with pytest.raises(config.ConfigError, match="Invalid or missing 'backup_sources'"):
        backup.perform_backup(config_data)

    # Assert network connection and disconnection were not called
    mock_network_connect.assert_not_called()
    mock_network_disconnect.assert_not_called()

def test_perform_backup_with_source_override(mock_os_path_exists, mock_os_path_isdir, mock_os_stat, mock_os_makedirs, mock_copy_with_progress, mock_network_connect, mock_network_disconnect, mock_os_uname, mock_datetime_now):
    """Tests successful backup with source override."""
    config_data = {
        "backup_sources": ["/fake/config_source"], # This should be ignored
        "backup_target": {
            "path": "//server/share",
            "type": "smb"
        },
        "schedule": {"daily": "02:00"}
    }
    source_override = ["/fake/override_source1", "/fake/override_source2"]
    mock_os_path_isdir.side_effect = lambda path: False # All sources are files

    backup.perform_backup(config_data, source_override=source_override)

    # Assert network connection and disconnection were called
    mock_network_connect.assert_called_once_with("//server/share", "smb", None)
    mock_network_disconnect.assert_called_once_with("//mock_server/mock_share", "smb")

    # Assert copy_with_progress was called for each override source
    expected_backup_base = os.path.join("//mock_server/mock_share", "backups", "mock_hostname", "20231027_100000")
    mock_copy_with_progress.assert_any_call("/fake/override_source1", os.path.join(expected_backup_base, "fake", "override_source1"))
    mock_copy_with_progress.assert_any_call("/fake/override_source2", os.path.join(expected_backup_base, "fake", "override_source2"))
    assert mock_copy_with_progress.call_count == 2 # Ensure it was called exactly twice

def test_perform_backup_with_target_override(mock_os_path_exists, mock_os_path_isdir, mock_os_stat, mock_os_makedirs, mock_copy_with_progress, mock_network_connect, mock_network_disconnect, mock_os_uname, mock_datetime_now):
    """Tests successful backup with target override."""
    config_data = {
        "backup_sources": ["/fake/source1"],
        "backup_target": {
            "path": "//config_server/config_share", # This should be ignored
            "type": "smb"
        },
        "schedule": {"daily": "02:00"}
    }
    target_override = {
        "path": "//override_server/override_share",
        "type": "nfs",
        "credentials": {"username": "override_user"}
    }
    mock_os_path_isdir.side_effect = lambda path: False # Source is a file

    backup.perform_backup(config_data, target_override=target_override)

    # Assert network connection and disconnection were called with override target
    mock_network_connect.assert_called_once_with("//override_server/override_share", "nfs", {"username": "override_user"})
    mock_network_disconnect.assert_called_once_with("//mock_server/mock_share", "nfs") # Disconnect uses the type from override

    # Assert copy_with_progress was called with the correct destination based on override target
    expected_backup_base = os.path.join("//mock_server/mock_share", "backups", "mock_hostname", "20231027_100000")
    mock_copy_with_progress.assert_called_once_with("/fake/source1", os.path.join(expected_backup_base, "fake", "source1"))

# --- Test Cases for copy_with_progress ---

@patch('builtins.open', new_callable=mock_open)
@patch('os.stat')
@patch('os.makedirs')
@patch('time.time')
def test_copy_with_progress_success(mock_time, mock_makedirs, mock_stat, mock_open):
    """Tests successful file copy with progress reporting."""
    mock_stat.return_value.st_size = 1000 # 1000 bytes file size
    mock_file_content = b"#" * 1000
    mock_open.return_value.__enter__.return_value.read.side_effect = [mock_file_content[i:i+100] for i in range(0, 1000, 100)] + [b""] # Read in chunks

    # Mock time.time to control progress reporting intervals
    mock_time.side_effect = [0, 0.5, 1.1, 1.8, 2.5, 3.1, 3.8, 4.5, 5.1, 5.8, 6.1] # Report every ~1 second

    src = "/fake/source/file.txt"
    dst = "/fake/destination/file.txt"

    with patch('backup_tool.backup.logger.info') as mock_logger_info:
        backup.copy_with_progress(src, dst, buffer_size=100, progress_interval=1)

    # Assert file was opened correctly
    mock_open.assert_any_call(src, 'rb')
    mock_open.assert_any_call(dst, 'wb')

    # Assert data was written
    handle = mock_open()
    handle.write.assert_called()
    assert handle.write.call_count == 10 # 10 chunks of 100 bytes

    # Assert progress was reported
    mock_logger_info.assert_any_call(f"Copying file: {src} to {dst} (1000 bytes)")
    # Check for progress reports at expected intervals
    mock_logger_info.assert_any_call("  Progress: 100/1000 bytes (10.00%)")
    mock_logger_info.assert_any_call("  Progress: 200/1000 bytes (20.00%)")
    mock_logger_info.assert_any_call("  Progress: 300/1000 bytes (30.00%)")
    mock_logger_info.assert_any_call("  Progress: 400/1000 bytes (40.00%)")
    mock_logger_info.assert_any_call("  Progress: 500/1000 bytes (50.00%)")
    mock_logger_info.assert_any_call("  Progress: 600/1000 bytes (60.00%)")
    mock_logger_info.assert_any_call("  Progress: 700/1000 bytes (70.00%)")
    mock_logger_info.assert_any_call("  Progress: 800/1000 bytes (80.00%)")
    mock_logger_info.assert_any_call("  Progress: 900/1000 bytes (90.00%)")
    mock_logger_info.assert_any_call("  Progress: 1000/1000 bytes (100.00%) - Complete")


@patch('builtins.open', new_callable=mock_open)
@patch('os.stat')
@patch('os.makedirs')
def test_copy_with_progress_file_not_found(mock_makedirs, mock_stat, mock_open):
    """Tests copy_with_progress when source file is not found."""
    mock_stat.side_effect = FileNotFoundError
    src = "/fake/non_existent_source/file.txt"
    dst = "/fake/destination/file.txt"

    with pytest.raises(backup.BackupError, match="Source file not found during copy"):
        backup.copy_with_progress(src, dst)

    mock_open.assert_not_called() # Ensure file was not opened

@patch('builtins.open', new_callable=mock_open)
@patch('os.stat')
@patch('os.makedirs')
def test_copy_with_progress_permission_error(mock_makedirs, mock_stat, mock_open):
    """Tests copy_with_progress when permission is denied."""
    mock_stat.return_value.st_size = 1000
    mock_open.side_effect = PermissionError
    src = "/fake/source/file.txt"
    dst = "/fake/destination/file.txt"

    with pytest.raises(backup.BackupError, match="Permission denied during copy"):
        backup.copy_with_progress(src, dst)

    mock_open.assert_any_call(src, 'rb') # Should attempt to open source

@patch('builtins.open', new_callable=mock_open)
@patch('os.stat')
@patch('os.makedirs')
def test_copy_with_progress_io_error(mock_makedirs, mock_stat, mock_open):
    """Tests copy_with_progress when an IO error occurs during writing."""
    mock_stat.return_value.st_size = 1000
    mock_open.return_value.__enter__.return_value.write.side_effect = IOError("Disk full")
    src = "/fake/source/file.txt"
    dst = "/fake/destination/file.txt"

    with pytest.raises(backup.BackupError, match="IO error during copy"):
        backup.copy_with_progress(src, dst)

    mock_open.assert_any_call(src, 'rb')
    mock_open.assert_any_call(dst, 'wb')