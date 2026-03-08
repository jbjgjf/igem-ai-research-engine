from agents.literature_agent import BaseAgent
from typing import Dict, Any

class BiologyCriticAgent(BaseAgent):
    def __init__(self):
        super().__init__("prompts/biology_critic_prompt.txt")

    def evaluate(self, hypothesis: str, mechanism: str, circuit_design: str, readout: str) -> Dict[str, Any]:
        user_prompt = self.prompt_template.format(
            hypothesis=hypothesis,
            mechanism=mechanism,
            circuit_design=circuit_design,
            readout=readout
        )
        
        required_keys = [
            "critic_verdict", "biological_plausibility_score", 
            "experimental_feasibility_score", "main_scientific_risk",
            "host_compatibility", "measurement_risk", 
            "hallucination_risk", "minimum_salvage_plan", "critic_comments"
        ]
        
        for _ in range(2):
            result = self._call_llm(
                "You are a Biology Critic. Evaluate the scientific merit and plausibility of synthetic biology ideas. Return JSON.", 
                user_prompt
            )
            if self._validate_json(result, required_keys):
                return result
                
        raise RuntimeError("BiologyCriticAgent failed to generate valid JSON with required keys.")
