import openai
import json
from config import settings

class BaseAgent:
    def __init__(self, prompt_path: str):
        with open(prompt_path, "r") as f:
            self.prompt_template = f.read()
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

    def _call_llm(self, system_prompt: str, user_prompt: str) -> dict:
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)

class LiteratureAgent(BaseAgent):
    def __init__(self):
        super().__init__("prompts/literature_prompt.txt")

    def analyze(self, title: str, abstract: str) -> dict:
        user_prompt = self.prompt_template.format(title=title, abstract=abstract)
        return self._call_llm("You are a literature analysis assistant.", user_prompt)
