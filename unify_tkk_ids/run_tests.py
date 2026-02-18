#!/usr/bin/env python3
"""
Test runner script for unify_tkk_ids

Usage:
    python run_tests.py           # Run all tests
    python run_tests.py -unit     # Run only unit tests  
    python run_tests.py -int      # Run only integration tests
    python run_tests.py -cov      # Run tests with coverage report
"""

import sys
import subprocess
import argparse


def run_tests(test_type=None, coverage=False):
    """Run tests with specified options"""
    
    cmd = ["python", "-m", "pytest"]
    
    if test_type == "unit":
        cmd.extend(["-m", "unit"])
    elif test_type == "integration": 
        cmd.extend(["-m", "integration"])
    
    if coverage:
        cmd.extend(["--cov=unify_tkk_ids", "--cov-report=term-missing"])
    
    cmd.append("tests/")
    
    print(f"Running: {' '.join(cmd)}")
    return subprocess.run(cmd).returncode


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Run tests for unify_tkk_ids")
    parser.add_argument("-unit", action="store_true", help="Run only unit tests")
    parser.add_argument("-int", "--integration", action="store_true", help="Run only integration tests")
    parser.add_argument("-cov", "--coverage", action="store_true", help="Run with coverage report")
    
    args = parser.parse_args()
    
    test_type = None
    if args.unit:
        test_type = "unit"
    elif args.integration:
        test_type = "integration"
    
    exit_code = run_tests(test_type, args.coverage)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()