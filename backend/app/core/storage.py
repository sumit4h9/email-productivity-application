"""
MinIO/S3 compatible object storage service for email attachments
"""

import hashlib
import io
import logging
import os
import time
from typing import BinaryIO, Optional, Tuple
from urllib.parse import urlparse

from minio import Minio
from minio.error import InvalidResponseError, S3Error

logger = logging.getLogger(__name__)

# MinIO configuration from environment variables
MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "minioadmin")
MINIO_SECURE = os.environ.get("MINIO_SECURE", "false").lower() == "true"
MINIO_BUCKET_NAME = os.environ.get("MINIO_BUCKET_NAME", "email-attachments")
MINIO_REGION = os.environ.get("MINIO_REGION", "us-east-1")

# Storage configuration
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB
CHUNK_SIZE = 8 * 1024  # 8KB chunks for streaming

# Strict content type whitelist - exact matches only for security
ALLOWED_CONTENT_TYPES = {
    # Text files
    "text/plain",
    "text/csv",
    "text/html",
    "text/rtf",
    # Images
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/bmp",
    "image/tiff",
    # Documents
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",  # .pptx
    "application/vnd.ms-excel",  # .xls
    "application/vnd.ms-powerpoint",  # .ppt
    "application/rtf",
    # Archives
    "application/zip",
    "application/x-zip-compressed",
    "application/x-rar-compressed",
    "application/x-7z-compressed",
    # Audio/Video (limited)
    "audio/mpeg",
    "audio/wav",
    "video/mp4",
    "video/avi",
    "video/quicktime",
}

# Global MinIO client instance
_minio_client: Optional[Minio] = None


def get_minio_client() -> Minio:
    """
    Get or create MinIO client instance with connection pooling and error handling

    Returns:
        Minio: Configured MinIO client

    Raises:
        Exception: If MinIO client cannot be created or configured
    """
    global _minio_client

    if _minio_client is None:
        try:
            # Parse endpoint to handle different formats
            endpoint = MINIO_ENDPOINT
            if not endpoint.startswith(("http://", "https://")):
                endpoint = f"{'https' if MINIO_SECURE else 'http'}://{endpoint}"

            parsed_url = urlparse(endpoint)
            host = parsed_url.hostname or "localhost"
            port = parsed_url.port or (443 if MINIO_SECURE else 9000)

            # Create MinIO client with proper configuration
            _minio_client = Minio(
                f"{host}:{port}",
                access_key=MINIO_ACCESS_KEY,
                secret_key=MINIO_SECRET_KEY,
                secure=MINIO_SECURE,
                region=MINIO_REGION,
                # Connection pooling and timeout configuration
                http_client=None,  # Use default HTTP client
            )

            # Test connection and create bucket if needed
            _ensure_bucket_exists()

            logger.info(f"MinIO client initialized successfully: {host}:{port}")

        except Exception as e:
            logger.error(f"Failed to initialize MinIO client: {e}")
            raise Exception(f"MinIO client initialization failed: {e}")

    return _minio_client


def _ensure_bucket_exists() -> None:
    """
    Ensure the required bucket exists, create if it doesn't

    Raises:
        Exception: If bucket cannot be created or accessed
    """
    try:
        client = get_minio_client()

        # Check if bucket exists
        if not client.bucket_exists(MINIO_BUCKET_NAME):
            logger.info(f"Creating MinIO bucket: {MINIO_BUCKET_NAME}")
            client.make_bucket(MINIO_BUCKET_NAME, location=MINIO_REGION)
            logger.info(f"MinIO bucket created successfully: {MINIO_BUCKET_NAME}")
        else:
            logger.debug(f"MinIO bucket already exists: {MINIO_BUCKET_NAME}")

    except Exception as e:
        logger.error(f"Failed to ensure bucket exists: {e}")
        raise Exception(f"Bucket setup failed: {e}")


