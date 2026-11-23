from fastapi.testclient import TestClient

from app.infrastructure.code_fingerprint import code_fingerprint, fingerprint_of
from app.main import app

client = TestClient(app)


def test_health_publishes_the_fingerprint_of_the_running_code():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "code_fingerprint": code_fingerprint(),
    }


def test_the_same_code_has_the_same_fingerprint_on_windows_and_linux():
    linux = [("main.py", b"a = 1\nb = 2\n"), ("otro.py", b"c = 3\n")]
    windows = [("otro.py", b"c = 3\r\n"), ("main.py", b"a = 1\r\nb = 2\r\n")]

    assert fingerprint_of(linux) == fingerprint_of(windows)


def test_a_code_change_changes_the_fingerprint():
    assert fingerprint_of([("main.py", b"a = 1\n")]) != fingerprint_of(
        [("main.py", b"a = 2\n")]
    )


def test_a_renamed_file_changes_the_fingerprint():
    assert fingerprint_of([("uno.py", b"a = 1\n")]) != fingerprint_of(
        [("dos.py", b"a = 1\n")]
    )
