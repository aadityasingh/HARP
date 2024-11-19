"""
Helper functions for a unified API for calling LLM APIs
"""

from __future__ import annotations

import os
import pprint
import time
from collections.abc import Iterable
from typing import Any

import numpy as np

from anthropic import Anthropic
from anthropic.types.message import Message
from openai import OpenAI
from openai.types.chat.chat_completion import ChatCompletion
from together import Together
import vertexai
from vertexai.generative_models import (
    GenerativeModel,
)

from eval.enums import ModelAPI
from eval.prompt import Prompt


def openai_api_call(
    model: str,
    prompt: Prompt,
    *,
    max_tokens: int | None = 10,
    num_completions: int = 1,
    temperature: float = 0,
    top_p: float = 1,
    stop_sequences: list[str] | None = None,
    logprobs: bool = True,
    top_logprobs: int | None = 20,  # [0, 20], number of most likely logprobs
    seed: int | None = None,
    # args to generate batch api inputs
    return_params: bool = False,
    custom_id: str | None = None,
) -> dict[str, Any]:
    """Makes an OpenAI API call for the specified model.

    Use for GPT and o1 models
    """
    if num_completions > 1 and temperature == 0:
        raise ValueError("You are asking for multiple completions with temperature 0. Is this intended? You'll almost surely get the same result back N times")
    
    messages = prompt.to_merged_format()

    # Initialize config kwargs in a separate dict first so we can filter out None values
    # This is because the OpenAI api defaults to its own custom NotGiven value and
    # can treat it differently from null (e.g. o1 errors on null stop sequences)
    config = dict(
        max_completion_tokens=max_tokens,
        n=num_completions,
        temperature=temperature,
        top_p=top_p,
        logprobs=logprobs,
        top_logprobs=top_logprobs,
        seed=seed,
        stop=stop_sequences,
    )
    config = {k: v for k, v in config.items() if v is not None}

    if return_params:
        if custom_id is None:
            raise ValueError("return_params is True but custom_id is not set.")
        return {
            "custom_id": custom_id,
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": model,
                "messages": messages,
                **config,
            }
        }

    client = OpenAI()
    response: ChatCompletion = client.chat.completions.create(
        model=model,
        messages=messages,
        **config,
    )
    return response.to_dict()


def anthropic_api_call(
    model: str,
    prompt: Prompt,
    *,
    max_tokens: int = 10,
    temperature: float = 0,
    top_p: float = 1,
    stop_sequences: list[str] | None = None,
    # args to generate batch api inputs
    return_params: bool = False,
    custom_id: str | None = None,
) -> dict[str, Any]:
    """Makes a Anthropic API call for the specified model.

    Use for Claude
    
    Notes:
        - For prompt.messages, *must* be alternating user/assistant content blocks
        - Left out `top_k` as a surfaced arg, but it is available for Anthropic

    Prompt caching:
        The Anthropic API supports prompt caching prefixes for cheaper reuse. To do so,
        you can establish up to four breakpoints by replacing the content field of a
        system prompt or message block, usually a single string, with a dict of
        ```
        {
            "type": "text", 
            "text": <str>,
            "cache_control": {"type": "ephemeral"}
        }
        ```
        This is not well supported in the code right now, as we didn't end up with very long prompts
        doing zero-shot experiments, but can use prompt caching by adding the breakpoints into
        your prompt messages manually.
    """
    messages, system = prompt.to_anthropic_format()

    if return_params:
        if custom_id is None:
            raise ValueError("return_params is True but custom_id is not set.")
        config = {
            "model": model,
            "system": system,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "stop_sequences": stop_sequences,
        }
        return {
            "custom_id": custom_id.replace("/", "-"),
            "params": {k: v for k, v in config.items() if v is not None},
        }

    client = Anthropic()
    response: Message = client.messages.create(
        model=model,
        **({"system": system} if system is not None else {}),
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        stop_sequences=stop_sequences,
    )
    return response.to_dict()


