"""Static AST and runtime inspection verifying zero external dependencies in domain/."""

import ast
import sys
from pathlib import Path

ALLOWED_STDLIB_MODULES = {
    "dataclasses",
    "enum",
    "math",
    "typing",
    "sys",
    "pathlib",
    "collections",
    "itertools",
    "abc",
    "numbers",
    "copy",
}

FORBIDDEN_PACKAGES = {
    "pandas",
    "polars",
    "torch",
    "torch_geometric",
    "xgboost",
    "scipy",
    "sklearn",
    "numpy",
    "floodlight",
    "unravelsports",
    "mplbasketball",
    "skillcornerviz",
}


def test_domain_zero_external_dependencies_ast():
    """Parse all source files in src/domain/ and assert no forbidden or external imports exist."""
    domain_dir = Path(__file__).resolve().parent.parent.parent / "src" / "domain"
    py_files = list(domain_dir.glob("*.py"))
    assert len(py_files) > 0, "No domain python files found to inspect"

    for file_path in py_files:
        tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_pkg = alias.name.split(".")[0]
                    assert root_pkg not in FORBIDDEN_PACKAGES, (
                        f"Forbidden package '{root_pkg}' imported in {file_path.name}:L{node.lineno}"
                    )
                    assert root_pkg in ALLOWED_STDLIB_MODULES or root_pkg == "domain", (
                        f"External package '{root_pkg}' found in {file_path.name}:L{node.lineno}"
                    )
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root_pkg = node.module.split(".")[0]
                    assert root_pkg not in FORBIDDEN_PACKAGES, (
                        f"Forbidden package '{root_pkg}' imported in {file_path.name}:L{node.lineno}"
                    )
                    assert root_pkg in ALLOWED_STDLIB_MODULES or root_pkg == "domain", (
                        f"External package '{root_pkg}' found in {file_path.name}:L{node.lineno}"
                    )


def test_domain_zero_external_dependencies_runtime():
    """Verify loaded domain modules at runtime do not contain references to forbidden libraries."""
    domain_modules = [
        mod for name, mod in sys.modules.items()
        if name.startswith("domain") and hasattr(mod, "__file__") and mod.__file__
    ]

    for mod in domain_modules:
        for pkg in FORBIDDEN_PACKAGES:
            assert pkg not in mod.__dict__, (
                f"Forbidden package reference '{pkg}' found in namespace of {mod.__name__}"
            )
