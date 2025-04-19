import os
import sys
import logging
import subprocess
import tempfile

logger = logging.getLogger("backup_tool")

class NetworkError(Exception):
    """Custom exception for network-related errors."""
    pass

def is_windows():
    """Checks if the current operating system is Windows."""
    return sys.platform.startswith('win')

def is_linux():
    """Checks if the current operating system is Linux."""
    return sys.platform.startswith('linux')

def connect_to_share(share_path, share_type, credentials=None):
    """
    Connects to a network share (SMB or NFS).

    Args:
        share_path (str): The path to the network share (e.g., '//server/share' or 'server:/export').
        share_type (str): The type of share ('smb' or 'nfs').
        credentials (dict, optional): A dictionary containing 'username' and 'password' for authentication.

    Returns:
        str: The path to the connected share (UNC path on Windows, mount point on Linux).

    Raises:
        NetworkError: If connection fails or share type is unsupported.
    """
    logger.info(f"Attempting to connect to {share_type} share: {share_path}")

    if share_type.lower() == 'smb':
        if is_windows():
            logger.info(f"Attempting Windows SMB connection to: {share_path}")
            command = ["net", "use", share_path]
            if credentials and "username" in credentials and "password" in credentials:
                command.extend([credentials["password"], "/user:" + credentials["username"]])

            try:
                # Use shell=True on Windows for net use command
                result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
                logger.info(f"net use command successful: {result.stdout.strip()}")
                # On Windows, the share_path itself is the path to use after connection
                return share_path
            except subprocess.CalledProcessError as e:
                logger.error(f"net use command failed: {e.stderr.strip()}")
                raise NetworkError(f"Failed to connect to SMB share {share_path}: {e.stderr.strip()}") from e
            except Exception as e:
                logger.error(f"An unexpected error occurred during Windows SMB connection: {e}")
                raise NetworkError(f"An unexpected error occurred during Windows SMB connection: {e}") from e

        elif is_linux():
            logger.info(f"Attempting Linux SMB (CIFS) connection to: {share_path}")
            # Need a mount point. For simplicity, let's use a temporary directory.
            mount_point = f"/mnt/backup_tool_smb_{os.getpid()}" # Simple temporary mount point
            os.makedirs(mount_point, exist_ok=True)

            command = ["sudo", "mount", "-t", "cifs", share_path, mount_point]
            options = ["vers=3.0"] # Specify SMB version, adjust if needed

            # Use a temporary credentials file for security
            creds_file = None
            if credentials and "username" in credentials and "password" in credentials:
                try:
                    # Create a temporary file to store credentials
                    with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
                        creds_file = tmp_file.name
                        tmp_file.write(f"username={credentials['username']}\n")
                        tmp_file.write(f"password={credentials['password']}\n")
                    # Set permissions to be readable only by the owner
                    os.chmod(creds_file, 0o600)
                    options.append(f"credentials={creds_file}")
                except Exception as e:
                    # Clean up the temporary mount point directory
                    if os.path.exists(mount_point) and not os.path.ismount(mount_point):
                         os.rmdir(mount_point)
                    logger.error(f"Failed to create temporary credentials file: {e}")
                    raise NetworkError(f"Failed to create temporary credentials file: {e}") from e


            command.extend(["-o", ",".join(options)])

            try:
                # Running mount requires root privileges, hence 'sudo'.
                result = subprocess.run(command, check=True, capture_output=True, text=True)
                logger.info(f"mount -t cifs command successful: {result.stdout.strip()}")
                # Return the mount point path
                return mount_point
            except subprocess.CalledProcessError as e:
                logger.error(f"mount -t cifs command failed: {e.stderr.strip()}")
                # Clean up the temporary mount point directory if mount failed
                if os.path.exists(mount_point) and not os.path.ismount(mount_point):
                     os.rmdir(mount_point)
                # Clean up credentials file if it exists
                if creds_file and os.path.exists(creds_file):
                    os.remove(creds_file)
                raise NetworkError(f"Failed to connect to SMB share {share_path}: {e.stderr.strip()}") from e
            except Exception as e:
                logger.error(f"An unexpected error occurred during Linux SMB connection: {e}")
                # Clean up the temporary mount point directory
                if os.path.exists(mount_point) and not os.path.ismount(mount_point):
                     os.rmdir(mount_point)
                # Clean up credentials file if it exists
                if creds_file and os.path.exists(creds_file):
                    os.remove(creds_file)
                raise NetworkError(f"An unexpected error occurred during Linux SMB connection: {e}") from e
        else:
            raise NetworkError(f"Unsupported operating system for SMB: {sys.platform}")

    elif share_type.lower() == 'nfs':
        if is_linux():
            logger.info(f"Attempting Linux NFS connection to: {share_path}")
            # Need a mount point.
            mount_point = f"/mnt/backup_tool_nfs_{os.getpid()}" # Simple temporary mount point
            os.makedirs(mount_point, exist_ok=True)

            command = ["sudo", "mount", "-t", "nfs", share_path, mount_point]
            # NFS typically doesn't use username/password in the mount command itself.
            # Authentication is usually handled by server-side configuration (e.g., IP-based, Kerberos).
            # Mount options can be added if needed (e.g., vers=4, proto=tcp)
            # command.extend(["-o", "vers=4,proto=tcp"])

            try:
                # Running mount requires root privileges.
                result = subprocess.run(command, check=True, capture_output=True, text=True)
                logger.info(f"mount -t nfs command successful: {result.stdout.strip()}")
                # Return the mount point path
                return mount_point
            except subprocess.CalledProcessError as e:
                logger.error(f"mount -t nfs command failed: {e.stderr.strip()}")
                # Clean up the temporary mount point directory if mount failed
                if os.path.exists(mount_point) and not os.path.ismount(mount_point):
                     os.rmdir(mount_point)
                raise NetworkError(f"Failed to connect to NFS share {share_path}: {e.stderr.strip()}") from e
            except Exception as e:
                logger.error(f"An unexpected error occurred during Linux NFS connection: {e}")
                # Clean up the temporary mount point directory
                if os.path.exists(mount_point) and not os.path.ismount(mount_point):
                     os.rmdir(mount_point)
                raise NetworkError(f"An unexpected error occurred during Linux NFS connection: {e}") from e
        elif is_windows():
             # Windows typically uses SMB for network shares, NFS client needs to be installed and configured
             logger.error("NFS shares are not natively supported on Windows without additional setup.")
             raise NetworkError("NFS shares are not natively supported on Windows without additional setup.")
        else:
            raise NetworkError(f"Unsupported operating system for NFS: {sys.platform}")

    else:
        raise NetworkError(f"Unsupported share type: {share_type}. Must be 'smb' or 'nfs'.")

