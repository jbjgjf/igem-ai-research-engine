from agents.literature_agent import BaseAgent
from typing import Dict, Any

class CircuitAgent(BaseAgent):
    def __init__(self):
        super().__init__("prompts/circuit_prompt.txt")

    def design(self, hypothesis: str, mechanism: str) -> Dict[str, Any]:
        user_prompt = self.prompt_template.format(hypothesis=hypothesis, mechanism=mechanism)
        required_keys = ["host_organism", "sensor", "genetic_circuit", "reporter", "measurement_method"]
        
        for _ in range(2):
            result = self._call_llm("You are a synthetic biology circuit designer. Return JSON.", user_prompt)
            if self._validate_json(result, required_keys):
                return result
                
        raise RuntimeError("CircuitAgent failed to generate valid JSON with required keys.")
