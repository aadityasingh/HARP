"""
A unified class for representing responses from the different LLM APIs.

NOTE: this Response class only supports the intersection of the different
API responses. We always want to store the original raw responses (usually
using `.to_dict()` or equivalent), but this offers an easier way to access
common parts of responses, like the generated text or finish reason.
"""

from __future__ import annotations

from typing import Any

from attrs import Attribute, define, field

from eval.enums import FinishReason, ModelAPI


@define
class Usage:
    input_tokens: int
    output_tokens: int
    reasoning_tokens: int | None = field(default=0)
    # cache_creation_input_tokens: int | None = field(default=None)
    # cache_read_input_tokens: int | None = field(default=None)

    def to_dict(self) -> dict[str, Any]:
        d = {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
        }

        if self.reasoning_tokens is not None:
            d["reasoning_tokens"] = self.reasoning_tokens

        # if self.cache_creation_input_tokens is not None:
        #     d["cache_creation_input_tokens"] = self.cache_creation_input_tokens

        # if self.cache_read_input_tokens is not None:
        #     d["cache_read_input_tokens"] = self.cache_read_input_tokens

        return d


@define
class ModelCompletion:
    index: int
    completion: str | None
    finish_reason: FinishReason
    role: str
    # TODO logprobs?


@define
class ModelResponse:
    completions: ModelCompletion

    api: ModelAPI
    model: str

    usage: Usage

    @classmethod
    def from_openai_response(cls, resp: dict[str, Any]) -> ModelResponse:
        completions = []
        for cand in resp["choices"]:
            completions.append(
                ModelCompletion(
                    index=cand["index"],
                    completion=cand["message"]["content"],
                    finish_reason=FinishReason.from_openai_reason(cand["finish_reason"]),
                    role=cand["message"]["role"],
                )
            )
        
        usage = Usage(
            input_tokens=resp["usage"]["prompt_tokens"],
            output_tokens=resp["usage"]["completion_tokens"],
            reasoning_tokens=resp["usage"]["completion_tokens_details"]["reasoning_tokens"],
        )

        return cls(
            completions=completions,
            api=ModelAPI.OPENAI,
            model=resp["model"],
            usage=usage,
        )
    
    @classmethod
    def from_anthropic_response(cls, resp: dict[str, Any]) -> ModelResponse:
        completions = []
        input_tokens = 0
        output_tokens = 0
        for i, cand in enumerate(resp["candidates"]):
            completions.append(
                ModelCompletion(
                    index=i,
                    completion=cand["content"][0]["text"],
                    finish_reason=FinishReason.from_anthropic_reason(cand["stop_reason"]),
                    role=cand["role"],
                )
            )

            input_tokens += cand["usage"]["input_tokens"]
            output_tokens += cand["usage"]["output_tokens"]
        
        usage = Usage(input_tokens=input_tokens, output_tokens=output_tokens)

        return cls(
            completions=completions,
            api=ModelAPI.ANTHROPIC,
            model=resp["model"],
            usage=usage,
        )
    
    @classmethod
    def from_anthropic_raw_response(cls, resp: dict[str, Any]) -> ModelResponse:        
        completions = [
            ModelCompletion(
                index=0,
                completion=resp["content"][0]["text"],
                finish_reason=FinishReason.from_anthropic_reason(resp["stop_reason"]),
                role=resp["role"],
            )
        ]

        input_tokens = resp["usage"]["input_tokens"]
        output_tokens = resp["usage"]["output_tokens"]
        
        usage = Usage(input_tokens=input_tokens, output_tokens=output_tokens)

        return cls(
            completions=completions,
            api=ModelAPI.ANTHROPIC,
            model=resp["model"],
            usage=usage,
        )

    @classmethod
    def from_gemini_response(cls, resp: dict[str, Any]) -> ModelResponse:
        completions = []
        for i, cand in enumerate(resp["candidates"]):
            try:
                text: str = cand["content"]["parts"][0]["text"]
                role: str = cand["content"]["role"]
                if role == "model":
                    role = "assistant"
            except KeyError:
                text = None
                role = None
            
            completions.append(
                ModelCompletion(
                    index=i,
                    completion=text,
                    finish_reason=FinishReason.from_google_reason(cand["finish_reason"]),
                    role=role,
                )
            )

        usage = Usage(
            input_tokens=resp["usage_metadata"].get("prompt_token_count", 0),
            output_tokens=resp["usage_metadata"].get("candidates_token_count", 0),
        )

        return cls(
            completions=completions,
            api=ModelAPI.GOOGLE,
            model=resp["model"],
            usage=usage,
        )

    @classmethod
    def from_gemini_html_response(cls, resp: dict[str, Any]) -> ModelResponse:
        completions = []
        for i, cand in enumerate(resp["candidates"]):
            try:
                text: str = cand["content"]["parts"][0]["text"]
                role: str = cand["content"]["role"]
                if role == "model":
                    role = "assistant"
            except KeyError:
                text = None
                role = None
            
            completions.append(
                ModelCompletion(
                    index=i,
                    completion=text,
                    finish_reason=FinishReason.from_google_reason(cand["finishReason"]),
                    role=role,
                )
            )

        usage = Usage(
            input_tokens=resp["usageMetadata"].get("promptTokenCount", 0),
            output_tokens=resp["usageMetadata"].get("candidatesTokenCount", 0),
        )

        return cls(
            completions=completions,
            api=ModelAPI.GOOGLE,
            model=resp["modelVersion"].split("@")[0],
            usage=usage,
        )

    @classmethod
    def from_together_response(cls, resp: dict[str, Any]) -> ModelResponse:
        # TODO: have to make sure this actually works
        completions = []
        for cand in resp["choices"]:
            completions.append(
                ModelCompletion(
                    index=cand["index"],
                    completion=cand["message"]["content"],
                    finish_reason=FinishReason.from_together_reason(cand["finish_reason"]),
                    role=cand["message"]["role"]
                )
            )
        
        usage = Usage(
            input_tokens=resp["usage"].get("prompt_tokens", 0),
            output_tokens=resp["usage"].get("completion_tokens", 0),
        )

        return cls(
            completions=completions,
            api=ModelAPI.TOGETHER,
            model=resp["model"],
            usage=usage,
        )

    @classmethod
    def from_response(cls, resp: dict[str, Any], api: ModelAPI, use_batch_api: bool = False) -> ModelResponse:
        match api:
            case ModelAPI.OPENAI:
                return cls.from_openai_response(resp)
            case ModelAPI.ANTHROPIC:
                if use_batch_api:
                    return cls.from_anthropic_raw_response(resp)
                else:
                    return cls.from_anthropic_response(resp)
            case ModelAPI.GOOGLE:
                if use_batch_api:
                    return cls.from_gemini_html_response(resp)
                else:
                    return cls.from_gemini_response(resp)
            case ModelAPI.TOGETHER:
                return cls.from_together_response(resp)
            case _:
                raise NotImplementedError(f"Got unknown api {api}")
