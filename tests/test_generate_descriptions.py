import importlib.util
import os
from pathlib import Path
from unittest.mock import patch

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
