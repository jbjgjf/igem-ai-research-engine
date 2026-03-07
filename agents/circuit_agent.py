from agents.literature_agent import BaseAgent

class CircuitAgent(BaseAgent):
    def __init__(self):
        super().__init__("prompts/circuit_prompt.txt")

    def design(self, hypothesis: str, mechanism: str) -> dict:
        user_prompt = self.prompt_template.format(hypothesis=hypothesis, mechanism=mechanism)
        return self._call_llm("You are a synthetic biology circuit designer.", user_prompt)
