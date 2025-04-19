import os
import sys
import pytest
import subprocess
import tempfile
from unittest.mock import patch, MagicMock

# Add the src directory to the path to import the backup_tool module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from backup_tool import network

# Fixture to mock subprocess.run
@pytest.fixture
def mock_subprocess_run():
    """Mocks subprocess.run to prevent actual command execution."""
    with patch('subprocess.run') as mock_run:
        # Configure the mock to return a successful result by default
        mock_run.return_value = MagicMock(
            stdout="Command executed successfully",
            stderr="",
            returncode=0,
            check_returncode=lambda: None # Simulate check=True success
        )
        yield mock_run

# Fixture to mock os.makedirs
@pytest.fixture
def mock_os_makedirs():
    """Mocks os.makedirs to prevent actual directory creation."""
    with patch('os.makedirs') as mock_makedirs:
        yield mock_makedirs

# Fixture to mock os.path.exists
@pytest.fixture
def mock_os_path_exists():
    """Mocks os.path.exists."""
    with patch('os.path.exists') as mock_exists:
        # Default to True for paths unless specified otherwise in tests
        mock_exists.return_value = True
        yield mock_exists

# Fixture to mock os.path.ismount
@pytest.fixture
def mock_os_path_ismount():
    """Mocks os.path.ismount."""
    with patch('os.path.ismount') as mock_ismount:
        # Default to False unless specified otherwise
        mock_ismount.return_value = False
        yield mock_ismount

# Fixture to mock os.rmdir
@pytest.fixture
def mock_os_rmdir():
    """Mocks os.rmdir."""
    with patch('os.rmdir') as mock_rmdir:
        yield mock_rmdir

# Fixture to mock tempfile.NamedTemporaryFile
@pytest.fixture
def mock_tempfile_namedtemporaryfile():
    """Mocks tempfile.NamedTemporaryFile."""
    with patch('tempfile.NamedTemporaryFile') as mock_tempfile:
        # Create a mock file object
        mock_file = MagicMock()
        mock_file.name = "/tmp/mock_creds_file" # Assign a mock name
        mock_tempfile.return_value.__enter__.return_value = mock_file
        yield mock_tempfile

# Fixture to mock os.chmod
@pytest.fixture
def mock_os_chmod():
    """Mocks os.chmod."""
    with patch('os.chmod') as mock_chmod:
        yield mock_chmod

# Fixture to mock os.remove
@pytest.fixture
def mock_os_remove():
    """Mocks os.remove."""
    with patch('os.remove') as mock_remove:
        yield mock_remove


# --- Test Cases for connect_to_share ---

@patch('backup_tool.network.is_windows', return_value=True)
@patch('backup_tool.network.is_linux', return_value=False)
def test_connect_to_share_smb_windows_success(mock_is_linux, mock_is_windows, mock_subprocess_run):
    """Tests successful SMB connection on Windows."""
    share_path = "//server/share"
    connected_path = network.connect_to_share(share_path, "smb")
    mock_subprocess_run.assert_called_once_with(
        ["net", "use", share_path], shell=True, check=True, capture_output=True, text=True
    )
    assert connected_path == share_path

@patch('backup_tool.network.is_windows', return_value=True)
@patch('backup_tool.network.is_linux', return_value=False)
def test_connect_to_share_smb_windows_with_credentials_success(mock_is_linux, mock_is_windows, mock_subprocess_run):
    """Tests successful SMB connection with credentials on Windows."""
    share_path = "//server/share"
    credentials = {"username": "user", "password": "password"}
    connected_path = network.connect_to_share(share_path, "smb", credentials)
    mock_subprocess_run.assert_called_once_with(
        ["net", "use", share_path, "password", "/user:user"], shell=True, check=True, capture_output=True, text=True
    )
    assert connected_path == share_path

