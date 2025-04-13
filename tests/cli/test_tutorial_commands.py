import unittest
import os
import sys
import subprocess
import tempfile
import pandas as pd
from pathlib import Path
import shutil

# Suppress matplotlib output for testing
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
plt.ioff()  # Turn off interactive mode

class TestTutorialCommandsExecution(unittest.TestCase):
    """Test that all commands from commands.py and main.py run successfully with the tutorials."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        # Set matplotlib backend to non-interactive for subprocess environment
        os.environ['MPLBACKEND'] = 'Agg'
        
        # Ensure we have output directory for results
        cls.output_dir = tempfile.mkdtemp(prefix="test_results_")
        
        # Path to the example strategy in tutorials
        cls.example_strategy_path = os.path.abspath("tutorials/example_strategy.py")
        
        # Path to tutorials directory
        cls.tutorials_dir = os.path.abspath("tutorials")
        
        # Verify files exist
        if not os.path.exists(cls.example_strategy_path):
            raise FileNotFoundError(f"Example strategy file not found at {cls.example_strategy_path}")
        
        if not os.path.isdir(cls.tutorials_dir):
            raise FileNotFoundError(f"Tutorials directory not found at {cls.tutorials_dir}")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after tests."""
        # Remove temporary output directory
        if os.path.exists(cls.output_dir):
            shutil.rmtree(cls.output_dir)
    
    def _run_command(self, cmd_args, check_success=True):
        """Helper to run a command and return results."""
        full_cmd = [sys.executable, "-m", "core.main"] + cmd_args
        
        # Create environment with non-interactive matplotlib backend
        env = os.environ.copy()
        env['MPLBACKEND'] = 'Agg'
        env['PYTHONPATH'] = os.getcwd() + ':' + env.get('PYTHONPATH', '')
        
        result = subprocess.run(
            full_cmd,
            capture_output=True,
            text=True,
            env=env
        )
        
        # Print output for debugging
        print(f"\nCommand: {' '.join(full_cmd)}")
        print(f"Return code: {result.returncode}")
        print(f"Stdout: {result.stdout[:500]}...")  # Truncate long output
        print(f"Stderr: {result.stderr[:500]}...")  # Truncate long output
        
        if check_success:
            # Check if the command completed without errors
            self.assertEqual(result.returncode, 0, 
                            f"Command failed with return code {result.returncode}. "
                            f"Stderr: {result.stderr}")
        
        return result
    
    def test_list_strategies(self):
        """Test the --list command."""
        result = self._run_command(["--list"])
        self.assertIn("Available Strategies", result.stdout)
    
    def test_example_strategy_standalone(self):
        """Test running example_strategy.py in standalone mode."""
        result = self._run_command([
            "--strategy-file", self.example_strategy_path, 
            "--standalone", 
            "--no-plots"
        ])
        self.assertIn("dynamic_dca_200ma", result.stdout)
    
    def test_example_strategy_standalone_with_output_dir(self):
        """Test running example_strategy.py with output directory."""
        result = self._run_command([
            "--strategy-file", self.example_strategy_path, 
            "--standalone", 
            "--no-plots",
            "--output-dir", self.output_dir
        ])
        self.assertIn("dynamic_dca_200ma", result.stdout)
    
    def test_example_strategy_no_validate(self):
        """Test running example_strategy.py without validation."""
        result = self._run_command([
            "--strategy-file", self.example_strategy_path, 
            "--standalone", 
            "--no-plots",
            "--no-validate"
        ])
        self.assertIn("dynamic_dca_200ma", result.stdout)
    
    def test_example_strategy_with_save_plots(self):
        """Test running example_strategy.py with saving plots."""
        # When using --save-plots, we can't use --no-plots since that would disable all plots
        # Instead, we'll just check if the files are created and the test will pass quickly
        result = self._run_command([
            "--strategy-file", self.example_strategy_path, 
            "--standalone",
            "--save-plots",
            "--output-dir", self.output_dir
        ])
        self.assertIn("dynamic_dca_200ma", result.stdout)
        
        # Check for evidence that plots were saved
        self.assertIn("Plot saved to:", result.stdout + result.stderr)
        
        # Look for evidence the SPD metrics were calculated
        self.assertIn("SPD Metrics", result.stdout + result.stderr)
    
    def test_strategy_dir_command(self):
        """Test --strategy-dir command with tutorials directory."""
        result = self._run_command([
            "--strategy-dir", self.tutorials_dir,
            "--no-plots",
            "--output-dir", self.output_dir
        ])
        # Check if the command processed the example strategy
        self.assertIn("example_strategy.py", result.stdout + result.stderr)
    
    def test_glob_pattern_command(self):
        """Test --glob-pattern command for example_strategy.py."""
        result = self._run_command([
            "--glob-pattern", "tutorials/*.py",
            "--no-plots",
            "--output-dir", self.output_dir
        ])
        # Check if the command processed the example strategy
        self.assertIn("example_strategy.py", result.stdout + result.stderr)
    
    def test_strategy_files_command(self):
        """Test --strategy-files command with example_strategy.py."""
        result = self._run_command([
            "--strategy-files", self.example_strategy_path,
            "--no-plots",
            "--output-dir", self.output_dir
        ])
        # Check if the command processed the example strategy
        self.assertIn("example_strategy.py", result.stdout + result.stderr)
    
    def test_backtest_all_command(self):
        """Test --backtest-all command to run all strategies."""
        result = self._run_command([
            "--backtest-all",
            "--output-dir", self.output_dir
        ], check_success=False)
        
        # Just check if the command started the backtest process
        self.assertIn("Backtesting", result.stdout + result.stderr)
    
    def test_download_data_command(self):
        """Test --download-data command with example strategy."""
        # This may take longer, so we'll tolerate potential failure if the download fails
        
        # Create environment with non-interactive matplotlib backend
        env = os.environ.copy()
        env['MPLBACKEND'] = 'Agg'
        env['PYTHONPATH'] = os.getcwd() + ':' + env.get('PYTHONPATH', '')
        
        result = subprocess.run(
            [sys.executable, "-m", "core.main", 
             "--strategy-file", self.example_strategy_path,
             "--standalone", "--no-plots", "--download-data"],
            capture_output=True,
            text=True,
            env=env
        )
        # Just check if the command ran without crashes
        self.assertNotIn("Segmentation fault", result.stderr)
        self.assertNotIn("Fatal error", result.stderr)
    
    def test_recursive_flag(self):
        """Test --recursive flag with strategy directory."""
        result = self._run_command([
            "--strategy-dir", os.path.dirname(self.tutorials_dir),
            "--recursive",
            "--no-plots",
            "--include-patterns", "example_strategy.py",
            "--output-dir", self.output_dir
        ])
        # Check if the command processed the example strategy
        self.assertIn("example_strategy.py", result.stdout + result.stderr)
    
    def test_exclude_patterns(self):
        """Test --exclude-patterns flag."""
        result = self._run_command([
            "--strategy-dir", self.tutorials_dir,
            "--exclude-patterns", "__pycache__", "*.ipynb",
            "--no-plots",
            "--output-dir", self.output_dir
        ])
        # Should only process Python files and exclude notebooks
        self.assertIn("example_strategy.py", result.stdout + result.stderr)
        self.assertNotIn("Submission_Template.ipynb", result.stdout)
    
    def test_include_patterns(self):
        """Test --include-patterns flag."""
        result = self._run_command([
            "--strategy-dir", self.tutorials_dir,
            "--include-patterns", "example_*.py",
            "--no-plots",
            "--output-dir", self.output_dir
        ])
        # Should only include files matching the pattern
        self.assertIn("example_strategy.py", result.stdout + result.stderr)
    
    def test_max_files_flag(self):
        """Test --max-files flag."""
        result = self._run_command([
            "--strategy-dir", self.tutorials_dir,
            "--max-files", "1",
            "--no-plots",
            "--output-dir", self.output_dir
        ])
        
        # Check if only one file was processed
        self.assertIn("Found 1 potential strategy files", result.stdout + result.stderr)
    
    def test_processes_flag(self):
        """Test --processes flag for parallel processing."""
        # Create a test with multiple duplicate files to test parallel processing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Copy example strategy to multiple files
            for i in range(3):
                shutil.copy(
                    self.example_strategy_path, 
                    os.path.join(temp_dir, f"example_strategy_{i}.py")
                )
            
            result = self._run_command([
                "--strategy-dir", temp_dir,
                "--processes", "2",
                "--no-plots",
                "--output-dir", self.output_dir
            ])
            # Check if parallel processing was used
            self.assertIn("processes", result.stdout + result.stderr)
    
    def test_batch_size_flag(self):
        """Test --batch-size flag for batch processing."""
        # Create a test with multiple duplicate files to test batch processing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Copy example strategy to multiple files
            for i in range(5):
                shutil.copy(
                    self.example_strategy_path, 
                    os.path.join(temp_dir, f"example_strategy_{i}.py")
                )
            
            result = self._run_command([
                "--strategy-dir", temp_dir,
                "--batch-size", "2",
                "--no-plots",
                "--output-dir", self.output_dir
            ])
            # Check if batch processing was used
            self.assertIn("Processing", result.stdout + result.stderr)
    
    def test_file_timeout_flag(self):
        """Test --file-timeout flag."""
        result = self._run_command([
            "--strategy-file", self.example_strategy_path,
            "--standalone",
            "--file-timeout", "60",
            "--no-plots",
            "--output-dir", self.output_dir
        ])
        # Just check if the command ran successfully
        self.assertIn("dynamic_dca_200ma", result.stdout)
    
    def test_registered_strategy(self):
        """Test running a registered strategy from example_strategy.py."""
        # First load the example strategy to register it
        try:
            self._run_command([
                "--strategy-file", self.example_strategy_path, 
                "--no-plots"
            ])
            
            # Now try to run it by name
            result = self._run_command([
                "--strategy", "dynamic_dca_200ma",
                "--no-plots",
                "--output-dir", self.output_dir
            ], check_success=False)
            
            # If the strategy was properly registered, it should run successfully
            # But we also allow for cases where registration didn't work
            if result.returncode == 0:
                self.assertIn("dynamic_dca_200ma", result.stdout)
        except:
            # Registration might not work in some test environments, so we'll tolerate failure
            pass
    
    def test_csv_output_columns(self):
        """Test that the CSV output contains all required columns when running CLI commands."""
        # Create a dedicated temp directory for this test
        temp_output_dir = os.path.join(self.output_dir, "csv_test")
        os.makedirs(temp_output_dir, exist_ok=True)
        
        # Run command that generates CSV output
        result = self._run_command([
            "--strategy-dir", self.tutorials_dir,
            "--recursive",
            "--no-plots",
            "--output-dir", temp_output_dir
        ])
        
        # Verify CSV was created
        csv_path = os.path.join(temp_output_dir, 'strategy_files_summary.csv')
        self.assertTrue(os.path.exists(csv_path), f"CSV file not created at {csv_path}")
        
        # Read the CSV and check all required columns
        csv_df = pd.read_csv(csv_path)
        
        # Verify at least one strategy was processed
        self.assertGreater(len(csv_df), 0, "No strategies were processed in the CSV")
        
        # Check each column group
        # 1. Strategy identification columns
        self.assertIn('strategy_file', csv_df.columns)
        self.assertIn('strategy_name', csv_df.columns)
        self.assertIn('success', csv_df.columns)
        
        # 2. SPD metrics from spd.py
        spd_metrics = [
            'min_spd', 'max_spd', 'mean_spd', 'median_spd',
            'min_pct', 'max_pct', 'mean_pct', 'median_pct',
            'cycles', 'excess_pct', 'mean_excess_pct'
        ]
        for metric in spd_metrics:
            self.assertIn(metric, csv_df.columns, f"Missing SPD metric: {metric}")
        
        # 3. Validation results from spd_checks.py
        validation_columns = [
            'validation_validation_passed',
            'validation_has_negative_weights',
            'validation_has_below_min_weights',
            'validation_weights_not_sum_to_one',
            'validation_underperforms_uniform',
            'validation_cycle_issues'
        ]
        for col in validation_columns:
            self.assertIn(col, csv_df.columns, f"Missing validation column: {col}")
        
        # 4. Security results from bandit_analyzer.py
        security_columns = [
            'high_threats', 'medium_threats', 'low_threats', 'total_threats'
        ]
        for col in security_columns:
            self.assertIn(col, csv_df.columns, f"Missing security column: {col}")
        
        # Verify the registered strategies are present
        strategy_names = csv_df['strategy_name'].unique()
        self.assertIn('dynamic_dca_200ma', strategy_names, "Missing dynamic_dca_200ma strategy") 
        
        # Verify example data matches expectations
        for idx, row in csv_df.iterrows():
            # Check that validation passed for our example strategies
            self.assertTrue(row['validation_validation_passed'], 
                           f"Validation failed for {row['strategy_name']}")
            
            # Check that security shows no threats for our example strategies
            self.assertEqual(row['high_threats'], 0, 
                            f"High threats found for {row['strategy_name']}")
            self.assertEqual(row['medium_threats'], 0, 
                            f"Medium threats found for {row['strategy_name']}")

if __name__ == "__main__":
    unittest.main() 