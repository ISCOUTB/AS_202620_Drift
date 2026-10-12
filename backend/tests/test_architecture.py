import ast
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "app"

# Librerías de infraestructura que el núcleo no debe conocer.
FORBIDDEN_LIBRARIES = {"fastapi", "httpx", "requests", "uvicorn", "starlette"}


def _imported_modules(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name

        if isinstance(node, ast.ImportFrom) and node.module:
            yield node.module


def _violations(layer, forbidden_prefixes):
    found = []

    for path in sorted((APP / layer).rglob("*.py")):
        for module in _imported_modules(path):
            root = module.split(".")[0]

            if module.startswith(forbidden_prefixes) or root in FORBIDDEN_LIBRARIES:
                found.append(f"{path.relative_to(APP)} importa {module}")

    return found


def test_domain_depends_on_nothing_outside_the_domain():
    """Falla si el dominio se erosiona hacia aplicación o infraestructura."""

    assert _violations(
        "domain",
        ("app.application", "app.infrastructure"),
    ) == []


def test_application_does_not_depend_on_infrastructure():
    """Falla si un caso de uso importa un adaptador en lugar de un puerto."""

    assert _violations(
        "application",
        ("app.infrastructure",),
    ) == []
