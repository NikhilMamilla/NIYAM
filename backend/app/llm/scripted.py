from app.llm.base import LLMError, LLMResponse, Message


class ScriptedProvider:
    """Test double: replays responses in order and records every call."""

    def __init__(self, responses: list[str], model: str = "scripted", input_tokens: int = 10, output_tokens: int = 20):
        self.responses = list(responses)
        self.model = model
        self.calls: list[dict] = []
        self._usage = (input_tokens, output_tokens)

    def complete(self, system: str, messages: list[Message], *, temperature: float, max_tokens: int) -> LLMResponse:
        self.calls.append({"system": system, "messages": list(messages), "temperature": temperature,
                           "max_tokens": max_tokens})
        if len(self.calls) > len(self.responses):
            raise LLMError(f"scripted provider exhausted after {len(self.responses)} response(s)")
        return LLMResponse(self.responses[len(self.calls) - 1], self.model, *self._usage, latency_s=0.0)