def google_api_call(
    model: str,
    prompt: Prompt,
    *,
    max_tokens: int | None = 10,
    num_completions: int = 1,
    temperature: float = 0,
    top_p: float = 1,
    stop_sequences: list[str] | None = None,
    seed: int | None = None,
    # args to generate batch api inputs
    return_params: bool = False,
    custom_id: str | None = None,
) -> dict[str, Any]:
    """Makes a Google API call for the specified model.

    Use for Gemini

    NOTE: system prompt right now only supports a string. You could also have a list of strs
    which is passed in as a list of "parts" instead of one part. There might be some small
    difference in the input then (e.g. maybe something like <part>part1</part><part>part2<part2>)

    TODO: context caching. Notably, we must have system_instruction=None
        Again, didn't find it too relevant for zero-shot experiments
    """
    if num_completions < 1 or num_completions > 8:
        raise ValueError(f"Google Vertex API only supports num_completions between 1 to 8, but got: {num_completions}")

    messages, system = prompt.to_google_format()
    config = {
        "temperature": temperature,
        "top_p": top_p,
        "candidate_count": num_completions,
        "max_output_tokens": max_tokens,
        "stop_sequences": stop_sequences,
        "seed": seed,
    }
    config = {k: v for k, v in config.items() if v is not None}

    if return_params:
        return {
            **({"custom_id": custom_id} if custom_id is not None else {}),
            "request": {
                "contents": [msg.to_dict() for msg in messages],
                "generation_config": config,
                "system_instruction": {"parts": [{"text": ss} for ss in system]},
            },
        }

    gen_model = GenerativeModel(model, **{"system_instruction": system} if system is not None else {})
    response = gen_model.generate_content(
        contents=messages,
        generation_config=config,
    )
    return response.to_dict()


def together_api_call(
    model: str,
    prompt: Prompt,
    *,
    max_tokens: int = 10,
    num_completions: int = 1,
    temperature: float = 0,
    top_p: float = 1,
    stop_sequences: list[str] | None = None,
    logprobs: bool = True,  # get logprobs of generated tokens
) -> dict[str, Any]:
    """Makes a Together API call for the specified model

    Use for Llama
    """
    messages = prompt.to_merged_format()

    client = Together()
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        n=num_completions,
        temperature=temperature,
        top_p=top_p,
        stop=stop_sequences,
        logprobs=1 if logprobs else None,  # at least for Llama 3.1 8B, >1 leads to an error
    )
    return response.model_dump()


def unified_api_call(
    api: ModelAPI,
    model: str,
    prompt: Prompt,
    *,
    max_tokens: int | None = 10,
    num_completions: int = 1,
    temperature: float = 0,
    top_p: float = 1,
    stop_sequences: list[str] | None = None,
    logprobs: bool = True,  # openai/together, give logprobs of generated tokens
    top_logprobs: int | None = 20,  # openai [0, 20], number of most likely logprobs
    seed: int | None = None,  # only works for openai and gemini
    # args to generate batch api inputs
    return_params: bool = False,
    custom_id: str | None = None,
) -> dict[str, Any]:
    if num_completions > 1 and temperature == 0:
        raise ValueError("You are asking for multiple completions with temperature 0. Is this intended? You'll almost surely get the same result back N times")
    if not logprobs and top_logprobs is not None:
        raise ValueError("logprobs must be set to True for top_logprobs to be non-None")

    if api == ModelAPI.OPENAI:
        return openai_api_call(
            model=model,
            prompt=prompt,
            max_tokens=max_tokens,
            num_completions=num_completions,
            temperature=temperature,
            top_p=top_p,
            stop_sequences=stop_sequences,
            logprobs=logprobs,
            top_logprobs=top_logprobs,
            seed=seed,
            return_params=return_params,
            custom_id=custom_id,
        )

    elif api == ModelAPI.ANTHROPIC:
        if max_tokens is None:
            raise ValueError("max_tokens must be set for Anthropic API")
        if logprobs:
            raise ValueError("logprobs is not supported by Anthropic API")
        if seed is not None:
            raise ValueError(f"Got seed arg {seed} but arg isn't support for Anthropic API")
        if top_logprobs is not None:
            print(f"WARNING: top_logprobs {top_logprobs} has no effect on Anthropic API")
        
        responses = []
        for i in range(num_completions):
            responses.append(anthropic_api_call(
                model=model,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stop_sequences=stop_sequences,
                return_params=return_params,
                custom_id=f"{custom_id}_{i}" if num_completions > 1 else custom_id,
            ))
        
        if return_params:
            return {"batch": responses}

        model_strs = set(r["model"] for r in responses)
        if len(model_strs) != 1:
            print(f"WARNING: saw multiple unique model strings!!! {model_strs}")
        return {
            "candidates": responses,
            "model": responses[0]["model"]
        }

    elif api == ModelAPI.GOOGLE:
        if logprobs:
            raise ValueError("logprobs is not supported by Google Vertex API")
        if top_logprobs is not None:
            print(f"WARNING: top_logprobs {top_logprobs} has no effect on Google Vertex API")
    
        resp = google_api_call(
            model=model,
            prompt=prompt,
            max_tokens=max_tokens,
            num_completions=num_completions,
            temperature=temperature,
            top_p=top_p,
            stop_sequences=stop_sequences,
            seed=seed,
            return_params=return_params,
            custom_id=custom_id,
        )
        resp["model"] = model
        return resp

    elif api == ModelAPI.TOGETHER:
        if seed is not None:
            raise ValueError(f"Got seed arg {seed} but arg isn't support for Together API")
        if top_logprobs is not None:
            print(f"WARNING: top_logprobs {top_logprobs} has no effect on Together API")
        if return_params or custom_id:
            raise ValueError("Together AI doesn't have a batch api")

        return together_api_call(
            model=model,
            prompt=prompt,
            max_tokens=max_tokens,
            num_completions=num_completions,
            temperature=temperature,
            top_p=top_p,
            stop_sequences=stop_sequences,
            logprobs=logprobs,
        )
    else:
        raise NotImplementedError(f"API {api} is not supported yet.")
    

