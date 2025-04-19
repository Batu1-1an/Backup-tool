import os
import sys
import pytest
import shutil
from unittest.mock import patch, MagicMock, mock_open

# Add the src directory to the path to import the backup_tool module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from backup_tool import restore, config, network

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
        # Default to True (is a directory) unless specified otherwise
        mock_isdir.return_value = True
        yield mock_isdir

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

# --- Test Cases for perform_restore ---

def test_perform_restore_success_overwrite(mock_os_path_exists, mock_os_path_isdir, mock_os_makedirs, mock_shutil_copytree, mock_network_connect, mock_network_disconnect, mock_os_uname):
    """Tests successful restore with overwrite strategy."""
    config_data = {
        "backup_target": {
            "path": "//server/share",
            "type": "smb"
        }
    }
    backup_timestamp = "20231027_100000"
    destination_path = "/fake/local/destination"

    restore.perform_restore(config_data, backup_timestamp, destination_path, conflict_strategy="overwrite")

    # Assert network connection and disconnection were called
    mock_network_connect.assert_called_once_with("//server/share", "smb", None)
    mock_network_disconnect.assert_called_once_with("//mock_server/mock_share", "smb")

    # Assert destination directory was checked and copytree was called with dirs_exist_ok=True
    mock_os_path_exists.assert_any_call(destination_path)
    expected_backup_source = os.path.join("//mock_server/mock_share", "backups", "mock_hostname", backup_timestamp)
    mock_shutil_copytree.assert_called_once_with(expected_backup_source, destination_path, dirs_exist_ok=True)

def test_perform_restore_success_destination_not_exists(mock_os_path_exists, mock_os_path_isdir, mock_os_makedirs, mock_shutil_copytree, mock_network_connect, mock_network_disconnect, mock_os_uname):
    """Tests successful restore when destination does not exist."""
    config_data = {
        "backup_target": {
            "path": "//server/share",
            "type": "smb"
        }
    }
    backup_timestamp = "20231027_100000"
    destination_path = "/fake/local/destination"
    mock_os_path_exists.side_effect = lambda path: path != destination_path # Destination does not exist

    restore.perform_restore(config_data, backup_timestamp, destination_path)

    # Assert network connection and disconnection were called
    mock_network_connect.assert_called_once_with("//server/share", "smb", None)
    mock_network_disconnect.assert_called_once_with("//mock_server/mock_share", "smb")

    # Assert destination directory was created and copytree was called
    mock_os_path_exists.assert_any_call(destination_path)
    mock_os_makedirs.assert_called_once_with(destination_path)
    expected_backup_source = os.path.join("//mock_server/mock_share", "backups", "mock_hostname", backup_timestamp)
    mock_shutil_copytree.assert_called_once_with(expected_backup_source, destination_path, dirs_exist_ok=True)


def test_perform_restore_backup_timestamp_not_found(mock_os_path_exists, mock_os_path_isdir, mock_network_connect, mock_network_disconnect, mock_os_uname):
    """Tests restore when the backup timestamp directory is not found on the share."""
    config_data = {
        "backup_target": {
            "path": "//server/share",
            "type": "smb"
        }
    }
    backup_timestamp = "non_existent_timestamp"
    destination_path = "/fake/local/destination"
    # Configure mock_os_path_exists to return False for the backup source path
    mock_os_path_exists.side_effect = lambda path: path != os.path.join("//mock_server/mock_share", "backups", "mock_hostname", backup_timestamp)

    with pytest.raises(FileNotFoundError, match="Backup timestamp directory not found on share"):
        restore.perform_restore(config_data, backup_timestamp, destination_path)

    # Assert network connection was called, and disconnection was also called (as connection succeeded)
    mock_network_connect.assert_called_once_with("//server/share", "smb", None)
    mock_network_disconnect.assert_called_once_with("//mock_server/mock_share", "smb")


def test_perform_restore_backup_source_is_not_directory(mock_os_path_exists, mock_os_path_isdir, mock_network_connect, mock_network_disconnect, mock_os_uname):
    """Tests restore when the backup source path is not a directory."""
    config_data = {
        "backup_target": {
            "path": "//server/share",
            "type": "smb"
        }
    }
    backup_timestamp = "20231027_100000"
    destination_path = "/fake/local/destination"
    # Configure mock_os_path_isdir to return False for the backup source path
    mock_os_path_isdir.side_effect = lambda path: path != os.path.join("//mock_server/mock_share", "backups", "mock_hostname", backup_timestamp)

    with pytest.raises(FileNotFoundError, match="Backup source path is not a directory"):
        restore.perform_restore(config_data, backup_timestamp, destination_path)

    # Assert network connection was called, and disconnection was also called
    mock_network_connect.assert_called_once_with("//server/share", "smb", None)
    mock_network_disconnect.assert_called_once_with("//mock_server/mock_share", "smb")


def test_perform_restore_conflict_strategy_error(mock_os_path_exists, mock_os_path_isdir, mock_network_connect, mock_network_disconnect, mock_os_uname):
    """Tests restore with conflict strategy 'error' when destination exists."""
    config_data = {
        "backup_target": {
            "path": "//server/share",
            "type": "smb"
        }
    }
    backup_timestamp = "20231027_100000"
    destination_path = "/fake/local/destination"
    # Ensure destination exists
    mock_os_path_exists.return_value = True
    mock_os_path_isdir.side_effect = lambda path: path != os.path.join("//mock_server/mock_share", "backups", "mock_hostname", backup_timestamp) # Backup source is dir, destination exists

    with pytest.raises(restore.RestoreError, match="Destination path already exists"):
        restore.perform_restore(config_data, backup_timestamp, destination_path, conflict_strategy="error")

    # Assert network connection was called, and disconnection was also called
    mock_network_connect.assert_called_once_with("//server/share", "smb", None)
    mock_network_disconnect.assert_called_once_with("//mock_server/mock_share", "smb")

def test_perform_restore_network_error(mock_network_connect, mock_network_disconnect):
    """Tests restore when a network error occurs during connection."""
    config_data = {
        "backup_target": {
            "path": "//server/share",
            "type": "smb"
        }
    }
    backup_timestamp = "20231027_100000"
    destination_path = "/fake/local/destination"
    mock_network_connect.side_effect = network.NetworkError("Connection failed")

    with pytest.raises(network.NetworkError, match="Connection failed"):
        restore.perform_restore(config_data, backup_timestamp, destination_path)

    # Assert network connection was called, but disconnection was not
    mock_network_connect.assert_called_once_with("//server/share", "smb", None)
    mock_network_disconnect.assert_not_called()

def test_perform_restore_copy_error(mock_os_path_exists, mock_os_path_isdir, mock_os_makedirs, mock_shutil_copytree, mock_network_connect, mock_network_disconnect, mock_os_uname):
    """Tests restore when an error occurs during file copying."""
    config_data = {
        "backup_target": {
            "path": "//server/share",
            "type": "smb"
        }
    }
    backup_timestamp = "20231027_100000"
    destination_path = "/fake/local/destination"
    mock_shutil_copytree.side_effect = Exception("Copy failed")

    with pytest.raises(restore.RestoreError, match="Error during file copying for restore"):
        restore.perform_restore(config_data, backup_timestamp, destination_path)

    # Assert network connection and disconnection were called
    mock_network_connect.assert_called_once_with("//server/share", "smb", None)
    mock_network_disconnect.assert_called_once_with("//mock_server/mock_share", "smb")