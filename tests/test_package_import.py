"""Smoke checks for the initial package skeleton."""


def test_package_is_importable() -> None:
    import ai_stock

    assert ai_stock.__version__ == "0.1.0"
