import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def test_ui_imports():
    # PySide6 must be importable
    import PySide6  # noqa: F401
    from ui.main_window import InstitutionalMainWindow  # noqa: F401
    from ui.app import main  # noqa: F401

    assert callable(main)
    assert InstitutionalMainWindow is not None

