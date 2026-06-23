"""
API Middleware Components
Security, logging, and request processing middleware
"""

from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional
import time
import jwt
from datetime import datetime, timedelta

from src.config.settings import settings
from src.utils.logger import logger

class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Security middleware for API requests
    Implements JWT validation and rate limiting
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.security = HTTPBearer()
        self.rate_limit_cache = {}
    
    async def dispatch(self, request: Request, call_next):
        """
        Process each request through security checks
        """
        # Skip security for health check and docs
        if request.url.path in ['/health', '/api/docs', '/api/redoc']:
            return await call_next(request)
        
        try:
            # Rate limiting check
            client_ip = request.client.host
            if not await self._check_rate_limit(client_ip):
                raise HTTPException(status_code=429, detail="Too many requests")
            
            # JWT token validation
            if request.url.path.startswith('/api/'):
                token = await self._extract_token(request)
                if token:
                    await self._validate_token(token)
            
            # Add request ID for tracing
            request_id = self._generate_request_id()
            request.state.request_id = request_id
            
            # Process request
            response = await call_next(request)
            
            # Add security headers
            response.headers['X-Request-ID'] = request_id
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Security middleware error: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    async def _extract_token(self, request: Request) -> Optional[str]:
        """Extract JWT token from request"""
        try:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                return auth_header.split(' ')[1]
            return None
        except:
            return None
    
    async def _validate_token(self, token: str) -> bool:
        """Validate JWT token"""
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            return True
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
    
    async def _check_rate_limit(self, client_ip: str) -> bool:
        """Check rate limiting for client IP"""
        now = time.time()
        window = 60  # 1 minute window
        max_requests = 100  # Max requests per window
        
        # Clean old entries
        self.rate_limit_cache = {
            ip: timestamps 
            for ip, timestamps in self.rate_limit_cache.items()
            if any(now - ts < window for ts in timestamps)
        }
        
        # Check current client
        if client_ip not in self.rate_limit_cache:
            self.rate_limit_cache[client_ip] = []
        
        # Filter requests in current window
        recent_requests = [
            ts for ts in self.rate_limit_cache[client_ip]
            if now - ts < window
        ]
        
        if len(recent_requests) >= max_requests:
            return False
        
        # Add current request
        recent_requests.append(now)
        self.rate_limit_cache[client_ip] = recent_requests
        
        return True
    
    def _generate_request_id(self) -> str:
        """Generate unique request ID for tracing"""
        import uuid
        return str(uuid.uuid4())

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Request/Response logging middleware
    Tracks API usage and performance metrics
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        Log request and response details
        """
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"from {request.client.host}"
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log response
            logger.info(
                f"Response: {response.status_code} "
                f"duration={duration:.3f}s"
            )
            
            # Add timing header
            response.headers['X-Response-Time'] = f"{duration:.3f}s"
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Error: {str(e)} "
                f"duration={duration:.3f}s"
            )
            raise
