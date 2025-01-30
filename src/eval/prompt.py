"""
A unified class for representing prompts to the different LLM APIs
"""

from __future__ import annotations

from typing import Any

from attrs import Attribute, define, field

from vertexai.generative_models import (
    Content as GoogleContent,
    Part as GooglePart,
)

@define
class Prompt:
    """A unified representation for prompts across APIs. Has member functions
    to convert into the necessary format for each API function.

    For now we only support text-based inputs.

    Each message dict has keys
        - role: str
        - content: str

    NOTE: currently I assume that every content block will only have one part
    Not super clear to me if having multiple parts is useful? I tried a few prompts
    and didn't see much difference. Also AFAICT, Together doesn't support content parts

    Doesn't support prompt-caching args. Anthropic and Google do it in pretty different ways!
    This also didn't end up being that relevant because we used shorter zero-shot prompts
    """
    messages: list[dict[str, Any]] = field()
    # List of system prompt text. Each element will be a distinct system content object
    system: list[str] | None = field(default=None)

    @messages.validator
    def _check_messages(self, attribute: Attribute, value: list[dict[str, Any]]) -> bool:
        for block in value:
            if set(block.keys()) != {"role", "content"}:
                raise ValueError(f"Found message block with wrong set of keys: {block}")
            if block["role"] not in {"user", "assistant"}:
                raise ValueError(f"Found message with unknown role {block['role']}: {block}")

    def to_merged_format(self) -> list[dict[str, Any]]:
        """Output all messages in prompt in a single list of dicts.
        
        This is the format used for OpenAI and Together APIs.
        """
        system_prompts = []
        if self.system is not None:
            system_prompts = [
                {"role": "system", "content": text}
                for text in self.system
            ]

        msg_prompts = [
            {
                "role": msg["role"],
                "content": msg["content"],
            }
            for msg in self.messages
        ]
        return system_prompts + msg_prompts

    def to_anthropic_format(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]] | None]:
        """Output messages and system prompt in Anthropic format
        
        Returns:
            - messages: list of user/assistant prompt content blocks of the form
                ```
                {
                    "role": "user" | "assistant",
                    "content": [
                        {
                            "type": "text", "text": <str>,
                            <"cache_control": {"type": "ephemeral"}> (if using prompt caching)
                        }
                    ]
                }
                ```
            - system: list of system prompt content blocks of the form
                ```
                {
                    "type": "text", "text": <str>,
                    <"cache_control": {"type": "ephemeral"}> (if using prompt caching)
                }
                ```
        """
        msg_prompts = [
            {
                "role": msg["role"],
                "content": [{"type": "text", "text": msg["content"]}],
            }
            for msg in self.messages
        ]

        if self.system is not None:
            system_prompts = [
                {"type": "text", "text": text}
                for text in self.system
            ]
        else:
            system_prompts = None
        
        return msg_prompts, system_prompts
    
    def to_google_format(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]] | None]:
        def get_google_role(role: str) -> str:
            match role:
                case "user":
                    return "user"
                case "assistant":
                    return "model"
                case _:
                    raise NotImplementedError(f"No Google role mapping for {role}")

        msg_prompts = [
            GoogleContent(
                role=get_google_role(msg["role"]),
                parts=[GooglePart.from_text(msg["content"])]
            )
            for msg in self.messages
        ]
        
        return msg_prompts, self.system


def create_prompt(
    problem_text: str,
    fewshot_messages: list[dict[str, Any]],
    system_prompt: str | list[str] | None,
    user_prompt_template: str | None = "Problem:\n{problem}",
    ending_assistant_prompt: str | None = "Solution:",
) -> Prompt:
    """Create a prompt object from the necessary args

    Args:
        - ending_assistant_prompt: a leading prompt for the LLM to complete
            for its generation of a solution. Note that it cannot have 
            trailing whitespace for the Anthropic API
    """
    if isinstance(system_prompt, str):
        system_prompt = [system_prompt]
    elif isinstance(system_prompt, list):
        system_prompt = system_prompt.copy()

    # Avoid mutation when running code in a for loop
    messages = fewshot_messages.copy()

    if user_prompt_template is not None:
        messages.append({
            "role": "user",
            "content": user_prompt_template.format(problem=problem_text),
        })
    else:
        messages.append({
            "role": "user",
            "content": problem_text,
        })
    
    if ending_assistant_prompt is not None:
        messages.append({
            "role": "assistant",
            "content": ending_assistant_prompt,
        })

    return Prompt(messages=messages, system=system_prompt)
