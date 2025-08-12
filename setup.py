"""
Setup script for the FinanceQA Agent package.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="finance-qa-agent",
    version="1.0.0",
    author="FinanceQA Team",
    author_email="",
    description="A comprehensive AI-powered agent for answering financial questions",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-repo/finance_qa_agent",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "financeqa=finance_qa_agent_final.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "finance_qa_agent_final": ["*.md", "*.txt", "data/*"],
    },
)
