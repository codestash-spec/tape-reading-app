import os


def test_docs_presence():
    required = [
        "docs/PHASE_I.md",
        "docs/PHASE_II.md",
        "docs/PHASE_III.md",
        "docs/PHASE_IV.md",
        "docs/PHASE_V.md",
        "docs/PHASE_VI.md",
        "docs/PHASE_VII.md",
    ]
    for path in required:
        assert os.path.exists(path)


def test_packaging_files():
    assert os.path.exists("packaging/build_windows.ps1")
    assert os.path.exists("specs/tape_reading_app.spec")
