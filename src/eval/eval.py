from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import click
from tqdm.auto import tqdm

from eval.api import ModelAPI, safe_unified_api_call
from eval.prompt import create_prompt
from eval.response import ModelResponse
from eval.utils import AMC_LETTER_CHOICES, read_jsonl, get_uid


def run_one(
    problem: dict[str, Any],
    api: ModelAPI | str,
    model: str,
    fewshot_messages: list[dict[str, Any]],
    system_prompt: str | list[str],
    *,
    user_prompt_template: str | None = "Problem:\n{problem}",
    ending_assistant_prompt: str | None = "Solution:",
    max_tokens: int = 1024,
    num_completions: int = 1,
    temperature: float = 0,
    stop_sequences: list[str] | None = None,
    # stop_sequences=["I hope it is correct."],
    prompt_choices: str | None = None,
    return_params: bool = False,
    custom_id: str | None = None,
    **extra_kwargs,
) -> dict[str, Any]:
    if prompt_choices is not None and problem["choices"] is None:
        raise ValueError("Problem doesn't have answer choices.")
    
    # Options for formatting answer choices to append to the problem text
    if prompt_choices is None:
        problem_text: str = problem["problem"]
    elif prompt_choices == "from_text":
        full_text: str = problem["full_text"]
        problem_text = full_text.split("\n\n")[0].split("# Problem\n", maxsplit=1)[1]
    elif prompt_choices == "newline_dot":
        choices_text = "\n".join([f'{letter}. {problem["choices"][letter]}' for letter in AMC_LETTER_CHOICES])
        problem_text = f'{problem["problem"]}\n{choices_text}'
    elif prompt_choices == "newline_paren":
        choices_text = "\n".join([f'({letter}) {problem["choices"][letter]}' for letter in AMC_LETTER_CHOICES])
        problem_text = f'{problem["problem"]}\n{choices_text}'
    else:
        raise NotImplementedError(f"Don't recognize {prompt_choices=}")

    prompt = create_prompt(
        problem_text,
        fewshot_messages,
        system_prompt,
        user_prompt_template=user_prompt_template,
        ending_assistant_prompt=ending_assistant_prompt,
    )

    if api == ModelAPI.OPENAI:
        if model.startswith("o1"):
            assert temperature == 1
            extra_kwargs = {
                "logprobs": False,
                "top_logprobs": None,
            } | extra_kwargs
    elif api == ModelAPI.ANTHROPIC:
        extra_kwargs = {
            "logprobs": False,
            "top_logprobs": None,
        } | extra_kwargs
    elif api == ModelAPI.GOOGLE:
        extra_kwargs = {
            "logprobs": False,
            "top_logprobs": None,
        } | extra_kwargs
    elif api == ModelAPI.TOGETHER:
        extra_kwargs = {
            "top_logprobs": None,
        } | extra_kwargs
    else:
        raise NotImplementedError
    
    response, success = safe_unified_api_call(
        api=api,
        model=model,
        prompt=prompt,
        max_tokens=max_tokens,
        num_completions=num_completions,
        temperature=temperature,
        stop_sequences=stop_sequences,
        return_params=return_params,
        custom_id=custom_id,
        **extra_kwargs,
    )
    if return_params:
        return response
    return {
        "uid": get_uid(problem),
        "system": prompt.system,
        "prompt": prompt.messages,
        "response": response if success else None,
    }


def create_batch(
    dataset: list[dict[str, Any]],
    api: ModelAPI | str,
    model: str,
    fewshot_messages: list[dict[str, Any]],
    system_prompt: str | list[str],
    *,
    user_prompt_template: str | None = "Problem:\n{problem}",
    ending_assistant_prompt: str | None = "Solution:",
    prompt_choices: str | None = None,
    max_tokens: int = 1024,
    num_completions: int = 1,
    temperature: float = 0,
    stop_sequences: list[str] | None = None,
    **extra_kwargs,
):
    """Create inputs for batch api"""
    batch = []
    for prob in dataset:
        uid = get_uid(prob)
        request = run_one(
            prob,
            api=api,
            model=model,
            fewshot_messages=fewshot_messages,
            system_prompt=system_prompt,
            user_prompt_template=user_prompt_template,
            ending_assistant_prompt=ending_assistant_prompt,
            max_tokens=max_tokens,
            num_completions=num_completions,
            temperature=temperature,
            stop_sequences=stop_sequences,
            prompt_choices=prompt_choices,
            return_params=True,
            custom_id=uid,
            **extra_kwargs,
        )
        if api == ModelAPI.ANTHROPIC:
            batch.extend(request["batch"])
        else:
            batch.append(request)
    return batch


def make_answer_check_dict_from_jsonl(
    responses: list[str, Any], dataset_map: dict[str, dict[str, Any]]
) -> list[dict[str, str]]:
    """Create dict with the necessary data to pass into `latex_answer_check` for answer checking

    Args:
        responses: parsed responses from the raw saved eval file. Can be slightly different
            for different files, but the general code is of the form:
        
        ```
        responses = [
            {
                "uid": x["uid"],
                "system": x["request"]["system_instruction"],
                "prompt": x["request"]["contents"],
                "response": ModelResponse.from_response(x["response"], <API>, used_batch_api=<True|False>)
            }
            for x in raw_responses
        ]
        ```
    """
    answer_check_dicts = []
    for resp in responses:
        for i, completion in enumerate(resp["response"].completions):
            resp_text: str = completion.completion
            finish_reason: str = completion.finish_reason
            prob = dataset_map[resp["uid"]]
            
            a = {
                "uid": resp["uid"] if i == 0 else f'{resp["uid"]}_{i}',
                "problem": prob["problem"],
                "finish_reason": finish_reason,
                "generated_text": resp_text,
                "answer": prob["answer"],
                "answer_choice": prob["answer_choice"],
            }
            answer_check_dicts.append(a)
    return answer_check_dicts


def make_choice_check_dict_from_jsonl(
    responses: list[str, Any], dataset_map: dict[str, dict[str, Any]]
) -> list[dict[str, str]]:
    """
    Like `make_choice_check_dict_from_jsonl`, but for `latex_choice_check`

    Args:
        responses: parsed responses from the raw saved eval file. Can be slightly different
            for different files, but the general code is of the form:
        
        ```
        responses = [
            {
                "uid": x["uid"],
                "system": x["request"]["system_instruction"],
                "prompt": x["request"]["contents"],
                "response": ModelResponse.from_response(x["response"], <API>, used_batch_api=<True|False>)
            }
            for x in raw_responses
        ]
        ```
    """
    answer_check_dicts = []
    for resp in responses:
        for i, completion in enumerate(resp["response"].completions):
            resp_text: str = completion.completion
            finish_reason: str = completion.finish_reason
            prob = dataset_map[resp["uid"]]
            if prob["choices"] is not None:
                a = {
                    "uid": resp["uid"] if i == 0 else f'{resp["uid"]}_{i}',
                    "problem": prob["problem"],
                    "finish_reason": finish_reason,
                    "generated_text": resp_text,
                    "choices": prob["choices"],
                    "answer_choice": prob["answer_choice"],
                }
                answer_check_dicts.append(a)
    return answer_check_dicts