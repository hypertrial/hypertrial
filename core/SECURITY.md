# Hypertrial: Stacking Sats Challenge - Security Model

This document outlines the security model implemented in the Stacking Sats Challenge to ensure safe execution of submitted strategies. The security system is designed to prevent potentially harmful code from running while allowing legitimate strategy implementations.

## Overview

Hypertrial implements a comprehensive security model that includes:

1. **Code Complexity Analysis**: Detects and limits overly complex code that could lead to resource exhaustion
2. **Data Flow Analysis**: Tracks external data usage to prevent exploitation
3. **Resource Monitoring**: Enforces limits on CPU, memory, and execution time
4. **Import Restrictions**: Controls which modules can be imported
5. **AST-based Validation**: Analyzes code structure to detect dangerous patterns
6. **URL and External Data Validation**: Ensures data comes from trusted sources only

## Security Components

### Resource Limits

The following resource limits are enforced:

| Resource              | Default Limit  | Test Mode Limit               |
| --------------------- | -------------- | ----------------------------- |
| Memory                | 512 MB         | 512 MB                        |
| CPU Time              | 10 seconds     | 30 seconds                    |
| Execution Time        | 30 seconds     | 60 seconds                    |
| Module Complexity     | 500 lines      | 500 lines                     |
| Function Complexity   | 120 statements | 120 statements (warning only) |
| Cyclomatic Complexity | 25             | 25 (warning only)             |
| Nested Depth          | 6 levels       | 6 levels (warning only)       |

### Resource Monitoring (`ResourceMonitor`)

The `ResourceMonitor` class provides real-time tracking of resource usage:

- **Memory Usage Tracking**: Monitors memory consumption over time to detect leaks
- **CPU Usage Monitoring**: Tracks CPU utilization to prevent computational abuse
- **Continuous Monitoring**: Can run in a background thread for real-time monitoring
- **Leak Detection**: Analyzes memory growth patterns to identify potential memory leaks
- **Limit Enforcement**: Terminates execution when limits are exceeded

### Import Control (`ImportHook`)

The `ImportHook` restricts which modules can be imported:

- **Allowlist Approach**: Only specifically allowed modules can be imported
- **Usage Tracking**: Monitors import frequency and patterns
- **Suspicious Activity Detection**: Identifies abnormal import patterns (frequent imports, rapid successive imports)

### Code Complexity Analysis (`ComplexityAnalyzer`)

The `ComplexityAnalyzer` identifies code that could be resource-intensive or malicious:

- **Module Complexity**: Limits total lines of code
- **Function Complexity**: Restricts statement count per function
- **Cyclomatic Complexity**: Limits decision paths in functions
- **Nested Depth**: Restricts nesting of control structures
- **Infinite Loop Detection**: Identifies potential infinite loops (while True without break)
- **Recursion Detection**: Finds both direct and indirect recursive calls
- **Comment Ratio Analysis**: Identifies suspiciously uncommented code

### Data Flow Analysis (`DataFlowAnalyzer`)

The `DataFlowAnalyzer` tracks how data moves through the code:

- **External Data Tracking**: Identifies variables containing external data
- **Variable Flow Tracking**: Follows data as it transforms through operations
- **Sensitive Operation Detection**: Identifies when external data is used in dangerous operations
- **Control Flow Taint Analysis**: Detects when external data indirectly influences sensitive operations
- **Data Leakage Detection**: Identifies when external data might be exfiltrated

### Strategy Security (`StrategySecurity`)

The `StrategySecurity` class provides the main security interface:

- **AST Analysis**: Deep inspection of code structure
- **URL Validation**: Ensures external data comes from approved sources
- **Security Decorator**: Wraps strategy functions with security checks
- **Security Context**: Maintains audit trail of strategy execution
- **Pattern Detection**: Uses regex to identify potentially dangerous code patterns

## Allowed Modules and Functions

Hypertrial restricts imports to a specific set of modules:

- Core data science: `pandas`, `numpy`, `scipy`
- Time and date: `datetime`, `time`
- Type information: `typing`
- Core framework: `core.config`, `core.strategies`, `core.strategies.base_strategy`
- Strategy modules: `submit_strategies`
- Data access: `pandas_datareader`

### Restricted OS Access

While the `os` module is allowed, access is limited to specific functions:

- `os.path.join`, `os.path.exists`, `os.path.abspath`
- `os.path.dirname`, `os.makedirs`, `os.path.isfile`
- `os.path.isdir`, `os.path.getsize`

All other OS operations are blocked.

## External Data Sources

Only the following data sources are allowed:

- CoinMetrics API: `api.coinmetrics.io`
- Yahoo Finance: `query1.finance.yahoo.com`, `finance.yahoo.com`
- CoinGecko: `api.coingecko.com`
- Nasdaq Data: `data.nasdaq.com`

## Dangerous Patterns

The security system detects and blocks many dangerous code patterns, including:

- Subprocess execution: `subprocess.`, `os.system()`
- System manipulation: `sys.exit`, `sys.path`
- Network operations: `socket.`
- Code execution: `eval()`, `exec()`, `compile()`
- Dynamic imports: `__import__()`, `importlib`
- Access to internal state: `globals()`, `locals()`
- Accessing dunder methods: `getattr(x, "__...")`
- File operations: Write operations, access to user directories
- Environment access: `os.environ`

## Implementation Details

### Security Decorator

Strategies are wrapped with the `@StrategySecurity.secure_strategy` decorator, which:

1. Creates a security context to track execution
2. Installs import hooks to restrict module access
3. Monitors resource usage during execution
4. Logs security events for auditing
5. Terminates execution if security violations occur

### File Validation

Before execution, strategy files undergo validation:

1. File size check (max 500KB)
2. Line length check (max 800 chars per line)
3. AST-based security analysis
4. Regex pattern matching for dangerous code

## Best Practices for Strategy Authors

When writing strategies, follow these guidelines to avoid security violations:

1. **Use Allowed Libraries**: Stick to pandas, numpy, and other allowed libraries
2. **Limit Complexity**: Keep functions simple and avoid deep nesting
3. **Avoid Infinite Loops**: Always include exit conditions in loops
4. **Handle External Data Safely**: Never use external data in eval() or similar functions
5. **Use Vectorized Operations**: Prefer pandas/numpy operations over explicit loops
6. **Limit Memory Usage**: Release large objects when no longer needed

## Security Warnings vs. Errors

In normal operation mode, security violations result in immediate termination. In test mode, some checks produce warnings instead of errors to facilitate development and testing.

## Extending the Security Model

The security model can be extended by:

1. Adding patterns to the dangerous patterns list
2. Updating the allowed modules set
3. Adding new checks to the complexity and data flow analyzers
4. Adjusting resource limits for specific environments

For questions or to report security issues, please contact the Hypertrial maintainers.
