"""Bandit-based security code analyzer for Python strategies."""

import os
import logging
import json
import tempfile
import subprocess
from typing import Dict, List, Any, Optional, Tuple

from core.security.config import BANDIT_CONF

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BanditAnalyzer:
    """Analyzes Python code for security vulnerabilities using the Bandit package"""
    
    def __init__(self, code: str):
        """Initialize the analyzer with strategy code
        
        Args:
            code: The Python code to analyze
        """
        self.code = code
        self.results = None
        self.issues = []
        self.config = BANDIT_CONF
        
    def analyze(self) -> Tuple[bool, List[Dict[str, Any]]]:
        """Run Bandit security analysis on the strategy code
        
        This method executes the Bandit security analyzer on the provided code and
        raises a SecurityError if high or medium severity issues are found.
        
        Returns:
            Tuple[bool, List[Dict]]: Success status and list of security issues found
            
        Raises:
            SecurityError: If high or medium severity security issues are found
        """
        from core.security import SecurityError
        
        try:
            with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as temp_file:
                temp_filepath = temp_file.name
                temp_file.write(self.code.encode('utf-8'))
            
            # Run Bandit with configuration from config.py
            cmd = [
                'bandit',
                # Use --exit-zero to always return 0 exit code (avoid failing on findings)
                '--exit-zero',
                # JSON output format
                '-f', 'json',
                # Confidence level threshold
                '--confidence-level=' + self.config['CONFIDENCE_THRESHOLD'],
                # Severity level threshold
                '--severity-level=' + self.config['SEVERITY_THRESHOLD']
            ]
            
            # Add skip tests if configured
            if self.config['SKIP_TESTS']:
                skip_tests = ','.join(self.config['SKIP_TESTS'])
                cmd.extend(['-s', skip_tests])
            
            # Add nosec flag if configured
            if self.config['IGNORE_NOSEC']:
                cmd.append('--ignore-nosec')
            
            # Add the target file
            cmd.append(temp_filepath)
            
            try:
                # Execute Bandit
                process = subprocess.run(
                    cmd, 
                    check=False,  # Don't raise exception on non-zero exit code
                    capture_output=True,
                    text=True
                )
                
                if process.returncode != 0:  # Should always be 0 with --exit-zero
                    logger.error(f"Bandit execution failed with code {process.returncode}")
                    logger.error(f"Error output: {process.stderr}")
                    logger.warning("Continuing without Bandit security analysis")
                    return False, []
                
                try:
                    # Parse results
                    self.results = json.loads(process.stdout)
                    self.issues = self._parse_issues(self.results)
                    
                    # Process security issues by severity
                    high_severity_issues = self._get_high_severity_issues()
                    medium_severity_issues = self._get_medium_severity_issues()
                    low_severity_issues = self._get_low_severity_issues()
                    
                    # Log summary information
                    severity_summary = f"Bandit found: {len(high_severity_issues)} high, " \
                                     f"{len(medium_severity_issues)} medium, " \
                                     f"{len(low_severity_issues)} low severity issues"
                    logger.info(severity_summary)
                    
                    # Log low severity issues as warnings
                    if low_severity_issues:
                        for issue in low_severity_issues:
                            logger.warning(f"Low severity issue: {issue['issue_text']} ({issue['issue_id']}) at line {issue['line_number']}")
                    
                    # Block strategies with high or medium severity issues
                    if high_severity_issues:
                        issue_details = [f"{i['issue_text']} ({i['issue_id']}) at line {i['line_number']}" for i in high_severity_issues]
                        raise SecurityError(f"Critical security issues found: {', '.join(issue_details)}")
                    
                    if medium_severity_issues:
                        issue_details = [f"{i['issue_text']} ({i['issue_id']}) at line {i['line_number']}" for i in medium_severity_issues]
                        raise SecurityError(f"Medium severity security issues found: {', '.join(issue_details)}")
                    
                    return True, self.issues
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse Bandit output as JSON: {str(e)}")
                    logger.error(f"Raw output: {process.stdout[:200]}...")  # Only show first 200 chars
                    logger.warning("Continuing without Bandit security analysis")
                    return False, []
            
            except Exception as e:
                logger.error(f"Error executing Bandit: {str(e)}")
                logger.warning("Continuing without Bandit security analysis")
                return False, []
            
        except FileNotFoundError:
            logger.error("Bandit package not installed or not found in PATH")
            # Gracefully handle missing Bandit by returning empty results
            return False, []
            
        finally:
            # Clean up temp file
            if 'temp_filepath' in locals():
                try:
                    os.unlink(temp_filepath)
                except:
                    pass
    
    def _parse_issues(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse the Bandit results into a simplified format
        
        Args:
            results: The raw JSON results from Bandit
            
        Returns:
            List of simplified issue dictionaries
        """
        if not results or 'results' not in results:
            return []
            
        parsed_issues = []
        for issue in results['results']:
            parsed_issue = {
                'issue_id': issue.get('test_id', 'unknown'),
                'issue_severity': issue.get('issue_severity', 'UNKNOWN'),
                'issue_confidence': issue.get('issue_confidence', 'UNKNOWN'),
                'issue_text': issue.get('issue_text', 'Unknown issue'),
                'line_number': issue.get('line_number', 0),
                'line_range': issue.get('line_range', []),
                'test_name': issue.get('test_name', 'unknown')
            }
            parsed_issues.append(parsed_issue)
            
        return parsed_issues
    
    def _get_high_severity_issues(self) -> List[Dict[str, Any]]:
        """Get high severity issues, including tests configured as high severity
        
        Returns:
            List of high severity issues
        """
        high_issues = [i for i in self.issues if i['issue_severity'] == 'HIGH']
        
        # Also include issues from specific tests that should be treated as high severity
        high_severity_tests = self.config['HIGH_SEVERITY_TESTS']
        additional_high_issues = [
            i for i in self.issues 
            if i['issue_id'] in high_severity_tests and i not in high_issues
        ]
        
        return high_issues + additional_high_issues
    
    def _get_medium_severity_issues(self) -> List[Dict[str, Any]]:
        """Get medium severity issues, including tests configured as medium severity
        
        Returns:
            List of medium severity issues
        """
        medium_issues = [i for i in self.issues if i['issue_severity'] == 'MEDIUM']
        
        # Also include issues from specific tests that should be treated as medium severity
        medium_severity_tests = self.config['MEDIUM_SEVERITY_TESTS']
        additional_medium_issues = [
            i for i in self.issues 
            if i['issue_id'] in medium_severity_tests and i not in medium_issues
        ]
        
        return medium_issues + additional_medium_issues
    
    def _get_low_severity_issues(self) -> List[Dict[str, Any]]:
        """Get low severity issues, including tests configured as low severity
        
        Returns:
            List of low severity issues
        """
        low_issues = [i for i in self.issues if i['issue_severity'] == 'LOW']
        
        # Also include issues from specific tests that should be treated as low severity
        low_severity_tests = self.config.get('LOW_SEVERITY_TESTS', [])
        additional_low_issues = [
            i for i in self.issues 
            if i['issue_id'] in low_severity_tests and i not in low_issues
        ]
        
        return low_issues + additional_low_issues
    
    def get_issues_by_severity(self, severity: str) -> List[Dict[str, Any]]:
        """Get issues filtered by severity level
        
        Args:
            severity: Severity level to filter by (HIGH, MEDIUM, LOW)
            
        Returns:
            List of issues matching the severity
        """
        if not self.issues:
            return []
            
        return [i for i in self.issues if i['issue_severity'] == severity.upper()]
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the security analysis
        
        Returns:
            Dictionary with summary information
        """
        if not self.results:
            return {"status": "not_run", "issues_count": 0}
            
        high_issues = len(self.get_issues_by_severity('HIGH'))
        medium_issues = len(self.get_issues_by_severity('MEDIUM'))
        low_issues = len(self.get_issues_by_severity('LOW'))
        
        return {
            "status": "complete",
            "issues_count": len(self.issues),
            "high_severity_count": high_issues,
            "medium_severity_count": medium_issues,
            "low_severity_count": low_issues
        } 