"""Gate each incremental commit on tests and a concrete example."""
import argparse
import subprocess
import sys
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("phase")
parser.add_argument("example")
args = parser.parse_args()
subprocess.run([sys.executable, "-m", "pytest", "-q"], check=True)
subprocess.run([sys.executable, "-c", args.example], check=True)
with Path("docs/development/PHASE_LOG.md").open("a", encoding="utf8") as file:
    file.write(f"\n{args.phase}: offline test suite passed; example executed successfully. See commit for implementation and tests.\n")
subprocess.run(["git", "add", "app", "tests", "scripts", "docs", "migrations", "alembic.ini", "pyproject.toml"], check=True)
subprocess.run(["git", "commit", "-m", args.phase], check=True)
