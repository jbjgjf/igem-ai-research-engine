import json
from typing import Dict, Any, List
from config import settings

class BaseAgent:
    def __init__(self, prompt_path: str):
        with open(prompt_path, "r") as f:
            self.prompt_template = f.read()
        
        from agents.llm_client import MLXClient
        self.client = MLXClient()

    def _call_llm(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        return self.client.generate_json(system_prompt, user_prompt)

    def _validate_json(self, data: Dict[str, Any], required_keys: List[str]) -> bool:
        missing = [k for k in required_keys if k not in data]
        if missing:
            print(f"Validation Error: Missing keys {missing} in response.")
            return False
        return True

class LiteratureAgent(BaseAgent):
    def __init__(self):
        super().__init__("prompts/literature_prompt.txt")

    def analyze(self, title: str, abstract: str) -> Dict[str, Any]:
        user_prompt = self.prompt_template.format(title=title, abstract=abstract)
        required_keys = ["biological_question", "novelty_score", "relevance_to_aging"]
        
        # Simplified retry loop for validation at agent level
        for _ in range(2):
            result = self._call_llm("You are a literature analysis assistant. Return JSON.", user_prompt)
            if self._validate_json(result, required_keys):
                return result
        
        raise RuntimeError("LiteratureAgent failed to generate valid JSON with required keys.")
