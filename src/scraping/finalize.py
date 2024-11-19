"""
This takes the deduped AoPS data and creates the final dataset

Does a few things
- Adds in expert-labelled subject annotations
- Standardize the final boxed answer to be the answer value
"""

import re
from typing import Any

from eval.utils import read_jsonl, write_jsonl, get_uid
from scraping.aops_wiki.process import find_closing_brace


def fix_solutions_manual(problem: dict[str, Any]) -> dict[str, Any]:
    uid = get_uid(problem)
    num_solutions = problem["num_solutions"]

    match uid:
        case "1985/AIME/12":
            # Solutions 1 and 2 rely on a common recursion setup that is in a separate section
            assert (
                problem["solution_1_metadata"] == "Recursive Formula"
                and problem["solution_2_metadata"] == "Explicit Formula"
            ), "Solution headers have changed for 1985/AIME/12. Double check that this is still correct!"
            for i in range(3, num_solutions+1):
                problem[f"solution_{i-2}"] = problem[f"solution_{i}"]
                problem[f"solution_{i-2}_metadata"] = problem[f"solution_{i}_metadata"]
            del problem[f"solution_{num_solutions-1}"]
            del problem[f"solution_{num_solutions-1}_metadata"]
            del problem[f"solution_{num_solutions}"]
            del problem[f"solution_{num_solutions}_metadata"]
            problem["num_solutions"] -= 2
        case "2010/USAJMO/2":
            # Solution 1 has two subheaders for different proofs
            assert (
                problem["solution_1"] == "The sequence is $2, 4, 6, \\ldots, 2n-2$."
            ), "Solution 1 has changed for 2010/USAJMO/2. Double check that this is still correct!"
            for i in range(2, num_solutions+1):
                problem[f"solution_{i-1}"] = problem[f"solution_{i}"]
                problem[f"solution_{i-1}_metadata"] = problem[f"solution_{i}_metadata"]
            del problem[f"solution_{num_solutions}"]
            del problem[f"solution_{num_solutions}_metadata"]
            problem["num_solutions"] -= 1
        case "2013/USAMO/2":
            # Solution 3 is incomplete
            assert (
                "Work In Progress" in problem["solution_3"]
            ), "Solution 3 has changed for 2013/USAJMO/2. Double check that this is still correct!"
            del problem["solution_3"]
            del problem["solution_3_metadata"]
            problem["num_solutions"] -= 1
    
    num_solutions = problem["num_solutions"] 
    soln_using_choices = []
    for i in range(1, num_solutions+1):
        # there is one false positive, in 2022/AMC_8/20
        if "choice" in problem[f"solution_{i}_metadata"]:
            soln_using_choices.append(i)
    if soln_using_choices:
        # move these solutions to the back
        new_order = [i for i in range(1, num_solutions+1) if i not in soln_using_choices] + soln_using_choices
        tmp_solutions = [problem[f"solution_{i}"] for i in range(1, num_solutions+1)]
        tmp_solution_metadatas = [problem[f"solution_{i}_metadata"] for i in range(1, num_solutions+1)]
        for i in range(1, num_solutions+1):
            problem[f"solution_{i}"] = tmp_solutions[new_order[i-1]-1]
            problem[f"solution_{i}_metadata"] = tmp_solution_metadatas[new_order[i-1]-1]

    return problem


def standardize_last_boxed_answer(problem: dict[str, Any]) -> dict[str, Any]:
    answer: str = problem["answer"]
    if answer is None:
        return problem

    parts = answer.split("$")
    processed = []
    for i, t in enumerate(parts):
        if bool(re.fullmatch(r"\s*", t)):
            continue
        if i % 2 == 0:
            processed.append(f"\\text{{{t}}}")
        else:
            processed.append(t)
    answer = " ".join(processed)

    for i in range(1, problem["num_solutions"]+1):
        text: str = problem[f"solution_{i}"]
        prefix = "\\boxed{"
        ind = text.rfind(prefix)
        close_idx = find_closing_brace(text[ind+len(prefix):])
        problem[f"solution_{i}"] = text[:ind+len(prefix)] + answer + text[ind+len(prefix)+close_idx:]
    return problem


def main() -> None:
    fname = "data/processed/aops_wiki_deduped.jsonl"
    subject_labels_fname = "data/raw/aops_subject_labels.jsonl"
    out_fname = "data/processed/aops_wiki_final.jsonl"

    dataset: list[dict[str, Any]] = read_jsonl(fname)
    # dataset = [dataset[0]]
    subject_labels_map = {l["uid"]: l for l in read_jsonl(subject_labels_fname)}
    new_dataset = []
    for prob in dataset:
        label = subject_labels_map[get_uid(prob)]
        notes = [n.strip() for n in label["notes"].split(",")]
        if "remove" in notes:
            continue

        subject = label["subject"]
        is_multiple_choice_only = "need choices" in notes

        # Fix some solutions from some problems
        # This is very ad-hoc, so you may want to double-check what you're deleting
        # if you re-run this process
        prob = fix_solutions_manual(prob)
        prob = standardize_last_boxed_answer(prob)

        # this ordering is just for aesthetics
        start_keys = ["year", "contest", "number", "url", "level"]
        new_prob = {
            **{k: v for k, v in prob.items() if k in start_keys},
            "subject": subject,
            "multiple_choice_only": is_multiple_choice_only, 
            **{k: v for k, v in prob.items() if k not in start_keys},
        }
        new_dataset.append(new_prob)

    write_jsonl(new_dataset, out_fname)


if __name__ == "__main__":
    main()
