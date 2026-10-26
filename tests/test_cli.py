"""
Integration tests for CLI.
"""

import json
import tempfile
from pathlib import Path
import pytest


@pytest.fixture
def temp_brief_file():
    brief = {
        "product": "TestCoffee",
        "audience": "coffee lovers",
        "channel": "twitter",
        "tone": "casual"
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(brief, f)
        temp_path = f.name
    
    yield temp_path
    
    Path(temp_path).unlink(missing_ok=True)


def test_cli_imports():
    from marketing_agent import cli
    assert hasattr(cli, 'main')
    assert hasattr(cli, 'load_brief_from_file')


def test_load_brief_from_file(temp_brief_file):
    from marketing_agent.cli import load_brief_from_file
    
    brief = load_brief_from_file(temp_brief_file)
    assert brief["product"] == "TestCoffee"
    assert brief["channel"] == "twitter"
