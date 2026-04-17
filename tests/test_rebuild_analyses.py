from deployment.rebuild_analyses import _clean

def test_clean_valid_floats():
    assert _clean("123") == 123.0
    assert _clean("-45.6") == -45.6
    assert _clean("  78.9  ") == 78.9
    assert _clean("0") == 0.0
    assert _clean("0.0") == 0.0

def test_clean_special_strings():
    for val in ('', '..', 'F', 'x', 'E', 'r', 'p'):
        assert _clean(val) is None
        assert _clean(f"  {val}  ") is None

def test_clean_invalid_strings():
    assert _clean("not a number") is None
    assert _clean("12.34.56") is None
