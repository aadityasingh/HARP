# ---------------------------------------------------------
# Xwin-Math
# Copyright (c) 2023 Xwin-Math Team
# Licensed under The MIT License [see LICENSE for details]
# Based on ToRA (https://github.com/microsoft/ToRA/blob/main/src/eval/grader.py)
# Modified by Weiqi Wang
# Modified again by Ted Moskovitz and Albert Yue
# ---------------------------------------------------------

from __future__ import annotations

import pdb
from math import isclose
from pathlib import Path
from typing import Any

from sympy import simplify, N
from sympy.parsing.sympy_parser import parse_expr
from sympy.parsing.latex import parse_latex
from tqdm.auto import tqdm

from eval.enums import ModelAPI
from eval.parsing_lib import (
    extract_answer,
    remove_prefix_and_suffix,
    string_normalization,
    search_for_numbers,
    remove_boxes_keep_content,
    remove_text_box_only,
    remove_equals,
    split_tuple,
)
from eval.utils import run_with_timeout


def has_numbers(input_string: str) -> bool:
    """
    Checks if a string contains a number. 
    """
    return any(char.isdigit() for char in input_string)


def has_structure(input_string: str) -> bool:
    """
    Checks if a string contains structured content. 
    """
    STRUCTURE_CHARS = ["(", ")", "[", "]", "\\", "<", ">", ",", "x", "y", "z"]
    return any(c in input_string for c in STRUCTURE_CHARS)


def sympy_parse(input_string: str) -> Any:
    """
    Parsing strings into mathematical expressions using sympy
    """
    for f in [parse_latex, parse_expr]:
        try:
            return f(input_string)
        except:
            pass
    return input_string


def symbolic_equal(a: str, b: str) -> bool | None:
    """
    Check if two strings are symbolic equal. 
    """
    a = sympy_parse(a)
    b = sympy_parse(b)

    try:
        if simplify(a-b) == 0:
            return True
    except:
        pass

    # if a and b are ints, then skip the isclose tolerance check to avoid false positives
    try:
        if isclose(N(a), float(N(a)), rel_tol=1e-9) and isclose(N(b), float(N(b)), rel_tol=1e-9):
            return False
    except:
        pass

    try:
        if isclose(N(a), N(b), rel_tol=1e-4):
            return True
    except:
        pass
    return None


def text2int(textnum: str) -> int:
    """Convert text to number
    
    Copied from https://stackoverflow.com/questions/493174/is-there-a-way-to-convert-number-words-to-integers
    """
    numwords = {}
    units = [
        "zero", "one", "two", "three", "four", "five",
        "six", "seven", "eight", "nine", "ten",
        "eleven", "twelve", "thirteen", "fourteen", "fifteen",
        "sixteen", "seventeen", "eighteen", "nineteen",
    ]

    tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]

    scales = ["hundred", "thousand", "million", "billion", "trillion"]

    numwords["and"] = (1, 0)
    for idx, word in enumerate(units):
        numwords[word] = (1, idx)
    for idx, word in enumerate(tens):
        numwords[word] = (1, idx * 10)
    for idx, word in enumerate(scales):
        numwords[word] = (10 ** (idx * 3 or 2), 0)

    current = result = 0
    for word in textnum.split():
        if word not in numwords:
          raise Exception("Illegal word: " + word)

        scale, increment = numwords[word]
        current = current * scale + increment
        if scale > 100:
            result += current
            current = 0

    return result + current


def convert_to_int(input_string: str) -> int | None:
    """
    Try to convert a string into int. Return `None` if an error occurs. 
    """
    try:
        if input_string == "none":
            return 0
        int_s = text2int(input_string)
        if int_s:
            return int_s
    except:
        pass

    try:
        float_s = float(input_string)
        int_s = int(float_s)

        # If a floating-point number is converted to an integer that is very close to itself,
        # then we consider it to be an integer.
        if isclose(int_s, float_s, rel_tol=1e-9):
            return int_s
        return None
    except:
        return None


def convert_to_float(input_string: str) -> float | None:
    """
    Try to convert a string into float. Return `None` if an error occurs. 
    """
    try:
        float_s = float(input_string)
        return float_s
    except:
        return None


