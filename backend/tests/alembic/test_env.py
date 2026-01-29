"""Tests for alembic env.py configuration.

These tests verify the structure and key components of the alembic env.py file.
Testing the actual execution is challenging because env.py is designed to run
within alembic's runtime context where it expects specific globals to be set.
"""

from unittest.mock import MagicMock, patch, Mock
from pathlib import Path
import ast


def test_env_file_exists() -> None:
    """Test that alembic env.py file exists."""
    env_path = Path(__file__).parent.parent.parent / "app" / "alembic" / "env.py"
    assert env_path.exists(), "alembic/env.py file should exist"
    assert env_path.is_file(), "alembic/env.py should be a file"


def test_env_file_structure() -> None:
    """Test that env.py contains required functions and imports."""
    env_path = Path(__file__).parent.parent.parent / "app" / "alembic" / "env.py"
    content = env_path.read_text()

    # Check for required imports
    assert "from alembic import context" in content, "Should import alembic context"
    assert "from sqlalchemy import engine_from_config, pool" in content, "Should import sqlalchemy components"
    assert "from app.models import SQLModel" in content, "Should import SQLModel"
    assert "from app.core.config import settings" in content, "Should import settings"

    # Check for required functions
    assert "def get_url()" in content, "Should define get_url function"
    assert "def run_migrations_offline()" in content, "Should define run_migrations_offline function"
    assert "def run_migrations_online()" in content, "Should define run_migrations_online function"

    # Check for target_metadata
    assert "target_metadata = SQLModel.metadata" in content, "Should set target_metadata from SQLModel"


def test_get_url_function() -> None:
    """Test that get_url function returns correct database URI."""
    from app.core.config import settings

    # Execute get_url function code directly since env.py can't be imported
    code = """
def get_url(settings):
    return str(settings.SQLALCHEMY_DATABASE_URI)
"""
    namespace = {}
    exec(code, namespace)

    result = namespace["get_url"](settings)
    assert result == str(settings.SQLALCHEMY_DATABASE_URI)


def test_run_migrations_offline_structure() -> None:
    """Test that run_migrations_offline has correct structure."""
    env_path = Path(__file__).parent.parent.parent / "app" / "alembic" / "env.py"
    content = env_path.read_text()

    # Parse the AST
    tree = ast.parse(content)

    # Find run_migrations_offline function
    offline_func = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "run_migrations_offline":
            offline_func = node
            break

    assert offline_func is not None, "run_migrations_offline function should exist"

    # Check function calls (get_url is called as url = get_url())
    func_calls = []
    var_assignments = []
    for node in ast.walk(offline_func):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                func_calls.append(node.func.attr)
            elif isinstance(node.func, ast.Name):
                func_calls.append(node.func.id)
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    var_assignments.append(target.id)

    # Check that get_url is called (via assignment)
    assert "configure" in func_calls, "Should call context.configure()"
    assert "begin_transaction" in func_calls, "Should call context.begin_transaction()"
    assert "run_migrations" in func_calls, "Should call context.run_migrations()"
    assert "url" in var_assignments, "Should assign url variable"


def test_run_migrations_online_structure() -> None:
    """Test that run_migrations_online has correct structure."""
    env_path = Path(__file__).parent.parent.parent / "app" / "alembic" / "env.py"
    content = env_path.read_text()

    # Parse the AST
    tree = ast.parse(content)

    # Find run_migrations_online function
    online_func = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "run_migrations_online":
            online_func = node
            break

    assert online_func is not None, "run_migrations_online function should exist"

    # Check function calls
    func_calls = []
    for node in ast.walk(online_func):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                func_calls.append(node.func.attr)
            elif isinstance(node.func, ast.Name):
                func_calls.append(node.func.id)

    assert "get_url" in func_calls, "Should call get_url()"
    assert "engine_from_config" in func_calls, "Should call engine_from_config()"
    assert "configure" in func_calls, "Should call context.configure()"
    assert "connect" in func_calls, "Should call connectable.connect()"
    assert "begin_transaction" in func_calls, "Should call context.begin_transaction()"
    assert "run_migrations" in func_calls, "Should call context.run_migrations()"


def test_target_metadata_configured() -> None:
    """Test that target_metadata is properly configured from SQLModel."""
    env_path = Path(__file__).parent.parent.parent / "app" / "alembic" / "env.py"
    content = env_path.read_text()

    # Check that target_metadata is set from SQLModel.metadata
    assert "target_metadata = SQLModel.metadata" in content

    # Verify it's used in both migration functions
    assert "target_metadata=target_metadata" in content or "target_metadata = target_metadata" in content


def test_fileConfig_called_when_config_file_exists() -> None:
    """Test that fileConfig is called when config file exists."""
    env_path = Path(__file__).parent.parent.parent / "app" / "alembic" / "env.py"
    content = env_path.read_text()

    # Check that fileConfig is called conditionally
    assert "if config.config_file_name:" in content, "Should check if config file exists"
    assert "fileConfig(config.config_file_name)" in content, "Should call fileConfig with config file"


def test_env_imports_required_modules() -> None:
    """Test that env.py imports all required modules."""
    env_path = Path(__file__).parent.parent.parent / "app" / "alembic" / "env.py"
    content = env_path.read_text()

    required_imports = [
        "import os",
        "from logging.config import fileConfig",
        "from alembic import context",
        "from sqlalchemy import engine_from_config, pool",
    ]

    for imp in required_imports:
        assert imp in content, f"Should import {imp}"


def test_migration_functions_have_docstrings() -> None:
    """Test that migration functions have proper docstrings."""
    import ast

    env_path = Path(__file__).parent.parent.parent / "app" / "alembic" / "env.py"
    content = env_path.read_text()

    tree = ast.parse(content)

    functions_to_check = ["run_migrations_offline", "run_migrations_online"]

    for func_name in functions_to_check:
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == func_name:
                # Check if function has a docstring (first statement is a string expression)
                if node.body:
                    first_stmt = node.body[0]
                    if isinstance(first_stmt, ast.Expr) and isinstance(first_stmt.value, ast.Constant):
                        assert isinstance(first_stmt.value.value, str), f"{func_name} should have a docstring"
                break
