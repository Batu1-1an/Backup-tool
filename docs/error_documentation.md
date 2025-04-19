# Error Documentation

This document tracks major failure points in the Python Backup & Restoration Tool and their solutions.

## Network Connectivity Issues

### SMB Connection Failures

**Problem**: Unable to connect to SMB share from Linux systems.

**Symptoms**:
- Connection errors when attempting to mount or access SMB shares
- "Permission denied" errors even with correct credentials

**Causes**:
- Missing SMB client libraries
- Incompatible SMB protocol versions
- Incorrect credentials format

**Solutions**:
1. Ensure `smbclient` and related libraries are installed on Linux systems
2. Explicitly specify SMB protocol version in connection parameters
3. Format credentials correctly for the specific platform
4. Add proper error handling with detailed logging to identify the specific cause

**Implementation Notes**:
```python
# Example of improved SMB connectivity in network.py
try:
    # Attempt connection with fallback protocol versions
    conn = None
    for protocol_version in ["3.0", "2.1", "2.0"]:
        try:
            conn = SMBConnection(
                username,
                password,
                client_machine_name,
                server_name,
                use_ntlm_v2=True,
                sign_options=SMBConnection.SIGN_WHEN_REQUIRED,
                is_direct_tcp=True
            )
            conn.connect(server_ip, 445, timeout=10)
            logger.info(f"Successfully connected using SMB protocol {protocol_version}")
            break
        except Exception as e:
            logger.debug(f"Failed to connect with SMB {protocol_version}: {str(e)}")
            continue
    
    if conn is None:
        raise ConnectionError("Failed to connect to SMB share with all protocol versions")
        
except Exception as e:
    logger.error(f"SMB connection error: {str(e)}")
    # Provide specific guidance based on error type
    if "unknown user" in str(e).lower():
        logger.error("Authentication failure - verify username/password")
    elif "timeout" in str(e).lower():
        logger.error("Connection timeout - verify server is reachable and port 445 is open")
    # Additional error type handling...
    raise
```

## Large File Handling

### Memory Errors During Large File Backup

**Problem**: Out of memory errors when backing up very large files.

**Symptoms**:
- Process crashes with memory allocation errors
- Slow performance with excessive memory usage

**Causes**:
- Reading entire files into memory at once
- Inefficient buffer management

**Solutions**:
1. Implement chunked file reading/writing with appropriate buffer sizes
2. Monitor memory usage during operations
3. Add progress tracking for large files

**Implementation Notes**:
```python
def copy_large_file(source_path, dest_path, chunk_size=8192*1024):
    """Copy a large file in chunks to avoid memory issues."""
    file_size = os.path.getsize(source_path)
    copied = 0
    start_time = time.time()
    
    try:
        with open(source_path, 'rb') as src, open(dest_path, 'wb') as dst:
            while True:
                chunk = src.read(chunk_size)
                if not chunk:
                    break
                    
                dst.write(chunk)
                copied += len(chunk)
                
                # Update progress every 5% or at least every 10MB
                if copied % max(file_size // 20, 10*1024*1024) < chunk_size:
                    percent = (copied / file_size) * 100
                    elapsed = time.time() - start_time
                    rate = copied / elapsed if elapsed > 0 else 0
                    logger.debug(f"Progress: {percent:.1f}% ({format_size(copied)}/{format_size(file_size)}) at {format_size(rate)}/s")
        
        return True
    except Exception as e:
        logger.error(f"Error copying large file {source_path}: {str(e)}")
        if os.path.exists(dest_path):
            try:
                os.remove(dest_path)  # Clean up partial file
            except:
                pass
        return False
```

## Permissions and Security

### Permission Denied Errors

**Problem**: Unable to back up certain files due to permission issues.

**Symptoms**:
- "Permission denied" errors for specific files
- Incomplete backups
- Restore operations fail to set correct permissions

**Causes**:
- Running the tool without sufficient privileges
- Different permission models between Windows and Linux
- Special file types with restricted access

**Solutions**:
1. Run the tool with appropriate elevated privileges
2. Implement permission checking before operations
3. Add detailed logging for permission-related failures
4. Create a "skip list" capability for files that can't be accessed

