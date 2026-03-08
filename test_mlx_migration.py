from agents.llm_client import MLXClient
from agents.literature_agent import LiteratureAgent
from agents.hypothesis_agent import HypothesisAgent
from agents.circuit_agent import CircuitAgent
from agents.judge_agent import JudgeAgent
import unittest
from unittest.mock import MagicMock, patch

class TestMLXInference(unittest.TestCase):
    @patch('agents.llm_client.load')
    @patch('agents.llm_client.generate')
    def test_mlx_client_generate_json(self, mock_generate, mock_load):
        # Mock MLX client setup
        mock_load.return_value = (MagicMock(), MagicMock())
        mock_generate.return_value = '{"key": "value"}'
        
        client = MLXClient()
        result = client.generate_json("system", "user")
        
        self.assertEqual(result, {"key": "value"})
        mock_generate.assert_called()

    @patch('agents.llm_client.load')
    @patch('agents.llm_client.generate')
    def test_literature_agent_validation(self, mock_generate, mock_load):
        mock_load.return_value = (MagicMock(), MagicMock())
        # Missing "limitation"
        mock_generate.side_effect = [
            '{"paper_title": "test", "key_finding": "find", "open_question": "gap", "possible_igem_mapping": "map", "biological_system": "sys", "aging_mechanism": "mech", "method_used": "met"}',
            '{"paper_title": "test", "key_finding": "find", "open_question": "gap", "possible_igem_mapping": "map", "biological_system": "sys", "aging_mechanism": "mech", "method_used": "met", "limitation": "none"}'
        ]
        
        agent = LiteratureAgent()
        # Mocking the template file content since we are in a test
        agent.prompt_template = "Test {title} {abstract}"
        
        result = agent.analyze("title", "abstract")
        self.assertIn("limitation", result)
        self.assertIn("synbio_opportunity", result) # Check compatibility mapping
        self.assertEqual(mock_generate.call_count, 2)

if __name__ == '__main__':
    unittest.main()