def disconnect_from_share(share_path, share_type):
    """
    Disconnects from a network share (SMB or NFS).

    Args:
        share_path (str): The path to the connected network share (UNC path or mount point).
        share_type (str): The type of share ('smb' or 'nfs').

    Raises:
        NetworkError: If disconnection fails or share type is unsupported.
    """
    logger.info(f"Attempting to disconnect from {share_type} share: {share_path}")

    if share_type.lower() == 'smb':
        if is_windows():
            logger.info(f"Attempting Windows SMB disconnection from: {share_path}")
            command = ["net", "use", share_path, "/delete"]

            try:
                # Use shell=True on Windows for net use command
                result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
                logger.info(f"net use /delete command successful: {result.stdout.strip()}")
            except subprocess.CalledProcessError as e:
                logger.error(f"net use /delete command failed: {e.stderr.strip()}")
                # Note: Sometimes net use /delete fails if the share is not connected, which is fine.
                logger.warning(f"Failed to disconnect from SMB share {share_path}: {e.stderr.strip()}")
            except Exception as e:
                logger.error(f"An unexpected error occurred during Windows SMB disconnection: {e}")

        elif is_linux():
            logger.info(f"Attempting Linux SMB (CIFS) unmount from: {share_path}")
            command = ["sudo", "umount", share_path]

            try:
                # Running umount requires root privileges.
                result = subprocess.run(command, check=True, capture_output=True, text=True)
                logger.info(f"umount command successful: {result.stdout.strip()}")
                # Clean up the temporary mount point directory
                if os.path.exists(share_path) and not os.path.ismount(share_path):
                     os.rmdir(share_path)
                # Clean up the temporary credentials file if it exists (assuming it's named based on PID)
                # The temporary file name is stored in the connect_to_share function,
                # so we need a way to access it here. A more robust solution would
                # involve returning the creds_file path from connect_to_share and passing
                # it to disconnect_from_share, or storing it in a class instance.
                # For now, I'll add a placeholder comment.
                # TODO: Implement proper cleanup of the temporary credentials file.
                pass # Placeholder for credentials file cleanup

            except subprocess.CalledProcessError as e:
                logger.error(f"umount command failed: {e.stderr.strip()}")
                # Note: umount can fail if the share is busy.
                logger.warning(f"Failed to unmount SMB share {share_path}: {e.stderr.strip()}")
            except Exception as e:
                logger.error(f"An unexpected error occurred during Linux SMB unmount: {e}")
        else:
            logger.warning(f"Unsupported operating system for SMB disconnection: {sys.platform}")

    elif share_type.lower() == 'nfs':
        if is_linux():
            logger.info(f"Attempting Linux NFS unmount from: {share_path}")
            command = ["sudo", "umount", share_path]

            try:
                # Running umount requires root privileges.
                result = subprocess.run(command, check=True, capture_output=True, text=True)
                logger.info(f"umount command successful: {result.stdout.strip()}")
                # Clean up the temporary mount point directory
                if os.path.exists(share_path) and not os.path.ismount(share_path):
                     os.rmdir(share_path)
            except subprocess.CalledProcessError as e:
                logger.error(f"umount command failed: {e.stderr.strip()}")
                # Note: umount can fail if the share is busy.
                logger.warning(f"Failed to unmount NFS share {share_path}: {e.stderr.strip()}")
            except Exception as e:
                logger.error(f"An unexpected error occurred during Linux NFS unmount: {e}")
        elif is_windows():
             logger.warning("NFS shares are not natively supported on Windows for disconnection without additional setup.")
             pass # Placeholder
        else:
            logger.warning(f"Unsupported operating system for NFS disconnection: {sys.platform}")

    else:
        logger.warning(f"Unsupported share type for disconnection: {share_type}")

    logger.info("Disconnection logic executed.")


