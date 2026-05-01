import importlib.util
from pathlib import Path
from unittest.mock import patch
import sys

def load_refresh_module():
    path = Path(__file__).parent.parent / 'deployment' / 'refresh.py'
    spec = importlib.util.spec_from_file_location('refresh', path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module

def test_parse_args_defaults():
    module = load_refresh_module()

    with patch('sys.argv', ['refresh.py']):
        args = module.parse_args()

    assert args.no_push is False
    assert args.no_descriptions is False
    assert args.force_descriptions is False

def test_parse_args_no_push():
    module = load_refresh_module()

    with patch('sys.argv', ['refresh.py', '--no-push']):
        args = module.parse_args()

    assert args.no_push is True
    assert args.no_descriptions is False
    assert args.force_descriptions is False

def test_parse_args_no_descriptions():
    module = load_refresh_module()

    with patch('sys.argv', ['refresh.py', '--no-descriptions']):
        args = module.parse_args()

    assert args.no_push is False
    assert args.no_descriptions is True
    assert args.force_descriptions is False

def test_parse_args_force_descriptions():
    module = load_refresh_module()

    with patch('sys.argv', ['refresh.py', '--force-descriptions']):
        args = module.parse_args()

    assert args.no_push is False
    assert args.no_descriptions is False
    assert args.force_descriptions is True

def test_parse_args_all_flags():
    module = load_refresh_module()

    with patch('sys.argv', ['refresh.py', '--no-push', '--no-descriptions', '--force-descriptions']):
        args = module.parse_args()

    assert args.no_push is True
    assert args.no_descriptions is True
    assert args.force_descriptions is True
