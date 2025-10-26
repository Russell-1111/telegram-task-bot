"""
Test runner script for Telegram Task Bot

This script runs all tests with coverage reporting and generates
a comprehensive test report.

Usage:
    python run_tests.py                  # Run all tests
    python run_tests.py --unit           # Run only unit tests
    python run_tests.py --integration    # Run only integration tests
    python run_tests.py --coverage       # Run with detailed coverage report
"""
import sys
import subprocess
from pathlib import Path


def run_tests(test_type=None, with_coverage=True):
    """
    Run pytest with specified options
    
    Args:
        test_type: 'unit', 'integration', or None for all tests
        with_coverage: Whether to generate coverage reports
    """
    # Base pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add test markers if specified
    if test_type == "unit":
        cmd.extend(["-m", "unit"])
    elif test_type == "integration":
        cmd.extend(["-m", "integration"])
    
    # Add coverage options
    if with_coverage:
        cmd.extend([
            "--cov=src",
            "--cov-report=term-missing",
            "--cov-report=html",
            "--cov-fail-under=80"
        ])
    
    # Add verbose output
    cmd.extend(["-v", "--tb=short"])
    
    # Run the tests
    print(f"Running tests: {' '.join(cmd)}")
    print("=" * 60)
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    
    # Print coverage report location if generated
    if with_coverage and result.returncode == 0:
        print("\n" + "=" * 60)
        print("Coverage report generated in: htmlcov/index.html")
        print("=" * 60)
    
    return result.returncode


def main():
    """Main entry point"""
    # Parse command line arguments
    test_type = None
    with_coverage = True
    
    if "--unit" in sys.argv:
        test_type = "unit"
    elif "--integration" in sys.argv:
        test_type = "integration"
    
    if "--no-coverage" in sys.argv:
        with_coverage = False
    
    # Run tests
    exit_code = run_tests(test_type, with_coverage)
    
    # Exit with pytest's exit code
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
