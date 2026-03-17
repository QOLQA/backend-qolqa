"""
Audit logging system for tracking critical operations
Follows Python logging best practices and FastAPI patterns
"""
import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path
from logging.handlers import RotatingFileHandler

# Create logs directory if it doesn't exist
LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Configure audit logger
audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.INFO)
audit_logger.propagate = False  # Don't propagate to root logger

# Rotating file handler for audit logs
# Rotates when file reaches 10MB, keeps 5 backup files
audit_file_handler = RotatingFileHandler(
    LOGS_DIR / "audit.log",
    maxBytes=10_000_000,  # 10 MB per file
    backupCount=5,        # Keep 5 historical files (audit.log.1 to audit.log.5)
    encoding='utf-8'
)
audit_file_handler.setLevel(logging.INFO)

# JSON formatter for structured logging
class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured audit logs"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
        }
        
        # Add extra fields if present
        if hasattr(record, "audit_data"):
            log_data.update(record.audit_data)
        
        return json.dumps(log_data, ensure_ascii=False)

audit_file_handler.setFormatter(JSONFormatter())
audit_logger.addHandler(audit_file_handler)

# Console handler for development (optional)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter(
    '%(asctime)s - AUDIT - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
console_handler.setFormatter(console_formatter)
audit_logger.addHandler(console_handler)


def log_audit(
    action: str,
    user_id: Optional[str] = None,
    username: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    status: str = "success",
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> None:
    """
    Log an audit event with structured data
    
    Args:
        action: The action performed (e.g., "user.login", "solution.create")
        user_id: ID of the user performing the action
        username: Username of the user
        resource_type: Type of resource affected (e.g., "solution", "user")
        resource_id: ID of the affected resource
        status: Status of the operation ("success", "failed", "denied")
        details: Additional context information
        ip_address: Client IP address
        user_agent: Client user agent string
    """
    audit_data = {
        "action": action,
        "status": status,
    }
    
    if user_id:
        audit_data["user_id"] = user_id
    if username:
        audit_data["username"] = username
    if resource_type:
        audit_data["resource_type"] = resource_type
    if resource_id:
        audit_data["resource_id"] = resource_id
    if ip_address:
        audit_data["ip_address"] = ip_address
    if user_agent:
        audit_data["user_agent"] = user_agent
    if details:
        audit_data["details"] = details
    
    # Create log message
    message_parts = [action]
    if user_id or username:
        user_info = username or user_id
        message_parts.append(f"by {user_info}")
    if resource_type:
        message_parts.append(f"on {resource_type}")
        if resource_id:
            message_parts.append(f"#{resource_id}")
    message_parts.append(f"- {status}")
    
    message = " ".join(message_parts)
    
    # Log with extra data
    audit_logger.info(message, extra={"audit_data": audit_data})


def log_auth_attempt(
    username: str,
    success: bool,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    reason: Optional[str] = None
) -> None:
    """
    Log authentication attempt (login/register)
    
    Args:
        username: Username attempting to authenticate
        success: Whether the attempt was successful
        ip_address: Client IP address
        user_agent: Client user agent
        reason: Reason for failure (if failed)
    """
    status = "success" if success else "failed"
    details = {"reason": reason} if reason else None
    
    log_audit(
        action="user.login" if success else "user.login_failed",
        username=username,
        status=status,
        resource_type="user",
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
    )


def log_registration(
    user_id: str,
    username: str,
    email: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> None:
    """
    Log user registration
    
    Args:
        user_id: ID of the newly created user
        username: Username of the new user
        email: Email of the new user
        ip_address: Client IP address
        user_agent: Client user agent
    """
    log_audit(
        action="user.register",
        user_id=user_id,
        username=username,
        resource_type="user",
        resource_id=user_id,
        status="success",
        details={"email": email},
        ip_address=ip_address,
        user_agent=user_agent,
    )


def log_resource_operation(
    action: str,
    user_id: str,
    resource_type: str,
    resource_id: str,
    resource_name: Optional[str] = None,
    status: str = "success",
    ip_address: Optional[str] = None,
) -> None:
    """
    Log resource operation (create, update, delete)
    
    Args:
        action: Operation action (e.g., "solution.create", "solution.delete")
        user_id: ID of the user performing the action
        resource_type: Type of resource
        resource_id: ID of the resource
        resource_name: Name of the resource (if applicable)
        status: Operation status
        ip_address: Client IP address
    """
    details = {"name": resource_name} if resource_name else None
    
    log_audit(
        action=action,
        user_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        status=status,
        details=details,
        ip_address=ip_address,
    )


def log_access_denied(
    action: str,
    user_id: str,
    resource_type: str,
    resource_id: str,
    reason: str,
    ip_address: Optional[str] = None,
) -> None:
    """
    Log access denied events
    
    Args:
        action: Attempted action
        user_id: ID of the user who was denied
        resource_type: Type of resource
        resource_id: ID of the resource
        reason: Reason for denial
        ip_address: Client IP address
    """
    log_audit(
        action=action,
        user_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        status="denied",
        details={"reason": reason},
        ip_address=ip_address,
    )


def log_rate_limit_exceeded(
    path: str,
    method: str,
    limit: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    user_id: Optional[str] = None,
) -> None:
    """
    Log rate limit exceeded events
    
    Args:
        path: Request path that exceeded rate limit
        method: HTTP method (GET, POST, etc.)
        limit: Rate limit that was exceeded (e.g., "5/minute")
        ip_address: Client IP address
        user_agent: Client user agent
        user_id: User ID if authenticated (optional)
    """
    log_audit(
        action="security.rate_limit_exceeded",
        user_id=user_id or "anonymous",
        resource_type="endpoint",
        status="blocked",
        details={
            "path": path,
            "method": method,
            "limit": limit,
            "message": f"Rate limit exceeded for {method} {path}"
        },
        ip_address=ip_address,
        user_agent=user_agent,
    )
