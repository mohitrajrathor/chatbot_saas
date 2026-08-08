from abc import ABC, abstractmethod
from groq import AsyncGroq
from openai import AsyncOpenAI
from app.core.config import settings


class BaseLLMProvider(ABC):
    @abstractmethod
    async def complete(self, prompt: str, system_instruction: str = "") -> str:
        """Generate LLM completion from system instruction and user prompt."""
        pass


class GroqProvider(BaseLLMProvider):
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.model = settings.LLM_MODEL
        self.client = AsyncGroq(api_key=self.api_key)

    async def complete(self, prompt: str, system_instruction: str = "") -> str:
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        response = await self.client.chat.completions.create(
            messages=messages,
            model=self.model,
            temperature=0.2,
        )
        return response.choices[0].message.content or ""


class NIMProvider(BaseLLMProvider):
    def __init__(self):
        self.base_url = settings.NIM_BASE_URL
        self.api_key = settings.NIM_API_KEY
        self.model = settings.LLM_MODEL
        self.client = AsyncOpenAI(base_url=self.base_url, api_key=self.api_key or "dummy")

    async def complete(self, prompt: str, system_instruction: str = "") -> str:
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        response = await self.client.chat.completions.create(
            messages=messages,
            model=self.model,
            temperature=0.2,
        )
        return response.choices[0].message.content or ""


_llm_provider_instance: BaseLLMProvider | None = None


def get_llm_provider() -> BaseLLMProvider:
    global _llm_provider_instance
    if _llm_provider_instance is None:
        provider_type = settings.LLM_PROVIDER.lower()
        if provider_type == "nim":
            _llm_provider_instance = NIMProvider()
        else:
            _llm_provider_instance = GroqProvider()
    return _llm_provider_instance
