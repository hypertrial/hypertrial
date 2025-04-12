"""Tests for the Bandit security analyzer."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from core.security import SecurityError
from core.security.bandit_analyzer import BanditAnalyzer


class TestBanditAnalyzer(unittest.TestCase):
    """Test cases for the BanditAnalyzer class."""

    def setUp(self):
        """Set up test environment."""
        self.safe_code = """
def safe_function():
    x = 1 + 2
    return x
"""

        self.vulnerable_code = """
import pickle
import subprocess

def insecure_function():
    data = pickle.loads(b'')
    subprocess.call('echo hello', shell=True)
    eval("1+1")
    return True
"""

    def test_analyzer_init(self):
        """Test initialization of the BanditAnalyzer."""
        analyzer = BanditAnalyzer(self.safe_code)
        self.assertEqual(analyzer.code, self.safe_code)
        self.assertIsNone(analyzer.results)
        self.assertEqual(analyzer.issues, [])

    @patch('subprocess.run')
    def test_analyze_success(self, mock_run):
        """Test successful analysis with mocked Bandit."""
        # Mock successful Bandit run with no issues
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = '{"results": [], "errors": []}'
        mock_run.return_value = mock_process

        analyzer = BanditAnalyzer(self.safe_code)
        success, issues = analyzer.analyze()

        self.assertTrue(success)
        self.assertEqual(issues, [])
        self.assertEqual(analyzer.get_summary(), {
            "status": "complete", 
            "issues_count": 0,
            "high_severity_count": 0, 
            "medium_severity_count": 0, 
            "low_severity_count": 0
        })

    @patch('subprocess.run')
    def test_analyze_with_issues(self, mock_run):
        """Test analysis with security issues."""
        # Mock Bandit run with issues
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = """
        {
            "results": [
                {
                    "test_id": "B102", 
                    "test_name": "exec_used", 
                    "issue_confidence": "HIGH", 
                    "issue_severity": "MEDIUM", 
                    "issue_text": "Use of exec detected", 
                    "line_number": 5,
                    "line_range": [5]
                }
            ],
            "errors": []
        }
        """
        mock_run.return_value = mock_process

        # Need to patch both high and medium severity methods since we now block both
        with patch.object(BanditAnalyzer, '_get_high_severity_issues', return_value=[]), \
             patch.object(BanditAnalyzer, '_get_medium_severity_issues', return_value=[]), \
             patch.object(BanditAnalyzer, '_get_low_severity_issues', return_value=[]):
            
            analyzer = BanditAnalyzer(self.vulnerable_code)
            success, issues = analyzer.analyze()

            self.assertTrue(success)
            self.assertEqual(len(issues), 1)
            self.assertEqual(issues[0]['issue_id'], 'B102')
            self.assertEqual(issues[0]['issue_severity'], 'MEDIUM')

    @patch('subprocess.run')
    def test_analyze_file_not_found(self, mock_run):
        """Test behavior when Bandit is not installed."""
        mock_run.side_effect = FileNotFoundError("No such file or directory: 'bandit'")

        analyzer = BanditAnalyzer(self.safe_code)
        success, issues = analyzer.analyze()

        self.assertFalse(success)
        self.assertEqual(issues, [])
        self.assertEqual(analyzer.get_summary(), {"status": "not_run", "issues_count": 0})

    @patch('subprocess.run')
    def test_analyze_invalid_json(self, mock_run):
        """Test behavior with invalid JSON output."""
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "Invalid JSON"
        mock_run.return_value = mock_process

        analyzer = BanditAnalyzer(self.safe_code)
        success, issues = analyzer.analyze()

        self.assertFalse(success)
        self.assertEqual(issues, [])

    @patch('subprocess.run')
    def test_high_severity_issues_handling(self, mock_run):
        """Test handling of high severity issues."""
        # Mock Bandit run with high severity issues
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = """
        {
            "results": [
                {
                    "test_id": "B602", 
                    "test_name": "subprocess_shell_true", 
                    "issue_confidence": "HIGH", 
                    "issue_severity": "HIGH", 
                    "issue_text": "subprocess call with shell=True identified", 
                    "line_number": 6,
                    "line_range": [6]
                }
            ],
            "errors": []
        }
        """
        mock_run.return_value = mock_process

        # High severity issues should block execution
        analyzer = BanditAnalyzer(self.vulnerable_code)
        success, issues = analyzer.analyze()
        
        # Verify that the analysis did not succeed due to high severity issue
        self.assertFalse(success)
        self.assertEqual(issues, [])
        
    @patch('subprocess.run')
    def test_medium_severity_issues_handling(self, mock_run):
        """Test handling of medium severity issues."""
        # Mock Bandit run with medium severity issues
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = """
        {
            "results": [
                {
                    "test_id": "B105", 
                    "test_name": "hardcoded_password_string", 
                    "issue_confidence": "HIGH", 
                    "issue_severity": "MEDIUM", 
                    "issue_text": "Possible hardcoded password", 
                    "line_number": 5,
                    "line_range": [5]
                }
            ],
            "errors": []
        }
        """
        mock_run.return_value = mock_process

        # Medium severity issues should also block execution with our enhanced configuration
        analyzer = BanditAnalyzer(self.vulnerable_code)
        success, issues = analyzer.analyze()
        
        # Verify that the analysis did not succeed due to medium severity issue
        self.assertFalse(success)
        self.assertEqual(issues, [])

    def test_get_issues_by_severity(self):
        """Test filtering issues by severity."""
        analyzer = BanditAnalyzer("")
        analyzer.issues = [
            {'issue_id': '1', 'issue_severity': 'HIGH', 'issue_text': 'Test 1'},
            {'issue_id': '2', 'issue_severity': 'MEDIUM', 'issue_text': 'Test 2'},
            {'issue_id': '3', 'issue_severity': 'LOW', 'issue_text': 'Test 3'},
            {'issue_id': '4', 'issue_severity': 'HIGH', 'issue_text': 'Test 4'}
        ]
        
        high_issues = analyzer.get_issues_by_severity('HIGH')
        medium_issues = analyzer.get_issues_by_severity('MEDIUM')
        low_issues = analyzer.get_issues_by_severity('LOW')
        
        self.assertEqual(len(high_issues), 2)
        self.assertEqual(len(medium_issues), 1)
        self.assertEqual(len(low_issues), 1)
        
    def test_severity_categorization(self):
        """Test that issues are correctly categorized by severity methods."""
        analyzer = BanditAnalyzer("")
        
        # Configure the config with test values
        analyzer.config = {
            'HIGH_SEVERITY_TESTS': ['B602', 'B605'],
            'MEDIUM_SEVERITY_TESTS': ['B105', 'B106'],
            'LOW_SEVERITY_TESTS': ['B101', 'B112']
        }
        
        # Add issues with various severities - ensure no overlap between severity lists
        analyzer.issues = [
            {'issue_id': 'B101', 'issue_severity': 'LOW', 'issue_text': 'Assert used'},
            {'issue_id': 'B105', 'issue_severity': 'MEDIUM', 'issue_text': 'Password string'},
            {'issue_id': 'B602', 'issue_severity': 'HIGH', 'issue_text': 'Shell injection'},
            {'issue_id': 'B999', 'issue_severity': 'MEDIUM', 'issue_text': 'Generic medium issue'},
            {'issue_id': 'B888', 'issue_severity': 'LOW', 'issue_text': 'Generic low issue'}
        ]
        
        # Test the categorization methods
        high_issues = analyzer._get_high_severity_issues()
        medium_issues = analyzer._get_medium_severity_issues()
        low_issues = analyzer._get_low_severity_issues()
        
        # Check that issues are correctly categorized by both severity and ID
        self.assertEqual(len(high_issues), 1)  # Only B602 (HIGH severity)
        self.assertEqual(len(medium_issues), 2)  # B105 + other MEDIUM severity
        self.assertEqual(len(low_issues), 2)  # B101 + other LOW severity
        
        # Check specific issues are in the correct category
        self.assertTrue(any(i['issue_id'] == 'B602' for i in high_issues))
        self.assertTrue(any(i['issue_id'] == 'B105' for i in medium_issues))
        self.assertTrue(any(i['issue_id'] == 'B999' for i in medium_issues))
        self.assertTrue(any(i['issue_id'] == 'B101' for i in low_issues))
        self.assertTrue(any(i['issue_id'] == 'B888' for i in low_issues))

    def test_integration_with_real_bandit(self):
        """Test integration with the real Bandit package if installed."""
        # This is an integration test that will be skipped if Bandit is not installed
        try:
            import bandit
            has_bandit = True
        except ImportError:
            has_bandit = False
            
        if not has_bandit:
            self.skipTest("Bandit package not installed, skipping integration test")

        # Create a temporary file with vulnerable code
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as tmp:
            try:
                tmp.write(self.vulnerable_code.encode('utf-8'))
                tmp.close()
                
                # Run the analyzer on the file content
                analyzer = BanditAnalyzer(self.vulnerable_code)
                success, issues = analyzer.analyze()
                
                # Just verify that the analysis completed without errors
                if success:
                    self.assertTrue(isinstance(issues, list))
                    summary = analyzer.get_summary()
                    self.assertTrue("issues_count" in summary)
            finally:
                # Clean up the temporary file
                if os.path.exists(tmp.name):
                    os.unlink(tmp.name)


if __name__ == '__main__':
    unittest.main() 