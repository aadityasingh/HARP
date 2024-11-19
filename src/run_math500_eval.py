"""
Run evaluation on MATH-500
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import click
from tqdm.auto import tqdm

from eval.api import ModelAPI, safe_unified_api_call
from eval.latex_answer_check import latex_answer_check
from eval.parsing_lib import extract_answer
from eval.prompt import create_prompt
from eval.prompts.cot_chat import gemini_sysprompt, minerva_4shot_prompt
from eval.response import ModelResponse
from eval.utils import read_jsonl, write_jsonl, load_hendrycks_problem


def run_one(
    problem: dict[str, Any],
    api: ModelAPI | str,
    model: str,
    fewshot_messages: list[dict[str, Any]],
    system_prompt: str | list[str] | None,
    user_prompt_template: str | None = "Problem:\n{problem}",
    ending_assistant_prompt: str | None = "Solution:",
    *,
    max_tokens: int = 1024,
    temperature: float = 0,
    stop_sequences: list[str] | None = None,  # e.g. stop_sequences=["I hope it is correct."],
    seed: int | None = 0,
) -> dict[str, Any]:
    prompt = create_prompt(
        problem["problem"],
        fewshot_messages,
        system_prompt,
        user_prompt_template=user_prompt_template,
        ending_assistant_prompt=ending_assistant_prompt,
    )
    response, success = safe_unified_api_call(
        api=api,
        model=model,
        prompt=prompt,
        max_tokens=max_tokens,
        num_completions=1,
        temperature=temperature,
        stop_sequences=stop_sequences,
        seed=seed,
        logprobs=False,
        top_logprobs=None,
    )
    return {
        "uid": problem["uid"],
        "system": prompt.system,
        "prompt": prompt.messages,
        "response": response if success else None,
    }


def make_hendrycks_answer_check_dict_from_jsonl(
    filepath: Path, api: ModelAPI, data_dir: Path = Path("data/MATH")
) -> list[dict[str, str]]:
    responses = read_jsonl(filepath)
    responses = [
        {
            "uid": x["uid"],
            "system": x["system"],
            "prompt": x["prompt"],
            "response": ModelResponse.from_response(x["response"], api)
        }
        for x in responses
    ]

    answer_check_dicts = []
    for resp in responses:
        resp_text: str = resp["response"].completions[0].completion
        prob = load_hendrycks_problem(resp["uid"], data_dir=data_dir)
        
        a = {
            "uid": resp["uid"],
            "problem": prob["problem"],
            "generated_text": resp_text,
            "answer": extract_answer(prob["solution"], extract_policy="strict"),
        }
        answer_check_dicts.append(a)
    return answer_check_dicts


def check_answers_from_jsonl(
    filepath: Path,
    api: ModelAPI,
    data_dir: Path = Path("data/MATH"),
    extract_policy: str = "flex",
    eval_policy: str = "aggressive",
    debug: bool = False,
) -> list[dict[str, Any]]:
    answer_check_dicts = make_hendrycks_answer_check_dict_from_jsonl(
        filepath, api, data_dir=data_dir
    )
    return latex_answer_check(
        answer_check_dicts,
        extract_policy=extract_policy,
        eval_policy=eval_policy,
        debug=debug,
    )


@click.command()
@click.option("--out", type=Path)
@click.option("--api", type=str)
@click.option("--model", type=str)
@click.option("--max_tokens", default=10, type=int)
@click.option("--temperature", default=0, type=float)
def main(out: Path, api: str, model: str, max_tokens: int, temperature: int) -> None:
    prm_test_split = read_jsonl("data/prm800k/test.jsonl")
    prm_test_uids = [ex["unique_id"] for ex in prm_test_split]

    raw_prm_test_dataset = []
    for uid in prm_test_uids:
        raw_prm_test_dataset.append(load_hendrycks_problem(uid))
    
    # Sanity check that the MATH dataset matches the PRM800K data exactly
    assert len(prm_test_split) == len(raw_prm_test_dataset), "Datasets have different lengths???"
    for prm_ex, raw_ex in zip(prm_test_split, raw_prm_test_dataset):
        if prm_ex["problem"] != raw_ex["problem"]:
            print(f"Problem statements are different from {prm_ex['unique_id']}")
        if prm_ex["solution"] != raw_ex["solution"]:
            print(f"Solutions are different from {prm_ex['unique_id']}")
    
    outputs = []
    for prob in tqdm(raw_prm_test_dataset):
        outputs.append(
            run_one(
                prob,
                api=api,
                model=model,
                fewshot_messages=minerva_4shot_prompt,
                system_prompt=gemini_sysprompt,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        )
    write_jsonl(outputs, out)


if __name__ == "__main__":
    main()
