#!/bin/bash

set -euo pipefail

export PYTEST_ADDOPTS="--doctest-modules --junitxml=junit/test-results.xml"
export PY_IGNORE_IMPORTMISMATCH=1

source venv
poetry run pytest --collect-only -vvv
poetry run pytest -vvv
