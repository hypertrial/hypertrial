"""Custom import hook to restrict module imports."""

import sys
import time
import logging
from core.security.config import ALLOWED_MODULES

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImportHook:
    """Custom import hook to restrict module imports"""
    
    def __init__(self):
        self.allowed_modules = ALLOWED_MODULES
        self.original_import = __import__
        
        # Track module usage patterns
        self.module_usage = {}            # Count how many times each module is imported
        self.import_times = {}            # Track when each module was imported
        self.module_access_patterns = {}  # Track unusual access patterns
        self.suspicious_modules = set()   # Modules with unusual import patterns
        
        # Thresholds for flagging suspicious import behavior
        self.max_import_count = 15        # Maximum times a module can be imported
        self.min_import_interval = 0.5    # Minimum seconds between imports
    
    def __enter__(self):
        sys.meta_path.insert(0, self)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.meta_path.remove(self)
        
        # Log summary of module usage
        if any(self.suspicious_modules):
            logger.warning(f"Suspicious module usage detected: {', '.join(self.suspicious_modules)}")
    
    def find_module(self, fullname, path=None):
        # Import SecurityError here to avoid circular import
        from core.security import SecurityError
        
        # Track module usage
        current_time = time.time()
        
        if fullname not in self.module_usage:
            self.module_usage[fullname] = 0
            self.import_times[fullname] = []
            
        self.module_usage[fullname] += 1
        self.import_times[fullname].append(current_time)
        
        # Check for excessive imports (potential for import-based DoS)
        if self.module_usage[fullname] > self.max_import_count:
            message = f"Excessive imports of module: {fullname} ({self.module_usage[fullname]} times)"
            self.suspicious_modules.add(fullname)
            logger.warning(message)
            
        # Check for rapid repeated imports (potential for timing attacks)
        if len(self.import_times[fullname]) >= 2:
            latest_imports = self.import_times[fullname][-2:]
            if latest_imports[1] - latest_imports[0] < self.min_import_interval:
                message = f"Rapid repeated imports of module: {fullname}"
                self.suspicious_modules.add(fullname)
                logger.warning(message)
        
        # Allow importing strategy modules themselves
        if fullname.startswith('submit_strategies.'):
            return None
            
        # Special case: allow os but we'll restrict its usage in code analysis
        if fullname == 'os':
            return None
            
        # Check if the module is in the allowed list
        for allowed in self.allowed_modules:
            if fullname == allowed or fullname.startswith(allowed + '.'):
                return None
        
        # Track attempted imports of restricted modules
        message = f"Blocked import of module: {fullname}"
        self.suspicious_modules.add(fullname)
        logger.warning(message)
        raise SecurityError(f"Import of module '{fullname}' is not allowed")
    
    def get_import_summary(self):
        """Get a summary of module import patterns"""
        return {
            'module_usage_counts': self.module_usage,
            'suspicious_modules': list(self.suspicious_modules),
            'import_times': self.import_times
        } 