"""
llm_integration.py
LLM API integration layer. Supports Cohere.
Handles API calls, token tracking, retries, and output validation.
"""

import os
import time
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class LLMResponse:
    """Structured response from an LLM call."""
    content: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    template_name: str = ""
    topic: str = ""
    elapsed_seconds: float = 0.0
    metadata: dict = field(default_factory=dict)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def save(self, output_dir: str = "output") -> str:
        """Save response content to a timestamped markdown file."""
        os.makedirs(output_dir, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        safe_topic = "".join(c if c.isalnum() or c in "-_" else "_" for c in self.topic[:40])
        filename = f"{output_dir}/{timestamp}_{self.template_name}_{safe_topic}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"<!-- Generated: {time.strftime('%Y-%m-%d %H:%M:%S')} -->\n")
            f.write(f"<!-- Model: {self.model} | Tokens: {self.total_tokens} -->\n\n")
            f.write(self.content)
        print(f"[LLM] Saved output to: {filename}")
        return filename


class LLMClient:
    """
    Cohere API client with retry logic and structured output handling.
    """

    DEFAULT_MODEL = "command-r-08-2024"
    MAX_RETRIES = 3
    RETRY_DELAY = 2

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("COHERE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "COHERE_API_KEY not set. Add it to your .env file or environment."
            )
        self.model = model or os.getenv("COHERE_MODEL", self.DEFAULT_MODEL)
        self._client = None
        self._init_client()

    def _init_client(self):
        try:
            import cohere
            self._client = cohere.ClientV2(api_key=self.api_key)
            print(f"[LLM] Initialized Cohere client | Model: {self.model}")
        except ImportError:
            raise ImportError(
                "cohere package not installed. Run: pip install cohere"
            )

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        template_name: str = "",
        topic: str = "",
    ) -> LLMResponse:
        start_time = time.time()

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                print(f"[LLM] Generating content (attempt {attempt}/{self.MAX_RETRIES})...")

                response = self._client.chat(
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                )

                content = response.message.content[0].text
                elapsed = time.time() - start_time

                input_tokens = response.usage.tokens.input_tokens
                output_tokens = response.usage.tokens.output_tokens
                print(f"[LLM] Generated {output_tokens} tokens in {elapsed:.1f}s")

                return LLMResponse(
                    content=content,
                    model=self.model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    template_name=template_name,
                    topic=topic,
                    elapsed_seconds=elapsed,
                )

            except Exception as e:
                print(f"[LLM] Error on attempt {attempt}: {e}")
                if attempt < self.MAX_RETRIES:
                    print(f"[LLM] Retrying in {self.RETRY_DELAY}s...")
                    time.sleep(self.RETRY_DELAY)
                else:
                    raise RuntimeError(f"LLM generation failed after {self.MAX_RETRIES} attempts: {e}")

    def generate_with_template(
        self,
        template,
        topic: str = "",
        kb_context: str = "",
        extra_vars: Optional[dict] = None,
        **kwargs,
    ) -> LLMResponse:
        vars_dict = {"topic": topic, "kb_context": kb_context, **(extra_vars or {})}
        system_prompt, user_prompt = template.render(**vars_dict)

        return self.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            template_name=template.name,
            topic=topic,
            **kwargs,
        )

    def estimate_tokens(self, text: str) -> int:
        return len(text) // 4

    def check_context_limit(self, *texts: str, limit: int = 128_000) -> bool:
        total = sum(self.estimate_tokens(t) for t in texts)
        if total > limit:
            print(f"[LLM] WARNING: Estimated {total} tokens exceeds limit of {limit}")
            return False
        return True