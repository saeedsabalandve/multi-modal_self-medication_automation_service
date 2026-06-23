"""
Logging Configuration
Structured logging for AWS CloudWatch integration
"""

import logging
import json
from datetime import datetime
from typing import Any, Dict
import sys

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        if hasattr(record, "aws_request_id"):
            log_entry["aws_request_id"] = record.aws_request_id
        
        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = str(record.exc_info[1])
        
        return json.dumps(log_entry)

def setup_logging():
    """Configure application logging"""
    logger = logging.getLogger("self-medication-automation")
    logger.setLevel(logging.INFO)
    
    # Console handler with JSON formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)
    
    # Prevent duplicate logging
    logger.propagate = False
    
    return logger

logger = setup_logging()
