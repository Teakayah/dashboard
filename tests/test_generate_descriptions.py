import importlib.util
import os
import runpy
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def load_generate_descriptions_module():
    with patch.dict(os.environ, {'OLLAMA_URL': 'http://localhost:11434/api/generate', 'OLLAMA_MODEL': 'llama3'}):
        path = Path(__file__).parent.parent / 'deployment' / 'generate_descriptions.py'
        spec = importlib.util.spec_from_file_location('deployment.generate_descriptions', path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module

def test_ollama_describe_insecure_url():
    module = load_generate_descriptions_module()

    with patch.dict(os.environ, {'OLLAMA_URL': 'ftp://localhost:11434'}):
        # We need to re-load or manually update the module's OLLAMA_URL
        # since it was set at module-load time.
        module.OLLAMA_URL = 'ftp://localhost:11434'
        with pytest.raises(ValueError, match="Insecure URL scheme in OLLAMA_URL"):
            module.ollama_describe("<html>Content</html>", "test.html")

def test_ollama_describe_error_handling(capsys):
    module = load_generate_descriptions_module()

    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_urlopen.side_effect = Exception("Connection refused")

        result = module.ollama_describe("<html>Content</html>", "test.html")

        assert result == ""

        captured = capsys.readouterr()
        assert "[warn] Ollama unavailable for test.html: Connection refused" in captured.out

def test_load_dotenv_success(tmp_path):
    module = load_generate_descriptions_module()
    env_content = """
# This is a comment
OLLAMA_URL = http://test-url:11434
OLLAMA_MODEL=test-model

EMPTY_VAR=
NO_EQUALS_LINE
    """
    env_file = tmp_path / '.env'
    env_file.write_text(env_content, encoding='utf-8')

    with patch.object(module, 'ROOT', tmp_path), patch.dict(os.environ, clear=True):
        module._load_dotenv()
        assert os.environ.get('OLLAMA_URL') == 'http://test-url:11434'
        assert os.environ.get('OLLAMA_MODEL') == 'test-model'
        assert os.environ.get('EMPTY_VAR') == ''
        assert 'NO_EQUALS_LINE' not in os.environ

def test_load_dotenv_no_overwrite(tmp_path):
    module = load_generate_descriptions_module()
    env_content = "OLLAMA_URL=http://new-url:11434\n"
    env_file = tmp_path / '.env'
    env_file.write_text(env_content, encoding='utf-8')

    with patch.object(module, 'ROOT', tmp_path), patch.dict(os.environ, {'OLLAMA_URL': 'http://old-url:11434'}, clear=True):
        module._load_dotenv()
        assert os.environ.get('OLLAMA_URL') == 'http://old-url:11434'

def test_load_dotenv_missing_file(tmp_path):
    module = load_generate_descriptions_module()
    with patch.object(module, 'ROOT', tmp_path), patch.dict(os.environ, clear=True):
        module._load_dotenv()
        # Should not raise any errors, just return quietly
        assert 'OLLAMA_URL' not in os.environ

def test_load_descriptions_existing(tmp_path):
    module = load_generate_descriptions_module()
    desc_file = tmp_path / 'descriptions.json'
    desc_file.write_text('{"test.html": "A test description"}', encoding='utf-8')

    with patch.object(module, 'DESCRIPTIONS_FILE', desc_file):
        result = module.load_descriptions()
        assert result == {"test.html": "A test description"}

def test_load_descriptions_missing(tmp_path):
    module = load_generate_descriptions_module()
    desc_file = tmp_path / 'descriptions.json'

    with patch.object(module, 'DESCRIPTIONS_FILE', desc_file):
        result = module.load_descriptions()
        assert result == {}

def test_save_descriptions(tmp_path):
    module = load_generate_descriptions_module()
    desc_file = tmp_path / 'descriptions.json'

    with patch.object(module, 'DESCRIPTIONS_FILE', desc_file):
        module.save_descriptions({"test.html": "A test description"})

        content = desc_file.read_text(encoding='utf-8')
        assert '"test.html": "A test description"' in content
        assert content.endswith('\n')

def test_ollama_describe_success_short():
    module = load_generate_descriptions_module()

    mock_resp = MagicMock()
    mock_resp.read.return_value = b'{"response": "A short summary."}'

    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        result = module.ollama_describe("<html>Content</html>", "test.html")
        assert result == "A short summary."

def test_ollama_describe_success_long():
    module = load_generate_descriptions_module()

    long_desc = "A" * 150
    mock_resp = MagicMock()
    mock_resp.read.return_value = f'{{"response": "{long_desc}"}}'.encode()

    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        result = module.ollama_describe("<html>Content</html>", "test.html")
        assert len(result) == 118 # 117 chars + ellipsis
        assert result.endswith('…')
        assert result.startswith("A" * 117)

def test_parse_args_defaults():
    module = load_generate_descriptions_module()

    with patch('sys.argv', ['generate_descriptions.py']):
        args = module.parse_args()
        assert args.force is False
        assert args.file is None

def test_parse_args_flags():
    module = load_generate_descriptions_module()

    with patch('sys.argv', ['generate_descriptions.py', '--force', '--file', 'my_analysis.html']):
        args = module.parse_args()
        assert args.force is True
        assert args.file == 'my_analysis.html'

def test_main_execution(tmp_path, capsys):
    module = load_generate_descriptions_module()

    # 1. index.html (should be excluded)
    index_file = tmp_path / 'index.html'
    index_file.write_text('<html>Index</html>', encoding='utf-8')

    # 2. existing.html (has description, no force -> skipped)
    existing_file = tmp_path / 'existing.html'
    existing_file.write_text('<html>Existing</html>', encoding='utf-8')

    # 3. new.html (no description -> processed)
    new_file = tmp_path / 'new.html'
    new_file.write_text('<html>New</html>', encoding='utf-8')

    # 4. new_empty.html (ollama fails -> returns '')
    empty_file = tmp_path / 'new_empty.html'
    empty_file.write_text('<html>Empty</html>', encoding='utf-8')

    desc_json_file = tmp_path / 'descriptions.json'
    initial_descriptions = {'existing.html': 'Already described'}

    def mock_ollama(content, filename):
        if filename == 'new.html':
            return 'A generated description'
        return ''

    with patch.object(module, 'ROOT', tmp_path), \
         patch.object(module, 'DESCRIPTIONS_FILE', desc_json_file), \
         patch('sys.argv', ['generate_descriptions.py']), \
         patch.object(module, 'load_descriptions', return_value=initial_descriptions), \
         patch.object(module, 'save_descriptions') as mock_save, \
         patch.object(module, 'ollama_describe', side_effect=mock_ollama):

        module.main()

        # Verify save_descriptions was called with the updated dict
        mock_save.assert_called_once()
        saved_dict = mock_save.call_args[0][0]

        assert 'existing.html' in saved_dict
        assert saved_dict['existing.html'] == 'Already described'
        assert 'new.html' in saved_dict
        assert saved_dict['new.html'] == 'A generated description'
        assert 'new_empty.html' not in saved_dict
        assert 'index.html' not in saved_dict

        captured = capsys.readouterr()
        assert '[skip] index.html' not in captured.out # It continues implicitly before printing skip
        assert '[skip] existing.html already has a description' in captured.out
        assert 'Generating description for new.html' in captured.out
        assert '→ A generated description' in captured.out
        assert 'Generating description for new_empty.html' in captured.out
        assert '→ (no description generated)' in captured.out

def test_main_with_file_arg_and_force(tmp_path, capsys):
    module = load_generate_descriptions_module()

    target_file = tmp_path / 'target.html'
    target_file.write_text('<html>Target</html>', encoding='utf-8')

    desc_json_file = tmp_path / 'descriptions.json'
    initial_descriptions = {'target.html': 'Old description'}

    with patch.object(module, 'ROOT', tmp_path), \
         patch.object(module, 'DESCRIPTIONS_FILE', desc_json_file), \
         patch('sys.argv', ['generate_descriptions.py', '--file', 'target.html', '--force']), \
         patch.object(module, 'load_descriptions', return_value=initial_descriptions), \
         patch.object(module, 'save_descriptions') as mock_save, \
         patch.object(module, 'ollama_describe', return_value='Forced new description'):

        module.main()

        mock_save.assert_called_once()
        saved_dict = mock_save.call_args[0][0]

        assert saved_dict['target.html'] == 'Forced new description'

def test_main_missing_file(tmp_path, capsys):
    module = load_generate_descriptions_module()

    desc_json_file = tmp_path / 'descriptions.json'
    initial_descriptions = {}

    with patch.object(module, 'ROOT', tmp_path), \
         patch.object(module, 'DESCRIPTIONS_FILE', desc_json_file), \
         patch('sys.argv', ['generate_descriptions.py', '--file', 'missing.html']), \
         patch.object(module, 'load_descriptions', return_value=initial_descriptions), \
         patch.object(module, 'save_descriptions'):

        module.main()

        captured = capsys.readouterr()
        assert '[skip] missing.html not found' in captured.out

def test_missing_env_vars_exits():
    path = Path('deployment/generate_descriptions.py').resolve()

    # We must patch os.environ so that the module-level sys.exit triggers
    # and we must catch the SystemExit exception
    with patch.dict(os.environ, clear=True), \
         patch('sys.exit', side_effect=SystemExit) as mock_exit:
        with pytest.raises(SystemExit):
            runpy.run_path(str(path))

        mock_exit.assert_called_once()
        assert "OLLAMA_URL" in mock_exit.call_args[0][0]

def test_main_block():
    path = Path('deployment/generate_descriptions.py').resolve()

    # Provide env vars so it doesn't fail at module level
    with patch.dict(os.environ, {'OLLAMA_URL': 'test', 'OLLAMA_MODEL': 'test'}):
        # We patch sys.argv and underlying functions called by main()
        with patch('sys.argv', ['generate_descriptions.py']), \
             patch('pathlib.Path.glob', return_value=[]) as mock_glob, \
             patch('pathlib.Path.write_text'), \
             patch('pathlib.Path.exists', return_value=False):

            runpy.run_path(str(path), run_name='__main__')

            # If main() was called, glob should have been called
            mock_glob.assert_called_once_with('*.html')
