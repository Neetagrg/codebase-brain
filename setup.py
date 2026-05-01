"""
Codebase Brain - AI-friendly codebase documentation tool
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="codebase-brain",
    version="1.0.0",
    author="Codebase Brain Team",
    author_email="contact@codebasebrain.dev",
    description="AI-friendly codebase documentation tool for generating and maintaining AGENTS.md",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/codebase-brain",
    py_modules=["codebase_brain_cli"],
    python_requires=">=3.8",
    install_requires=[
        "click>=8.0.0",
        "rich>=13.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "codebase-brain=codebase_brain_cli:cli",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Documentation",
        "Topic :: Software Development :: Code Generators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    keywords="ai documentation agents copilot claude cursor github-copilot",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/codebase-brain/issues",
        "Source": "https://github.com/yourusername/codebase-brain",
        "Documentation": "https://github.com/yourusername/codebase-brain#readme",
    },
)

# Made with Bob
