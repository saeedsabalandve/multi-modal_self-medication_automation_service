"""
Setup configuration for the medication automation package
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="self-medication-automation",
    version="2.0.0",
    author="Your Team Name",
    author_email="team@example.com",
    description="Multi-modal self-medication automation using AWS and Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/self-medication-automation",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Healthcare Industry",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
    install_requires=[
        "fastapi>=0.109.0",
        "boto3>=1.34.0",
        "pydantic>=2.6.0",
        "uvicorn>=0.27.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "black>=24.1.0",
            "mypy>=1.8.0",
        ],
    },
)