def numerical_equal(a: str, b: str) -> bool | None:
    """
    Check if two strings are numerical equal. 
    """
    a_int = convert_to_int(a)
    b_int = convert_to_int(b)

    if a_int is not None and b_int is not None:
        return a_int == b_int

    a_float = convert_to_float(a)
    b_float = convert_to_float(b)

    if a_float is not None and b_float is not None:
        return isclose(a_float, b_float, rel_tol=1e-3)

    return None


def literal_check(model_generated_answer: str, ground_truth: str) -> bool:
    """
    Check if two strings are the same character by character
    """
    model_remove = model_generated_answer.replace(",", " ").replace(" ", "")
    gt_remove = ground_truth.replace(",", " ").replace(" ", "")

    if model_remove == gt_remove:
        return True

    if not has_numbers(model_generated_answer) and not has_numbers(ground_truth):
        model_generated_answer = model_remove.strip("[]() ")
        ground_truth = gt_remove.strip("[]() ")
        if model_generated_answer == ground_truth:
            return True

    return False


def number_check(model_generated_answer: str, ground_truth: str) -> bool | None:
    """
    Check if two strings have the same mathematical meaning. 
    """
    if "," in model_generated_answer or "," in ground_truth:
        return None

    model_generated_answer = remove_prefix_and_suffix(remove_equals(model_generated_answer))
    ground_truth = remove_prefix_and_suffix(remove_equals(ground_truth))

    numerical_equal_result = numerical_equal(model_generated_answer, ground_truth)
    if numerical_equal_result is not None:
        return numerical_equal_result

    symbolic_equal_result = symbolic_equal(model_generated_answer, ground_truth)

    if symbolic_equal_result is not None:
        return symbolic_equal_result

    return None


def clean_answer(string: str) -> str:
    string = string_normalization(string)
    string = remove_prefix_and_suffix(string)
    return string


def clean_answer_number(answer_part: str) -> str:
    answer_part = string_normalization(answer_part)
    answer_part = remove_text_box_only(answer_part)
    answer_part = remove_boxes_keep_content(answer_part)
    answer_part = remove_prefix_and_suffix(answer_part)
    return answer_part


EXTRACT_RE_PATTERNS = [
    ".* final answer is (.*)",
    "final answer is: (.*)",
    "answer is (.*)",
    "answer is: (.*)",
    r"\*\*Answer:\s+\\\((.*)\\\).*\*\*",
    r"\*\*Answer:\*\*\s+\\\((.*)\\\).*",
    r"Answer:\s+\\\((.*)\\\).*",
    r"\*\*Answer:\s+\\\[(.*)\\\].*\*\*",
    r"\*\*Answer:\*\*\s+\\\[(.*)\\\].*",
    r"Answer:\s+\\\[(.*)\\\].*",
    r"\*\*Answer:\s+(.*)\*\*",
    r"\*\*Answer:\*\*\s+(.*)",
    r"Answer:\s+(.*)",
]


def get_gt_answer(gt: str, extract_policy: str = "strict") -> str:
    gt = extract_answer(gt, extract_policy=extract_policy)

    gt_norm = clean_answer(gt)
    gt_norm_wo_boxes = remove_boxes_keep_content(gt_norm)

    return gt_norm_wo_boxes


