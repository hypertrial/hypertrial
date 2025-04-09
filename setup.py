from setuptools import setup, find_packages
import os

# Use the PyPI-specific README if it exists, otherwise use the main README
readme_path = "PYPI_README.md" if os.path.exists("PYPI_README.md") else "README.md"

setup(
    name="hypertrial",
    version="0.1.1",
    description="Bitcoin Dollar-Cost Averaging (DCA) Backtest Framework",
    long_description=open(readme_path).read(),
    long_description_content_type="text/markdown",
    author="Matt Faltyn",
    author_email="faltyn.matthew@gmail.com",
    url="https://github.com/hypertrial/hypertrial",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "pandas>=1.3.0",
        "numpy>=1.20.0",
        "matplotlib>=3.4.0",
        "coinmetrics-api-client>=2024.2.6.16",
        "pytest>=6.2.0",
        "pandas_datareader>=0.10.0",
        "scipy>=1.6.0",
        "psutil>=5.8.0",
        "bandit>=1.7.0",
        "safety>=2.0.0",
        "pylint>=2.12.0"
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Financial and Insurance Industry",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Topic :: Office/Business :: Financial :: Investment",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "hypertrial=core.main:main",
        ],
    },
) 