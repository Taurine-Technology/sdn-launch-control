"""
Database connection monitoring middleware
"""
import time
import logging
from django.db import connection
from django.conf import settings

logger = logging.getLogger(__name__)


class DatabaseConnectionMiddleware:
    """
    Middleware to monitor database connections and log connection usage
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Log connection status before request
        self._log_connection_status('before', request)
        
        start_time = time.time()
        
        try:
            response = self.get_response(request)
        finally:
            # Log connection status after request
            end_time = time.time()
            duration = end_time - start_time
            self._log_connection_status('after', request, duration)
        
        return response
    
    def _log_connection_status(self, stage, request, duration=None):
        """Log database connection status"""
        try:
            # Get connection info
            if hasattr(connection, 'connection'):
                conn = connection.connection
                if conn:
                    # Log connection details
                    log_data = {
                        'stage': stage,
                        'path': request.path,
                        'method': request.method,
                        'connection_id': id(conn),
                        'duration': duration,
                    }
                    
                    if duration and duration > 1.0:  # Log slow requests
                        logger.warning(f"Slow database request: {log_data}")
                    elif settings.DEBUG:
                        logger.debug(f"Database connection: {log_data}")
                        
        except Exception as e:
            logger.error(f"Error logging connection status: {e}")


class ConnectionPoolMiddleware:
    """
    Middleware to ensure proper connection pool usage
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Ensure connection is properly managed
        try:
            response = self.get_response(request)
        except Exception as e:
            # Log connection errors
            logger.error(f"Database connection error in {request.path}: {e}")
            raise
        finally:
            # Ensure connection is properly closed if needed
            if hasattr(connection, 'close'):
                # Only close if we're not in a transaction
                if not connection.in_atomic_block:
                    connection.close()
        
        return response
