#!/usr/bin/env python3
"""
BigAcademy Setup
AI Agent Knowledge Extraction and Dataset Generation Pipeline
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
README = (Path(__file__).parent / "README.md").read_text(encoding="utf-8")

# Read requirements
REQUIREMENTS = (Path(__file__).parent / "requirements.txt").read_text().strip().split('\n')
REQUIREMENTS = [req.strip() for req in REQUIREMENTS if req.strip() and not req.startswith('#')]

setup(
    name="bigacademy",
    version="0.1.0",
    description="AI Agent Knowledge Extraction and Dataset Generation Pipeline",
    long_description=README,
    long_description_content_type="text/markdown",
    author="BigAcademy Team",
    author_email="contact@bigacademy.ai",
    url="https://github.com/franckbirba/bigacademy",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.10",
    install_requires=REQUIREMENTS,
    entry_points={
        "console_scripts": [
            "bigacademy=bigacademy.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="ai agents knowledge extraction dataset generation llm training",
    project_urls={
        "Bug Reports": "https://github.com/franckbirba/bigacademy/issues",
        "Source": "https://github.com/franckbirba/bigacademy",
        "Documentation": "https://github.com/franckbirba/bigacademy#readme",
    },
)