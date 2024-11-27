"""
Makes the three HARP datasets for use by the community.

These files correspond to the three main use cases that we currently foresee in terms of answer format:
    - shortans_dataset.jsonl: Short answer, where the final answer is a short phrase or math expression
        that can be verified with our answer checker
    - mcq_dataset.jsonl: Multiple-choice, where the final answer is a letter choice A-E.
        We also shuffle the choices from the original ordering.
    - olympiad_dataset.jsonl: Proof-based questions where there may not be a clear final answer
These files are then put into a ZIP file to make it harder for accidental data contamination in future models.
"""

import os
import shutil
import zipfile
from typing import Any

import numpy as np

from eval.utils import AMC_LETTER_CHOICES, read_jsonl, write_jsonl

ALWAY_DROP_KEYS = ["url", "full_text", "num_gpt4_tokens", "other_appearances"]


def write_zipfile(jsonl: list[dict[str, Any]], out_fname: str) -> None:
    write_jsonl(jsonl, out_fname)
    zipfile.ZipFile(f"{out_fname}.zip", mode="w").write(out_fname)
    os.remove(out_fname)


def is_solution_metadata_key(k: str) -> bool:
    return k.startswith("solution_") and k.endswith("_metadata")


def get_derangement(length: int = 5) -> list[str]:
    letters = AMC_LETTER_CHOICES[:length]
    while True:
        shuffle = np.random.permutation(letters)
        is_derangement = True
        for l, x in zip(letters, shuffle):
            if l == x:
                is_derangement = False
        if is_derangement:
            return [str(x) for x in shuffle] + AMC_LETTER_CHOICES[length:]


def prepare_short_answer_dataset(full_dataset: list[dict[str, Any]]) -> list[dict[str, Any]]:
    to_drop_keys = ALWAY_DROP_KEYS + ["choices", "answer_choice"]
    return [
        {k: v for k, v in prob.items() if k not in to_drop_keys and not is_solution_metadata_key(k)}
        for prob in full_dataset
        if not prob["contest"].endswith("MO") and not prob["multiple_choice_only"]
    ]


def prepare_mcq_dataset(full_dataset: list[dict[str, Any]]) -> list[dict[str, Any]]:
    to_drop_keys = ALWAY_DROP_KEYS
    dataset = []

    for prob in full_dataset:
        if prob["contest"].endswith("MO") or prob["contest"].startswith("AIME"):
            continue

        new_prob = {k: v for k, v in prob.items() if k not in to_drop_keys and not is_solution_metadata_key(k)}

        choices = new_prob["choices"]
        length = 5
        if "none of" in choices["E"].lower() or "all of" in choices["E"].lower():
            length = 4
        new_order = get_derangement(length)

        new_choices = {}
        for letter, new_letter in zip(AMC_LETTER_CHOICES, new_order):
            new_choices[new_letter] = new_prob["choices"][letter]
        new_choices = {l: new_choices[l] for l in AMC_LETTER_CHOICES}
        new_prob["choices"] = new_choices
        new_prob["answer_choice"] = new_order[AMC_LETTER_CHOICES.index(new_prob["answer_choice"])]

        dataset.append(new_prob)
    return dataset


def prepare_olympiad_dataset(full_dataset: list[dict[str, Any]]) -> list[dict[str, Any]]:
    to_drop_keys = ALWAY_DROP_KEYS + ["choices", "answer_choice", "answer"]
    return [
        {k: v for k, v in prob.items() if k not in to_drop_keys and not is_solution_metadata_key(k)}
        for prob in full_dataset
        if prob["contest"].endswith("MO")
    ]


def main() -> None:
    os.makedirs("data/datasets", exist_ok=True)
    dataset = read_jsonl("data/processed/aops_wiki_final.jsonl")
    write_zipfile(dataset, "data/datasets/full_dataset.jsonl")

    # drop calculus problems from dataset splits
    dataset = [p for p in dataset if p["subject"]!= "calculus"]
    
    shortans_dataset = prepare_short_answer_dataset(dataset)
    mcq_dataset = prepare_mcq_dataset(dataset)
    olympiad_dataset = prepare_olympiad_dataset(dataset)

    print(f"Short answer dataset has length {len(shortans_dataset)}")
    print(f"MCQ dataset has length {len(mcq_dataset)}")
    print(f"Proof-based dataset has length {len(olympiad_dataset)}")

    write_zipfile(shortans_dataset, "data/datasets/shortans_dataset.jsonl")
    write_zipfile(mcq_dataset, "data/datasets/mcq_dataset.jsonl")
    write_zipfile(olympiad_dataset, "data/datasets/proof_dataset.jsonl")


if __name__ == "__main__":
    main()

