"""Configuration settings for the security module."""

# Allowed modules for strategy submissions
ALLOWED_MODULES = {
    'pandas', 'numpy', 'datetime', 'typing',
    'core.config', 'core.strategies', 'core.strategies.base_strategy',
    'submit_strategies', 'pandas_datareader', 'scipy', 'time'
}

# Allow specific os.path functions only
ALLOWED_OS_FUNCTIONS = {
    'os.path.join', 'os.path.exists', 'os.path.abspath', 
    'os.path.dirname', 'os.makedirs', 'os.path.isfile',
    'os.path.isdir', 'os.path.getsize'
}

# Allowed external data sources (domain whitelist)
ALLOWED_DATA_SOURCES = {
    'api.coinmetrics.io',  # CoinMetrics API
    'query1.finance.yahoo.com',  # Yahoo Finance
    'api.coingecko.com',  # CoinGecko
    'finance.yahoo.com',  # Yahoo Finance
    'data.nasdaq.com',    # Nasdaq Data Link
}

# Resource limits
MAX_MEMORY_MB = 512  # Maximum memory usage in MB
MAX_CPU_TIME = 10  # Maximum CPU time in seconds
MAX_EXECUTION_TIME = 30  # Maximum total execution time in seconds

# More relaxed limits for test environments
TEST_MAX_CPU_TIME = 30  # More relaxed CPU time limit for tests
TEST_MAX_EXECUTION_TIME = 60  # More relaxed execution time limit for tests

# Code complexity limits
MAX_CYCLOMATIC_COMPLEXITY = 25  # Maximum allowed cyclomatic complexity
MAX_NESTED_DEPTH = 6  # Maximum allowed nested depth (loops, conditionals)
MAX_FUNCTION_COMPLEXITY = 120  # Maximum allowed number of statements in a function
MAX_MODULE_COMPLEXITY = 500  # Maximum total lines of code in a module 