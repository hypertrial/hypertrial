"""Configuration settings for the security module."""

# Allowed modules for strategy submissions
ALLOWED_MODULES = {
    # Core dependencies from requirements.txt
    'pandas', 'numpy', 'matplotlib', 'coinmetrics_api_client', 'coinmetrics',
    'pytest', 'scipy', 'psutil', 'bandit', 'safety', 'pylint',
    
    # Standard library modules needed for strategy operation
    'datetime', 'typing', 'time',
    
    # Framework modules
    'core.config', 'core.strategies', 'core.strategies.base_strategy',
    'submit_strategies'
}

# Allow specific os.path functions only
ALLOWED_OS_FUNCTIONS = {
    'os.path.join', 'os.path.exists'
}

# Explicitly banned modules (will be checked in addition to not being in ALLOWED_MODULES)
BANNED_MODULES = {
    # Network and HTTP
    'requests', 'urllib', 'http', 'socket', 'pandas_datareader',
    
    # Process and system
    'subprocess', 'multiprocessing', 'threading', 'asyncio', 'concurrent',
    
    # Low-level and system access
    'ctypes', 'sys', 'os.path',
    
    # Serialization
    'pickle', 'marshal', 'shelve', 'json.tool',
    
    # File operations
    'tempfile', 'shutil', 
    
    # Code generation and execution
    'imp', 'importlib', 'ast', 'code', 'codeop',
    
    # Other dangerous modules
    'pty', 'pdb', 'trace', 'profile', 'bdb'
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

# Bandit configuration
BANDIT_CONF = {
    'SKIP_TESTS': [],  # Tests to skip (by test ID)
    
    # High severity tests that should block strategy execution
    'HIGH_SEVERITY_TESTS': [  
        # Code execution
        'B102',  # exec used - allows arbitrary code execution
        'B307',  # eval used - allows arbitrary code execution
        
        # Permissions and access
        'B103',  # set bad file permissions - can make files world-readable/writable
        
        # Cryptographic issues
        'B303',  # use of weak MD* hash functions
        'B324',  # hashlib insecure hashing functions (MD4, MD5)
        'B501',  # requests without certificate validation
        'B502',  # ssl with insecure protocol versions
        'B503',  # ssl with bad defaults
        'B504',  # ssl without version specification
        'B505',  # weak cryptographic key (< 2048 bits for RSA, < 224 bits for ECC)
        
        # Injection vulnerabilities
        'B601',  # paramiko command execution
        'B602',  # subprocess shell=True - command injection risk
        'B604',  # any function with shell=True - command injection risk
        'B605',  # start process with a shell - command injection risk
        'B607',  # start process with partial path - path injection risk
        'B608',  # hardcoded SQL expressions - SQL injection risk
        'B609',  # Linux wildcard injection in shell commands
        
        # Application configuration
        'B201',  # flask debug mode - exposes internal details
        
        # Template injection
        'B701',  # jinja2 autoescape disabled - XSS risk
        'B702',  # use of mako templates - potential SSTI
        'B703',  # django mark_safe - XSS risk
        'B704',  # use of markupsafe - XSS risk
    ],
    
    # Medium severity tests that should block strategy execution
    'MEDIUM_SEVERITY_TESTS': [  
        # Hardcoded credentials
        'B105',  # hardcoded password string
        'B106',  # hardcoded password function argument
        'B107',  # hardcoded password default
        'B108',  # hardcoded temporary directory - predictable paths
        'B109',  # password config option not marked secret
        
        # Unsafe deserialization
        'B506',  # yaml.load without safe loader - deserialization vulnerability
        'B614',  # pytorch loads without safeguards - deserialization vulnerability
        
        # Injection vulnerabilities
        'B610',  # django.db.models.extra() - SQL injection risk
        'B611',  # django.db.models.raw() - SQL injection risk
        
        # Networking
        'B507',  # ssh without host key verification
        'B508',  # snmp with insecure version (v1/v2)
        'B509',  # snmp with weak cryptography
        
        # Exception handling
        'B110',  # try-except-pass - swallows all errors silently
    ],
    
    # Low severity tests that generate warnings but don't block execution
    'LOW_SEVERITY_TESTS': [
        'B101',  # use of assert - can be removed in optimized mode
        'B112',  # try-except-continue - may swallow errors
        'B113',  # request without timeout - potential for hanging
        'B413',  # import with wildcard - namespace pollution
        'B602',  # subprocess without shell=True - safer but still check for injection
        'B606',  # start process without shell - safer but still check for injection
    ],
    
    # Ignore #nosec comments (set to True to ignore developer annotations)
    'IGNORE_NOSEC': False,
    
    # Minimum severity threshold for reporting (LOW, MEDIUM, HIGH)
    'SEVERITY_THRESHOLD': 'low',
    
    # Minimum confidence threshold for reporting (LOW, MEDIUM, HIGH)
    'CONFIDENCE_THRESHOLD': 'low',
    
    # Custom plugin configurations
    'CUSTOM_PLUGIN_CONFIG': {
        # Maximum allowed nested structure depth
        'max_nested_level': 5,
        
        # Minimum required entropy for secrets (higher = more complex)
        'min_entropy_for_secrets': 3.5,
        
        # Banned imports - these should never be used in strategies
        'banned_imports': [
            'requests', 'urllib', 'http', 'socket',
            'subprocess', 'pickle', 'marshal', 'shelve',
            'multiprocessing', 'ctypes', 'threading', 'asyncio',
            'concurrent'
        ]
    }
}

# Explicitly allowed pandas_datareader functions (whitelist approach) - REMOVED since pandas_datareader is now banned 