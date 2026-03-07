from agents.literature_agent import BaseAgent

class JudgeAgent(BaseAgent):
    def __init__(self):
        super().__init__("prompts/judge_prompt.txt")

    def evaluate(self, hypothesis: str, circuit_design: str) -> dict:
        user_prompt = self.prompt_template.format(hypothesis=hypothesis, circuit_design=circuit_design)
        return self._call_llm("You are a project judge.", user_prompt)
