"""Resource monitoring for strategy execution."""

import time
import resource
import psutil
import logging
from core.security.utils import is_test_mode
from core.security.config import (
    MAX_MEMORY_MB, MAX_CPU_TIME, MAX_EXECUTION_TIME,
    TEST_MAX_CPU_TIME, TEST_MAX_EXECUTION_TIME
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResourceMonitor:
    """Monitors resource usage of strategy execution"""
    
    def __init__(self):
        self.start_time = time.time()
        self.process = psutil.Process()
        self.max_memory = 0
        self.test_mode = is_test_mode()
        
        # Track resource usage history
        self.memory_history = []  # Track memory usage over time
        self.cpu_history = []     # Track CPU usage over time
        self.check_interval = 0.5 # Seconds between checks during continuous monitoring
        self.monitoring_active = False
        self.last_check_time = time.time()
        
        # Leak detection thresholds
        self.memory_growth_threshold = 0.15  # 15% growth rate is suspicious
        self.cpu_sustained_threshold = 0.80  # 80% sustained CPU usage is suspicious
        
    def start_continuous_monitoring(self):
        """Start background monitoring of resources (to be called in a separate thread)"""
        self.monitoring_active = True
        while self.monitoring_active:
            self.record_usage_snapshot()
            time.sleep(self.check_interval)
    
    def stop_monitoring(self):
        """Stop continuous resource monitoring"""
        self.monitoring_active = False
        
    def record_usage_snapshot(self):
        """Record current resource usage snapshot"""
        # Only record if enough time has passed since last check
        current_time = time.time()
        if current_time - self.last_check_time < self.check_interval:
            return
            
        # Record memory usage
        try:
            memory_mb = self.process.memory_info().rss / 1024 / 1024
            self.memory_history.append((current_time - self.start_time, memory_mb))
            self.max_memory = max(self.max_memory, memory_mb)
            
            # Record CPU usage (as percentage)
            cpu_percent = self.process.cpu_percent(interval=0.1)
            self.cpu_history.append((current_time - self.start_time, cpu_percent))
            
            self.last_check_time = current_time
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            logger.warning("Unable to access process info for resource monitoring")
        
    def check_limits(self):
        """Check if resource usage exceeds limits"""
        # Import SecurityError here to avoid circular import
        from core.security import SecurityError
        
        # Record current usage
        self.record_usage_snapshot()
        
        # Check memory usage
        memory_mb = self.process.memory_info().rss / 1024 / 1024
        if memory_mb > MAX_MEMORY_MB:
            raise SecurityError(f"Memory usage exceeded limit: {memory_mb:.2f}MB > {MAX_MEMORY_MB}MB")
        
        # Check CPU time
        cpu_time = resource.getrusage(resource.RUSAGE_SELF).ru_utime
        cpu_limit = TEST_MAX_CPU_TIME if self.test_mode else MAX_CPU_TIME
        if cpu_time > cpu_limit:
            raise SecurityError(f"CPU time exceeded limit: {cpu_time:.2f}s > {cpu_limit}s")
        
        # Check total execution time
        elapsed = time.time() - self.start_time
        execution_limit = TEST_MAX_EXECUTION_TIME if self.test_mode else MAX_EXECUTION_TIME
        if elapsed > execution_limit:
            raise SecurityError(f"Execution time exceeded limit: {elapsed:.2f}s > {execution_limit}s")
        
        # Check for potential memory leaks
        self.check_for_memory_leak()
        
        # Check for sustained high CPU usage
        self.check_for_cpu_abuse()
    
    def check_for_memory_leak(self):
        """Check for patterns suggesting memory leak"""
        # Import SecurityError here to avoid circular import
        from core.security import SecurityError
        
        if len(self.memory_history) >= 10:
            # Look at the trend of the last 10 measurements
            recent_history = self.memory_history[-10:]
            
            # Calculate rate of growth
            start_mem = recent_history[0][1]
            end_mem = recent_history[-1][1]
            
            # If memory usage has grown by more than threshold% and is still growing, flag it
            if end_mem > start_mem * (1 + self.memory_growth_threshold):
                # Check if the growth is consistent (not just a spike)
                consistent_growth = True
                for i in range(1, len(recent_history)):
                    if recent_history[i][1] < recent_history[i-1][1]:
                        consistent_growth = False
                        break
                
                if consistent_growth:
                    message = f"Potential memory leak detected: {start_mem:.2f}MB → {end_mem:.2f}MB"
                    if self.test_mode:
                        logger.warning(message)
                    else:
                        # In production, treat sustained leaks as an error
                        if end_mem > MAX_MEMORY_MB * 0.8:  # If approaching the limit
                            raise SecurityError(message)
                        else:
                            logger.warning(message)
    
    def check_for_cpu_abuse(self):
        """Check for sustained high CPU usage patterns"""
        if len(self.cpu_history) >= 10:
            # Calculate average CPU usage over the last 10 measurements
            recent_cpu = [usage for _, usage in self.cpu_history[-10:]]
            avg_cpu = sum(recent_cpu) / len(recent_cpu)
            
            # If average CPU usage is consistently high, flag it
            if avg_cpu > self.cpu_sustained_threshold * 100:  # Convert to percentage
                message = f"Sustained high CPU usage detected: {avg_cpu:.2f}%"
                if self.test_mode:
                    logger.warning(message)
                else:
                    # In production, treat sustained high CPU as a warning
                    logger.warning(message)
    
    def get_usage_summary(self):
        """Get a summary of resource usage"""
        return {
            'max_memory_mb': self.max_memory,
            'current_memory_mb': self.process.memory_info().rss / 1024 / 1024,
            'cpu_time': resource.getrusage(resource.RUSAGE_SELF).ru_utime,
            'elapsed_time': time.time() - self.start_time,
            'memory_history': self.memory_history,
            'cpu_history': self.cpu_history
        } 