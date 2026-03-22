#!/usr/bin/env python3
# scripts/setup_lexswarm.py
# One-command setup: installs deps, runs tests, launches demo
# Usage:
#   python scripts/setup_lexswarm.py              # full setup + demo
#   python scripts/setup_lexswarm.py --test-only  # just run tests
#   python scripts/setup_lexswarm.py --demo-only  # just run demo

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import subprocess
import argparse

REQUIRED_PACKAGES = [
    "httpx",
    "langdetect",
    "transformers",
    "torch",
    "fastapi",
    "uvicorn",
    "pydantic",
    "python-telegram-bot",
    "python-dotenv",
    "pyyaml",
    "loguru",
    "sentence-transformers",
    "pytest",
    "pytest-asyncio",
]

def install_deps():
    print("Installing LEXSWARM dependencies...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install"] + REQUIRED_PACKAGES + ["--quiet"],
        capture_output=False,
    )
    if result.returncode == 0:
        print("All dependencies installed.")
    else:
        print("Some packages failed. Try installing manually:")
        print(f"pip install {' '.join(REQUIRED_PACKAGES)}")

def run_tests():
    print("\nRunning LEXSWARM test suite...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short",
         "--ignore=tests/integration"],  # skip integration in quick mode
        env={**os.environ, "PYTHONPATH": os.getcwd()},
    )
    if result.returncode == 0:
        print("\nAll tests passed.")
    else:
        print("\nSome tests failed — check output above.")
    return result.returncode == 0

def run_demo():
    import asyncio
    from scripts.run_lexswarm import run_case

    print("\nRunning LEXSWARM demo case...")
    case_description = (
        "My landlord changed the locks tonight and threw my belongings outside in Karachi, Pakistan. "
        "I have three children and nowhere to sleep."
    )
    print(f"Demo case: {case_description}\n")
    asyncio.run(run_case(case_description))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LEXSWARM Setup")
    parser.add_argument("--test-only", action="store_true")
    parser.add_argument("--demo-only", action="store_true")
    parser.add_argument("--skip-install", action="store_true")
    args = parser.parse_args()

    if args.demo_only:
        run_demo()
    elif args.test_only:
        run_tests()
    else:
        if not args.skip_install:
            install_deps()
        tests_passed = run_tests()
        if tests_passed:
            run_demo()
        else:
            print("\nFix failing tests before running demo.")