def check_one_latex_answer(
    model_ans: str | None,
    gt: str,
    extract_policy: str = "flex",
    eval_policy: str = "aggressive",
    debug: bool = False,
) -> dict[str, Any]:
    """Compare answer extracted from model generation with ground-truth answer

    In practice, this function sometimes stalls on a query when run in a notebook, and
    requires a number of keyboard interrupts to keep going. It seems like complicated
    (or simply large) expressions can cause the latex parser to hang. We found it useful
    to add a timeout to the answer checker, failing if it worked for more than say 10s.

    Args:
        - model_ans: Model generated answer. Usually this is the full model generated text
        - gt: Ground truth answer. This should already for extracted from the solution text,
            e.g. `extract_answer(soln, extract_policy="strict")` was called
        - extract_policy: Policy for extraction, from ["flex", "none"]. This is an argument
            from the original code we ported over, and in practice is set to "flex". I added
            a new option "none" for cases where we have post-extraction model answers, and
            therefore can skip the first step.
        - eval_policy: Policy for answer checking. Again, from the original code.
            In practice, I've never changed from the default
        - debug: Starts a pdb session midway into the code for debugging
    """
    out = {
        "generated_text": model_ans,
        "answer": gt,
    }

    # Step 1: Extract answer from response
    if model_ans is not None and extract_policy != "none":
        model_ans = extract_answer(
            model_ans, EXTRACT_RE_PATTERNS, extract_policy=extract_policy
        )
    
    out["answer"] = gt
    out["is_literal_correct"] = False
    
    if model_ans is None:
        out["predict"] = None
        out["is_correct"] = False
        return out
    
    # Step 2: Remove boxes and perform literal check
    # We don't remove text via `remove_text_box_only` because some answer are only text
    # e.g. otherwise we have \boxed{\text{(E)}} -> <empty str>
    # Compare strings character by character after simple processing including remove $%.
    # First we remove the boxes in the string but keeps the content
    # \boxed{\frac{13}{4}} --> \frac{13}{4}
    model_ans_norm = clean_answer(model_ans)
    model_ans_norm_wo_boxes = remove_boxes_keep_content(model_ans_norm)
    gt_norm = clean_answer(gt)
    gt_norm_wo_boxes = remove_boxes_keep_content(gt_norm)
    if debug:
        pdb.set_trace()

    literal_check_result = literal_check(
        remove_prefix_and_suffix(model_ans_norm_wo_boxes),
        remove_prefix_and_suffix(gt_norm_wo_boxes)
    )
    if literal_check_result:
        out["predict"] = remove_prefix_and_suffix(model_ans_norm_wo_boxes)
        out["is_correct"] = literal_check_result
        out["is_literal_correct"] = literal_check_result
        return out

    # Step 3: Attempt to parse -- single
    # Treat a string as a single number/extract a single number from a string and then compare. 
    # 
    # If we can accept a few mistakes, we try to extract numbers from the answers and compare them
    if eval_policy == "aggressive":
        # We want to use raw model_ans to keep the $$
        # $13$ meters --> $13$ --> 13
        model_ans_num_lst = search_for_numbers(model_ans)

        # We want the original answer has $$
        # This way we are able to consider the answer as a whole
        # We don't want \frac{13}{4} --> [13, 4] to be considered as 2 numbers
        if gt[0] != "$" or gt[-1] != "$":
            gt_num_lst = search_for_numbers("$" + gt + "$")
        else:
            gt_num_lst = search_for_numbers(gt)

        # We want to judge only those answers that contain only one number that represents the full
        # meaning of the original string. If the string still has LaTeX components or variables 
        # in addition to this number, then we believe that this number may not represent the meaning 
        # of the answer.
        # Here we must be really really careful.
        # x \\leq -5 vs. x \\geq -5
        # (-\\infty, 5) vs. (5, +\\infty)
        # TODO: We may have better methods to check if the numbers are simple enough
        if (
            len(model_ans_num_lst) == 1 and len(gt_num_lst) == 1 and
            not has_structure(model_ans.replace(model_ans_num_lst[0], "")) and
            not has_structure(gt.replace(gt_num_lst[0], ""))
        ):
            model_num = clean_answer_number(model_ans_num_lst[0])
            gt_num = clean_answer_number(gt_num_lst[0])
            parse_result = number_check(model_num, gt_num)

            # As an additional method of judgment, even if it returns False we can't say that 
            # the answer is wrong, it could be caused by an unreasonable extraction of numbers
            if parse_result:
                out["predict"] = model_num
                out["is_correct"] = True
                return out
    
    # Step 4: Check if answer is ordered tuple and attempt parse and compare each elem
    # We added this to the original Xwin code
    # If the answer looks like a tuple, split by commas and evaluate each part separately
    # TODO: can we use similar logic for unordered tuples? Might not have wrapping parens
    model_ans_elems = split_tuple(model_ans_norm)
    gt_elems = split_tuple(gt_norm)
    if model_ans_elems is not None and gt_elems is not None and len(model_ans_elems) == len(gt_elems):
        # If we found two elements, make sure the answer use the same parentheses/brackets.
        # This is relevant if the answer is an interval. 
        if len(model_ans_elems) != 2 or (model_ans_norm[0] == gt_norm[0] and model_ans_norm[-1] == gt_norm[-1]):
            is_correct = True
            for model_elem, gt_elem in zip(model_ans_elems, gt_elems):
                model_num = clean_answer_number(model_elem)
                gt_num = clean_answer_number(gt_elem)
                if not number_check(model_num, gt_num):
                    is_correct = False
                    break
            if is_correct:
                out["predict"] = model_ans_elems
                out["is_correct"] = True
                return out

    # Step 5: Try parsing and comparing again, this time to the whole string
    parse_result = number_check(model_ans_norm_wo_boxes, gt_norm_wo_boxes)
    out["predict"] = model_ans_norm
    if parse_result:
        out["is_correct"] = True
        return out

    # If none of the above ways can determine whether the answer is correct or incorrect,
    # then return incorrect
    out["is_correct"] = False
    return out


