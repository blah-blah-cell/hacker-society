import sys
import unittest
from unittest.mock import patch, MagicMock
from src.wizard import install_ollama, install_vllm, run_wizard

class TestWizard(unittest.TestCase):
    @patch('src.wizard.sys.exit')
    @patch('src.wizard.input', return_value='n')
    def test_install_ollama_no_auto_yes(self, mock_input, mock_exit):
        install_ollama(auto_install=False)
        mock_input.assert_called_once()
        mock_exit.assert_called_with(1)

    @patch('src.wizard.subprocess.run')
    @patch('src.wizard.platform.system', return_value='Linux')
    @patch('src.wizard.input')
    def test_install_ollama_auto_yes(self, mock_input, mock_system, mock_run):
        install_ollama(auto_install=True)
        mock_input.assert_not_called()
        mock_run.assert_called_once()

    @patch('src.wizard.sys.exit')
    @patch('src.wizard.input', return_value='n')
    def test_install_vllm_no_auto_yes(self, mock_input, mock_exit):
        install_vllm(auto_install=False)
        mock_input.assert_called_once()
        mock_exit.assert_called_once_with(1)

    @patch('src.wizard.subprocess.run')
    @patch('src.wizard.input')
    def test_install_vllm_auto_yes(self, mock_input, mock_run):
        install_vllm(auto_install=True)
        mock_input.assert_not_called()
        mock_run.assert_called_once()

    @patch('src.wizard.subprocess.run')
    @patch('src.wizard.subprocess.Popen')
    @patch('src.wizard.detect_hardware', return_value={"os": "Linux", "arch": "x86_64", "has_nvidia": False, "vram_mb": 0, "gpu_name": "None", "recommended_profile": "4"})
    @patch('src.wizard.input')
    @patch('src.wizard.time.sleep')
    @patch.object(sys, 'argv', ['wizard.py', '--yes'])
    def test_run_wizard_auto_yes(self, mock_sleep, mock_input, mock_detect, mock_popen, mock_run):
        run_wizard()
        mock_input.assert_not_called()

if __name__ == '__main__':
    unittest.main()