@patch('backup_tool.network.is_windows', return_value=True)
@patch('backup_tool.network.is_linux', return_value=False)
def test_connect_to_share_smb_windows_failure(mock_is_linux, mock_is_windows, mock_subprocess_run):
    """Tests failed SMB connection on Windows."""
    mock_subprocess_run.side_effect = subprocess.CalledProcessError(1, ["net", "use"], stderr="Access Denied")
    share_path = "//server/share"
    with pytest.raises(network.NetworkError, match="Failed to connect to SMB share"):
        network.connect_to_share(share_path, "smb")
    mock_subprocess_run.assert_called_once_with(
        ["net", "use", share_path], shell=True, check=True, capture_output=True, text=True
    )

@patch('backup_tool.network.is_windows', return_value=False)
@patch('backup_tool.network.is_linux', return_value=True)
def test_connect_to_share_smb_linux_success(mock_is_linux, mock_is_windows, mock_subprocess_run, mock_os_makedirs, mock_tempfile_namedtemporaryfile, mock_os_chmod):
    """Tests successful SMB connection on Linux."""
    share_path = "//server/share"
    credentials = {"username": "user", "password": "password"}
    connected_path = network.connect_to_share(share_path, "smb", credentials)

    # Assert that temporary directory was created
    mock_os_makedirs.assert_called_once() # Check if called at least once

    # Assert that temporary credentials file was created and written to
    mock_tempfile_namedtemporaryfile.assert_called_once_with(mode='w', delete=False)
    mock_tempfile_namedtemporaryfile.return_value.__enter__.return_value.write.assert_any_call("username=user\n")
    mock_tempfile_namedtemporaryfile.return_value.__enter__.return_value.write.assert_any_call("password=password\n")

    # Assert that permissions were set on the credentials file
    mock_os_chmod.assert_called_once_with("/tmp/mock_creds_file", 0o600)

    # Assert that the mount command was called with the credentials file
    mock_subprocess_run.assert_called_once()
    called_command = mock_subprocess_run.call_args[0][0]
    assert "sudo" in called_command
    assert "mount" in called_command
    assert "-t" in called_command
    assert "cifs" in called_command
    assert share_path in called_command
    assert "/mnt/backup_tool_smb_" in "".join(called_command) # Check for the temporary mount point pattern
    assert "-o" in called_command
    options_index = called_command.index("-o") + 1
    options = called_command[options_index].split(',')
    assert "vers=3.0" in options
    assert "credentials=/tmp/mock_creds_file" in options

    # The connected path should be the temporary mount point
    assert "/mnt/backup_tool_smb_" in connected_path

@patch('backup_tool.network.is_windows', return_value=False)
@patch('backup_tool.network.is_linux', return_value=True)
def test_connect_to_share_smb_linux_failure(mock_is_linux, mock_is_windows, mock_subprocess_run, mock_os_makedirs, mock_os_rmdir, mock_tempfile_namedtemporaryfile, mock_os_remove):
    """Tests failed SMB connection on Linux."""
    mock_subprocess_run.side_effect = subprocess.CalledProcessError(1, ["sudo", "mount"], stderr="Mount failed")
    share_path = "//server/share"
    credentials = {"username": "user", "password": "password"}

    with pytest.raises(network.NetworkError, match="Failed to connect to SMB share"):
        network.connect_to_share(share_path, "smb", credentials)

    # Assert that temporary directory was created and then removed due to failure
    mock_os_makedirs.assert_called_once()
    mock_os_rmdir.assert_called_once()

    # Assert that temporary credentials file was created and then removed due to failure
    mock_tempfile_namedtemporaryfile.assert_called_once()
    mock_os_remove.assert_called_once_with("/tmp/mock_creds_file")


@patch('backup_tool.network.is_windows', return_value=False)
@patch('backup_tool.network.is_linux', return_value=True)
def test_connect_to_share_nfs_linux_success(mock_is_linux, mock_is_windows, mock_subprocess_run, mock_os_makedirs):
    """Tests successful NFS connection on Linux."""
    share_path = "server:/export"
    connected_path = network.connect_to_share(share_path, "nfs")

    # Assert that temporary directory was created
    mock_os_makedirs.assert_called_once()

    # Assert that the mount command was called
    mock_subprocess_run.assert_called_once()
    called_command = mock_subprocess_run.call_args[0][0]
    assert "sudo" in called_command
    assert "mount" in called_command
    assert "-t" in called_command
    assert "nfs" in called_command
    assert share_path in called_command
    assert "/mnt/backup_tool_nfs_" in "".join(called_command) # Check for the temporary mount point pattern

    # The connected path should be the temporary mount point
    assert "/mnt/backup_tool_nfs_" in connected_path

