from agents.literature_agent import BaseAgent
from typing import Dict, Any

class HypothesisAgent(BaseAgent):
    def __init__(self):
        super().__init__("prompts/hypothesis_prompt.txt")

    def generate(self, open_question: str) -> Dict[str, Any]:
        user_prompt = self.prompt_template.format(open_question=open_question)
        required_keys = ["observation", "hypothesis", "mechanism", "prediction"]
        
        for _ in range(2):
            result = self._call_llm("You are a biological hypothesis generator. Return JSON.", user_prompt)
            if self._validate_json(result, required_keys):
                return result
                
        raise RuntimeError("HypothesisAgent failed to generate valid JSON with required keys.")
