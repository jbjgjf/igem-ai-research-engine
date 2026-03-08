import json
import logging
from typing import Any, Dict, Optional
from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from mlx_lm import load, generate
except ImportError:
    logger.warning("mlx-lm not installed. MLXClient will fail if used.")
    load = None
    generate = None

class MLXClient:
    def __init__(self):
        self.model_id = settings.MLX_MODEL_ID
        self.model = None
        self.tokenizer = None
        self._ensure_model_loaded()

    def _ensure_model_loaded(self):
        if self.model is None and load is not None:
            logger.info(f"Loading MLX model: {self.model_id}...")
            self.model, self.tokenizer = load(self.model_id)
            logger.info("Model loaded successfully.")

    def generate_json(self, system_prompt: str, user_prompt: str, retries: int = 3) -> Dict[str, Any]:
        if not self.model:
            self._ensure_model_loaded()
            if not self.model:
                raise RuntimeError("MLX model could not be loaded. Please install mlx-lm.")

        # Constructing the chat prompt format (assuming Qwen2.5/ChatML style)
        messages = [
            {"role": "system", "content": system_prompt + "\nIMPORTANT: You must return ONLY valid JSON."},
            {"role": "user", "content": user_prompt}
        ]
        
        prompt = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        for attempt in range(retries):
            try:
                response_text = generate(
                    self.model,
                    self.tokenizer,
                    prompt=prompt,
                    max_tokens=settings.MLX_MAX_TOKENS,
                    temp=settings.MLX_TEMPERATURE
                )
                
                # Attempt to extract JSON from the response
                json_data = self._parse_json(response_text)
                if json_data:
                    return json_data
                
                logger.warning(f"Attempt {attempt + 1}: Failed to parse JSON. Raw response: {response_text}")
            except Exception as e:
                logger.error(f"Attempt {attempt + 1}: Inference error: {e}")

        raise RuntimeError(f"Failed to generate valid JSON after {retries} retries.")

    def _parse_json(self, text: str) -> Optional[Dict[str, Any]]:
        # Find the first occurrences of { and last }
        try:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end != 0:
                json_str = text[start:end]
                return json.loads(json_str)
        except (ValueError, json.JSONDecodeError):
            pass
        return None
