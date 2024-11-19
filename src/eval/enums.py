"""
Enums for eval functions
"""

from __future__ import annotations

from enum import Enum

from vertexai.generative_models import FinishReason as GoogleFinishReason


class ModelAPI(str, Enum):
    """API used"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    TOGETHER = "together"


class FinishReason(str, Enum):
    STOP = "stop"  # result hit a EOS or a stop sequence
    LENGTH = "length"  # hit max tokens
    TOOL_CALL = "tool_call"  # model invoked one or more tools
    
    # openai specific
    CONTENT_FILTER = "content_filter"  # omitted content due to filter
    
    # together api specific
    ERROR = "error"

    # google specific
    SAFETY = "safety"
    COPYRIGHT = "copyright"
    BLOCKLIST = "blocklist"
    PROHIBITED_CONTENT = "prohibited"
    SPII = "spii"
    TOOL_CALL_ERROR = "tool_call_error"
    OTHER = "other"
    UNSPECIFIED = "unspecified"

    @classmethod
    def from_openai_reason(cls, reason: str) -> FinishReason:
        match reason:
            case "stop":
                return cls.STOP
            case "length":
                return cls.LENGTH
            case "tool_calls":
                return cls.TOOL_CALL
            case "content_filter":
                return cls.CONTENT_FILTER
            case _:
                raise NotImplementedError(f"Got unknown finish reason {reason}")
    
    @classmethod
    def from_anthropic_reason(cls, reason: str) -> FinishReason:
        match reason:
            case "end_turn" | "stop_sequence":
                return cls.STOP
            case "max_tokens":
                return cls.LENGTH
            case "tool_use":
                return cls.TOOL_CALL
            case _:
                raise NotImplementedError(f"Got unknown finish reason {reason}")
    
    @classmethod
    def from_google_reason(cls, reason: GoogleFinishReason | str) -> FinishReason:
        match reason:
            case GoogleFinishReason.STOP | "STOP":
                return cls.STOP
            case GoogleFinishReason.MAX_TOKENS | "MAX_TOKENS":
                return cls.LENGTH
            case GoogleFinishReason.SAFETY | "SAFETY":
                return cls.SAFETY
            case GoogleFinishReason.RECITATION | "RECITATION":
                return cls.COPYRIGHT
            case GoogleFinishReason.BLOCKLIST | "BLOCKLIST":
                return cls.BLOCKLIST
            case GoogleFinishReason.PROHIBITED_CONTENT | "PROHIBITED_CONTENT":
                return cls.PROHIBITED_CONTENT
            case GoogleFinishReason.SPII | "SPII":
                return cls.SPII
            case GoogleFinishReason.MALFORMED_FUNCTION_CALL | "MALFORMED_FUNCTION_CALL":
                return cls.TOOL_CALL_ERROR
            case GoogleFinishReason.OTHER | "OTHER":
                return cls.OTHER
            case GoogleFinishReason.FINISH_REASON_UNSPECIFIED | "FINISH_REASON_UNSPECIFIED":
                return cls.UNSPECIFIED
            case _:
                raise NotImplementedError(f"Got unknown finish reason {reason}")

    @classmethod
    def from_together_reason(cls, reason: str) -> FinishReason:
        match reason:
            case "eos" | "stop":
                return cls.STOP
            case "length":
                return cls.LENGTH
            case "tool_calls":
                return cls.TOOL_CALL
            case "error":
                return cls.ERROR
            case _:
                raise NotImplementedError(f"Got unknown finish reason {reason}")
