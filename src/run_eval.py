"""
Script to run evals on our dataset
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import click
from tqdm.auto import tqdm

from eval.eval import run_one
from eval.prompts import (
    custom_claude_sysprompt,
    gemini_0shot_sysprompt,
    gemini_sysprompt,
    minerva_4shot_prompt,
    modified_openai_o1_prompt_template,
    llama3_prompt_template,
    gemini_multiple_choice_0shot_sysprompt,
    llama3_multiple_choice_prompt_template
)
from eval.utils import read_jsonl


def get_prompt_settings(
    model: str, do_multiple_choice: bool = False, use_minerva: bool = True
) -> dict[str, Any]:
    if use_minerva and not model.startswith("gemini"):
        raise NotImplementedError

    if model.startswith("o1"):
        return {
            "fewshot_messages": [],
            "system_prompt": None,  # o1 models don't support sys prompts
            "user_prompt_template": modified_openai_o1_prompt_template,
            "ending_assistant_prompt": None,
        }
    elif model.startswith("claude"):
        return {
            "fewshot_messages": [],
            "system_prompt": custom_claude_sysprompt,
            "user_prompt_template": "Problem:\n{problem}",
            "ending_assistant_prompt": "Solution:",
            "stop_sequences": ["I hope it is correct."],
        }
    elif model.startswith("gemini"):
        if do_multiple_choice:
            if use_minerva:
                raise NotImplementedError
            return {
                "fewshot_messages": [],
                "system_prompt": gemini_multiple_choice_0shot_sysprompt,
                "user_prompt_template": "Problem:\n{problem}",
                "ending_assistant_prompt": "Solution:",
                "stop_sequences": ["I hope it is correct."],
            }
        elif use_minerva:
            return {
                "fewshot_messages": minerva_4shot_prompt,
                "system_prompt": gemini_sysprompt,
                "user_prompt_template": "Problem:\n{problem}",
                "ending_assistant_prompt": "Solution:",
                "stop_sequences": ["I hope it is correct."],
            }
        else:
            return {
                "fewshot_messages": [],
                "system_prompt": gemini_0shot_sysprompt,
                "user_prompt_template": "Problem:\n{problem}",
                "ending_assistant_prompt": "Solution:",
                "stop_sequences": ["I hope it is correct."],
            }
    elif model.startswith("meta-llama"):
        if do_multiple_choice:
            return {
                "fewshot_messages": [],
                "system_prompt": None,
                "user_prompt_template": llama3_multiple_choice_prompt_template,
                "ending_assistant_prompt": None,
                "stop_sequences": ["I hope it is correct."],
            }
        else:
            return {
                "fewshot_messages": [],
                "system_prompt": None,
                "user_prompt_template": llama3_prompt_template,
                "ending_assistant_prompt": None,
                "stop_sequences": ["I hope it is correct."],
            }
    else:
        raise NotImplementedError(model)


@click.command()
@click.option("--model", type=str)
@click.option("--data_fname", type=Path)
@click.option("--out", type=Path, help="file name")
@click.option("--outdir", type=Path, default="outputs/", help="Top-level dir for outputs")
@click.option("--api", default="openai", type=str)
@click.option("--start-idx", default=0, type=int, help="Index of dataset to start eval at. Helpful for restarting evals midway.")
@click.option("--max-tokens", default=10, type=int)
@click.option("--temperature", default=1, type=float)
@click.option("--seed", default=None, type=int)
@click.option("--do-multiple-choice", is_flag=True, default=False, type=bool)
@click.option("--prompt-choices", default=None, type=str, help="How to prompt choices when doing MCQ prompting")
@click.option("--use-minerva", is_flag=True, default=False, type=bool)
def main(
    model: str,
    data_fname: Path,
    out: Path,
    outdir: Path,
    api: str,
    start_idx: int,
    max_tokens: int,
    temperature: int,
    seed: int | None,
    do_multiple_choice: bool,
    prompt_choices: str | None,
    use_minerva: bool,
) -> None:
    folder_name = "multiple_choice" if do_multiple_choice else "short_answer"
    out_fname = outdir / folder_name / model.split("/")[-1] / out
    os.makedirs(out_fname.parent, exist_ok=True)

    full_dataset = read_jsonl(data_fname)
    if do_multiple_choice:
        dataset = [
            p 
            for p in full_dataset 
            if not p["contest"].endswith("MO") and not p["contest"].startswith("AIME")
        ]
    else:
        dataset = [
            p 
            for p in full_dataset 
            if not p["contest"].endswith("MO") and not p["multiple_choice_only"]
        ]

    with open(out_fname, "a+") as f:
        for prob in tqdm(dataset[start_idx:]):
            prompt_settings = get_prompt_settings(
                model, do_multiple_choice=do_multiple_choice, use_minerva=use_minerva
            )
            resp = run_one(
                prob,
                api=api,
                model=model,
                **prompt_settings,
                max_tokens=max_tokens,
                temperature=temperature,
                seed=seed,
                prompt_choices=prompt_choices,
            )
            f.write(json.dumps(resp)+'\n')


if __name__ == "__main__":
    main()
