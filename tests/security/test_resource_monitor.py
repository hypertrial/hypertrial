"""Tests for resource monitoring functionality."""

import time
import pytest
import threading
from unittest.mock import patch, MagicMock
from core.security.resource_monitor import ResourceMonitor
from core.security import SecurityError

class TestResourceMonitor:
    """Tests for ResourceMonitor class"""
    
    def test_init(self):
        """Test initialization of ResourceMonitor"""
        monitor = ResourceMonitor()
        assert monitor.max_memory == 0
        assert isinstance(monitor.memory_history, list)
        assert isinstance(monitor.cpu_history, list)
        assert monitor.monitoring_active is False
    
    def test_record_usage_snapshot(self):
        """Test recording usage snapshots"""
        monitor = ResourceMonitor()
        
        # Mock process methods
        mock_memory_info = MagicMock(return_value=MagicMock(rss=100*1024*1024))  # 100MB
        mock_cpu_percent = MagicMock(return_value=25.5)  # 25.5% CPU
        
        # Force the last check time to be far enough in the past
        monitor.last_check_time = time.time() - monitor.check_interval - 1
        
        with patch.object(monitor.process, 'memory_info', mock_memory_info), \
             patch.object(monitor.process, 'cpu_percent', mock_cpu_percent):
            
            # First snapshot
            monitor.record_usage_snapshot()
            
            # Check that memory and CPU history have one entry
            assert len(monitor.memory_history) == 1
            assert len(monitor.cpu_history) == 1
            
            # Check memory values
            assert monitor.memory_history[0][1] == 100.0  # 100MB
            assert monitor.max_memory == 100.0
            
            # Check CPU values
            assert monitor.cpu_history[0][1] == 25.5  # 25.5%
            
            # Update mock for second snapshot (higher memory)
            mock_memory_info.return_value = MagicMock(rss=200*1024*1024)  # 200MB
            
            # Force update time to ensure a new snapshot is taken
            monitor.last_check_time -= monitor.check_interval
            
            # Second snapshot
            monitor.record_usage_snapshot()
            
            # Check updated values
            assert len(monitor.memory_history) == 2
            assert monitor.max_memory == 200.0  # Max should be updated
    
    def test_record_usage_snapshot_error(self):
        """Test error handling in record_usage_snapshot"""
        monitor = ResourceMonitor()
        
        # Mock process methods to raise exception
        with patch.object(monitor.process, 'memory_info', side_effect=Exception("Process error")):
            # Should not raise exception but log warning
            monitor.record_usage_snapshot()
            # Memory history should remain empty
            assert len(monitor.memory_history) == 0
    
    def test_check_limits_memory_exceeded(self):
        """Test memory limit checking"""
        monitor = ResourceMonitor()
        
        # Mock process with high memory usage
        mock_memory_info = MagicMock(return_value=MagicMock(rss=1000*1024*1024))  # 1000MB (over limit)
        
        with patch.object(monitor.process, 'memory_info', mock_memory_info):
            # Should raise SecurityError
            with pytest.raises(SecurityError, match="Memory usage exceeded limit"):
                monitor.check_limits()
    
    def test_check_limits_cpu_exceeded(self):
        """Test CPU limit checking"""
        monitor = ResourceMonitor()
        
        # Mock resource usage with high CPU time
        mock_getrusage = MagicMock(return_value=MagicMock(ru_utime=1000))  # 1000s (over limit)
        
        with patch('resource.getrusage', mock_getrusage):
            # Should raise SecurityError
            with pytest.raises(SecurityError, match="CPU time exceeded limit"):
                monitor.check_limits()
    
    def test_check_limits_execution_time_exceeded(self):
        """Test execution time limit checking"""
        monitor = ResourceMonitor()
        
        # Set start time to way in the past
        monitor.start_time = time.time() - 1000  # 1000s ago (over limit)
        
        # Should raise SecurityError
        with pytest.raises(SecurityError, match="Execution time exceeded limit"):
            monitor.check_limits()
    
    def test_check_for_memory_leak(self):
        """Test memory leak detection"""
        monitor = ResourceMonitor()
        
        # Simulate consistent memory growth
        base_time = time.time()
        for i in range(10):
            # Add steadily increasing memory usage
            monitor.memory_history.append((base_time + i, 100.0 + i * 10))
        
        # Should detect a leak (in test mode it will log a warning)
        with patch.object(monitor, 'test_mode', True):
            monitor.check_for_memory_leak()
            # No assertion needed, just checking it runs without errors
        
        # In production mode with high memory, it should raise an error
        with patch.object(monitor, 'test_mode', False):
            # Simulate approaching the memory limit
            monitor.memory_history = []
            for i in range(10):
                # Add steadily increasing memory usage that's approaching the limit
                monitor.memory_history.append((base_time + i, 400.0 + i * 10))  # Will reach 490MB
            
            # Should raise SecurityError
            with pytest.raises(SecurityError, match="Potential memory leak detected"):
                monitor.check_for_memory_leak()
    
    def test_check_for_cpu_abuse(self):
        """Test CPU abuse detection"""
        monitor = ResourceMonitor()
        
        # Simulate high CPU usage
        base_time = time.time()
        for i in range(10):
            # Add consistently high CPU usage
            monitor.cpu_history.append((base_time + i, 90.0))  # 90% CPU
        
        # Should detect CPU abuse (in test mode it will log a warning)
        with patch.object(monitor, 'test_mode', True):
            monitor.check_for_cpu_abuse()
            # No assertion needed, just checking it runs without errors
        
        # In production mode, it should log a warning but not raise an error
        with patch.object(monitor, 'test_mode', False):
            # Patch the logger to check that warning is logged
            with patch('logging.Logger.warning') as mock_warning:
                monitor.check_for_cpu_abuse()
                mock_warning.assert_called_once()
    
    def test_get_usage_summary(self):
        """Test getting usage summary"""
        monitor = ResourceMonitor()
        
        # Add some mock data
        monitor.max_memory = 100.0
        monitor.memory_history = [(time.time(), 50.0), (time.time(), 100.0)]
        monitor.cpu_history = [(time.time(), 25.0), (time.time(), 50.0)]
        
        # Mock current memory
        mock_memory_info = MagicMock(return_value=MagicMock(rss=75*1024*1024))  # 75MB
        
        # Mock CPU time
        mock_getrusage = MagicMock(return_value=MagicMock(ru_utime=5.0))  # 5s
        
        with patch.object(monitor.process, 'memory_info', mock_memory_info), \
             patch('resource.getrusage', mock_getrusage):
            
            summary = monitor.get_usage_summary()
            
            # Check summary fields
            assert summary['max_memory_mb'] == 100.0
            assert summary['current_memory_mb'] == 75.0
            assert summary['cpu_time'] == 5.0
            assert 'elapsed_time' in summary
            assert summary['memory_history'] == monitor.memory_history
            assert summary['cpu_history'] == monitor.cpu_history
    
    def test_continuous_monitoring(self):
        """Test continuous monitoring in a separate thread"""
        monitor = ResourceMonitor()
        
        # Mock record_usage_snapshot
        mock_record = MagicMock()
        
        with patch.object(monitor, 'record_usage_snapshot', mock_record), \
             patch('time.sleep', MagicMock()):  # Don't actually sleep
            
            # Start monitoring in a thread
            monitor.monitoring_active = True
            thread = threading.Thread(target=monitor.start_continuous_monitoring)
            thread.daemon = True  # Don't hang on test exit
            thread.start()
            
            # Let it run briefly
            time.sleep(0.1)
            
            # Stop monitoring
            monitor.stop_monitoring()
            thread.join(timeout=0.5)
            
            # Should have called record_usage_snapshot at least once
            assert mock_record.call_count >= 1 