**Implementation Notes**:
```python
def check_file_permissions(file_path, need_write=False):
    """Check if we have sufficient permissions to access a file."""
    if not os.path.exists(file_path):
        return False, "File does not exist"
        
    try:
        # Check read access
        if os.access(file_path, os.R_OK):
            if need_write:
                # Also check write access if needed
                if os.access(file_path, os.W_OK):
                    return True, None
                else:
                    return False, "No write permission"
            else:
                return True, None
        else:
            return False, "No read permission"
    except Exception as e:
        return False, str(e)
```

## Scheduler Issues

### Missed Scheduled Backups

**Problem**: Scheduled backups not running at the configured times.

**Symptoms**:
- Missing backup sets
- Scheduler logs show no errors but backups aren't created

**Causes**:
- System hibernation/sleep during scheduled times
- Time zone confusion in schedule configuration
- Process termination without cleanup

**Solutions**:
1. Implement missed schedule detection and recovery
2. Use absolute time zone designations in the configuration
3. Add redundant scheduling mechanism with system's native scheduler
4. Implement proper process monitoring and watchdog

**Implementation Notes**:
```python
def handle_missed_schedules(config):
    """Check for and handle missed backup schedules."""
    last_backup_time = get_last_backup_time(config)
    current_time = datetime.now()
    
    # Check daily schedule
    if 'daily' in config['schedule']:
        daily_time = parse_time(config['schedule']['daily'])
        expected_last_daily = datetime.combine(current_time.date(), daily_time)
        
        # If we're past today's backup time and no backup was done today
        if current_time.time() > daily_time and (
           last_backup_time is None or last_backup_time.date() < current_time.date()):
            logger.warning("Detected missed daily backup, running now")
            return True
            
    # Similar checks for weekly schedule
    # ...
    
    return False
```

## Cross-Platform Compatibility

### Path Separator Issues

**Problem**: Path handling issues between Windows and Linux.

**Symptoms**:
- File not found errors
- Incorrect path construction
- Backup structure doesn't match source structure

**Causes**:
- Mixing of forward slashes and backslashes
- Different absolute path formats
- Special path handling for network shares

**Solutions**:
1. Use `pathlib` consistently throughout the codebase
2. Normalize all paths before operations
3. Implement platform-specific path handlers where needed

**Implementation Notes**:
```python
def normalize_path(path_str):
    """Normalize a path string for the current platform."""
    # Convert to Path object
    path = Path(path_str)
    
    # Handle UNC paths on Windows specially
    if platform.system() == 'Windows' and path_str.startswith('\\\\'):
        return path_str  # Keep UNC paths as-is
        
    # Otherwise return the normalized path
    return str(path.absolute())
```

## Data Integrity

### Corrupted Backup Files

**Problem**: Backup files occasionally become corrupted during transfer.

**Symptoms**:
- File size differences between source and destination
- Checksum verification failures
- Restore errors due to invalid files

**Causes**:
- Network interruptions during transfer
- Disk errors on source or destination
- Premature termination of backup process

**Solutions**:
1. Implement file verification via checksums
2. Use temporary files during transfer and rename on completion
3. Add retry logic for failed transfers
4. Implement a validation command to check backup integrity

**Implementation Notes**:
```python
def verify_file_integrity(source_path, dest_path):
    """Verify file integrity using MD5 checksums."""
    def calculate_md5(file_path, chunk_size=8192*1024):
        md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            while True:
                data = f.read(chunk_size)
                if not data:
                    break
                md5.update(data)
        return md5.hexdigest()
    
    try:
        source_md5 = calculate_md5(source_path)
        dest_md5 = calculate_md5(dest_path)
        
        if source_md5 == dest_md5:
            logger.debug(f"File integrity verified: {dest_path}")
            return True
        else:
            logger.error(f"File integrity check failed: {dest_path}")
            logger.error(f"Source MD5: {source_md5}, Destination MD5: {dest_md5}")
            return False
    except Exception as e:
        logger.error(f"Error verifying file integrity: {str(e)}")
        return False
``` 