@patch('backup_tool.network.is_windows', return_value=False)
@patch('backup_tool.network.is_linux', return_value=True)
def test_connect_to_share_nfs_linux_failure(mock_is_linux, mock_is_windows, mock_subprocess_run, mock_os_makedirs, mock_os_rmdir):
    """Tests failed NFS connection on Linux."""
    mock_subprocess_run.side_effect = subprocess.CalledProcessError(1, ["sudo", "mount"], stderr="Mount failed")
    share_path = "server:/export"

    with pytest.raises(network.NetworkError, match="Failed to connect to NFS share"):
        network.connect_to_share(share_path, "nfs")

    # Assert that temporary directory was created and then removed due to failure
    mock_os_makedirs.assert_called_once()
    mock_os_rmdir.assert_called_once()


@patch('backup_tool.network.is_windows', return_value=True)
@patch('backup_tool.network.is_linux', return_value=False)
def test_connect_to_share_nfs_windows_unsupported(mock_is_linux, mock_is_windows):
    """Tests unsupported NFS connection on Windows."""
    share_path = "server:/export"
    with pytest.raises(network.NetworkError, match="NFS shares are not natively supported on Windows"):
        network.connect_to_share(share_path, "nfs")

def test_connect_to_share_unsupported_type(mock_subprocess_run):
    """Tests connection with an unsupported share type."""
    share_path = "some_path"
    with pytest.raises(network.NetworkError, match="Unsupported share type"):
        network.connect_to_share(share_path, "ftp")
    mock_subprocess_run.assert_not_called() # Ensure subprocess.run was not called

# --- Test Cases for disconnect_from_share ---

@patch('backup_tool.network.is_windows', return_value=True)
@patch('backup_tool.network.is_linux', return_value=False)
def test_disconnect_from_share_smb_windows_success(mock_is_linux, mock_is_windows, mock_subprocess_run):
    """Tests successful SMB disconnection on Windows."""
    share_path = "//server/share"
    network.disconnect_from_share(share_path, "smb")
    mock_subprocess_run.assert_called_once_with(
        ["net", "use", share_path, "/delete"], shell=True, check=True, capture_output=True, text=True
    )

@patch('backup_tool.network.is_windows', return_value=True)
@patch('backup_tool.network.is_linux', return_value=False)
def test_disconnect_from_share_smb_windows_failure(mock_is_linux, mock_is_windows, mock_subprocess_run):
    """Tests failed SMB disconnection on Windows (logs a warning)."""
    mock_subprocess_run.side_effect = subprocess.CalledProcessError(2, ["net", "use", "/delete"], stderr="Share not found")
    share_path = "//server/share"
    # This should not raise an exception, but log a warning
    network.disconnect_from_share(share_path, "smb")
    mock_subprocess_run.assert_called_once_with(
        ["net", "use", share_path, "/delete"], shell=True, check=True, capture_output=True, text=True
    )

@patch('backup_tool.network.is_windows', return_value=False)
@patch('backup_tool.network.is_linux', return_value=True)
def test_disconnect_from_share_smb_linux_success(mock_is_linux, mock_is_windows, mock_subprocess_run, mock_os_path_exists, mock_os_path_ismount, mock_os_rmdir, mock_os_remove):
    """Tests successful SMB disconnection on Linux."""
    share_path = "/mnt/backup_tool_smb_123" # Example mount point
    network.disconnect_from_share(share_path, "smb")
    mock_subprocess_run.assert_called_once_with(
        ["sudo", "umount", share_path], check=True, capture_output=True, text=True
    )
    # Assert that the temporary mount point directory was removed
    mock_os_path_exists.assert_called_with(share_path)
    mock_os_path_ismount.assert_called_with(share_path)
    mock_os_rmdir.assert_called_once_with(share_path)
    # Assert that the temporary credentials file was attempted to be removed
    mock_os_remove.assert_called_once_with(f"/tmp/backup_tool_smb_creds_{os.getpid()}")