def latex_answer_check(
    question_answer_list: list[dict[str, str]],
    extract_policy: str = "flex",
    eval_policy: str = "aggressive",
    debug: bool = False,
    use_tqdm: bool = False,
    timeout=10,
) -> list[dict[str, Any]]:
    """Check answers for a list of model generations on short answer problems"""
    if use_tqdm:
        question_answer_list = tqdm(question_answer_list)
    
    results = []
    for prob in question_answer_list:
        model_ans = prob["generated_text"] if prob["finish_reason"] == "stop" else None
        gt = prob["answer"]
        out = run_with_timeout(check_one_latex_answer,
                                10,
                                {
                                    "generated_text": model_ans,
                                    "answer": gt,
                                    "predict": None,
                                    "is_correct": False,
                                    "is_literal_correct": False
                                },
                                model_ans,
                                gt,
                                extract_policy=extract_policy,
                                eval_policy=eval_policy,
                                debug=debug,
                            )
        results.append({**prob, **out})

    return results


def latex_answer_choice_check(
    question_answer_list: list[dict[str, str]],
    extract_policy: str = "flex",
    eval_policy: str = "aggressive",
    debug: bool = False,
    use_tqdm: bool = False,
) -> list[dict[str, Any]]:
    """Check answers for a list of model generations on multiple choice problems"""
    if use_tqdm:
        question_answer_list = tqdm(question_answer_list)
    
    results = []
    for prob in question_answer_list:
        model_ans = prob["generated_text"] if prob["finish_reason"] == "stop" else None
        gt = prob["answer_choice"]
        out = check_one_latex_answer(
            model_ans,
            gt,
            extract_policy=extract_policy,
            eval_policy=eval_policy,
            debug=debug,
        )
        
        # sanity check that I've enabled before and saw no errors
        # model_ans_choice = extract_answer(model_ans, EXTRACT_RE_PATTERNS) if model_ans is not None else "F"
        # model_ans_choice = remove_boxes_keep_content(clean_answer(model_ans_choice))
        # gt_choice = remove_boxes_keep_content(clean_answer(gt))
        # if out["is_correct"] != (model_ans_choice == gt_choice):
        #     print("WARNING: answer checker didnt match exact match:", out)
        
        results.append({**prob, **out})

    return results


def latex_choice_check(
    question_choice_list: list[dict[str, str]],
    extract_policy: str = "flex",
    eval_policy: str = "aggressive",
    debug: bool = False,
    use_tqdm: bool = False,
    timeout=10,
) -> list[dict[str, Any]]:
    if use_tqdm:
        question_choice_list = tqdm(question_choice_list)
    
    results = []
    for prob in question_choice_list:
        model_ans = prob["generated_text"] if prob["finish_reason"] == "stop" else None
        by_choice_dict = dict()
        for c in prob["choices"]:
            by_choice_dict[c] = run_with_timeout(
                check_one_latex_answer,
                timeout,
                {
                    "generated_text": model_ans,
                    "answer": prob["choices"][c],
                    "predict": None,
                    "is_correct": False,
                    "is_literal_correct": False,
                },
                model_ans,
                prob["choices"][c],
                extract_policy=extract_policy,
                eval_policy=eval_policy,
                debug=debug,
            )
        results.append({**by_choice_dict, **prob})

    return results