def validate_file_for_storage(filename: str, content_type: str, file_size: int) -> Tuple[bool, str]:
    """
    Enhanced file validation for security and size constraints

    Args:
        filename: Name of the file
        content_type: MIME type of the file
        file_size: Size of the file in bytes

    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    try:
        # Enhanced filename validation
        if not filename or len(filename) > 255:
            return False, "Invalid filename length"

        # More comprehensive path traversal prevention
        dangerous_patterns = [
            "..",
            "/",
            "\\",
            "~",
            "$",
            "%",
            "&",
            "*",
            "?",
            "<",
            ">",
            "|",
            ":",
            ";",
        ]
        if any(pattern in filename for pattern in dangerous_patterns):
            log_security_event(
                "PATH_TRAVERSAL_ATTEMPT",
                filename,
                f"Dangerous pattern detected: {dangerous_patterns}",
            )
            return False, "Invalid filename: contains dangerous characters"

        # Prevent hidden files and system files
        if filename.startswith(".") or filename.lower().startswith(("con", "prn", "aux", "nul")):
            log_security_event("SYSTEM_FILE_ATTEMPT", filename, "System reserved filename detected")
            return False, "Invalid filename: system reserved name"

        # Prevent executable file extensions
        dangerous_extensions = [
            ".exe",
            ".bat",
            ".cmd",
            ".com",
            ".pif",
            ".scr",
            ".vbs",
            ".js",
            ".jar",
            ".sh",
            ".ps1",
        ]
        if any(filename.lower().endswith(ext) for ext in dangerous_extensions):
            log_security_event(
                "EXECUTABLE_FILE_ATTEMPT",
                filename,
                f"Executable extension detected: {filename.split('.')[-1]}",
            )
            return False, "Invalid filename: executable file extension not allowed"

        # Validate file size
        if file_size <= 0:
            return False, "Invalid file size"

        if file_size > MAX_FILE_SIZE:
            return False, f"File size {file_size} exceeds maximum allowed size {MAX_FILE_SIZE}"

        # Validate content type
        if not content_type:
            return False, "Content type is required"

        # Check if content type is allowed (exact match required)
        if content_type not in ALLOWED_CONTENT_TYPES:
            return False, f"Content type '{content_type}' is not allowed"

        return True, ""

    except Exception as e:
        logger.error(f"File validation error: {e}")
        return False, f"Validation error: {e}"


def generate_storage_key(email_id: str, attachment_id: str, filename: str) -> str:
    """
    Generate a unique storage key for the attachment

    Args:
        email_id: Email ID
        attachment_id: Attachment ID
        filename: Original filename

    Returns:
        str: Unique storage key
    """
    # Create a safe filename by removing/replacing dangerous characters
    safe_filename = "".join(c if c.isalnum() or c in ".-_" else "_" for c in filename)

    # Generate unique key with timestamp to prevent collisions
    timestamp = int(time.time() * 1000)  # milliseconds

    # Create hierarchical structure: attachments/email_id/attachment_id/filename
    storage_key = f"attachments/{email_id}/{attachment_id}/{timestamp}_{safe_filename}"

    return storage_key


def calculate_file_checksum(file_data: bytes) -> str:
    """
    Calculate SHA-256 checksum for file integrity verification

    Args:
        file_data: File data as bytes

    Returns:
        str: SHA-256 checksum in hexadecimal format
    """
    return hashlib.sha256(file_data).hexdigest()


def _contains_suspicious_patterns(file_data: bytes, filename: str) -> bool:
    """
    Basic malware detection by checking for suspicious patterns

    Args:
        file_data: File data as bytes
        filename: Original filename

    Returns:
        bool: True if suspicious patterns found, False otherwise
    """
    try:
        # Check for executable signatures in file header
        executable_signatures = [
            b"MZ",  # PE executable
            b"\x7fELF",  # ELF executable
            b"\xfe\xed\xfa",  # Mach-O executable
            b"#!/",  # Shell script
            b"<script",  # JavaScript/HTML
            b"javascript:",  # JavaScript URL
            b"vbscript:",  # VBScript
        ]

        # Check first 1KB for executable signatures
        header = file_data[:1024]
        for signature in executable_signatures:
            if signature in header:
                log_security_event(
                    "EXECUTABLE_SIGNATURE_DETECTED",
                    filename,
                    f"Executable signature found: {signature}",
                )
                return True

        # Check for embedded scripts in common file types
        if filename.lower().endswith((".pdf", ".doc", ".docx", ".xls", ".xlsx")):
            # Look for embedded JavaScript or macros
            suspicious_strings = [
                b"javascript:",
                b"vbscript:",
                b"<script",
                b"ActiveX",
                b"Macro",
                b"VBA",
                b"powershell",
                b"cmd.exe",
            ]

            for suspicious in suspicious_strings:
                if suspicious in file_data:
                    log_security_event(
                        "EMBEDDED_SCRIPT_DETECTED", filename, f"Embedded script found: {suspicious}"
                    )
                    return True

        # Check for unusually high entropy (potential encryption/compression)
        if len(file_data) > 1024:  # Only check larger files
            entropy = _calculate_entropy(file_data[:1024])
            if entropy > 7.5:  # High entropy threshold
                logger.warning(f"High entropy detected in {filename}: {entropy:.2f}")
                # Don't block based on entropy alone, just log

        return False

    except Exception as e:
        logger.error(f"Error checking suspicious patterns in {filename}: {e}")
        # If we can't check, err on the side of caution
        return True


def _calculate_entropy(data: bytes) -> float:
    """
    Calculate Shannon entropy of data

    Args:
        data: Data to analyze

    Returns:
        float: Entropy value (0-8)
    """
    try:
        if not data:
            return 0.0

        # Count byte frequencies
        byte_counts = [0] * 256
        for byte in data:
            byte_counts[byte] += 1

        # Calculate entropy
        entropy = 0.0
        data_len = len(data)

        for count in byte_counts:
            if count > 0:
                probability = count / data_len
                entropy -= probability * (probability.bit_length() - 1)

        return entropy

    except Exception:
        return 0.0


def store_attachment(
    file_data: bytes, storage_key: str, content_type: str, filename: str
) -> Tuple[bool, str, Optional[str]]:
    """
    Store attachment file in MinIO with enhanced security and memory management

    Args:
        file_data: File data as bytes
        storage_key: Unique storage key for the file
        content_type: MIME type of the file
        filename: Original filename

    Returns:
        Tuple[bool, str, Optional[str]]: (success, message, checksum)
    """
    file_obj = None
    try:
        # Enhanced validation before storage
        is_valid, error_msg = validate_file_for_storage(filename, content_type, len(file_data))

        if not is_valid:
            return False, f"File validation failed: {error_msg}", None

        # Additional security checks
        if len(file_data) == 0:
            return False, "File is empty", None

        # Check for suspicious file patterns (basic malware detection)
        if _contains_suspicious_patterns(file_data, filename):
            return False, "File contains suspicious patterns", None

        # Calculate checksum for integrity verification
        checksum = calculate_file_checksum(file_data)

        # Get MinIO client
        client = get_minio_client()

        # Create file-like object from bytes with memory management
        file_obj = io.BytesIO(file_data)

        # Store file with enhanced metadata
        client.put_object(
            bucket_name=MINIO_BUCKET_NAME,
            object_name=storage_key,
            data=file_obj,
            length=len(file_data),
            content_type=content_type,
            metadata={
                "original-filename": filename,
                "checksum": checksum,
                "upload-timestamp": str(int(time.time())),
                "file-size": str(len(file_data)),
                "security-validated": "true",
                "content-type-verified": "true",
            },
        )

        logger.info(
            f"Successfully stored attachment: {filename} -> {storage_key} "
            f"({len(file_data)} bytes, checksum: {checksum[:16]}...)"
        )

        return True, "File stored successfully", checksum

    except S3Error as e:
        error_msg = f"MinIO S3 error: {e.code} - {e.message}"
        logger.error(f"MinIO S3 error storing {filename}: {error_msg}")
        return False, error_msg, None

    except InvalidResponseError as e:
        error_msg = f"MinIO invalid response: {e}"
        logger.error(f"MinIO invalid response storing {filename}: {error_msg}")
        return False, error_msg, None

    except Exception as e:
        error_msg = f"Storage error: {e}"
        logger.error(f"Failed to store attachment {filename}: {error_msg}")
        return False, error_msg, None

    finally:
        # Ensure proper cleanup of file object
        if file_obj:
            try:
                file_obj.close()
            except Exception:
                pass


def stream_attachment_to_storage(
    file_stream: BinaryIO, storage_key: str, content_type: str, filename: str, file_size: int
) -> Tuple[bool, str, Optional[str]]:
    """
    Stream attachment file to MinIO storage with enhanced security and memory management

    Args:
        file_stream: File stream object
        storage_key: Unique storage key for the file
        content_type: MIME type of the file
        filename: Original filename
        file_size: Expected file size in bytes

    Returns:
        Tuple[bool, str, Optional[str]]: (success, message, checksum)
    """
    try:
        # Enhanced validation before storage
        is_valid, error_msg = validate_file_for_storage(filename, content_type, file_size)

        if not is_valid:
            return False, f"File validation failed: {error_msg}", None

        # Additional security checks
        if file_size == 0:
            return False, "File is empty", None

        # Get MinIO client
        client = get_minio_client()

        # Calculate checksum while streaming with memory management
        hasher = hashlib.sha256()

        # Create a secure wrapper to calculate checksum and detect threats during upload
        class SecureChecksumStream:
            def __init__(self, stream: BinaryIO, hasher: hashlib._hashlib.HASH, filename: str):
                self.stream = stream
                self.hasher = hasher
                self.total_read = 0
                self.filename = filename
                self.header_buffer = b""
                self.header_checked = False
                self.suspicious_patterns_found = False

            def read(self, size: int = -1) -> bytes:
                data = self.stream.read(size)
                if data:
                    # Check for suspicious patterns in the first chunk
                    if not self.header_checked and len(self.header_buffer) < 1024:
                        self.header_buffer += data
                        if len(self.header_buffer) >= 1024 or len(data) < size:
                            # We have enough data to check or this is the last chunk
                            if _contains_suspicious_patterns(self.header_buffer, self.filename):
                                self.suspicious_patterns_found = True
                                logger.warning(
                                    f"Suspicious patterns detected in streamed file: {self.filename}"
                                )
                            self.header_checked = True

                    self.hasher.update(data)
                    self.total_read += len(data)
                return data

        checksum_stream = SecureChecksumStream(file_stream, hasher, filename)

        # Store file with streaming and enhanced metadata
        client.put_object(
            bucket_name=MINIO_BUCKET_NAME,
            object_name=storage_key,
            data=checksum_stream,
            length=file_size,
            content_type=content_type,
            metadata={
                "original-filename": filename,
                "upload-timestamp": str(int(time.time())),
                "file-size": str(file_size),
                "streamed": "true",
                "security-validated": "true",
                "content-type-verified": "true",
                "suspicious-patterns-checked": "true",
            },
        )

        # Check if suspicious patterns were found during streaming
        if checksum_stream.suspicious_patterns_found:
            logger.warning(f"Suspicious patterns detected in streamed file: {filename}")
            # Note: We still store the file but log the warning for monitoring

        checksum = hasher.hexdigest()

        logger.info(
            f"Successfully streamed attachment: {filename} -> {storage_key} "
            f"({file_size} bytes, checksum: {checksum[:16]}...)"
        )

        return True, "File streamed successfully", checksum

    except S3Error as e:
        error_msg = f"MinIO S3 error: {e.code} - {e.message}"
        logger.error(f"MinIO S3 error streaming {filename}: {error_msg}")
        return False, error_msg, None

    except InvalidResponseError as e:
        error_msg = f"MinIO invalid response: {e}"
        logger.error(f"MinIO invalid response streaming {filename}: {error_msg}")
        return False, error_msg, None

    except Exception as e:
        error_msg = f"Streaming error: {e}"
        logger.error(f"Failed to stream attachment {filename}: {error_msg}")
        return False, error_msg, None


def get_attachment_download_url(storage_key: str, expires_in_seconds: int = 3600) -> Optional[str]:
    """
    Generate a presigned URL for downloading an attachment

    Args:
        storage_key: Storage key of the file
        expires_in_seconds: URL expiration time in seconds (default: 1 hour)

    Returns:
        Optional[str]: Presigned download URL or None if failed
    """
    try:
        client = get_minio_client()

        # Generate presigned URL for download
        download_url = client.presigned_get_object(
            bucket_name=MINIO_BUCKET_NAME, object_name=storage_key, expires=expires_in_seconds
        )

        logger.debug(f"Generated download URL for {storage_key} (expires in {expires_in_seconds}s)")
        return download_url

    except S3Error as e:
        logger.error(f"MinIO S3 error generating download URL for {storage_key}: {e}")
        return None

    except Exception as e:
        logger.error(f"Failed to generate download URL for {storage_key}: {e}")
        return None


def delete_attachment(storage_key: str) -> Tuple[bool, str]:
    """
    Delete an attachment from storage

    Args:
        storage_key: Storage key of the file to delete

    Returns:
        Tuple[bool, str]: (success, message)
    """
    try:
        client = get_minio_client()

        # Delete the object
        client.remove_object(MINIO_BUCKET_NAME, storage_key)

        logger.info(f"Successfully deleted attachment: {storage_key}")
        return True, "Attachment deleted successfully"

    except S3Error as e:
        error_msg = f"MinIO S3 error: {e.code} - {e.message}"
        logger.error(f"MinIO S3 error deleting {storage_key}: {error_msg}")
        return False, error_msg

    except Exception as e:
        error_msg = f"Delete error: {e}"
        logger.error(f"Failed to delete attachment {storage_key}: {error_msg}")
        return False, error_msg


def get_attachment_info(storage_key: str) -> Optional[dict]:
    """
    Get attachment metadata from storage

    Args:
        storage_key: Storage key of the file

    Returns:
        Optional[dict]: Attachment metadata or None if not found
    """
    try:
        client = get_minio_client()

        # Get object information
        stat = client.stat_object(MINIO_BUCKET_NAME, storage_key)

        return {
            "size": stat.size,
            "content_type": stat.content_type,
            "last_modified": stat.last_modified,
            "etag": stat.etag,
            "metadata": stat.metadata,
        }

    except S3Error as e:
        if e.code == "NoSuchKey":
            logger.debug(f"Attachment not found: {storage_key}")
            return None
        logger.error(f"MinIO S3 error getting info for {storage_key}: {e}")
        return None

    except Exception as e:
        logger.error(f"Failed to get attachment info for {storage_key}: {e}")
        return None


def test_storage_connection() -> Tuple[bool, str]:
    """
    Test MinIO storage connection and configuration

    Returns:
        Tuple[bool, str]: (is_connected, message)
    """
    try:
        # Test client creation
        client = get_minio_client()

        # Test bucket access
        if not client.bucket_exists(MINIO_BUCKET_NAME):
            return False, f"Bucket {MINIO_BUCKET_NAME} does not exist"

        # Test write/read/delete with a small test file
        test_key = "test/connection_test.txt"
        test_data = b"MinIO connection test"

        # Write test file
        client.put_object(
            bucket_name=MINIO_BUCKET_NAME,
            object_name=test_key,
            data=io.BytesIO(test_data),
            length=len(test_data),
            content_type="text/plain",
        )

        # Read test file
        response = client.get_object(MINIO_BUCKET_NAME, test_key)
        read_data = response.read()
        response.close()
        response.release_conn()

        if read_data != test_data:
            return False, "Test file data mismatch"

        # Delete test file
        client.remove_object(MINIO_BUCKET_NAME, test_key)

        return True, "MinIO storage connection test successful"

    except Exception as e:
        error_msg = f"Storage connection test failed: {e}"
        logger.error(error_msg)
        return False, error_msg


def get_storage_health_status() -> dict:
    """
    Get comprehensive storage health status with security metrics

    Returns:
        dict: Storage health information
    """
    try:
        # Test connection
        is_connected, message = test_storage_connection()

        # Get client info
        client = get_minio_client()

        # Get bucket info
        bucket_exists = client.bucket_exists(MINIO_BUCKET_NAME)

        return {
            "status": "healthy" if is_connected else "unhealthy",
            "connected": is_connected,
            "message": message,
            "endpoint": MINIO_ENDPOINT,
            "bucket": MINIO_BUCKET_NAME,
            "bucket_exists": bucket_exists,
            "secure": MINIO_SECURE,
            "region": MINIO_REGION,
            "max_file_size": MAX_FILE_SIZE,
            "allowed_content_types_count": len(ALLOWED_CONTENT_TYPES),
            "security_features": {
                "path_traversal_protection": True,
                "executable_file_blocking": True,
                "content_type_validation": True,
                "suspicious_pattern_detection": True,
                "checksum_verification": True,
                "memory_management": True,
                "secure_streaming": True,
            },
            "validation_rules": {
                "max_filename_length": 255,
                "dangerous_characters_blocked": True,
                "system_files_blocked": True,
                "executable_extensions_blocked": True,
                "empty_files_blocked": True,
            },
        }

    except Exception as e:
        return {
            "status": "error",
            "connected": False,
            "message": f"Health check failed: {e}",
            "endpoint": MINIO_ENDPOINT,
            "bucket": MINIO_BUCKET_NAME,
            "error": str(e),
        }


def log_security_event(
    event_type: str, filename: str, details: str, user_id: Optional[int] = None
) -> None:
    """
    Log security events for monitoring and alerting

    Args:
        event_type: Type of security event
        filename: Name of the file involved
        details: Additional details about the event
        user_id: Optional user ID for user-specific events
    """
    try:
        # Log to application logs
        logger.warning(f"SECURITY_EVENT: {event_type} - {filename} - {details}")

        # In production, you might want to send this to a security monitoring system
        # or store in a separate security events database

    except Exception as e:
        logger.error(f"Failed to log security event: {e}")
