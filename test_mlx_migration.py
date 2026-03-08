import json
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
        
        full_valid_response = json.dumps({
            "paper_title": "test", "key_finding": "find", "open_question": "gap", 
            "possible_igem_mapping": "map", "biological_system": "sys", 
            "aging_mechanism": ["mech"], "method_used": ["met"], "limitation": "none",
            "aging_relevance": "high", "alternative_interpretation": "alt",
            "confidence": 0.9, "measurement_readout": "read", "observation": "obs",
            "raw_extraction": "raw", "why_unresolved": "why"
        })
        
        mock_generate.side_effect = [
            '{"paper_title": "incomplete"}', # Failure 1
            full_valid_response
        ]
        
        agent = LiteratureAgent()
        agent.prompt_template = "Test {title} {abstract}"
        
        result = agent.analyze("title", "abstract")
        self.assertEqual(result["confidence"], 0.9)
        self.assertEqual(mock_generate.call_count, 2)

    @patch('agents.llm_client.load')
    @patch('agents.llm_client.generate')
    def test_circuit_agent_validation(self, mock_generate, mock_load):
        mock_load.return_value = (MagicMock(), MagicMock())
        
        full_circuit_response = json.dumps({
            "host_organism": "E. coli", "genetic_parts": "parts", "measurement_method": "method",
            "circuit_design": "design", "expected_signal": "signal", "input_signal": "in",
            "output_signal": "out", "reporter": "GFP", "sensor": "LuxR", "mvp_version": "v1",
            "failure_points": "none", "biosafety_concerns": "none"
        })
        
        mock_generate.return_value = full_circuit_response
        
        agent = CircuitAgent()
        agent.prompt_template = "Test {hypothesis} {mechanism}"
        
        result = agent.design("hyp", "mech")
        self.assertEqual(result["host_organism"], "E. coli")

if __name__ == '__main__':
    unittest.main()
