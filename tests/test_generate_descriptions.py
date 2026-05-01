import importlib.util
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

def load_generate_descriptions_module():
    with patch.dict(os.environ, {'OLLAMA_URL': 'http://localhost:11434/api/generate', 'OLLAMA_MODEL': 'llama3'}):
        path = Path(__file__).parent.parent / 'deployment' / 'generate_descriptions.py'
        spec = importlib.util.spec_from_file_location('generate_descriptions', path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module

def test_ollama_describe_error_handling(capsys):
    module = load_generate_descriptions_module()

    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_urlopen.side_effect = Exception("Connection refused")

        result = module.ollama_describe("<html>Content</html>", "test.html")

        assert result == ""

        captured = capsys.readouterr()
        assert "[warn] Ollama unavailable for test.html: Connection refused" in captured.out

def test_load_descriptions_exists():
    module = load_generate_descriptions_module()

    with patch('pathlib.Path.exists') as mock_exists, patch('pathlib.Path.read_text') as mock_read_text:
        mock_exists.return_value = True
        mock_read_text.return_value = '{"file1.html": "description 1", "file2.html": "description 2"}'

        result = module.load_descriptions()

        assert result == {"file1.html": "description 1", "file2.html": "description 2"}
        mock_exists.assert_called_once()
        mock_read_text.assert_called_once_with(encoding='utf-8')

def test_load_descriptions_empty():
    module = load_generate_descriptions_module()

    with patch('pathlib.Path.exists') as mock_exists:
        mock_exists.return_value = False

        result = module.load_descriptions()

        assert result == {}
        mock_exists.assert_called_once()

def test_save_descriptions():
    module = load_generate_descriptions_module()

    with patch('pathlib.Path.write_text') as mock_write_text:
        descriptions = {"file1.html": "description 1", "file2.html": "description 2"}
        module.save_descriptions(descriptions)

        expected_json = '{\n  "file1.html": "description 1",\n  "file2.html": "description 2"\n}\n'
        mock_write_text.assert_called_once_with(expected_json, encoding='utf-8')
