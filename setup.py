from setuptools import setup, find_packages

setup(
    name="hypertrial",
    version="0.1.0",
    description="Bitcoin Dollar-Cost Averaging (DCA) Backtest Framework",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="",
    author_email="",
    url="https://github.com/mattfaltyn/hypertrial",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "pandas",
        "numpy",
        "matplotlib",
        "coinmetrics-api-client>=2024.2.6.16",
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
    ],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "hypertrial=core.main:main",
        ],
    },
) 