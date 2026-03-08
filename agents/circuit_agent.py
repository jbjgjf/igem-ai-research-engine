from agents.literature_agent import BaseAgent
from typing import Dict, Any

class CircuitAgent(BaseAgent):
    def __init__(self):
        super().__init__("prompts/circuit_prompt.txt")

    def design(self, hypothesis: str, mechanism: str) -> Dict[str, Any]:
        user_prompt = self.prompt_template.format(hypothesis=hypothesis, mechanism=mechanism)
        required_keys = [
            "host_organism", "genetic_parts", "measurement_method", 
            "circuit_design", "expected_signal", "input_signal", 
            "output_signal", "reporter", "sensor", "mvp_version",
            "failure_points", "biosafety_concerns"
        ]
        
        for _ in range(2):
            result = self._call_llm("You are a synthetic biology circuit designer. Return JSON.", user_prompt)
            if self._validate_json(result, required_keys):
                return result
                
        raise RuntimeError("CircuitAgent failed to generate valid JSON with required keys.")
