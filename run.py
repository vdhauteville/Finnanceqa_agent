#!/usr/bin/env python3
"""
Convenience script to run the FinanceQA Agent.
This allows running the agent from outside the package directory.
"""

import sys
import os

# Add the current directory to Python path to enable imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import main

if __name__ == "__main__":
    main()
