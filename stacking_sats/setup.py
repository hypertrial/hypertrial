from setuptools import setup, find_packages

setup(
    name="stacking_sats",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pandas>=1.3.0,<2.0.0",
        "numpy>=1.20.0,<2.0.0",
        "matplotlib>=3.4.0,<4.0.0",
        "pyarrow>=7.0.0",  # For parquet support
        "pyyaml>=6.0",     # For configuration management
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "isort>=5.10.0",
            "mypy>=1.0.0",
        ],
        "data": [
            "cryptocompare>=0.7.0",
            "yfinance>=0.2.0",  # Alternative data source
        ],
    },
    description="A flexible Bitcoin investment strategy backtesting library",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Matt Faltyn",
    author_email="your.email@example.com",
    url="https://github.com/mattfaltyn/stacking_sats",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Financial and Insurance Industry",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Office/Business :: Financial :: Investment",
        "License :: OSI Approved :: MIT License",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "stacksats=stacking_sats.cli.main:main",
        ],
    },
) 