def safe_unified_api_call(
    api: ModelAPI,
    model: str,
    prompt: Prompt,
    *,
    max_tokens: int | None = 10,
    num_completions: int = 1,
    temperature: float = 0,
    top_p: float = 1,
    stop_sequences: list[str] | None = None,
    logprobs: bool = True,  # openai/together, give logprobs of generated tokens
    top_logprobs: int | None = 20,  # openai [0, 20], number of most likely logprobs
    seed: int | None = None,  # only works for openai
    # args to generate batch api inputs
    return_params: bool = False,  # if return_params, return the request for batch API
    custom_id: str | None = None,
    # retry args
    max_retries: int = 10,
    retry_wait_range: tuple[int] = (2, 9),
) -> tuple[dict[str, Any] | None, bool]:
    """Calls unified_api_call with some additional error handling"""
    assert len(retry_wait_range) == 2, f"Expected two ints for retry_wait_range, but got: {retry_wait_range}"

    num_tries = 0
    success = False
    response = None
    while not success and num_tries < max_retries:
        try:
            response = unified_api_call(
                api=api,
                model=model,
                prompt=prompt,
                max_tokens=max_tokens,
                num_completions=num_completions,
                temperature=temperature,
                top_p=top_p,
                stop_sequences=stop_sequences,
                logprobs=logprobs,
                top_logprobs=top_logprobs,
                seed=seed,
                return_params=return_params,
                custom_id=custom_id,
            )
            success = True
        except Exception as e:
            wait_secs = np.random.randint(*retry_wait_range)
            num_tries += 1

            print(f"Hit error with API call. Waiting {wait_secs}s before retrying {num_tries+1} of {max_retries}.")
            print(f"Exception hit: {e}")

            time.sleep(wait_secs)
    return response, success


if __name__ == "__main__":
    vertexai.init(project=os.environ.get("VERTEXAI_PROJECT_ID"))

    prompt = Prompt(
        messages=[
            {"role": "user", "content": "Name a Genshin Impact character"}
        ],
        system="You are a helpful assistant.",
    )

    response = safe_unified_api_call(
        # api="openai",
        # model="gpt-4o-mini-2024-07-18",
        # api="anthropic",
        # model="claude-3-5-sonnet-20240620",
        api="google",
        model="gemini-1.5-flash-001",
        # api="together",
        # model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
        prompt=prompt,
        # logprobs=True,
        # top_logprobs=2,
        logprobs=False,
        top_logprobs=None,
        temperature=1,
        max_tokens=10,
        num_completions=1,
        # seed=0,
    )
    pprint.pprint(response)
