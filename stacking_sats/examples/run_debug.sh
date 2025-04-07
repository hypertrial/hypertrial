#!/bin/bash
# Script to run the comparison and analyze logs

# Change to project root directory
cd "$(dirname "$0")/.."
echo "Working directory: $(pwd)"

# Ensure Python can find our modules
export PYTHONPATH="$(pwd):$PYTHONPATH"

# Clean up old logs
echo "Cleaning up old logs..."
rm -f dynamic_strategy_debug.log functional_model_debug.log comparison_run.log

# Note: Using 'python3' instead of 'python' or 'py' for better compatibility on macOS
# Execute the comparison script
echo "Running comparison..."
python3 stacking_sats/examples/run_comparison.py

# Check if logs were created
if [ -f comparison_run.log ]; then
    echo "Logs created successfully"
    
    # Extract key information from logs
    echo -e "\n=== SUMMARY OF FINDINGS ==="
    echo "First differences in weights:"
    grep "First day with weight difference:" comparison_run.log
    
    echo -e "\nMaximum difference:"
    grep "Max difference at date:" comparison_run.log
    
    echo -e "\nCycle weight differences:"
    grep "Cycle .* weight sum difference:" comparison_run.log
    
    echo -e "\nComparison summary:"
    grep -A5 "=== COMPARISON SUMMARY ===" comparison_run.log
    
    # Check for numerical precision issues
    echo -e "\nChecking for floating point precision issues..."
    grep "diff:" comparison_run.log | awk '{print $NF}' | sort -n | uniq -c
    
    echo -e "\nLog files created:"
    echo "- dynamic_strategy_debug.log (class implementation)"
    echo "- functional_model_debug.log (functional implementation)"
    echo "- comparison_run.log (comparison results)"
    
    echo -e "\nNext steps:"
    echo "1. Check the detailed logs for specific differences"
    echo "2. Look at weight_comparison.png for visual comparison"
    echo "3. Consider numerical precision settings in both implementations"
else
    echo "Error: Logs not created, check for errors in execution"
fi 