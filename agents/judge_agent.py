from agents.literature_agent import BaseAgent
from typing import Dict, Any

class JudgeAgent(BaseAgent):
    def __init__(self):
        super().__init__("prompts/judge_prompt.txt")

    def evaluate(self, hypothesis: str, circuit_design: str) -> Dict[str, Any]:
        user_prompt = self.prompt_template.format(hypothesis=hypothesis, circuit_design=circuit_design)
        required_keys = ["feasibility_score", "novelty_score", "impact_score", "justification"]
        
        for _ in range(2):
            result = self._call_llm("You are a project judge. Return JSON.", user_prompt)
            if self._validate_json(result, required_keys):
                return result
                
        raise RuntimeError("JudgeAgent failed to generate valid JSON with required keys.")
