import re
from pathlib import Path
from deployment.config import (
    ROOT,
    SRC,
    SITE_URL,
    TABLES,
    OUR_IDS,
    EXTRACTION_CONFIGS,
    ACCENT_COLORS,
    LIBRARY_PATTERNS
)

def test_paths():
    """Test that ROOT and SRC are valid Path objects and SRC is derived from ROOT."""
    assert isinstance(ROOT, Path)
    assert isinstance(SRC, Path)
    assert SRC == ROOT / 'source' / 'Stat Can'

def test_site_url():
    """Test that SITE_URL is a valid URL string."""
    assert isinstance(SITE_URL, str)
    assert SITE_URL.startswith("http")

def test_tables():
    """Test the TABLES registry for expected structure."""
    assert isinstance(TABLES, list)
    assert len(TABLES) > 0
    for table in TABLES:
        assert 'id' in table
        assert isinstance(table['id'], str)
        assert 'path' in table
        assert isinstance(table['path'], Path)
        assert 'desc' in table
        assert isinstance(table['desc'], str)

def test_our_ids():
    """Test that OUR_IDS is a set matching the IDs in TABLES."""
    assert isinstance(OUR_IDS, set)
    expected_ids = {t['id'] for t in TABLES}
    assert OUR_IDS == expected_ids

def test_extraction_configs():
    """Test EXTRACTION_CONFIGS matches OUR_IDS and has the correct structure."""
    assert isinstance(EXTRACTION_CONFIGS, dict)

    # EXTRACTION_CONFIGS doesn't necessarily have to match ALL OUR_IDS,
    # but the IDs present in EXTRACTION_CONFIGS should exist in OUR_IDS
    for config_id in EXTRACTION_CONFIGS:
        assert config_id in OUR_IDS

    for config_id, config_data in EXTRACTION_CONFIGS.items():
        assert isinstance(config_data, dict)
        # Verify valid top-level keys for extraction configs
        valid_keys = {'default_filters', 'variants', 'measures'}
        for key in config_data:
            assert key in valid_keys

        if 'default_filters' in config_data:
            assert isinstance(config_data['default_filters'], dict)
        if 'variants' in config_data:
            assert isinstance(config_data['variants'], dict)
            for variant_name, variant_filters in config_data['variants'].items():
                assert isinstance(variant_name, str)
                assert isinstance(variant_filters, dict)
        if 'measures' in config_data:
            assert isinstance(config_data['measures'], list)

def test_accent_colors():
    """Test ACCENT_COLORS is a list of valid hex strings."""
    assert isinstance(ACCENT_COLORS, list)
    assert len(ACCENT_COLORS) > 0
    hex_color_pattern = re.compile(r'^#[0-9a-fA-F]{6}$')
    for color in ACCENT_COLORS:
        assert hex_color_pattern.match(color)

def test_library_patterns():
    """Test LIBRARY_PATTERNS are valid regular expressions."""
    assert isinstance(LIBRARY_PATTERNS, dict)
    assert len(LIBRARY_PATTERNS) > 0
    for library_name, pattern in LIBRARY_PATTERNS.items():
        assert isinstance(library_name, str)
        # Ensure it compiles without error
        re.compile(pattern)