@patch('backup_tool.network.is_windows', return_value=False)
@patch('backup_tool.network.is_linux', return_value=True)
def test_disconnect_from_share_smb_linux_failure(mock_is_linux, mock_is_windows, mock_subprocess_run, mock_os_path_exists, mock_os_path_ismount, mock_os_rmdir, mock_os_remove):
    """Tests failed SMB disconnection on Linux (logs a warning)."""
    mock_subprocess_run.side_effect = subprocess.CalledProcessError(1, ["sudo", "umount"], stderr="Device is busy")
    share_path = "/mnt/backup_tool_smb_123" # Example mount point
    # This should not raise an exception, but log a warning
    network.disconnect_from_share(share_path, "smb")
    mock_subprocess_run.assert_called_once_with(
        ["sudo", "umount", share_path], check=True, capture_output=True, text=True
    )
    # Assert that directory removal was attempted but likely failed (depending on mock_os_path_ismount)
    mock_os_path_exists.assert_called_with(share_path)
    mock_os_path_ismount.assert_called_with(share_path)
    # mock_os_rmdir might not be called if ismount returns True
    # Assert that the temporary credentials file was attempted to be removed
    mock_os_remove.assert_called_once_with(f"/tmp/backup_tool_smb_creds_{os.getpid()}")


@patch('backup_tool.network.is_windows', return_value=False)
@patch('backup_tool.network.is_linux', return_value=True)
def test_disconnect_from_share_nfs_linux_success(mock_is_linux, mock_is_windows, mock_subprocess_run, mock_os_path_exists, mock_os_path_ismount, mock_os_rmdir):
    """Tests successful NFS disconnection on Linux."""
    share_path = "/mnt/backup_tool_nfs_456" # Example mount point
    network.disconnect_from_share(share_path, "nfs")
    mock_subprocess_run.assert_called_once_with(
        ["sudo", "umount", share_path], check=True, capture_output=True, text=True
    )
    # Assert that the temporary mount point directory was removed
    mock_os_path_exists.assert_called_with(share_path)
    mock_os_path_ismount.assert_called_with(share_path)
    mock_os_rmdir.assert_called_once_with(share_path)


@patch('backup_tool.network.is_windows', return_value=False)
@patch('backup_tool.network.is_linux', return_value=True)
def test_disconnect_from_share_nfs_linux_failure(mock_is_linux, mock_is_windows, mock_subprocess_run, mock_os_path_exists, mock_os_path_ismount, mock_os_rmdir):
    """Tests failed NFS disconnection on Linux (logs a warning)."""
    mock_subprocess_run.side_effect = subprocess.CalledProcessError(1, ["sudo", "umount"], stderr="Device is busy")
    share_path = "/mnt/backup_tool_nfs_456" # Example mount point
    # This should not raise an exception, but log a warning
    network.disconnect_from_share(share_path, "nfs")
    mock_subprocess_run.assert_called_once_with(
        ["sudo", "umount", share_path], check=True, capture_output=True, text=True
    )
    # Assert that directory removal was attempted but likely failed (depending on mock_os_path_ismount)
    mock_os_path_exists.assert_called_with(share_path)
    mock_os_path_ismount.assert_called_with(share_path)
    # mock_os_rmdir might not be called if ismount returns True


@patch('backup_tool.network.is_windows', return_value=True)
@patch('backup_tool.network.is_linux', return_value=False)
def test_disconnect_from_share_nfs_windows_unsupported(mock_is_linux, mock_is_windows):
    """Tests unsupported NFS disconnection on Windows (logs a warning)."""
    share_path = "server:/export"
    # This should not raise an exception, but log a warning
    network.disconnect_from_share(share_path, "nfs")

def test_disconnect_from_share_unsupported_type(mock_subprocess_run):
    """Tests disconnection with an unsupported share type (logs a warning)."""
    share_path = "some_path"
    # This should not raise an exception, but log a warning
    network.disconnect_from_share(share_path, "ftp")
    mock_subprocess_run.assert_not_called() # Ensure subprocess.run was not called