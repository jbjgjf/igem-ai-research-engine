from agents.literature_agent import BaseAgent

class HypothesisAgent(BaseAgent):
    def __init__(self):
        super().__init__("prompts/hypothesis_prompt.txt")

    def generate(self, open_question: str) -> dict:
        user_prompt = self.prompt_template.format(open_question=open_question)
        return self._call_llm("You are a biological hypothesis generator.", user_prompt)