# Example usage (for testing/demonstration)
if __name__ == "__main__":
    # Assuming logging is already set up by main or another entry point
    # For standalone testing, uncomment the line below:
    # from logger import setup_logging; setup_logging()

    # Example of attempting to connect and disconnect (will likely fail due to fake share)
    fake_smb_share_path = "//fake_server/fake_share"
    fake_nfs_share_path = "fake_server:/fake_export"

    print(f"Attempting to connect and disconnect from fake SMB share: {fake_smb_share_path}")
    connected_path = None
    try:
        connected_path = connect_to_share(fake_smb_share_path, "smb", {"username": "user", "password": "password"})
        logger.info(f"Successfully connected (placeholder): {connected_path}")
        # In a real scenario, you would perform operations using connected_path here
    except (NetworkError, NotImplementedError) as e:
        logger.error(f"Caught expected error during example SMB connection attempt: {e}")
    finally:
        if connected_path:
            # Attempt to disconnect even if connection logic was a placeholder
            try:
                disconnect_from_share(connected_path, "smb")
                logger.info("Successfully disconnected (placeholder).")
            except NetworkError as e:
                 logger.error(f"Caught error during example SMB disconnection attempt: {e}")


    print(f"\nAttempting to connect and disconnect from fake NFS share: {fake_nfs_share_path}")
    connected_path = None
    try:
        connected_path = connect_to_share(fake_nfs_share_path, "nfs")
        logger.info(f"Successfully connected (placeholder): {connected_path}")
        # In a real scenario, you would perform operations using connected_path here
    except (NetworkError, NotImplementedError) as e:
        logger.error(f"Caught expected error during example NFS connection attempt: {e}")
    finally:
        if connected_path:
             # Attempt to disconnect even if connection logic was a placeholder
            try:
                disconnect_from_share(connected_path, "nfs")
                logger.info("Successfully disconnected (placeholder).")
            except NetworkError as e:
                 logger.error(f"Caught error during example NFS disconnection attempt: {e}")


    print("\nAttempting connection with unsupported type:")
    try:
        connect_to_share("some_path", "ftp") # Unsupported type
    except NetworkError as e:
         logger.error(f"Caught expected error for unsupported type: {e}")