from dataclasses import dataclass, field
from typing import Any, Literal, Protocol


@dataclass(frozen=True)
class Message:
    role: Literal["user", "assistant"]
    content: str


@dataclass
class LLMResponse:
    text: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_s: float
    raw: Any = field(default=None, repr=False)  # provider payload; never logged


class LLMError(RuntimeError):
    pass


class ProviderNotConfigured(LLMError):
    pass


class LLMProvider(Protocol):
    model: str

    def complete(
        self, system: str, messages: list[Message], *, temperature: float, max_tokens: int
    ) -> LLMResponse: ...
