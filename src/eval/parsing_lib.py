# ---------------------------------------------------------
# Xwin-Math
# Copyright (c) 2023 Xwin-Math Team
# Licensed under The MIT License [see LICENSE for details]
# Written by Weiqi Wang
# Modified by Albert Yue
# ---------------------------------------------------------

import re

from pyparsing import (
    Char,
    CharsNotIn,
    Combine,
    DelimitedList,
    Forward,
    Literal,
    OneOrMore,
    Optional,
    SkipTo,
    Suppress,
    Word,
    ZeroOrMore,
    nested_expr,
    one_of,
    original_text_for,
    alphanums as ALPHANUMS,
    nums as NUMS,
)


TEXT_BOX_CMDS = ["\\mbox", "\\textbf", "\\texttt", "\\text", "\\mathrm", "\\mathbf"]


def extract_answer(
    solution: str, extraction_regexes: list[str] | None = None, extract_policy: str = "flex"
) -> str:
    """
    Extract answer from response.

    Try the following in order:
        1. Given a list of possible regexes `split` for the answer format in the solution,
           search for each and take the text in the group. If there are multiple matches,
           use the shortest one
        2. Look for boxed expressions and return the last
        3. (if extract_policy == "flex"), Return the last numerical value
        4. Return None
    """
    if extraction_regexes is not None:
        solution_split_list = []
        for final_answer_format in extraction_regexes:
            if bool(re.search(final_answer_format, solution, flags=re.DOTALL)):
                solution_split_list.append(
                    re.findall(final_answer_format, solution, flags=re.DOTALL)[-1]
                )
    
        shortest = None
        if len(solution_split_list) != 0:
            for ans in solution_split_list:
                if shortest is None or len(ans) < len(shortest):
                    shortest = ans
            return shortest

    boxes = search_for_boxes(solution)
    if len(boxes) != 0:
        return boxes[-1]
    
    if extract_policy == "flex":
        numbers = search_for_numbers(solution)
        if len(numbers) != 0:
            return numbers[-1]

    return None


def remove_prefix_and_suffix(string: str) -> str:
    """
    Remove unnecessary prefixes and suffixes from the input strings
    """
    return string.strip(" \n").rstrip(".").strip(" \n").rstrip(".")


def clean_latex_whitespace(text: str) -> str:
    """
    Cleans up the many ways in latex to denote added whitespace

    Specifically, we remove:
    "\ ", "\qquad", "\quad", "~", "\!"
    """
    text = re.sub(r'\\\\', ' ', text)
    text = re.sub(r'\\ ', ' ', text)
    text = re.sub(r'\\;', ' ', text)
    text = re.sub(r'\\qquad', ' ', text)
    text = re.sub(r'\\quad', ' ', text)
    text = re.sub(r'[^\\]~+', ' ', text)
    text = re.sub(r'^~+', ' ', text)
    text = re.sub(r'\\!', '', text)
    return text.strip()


def clean_latex_leftright(text: str) -> str:
    text = re.sub(r'\\left', '', text)
    text = re.sub(r'\\right', '', text)
    return text.strip()


def clean_aesthetic_latex_cmds(text: str) -> str:
    """Clean up some latex commands that are mainly aesthetic"""
    text = extract_content_from_cmds(text, ['\\displaystyle', '\\textstyle'])
    text = re.sub(r'\\textstyle', '', text)
    text = re.sub(r'\\displaystyle', '', text)
    return text


def fix_mixed_fractions(string: str) -> str:
    """Fixes mixed fractions for latex parsing
    By default, parse_latex("1 1/2") would be interpreted as 1*1/2 = 1/2.
    This function adds a `+` sign to get the correct interpretation
    """
    regex = re.compile(r"([0-9]+) +([0-9]+/[0-9]+)")
    string = regex.sub("\\1+\\2", string)

    latex_regex = re.compile(r"([0-9]) *(\\frac)")
    string = latex_regex.sub("\\1+\\2", string)
    return string


def fix_sqrt(string: str) -> str:
    """Fixes missing braces for latex parsing
    Taken from prm800k/grading/math_normalize.py
    """
    if "\\sqrt" not in string:
        return string
    splits = string.split("\\sqrt")
    new_string = splits[0]
    for split in splits[1:]:
        if split[0] != "{" and split[0] != "[":
            a = split[0]
            new_substr = "\\sqrt{" + a + "}" + split[1:]
        else:
            new_substr = "\\sqrt" + split
        new_string += new_substr
    return new_string


def string_normalization(string: str) -> str:
    """
    Remove or replace special symbols and convert to lowercase
    """
    string = (
        string
        .replace("\\$", "")
        .replace("$","")
        .replace("\\%", "")
        .replace("%", "")
        .replace("\u00b0", "")
        .replace("^\\circ", "")
        .replace("^{\\circ}", "")
        .replace("\u03c0", "\\pi")
        .replace("{,}", "")
        .replace("\\textstyle", "")
        .lower()
    )
    string = (
        string
        .replace("\\dfrac", "\\frac")
        .replace("\\tfrac", "\\frac")
    )
    string = re.sub(r"\\hspace{.*?}", "", string)
    string = clean_latex_whitespace(string)
    string = clean_latex_leftright(string)
    string = clean_aesthetic_latex_cmds(string)
    string = fix_sqrt(string)
    string = fix_mixed_fractions(string)
    return string


def search_for_intervals(input: str) -> str:
    r"""
    Extract the interval in the answer
    For example:
        The answer is: (-\infty, 0) \cup (1, +\infty) and [1, 2]. --> ["(-\infty, 0) \cup (1, +\infty)", "[1, 2]"]
    """
    latex_objects = Word(ALPHANUMS + "+ - * / ^ | % $ ! \\ { }")
    left_bracket = one_of("[ (")
    right_bracket = one_of("] )")
    space = Optional(" ")
    interval = left_bracket + latex_objects + space + "," + space + latex_objects + right_bracket
    intervals = Combine(DelimitedList(interval, delim=space + "\\cup" + space, combine=True))

    result = intervals.search_string(input)
    return [_[0] for _ in result]


def search_for_joint_element_with_bracket(input: str) -> list[str]:
    """Extract parallel elements wrapped in parentheses"""
    nestedParens = Forward()
    nestedBraces = Forward()
    nestedSquareBrackets = Forward()

    nestedParens << ("(" + ZeroOrMore(nestedParens | nestedBraces | nestedSquareBrackets | CharsNotIn("()")) + ")")
    nestedBraces << ("{" + ZeroOrMore(nestedParens | nestedBraces | nestedSquareBrackets | CharsNotIn("{}")) + "}")
    nestedSquareBrackets << ("[" + ZeroOrMore(nestedParens | nestedBraces | nestedSquareBrackets | CharsNotIn("[]")) + "]")

    parser = nestedParens | nestedBraces | nestedSquareBrackets

    result_list = parser.search_string(input)
    filtered_result_list = []

    for result_item in result_list:
        result_item_str = "".join(result_item)
        if "," in  result_item_str:
            filtered_result_list.append(result_item_str)

    return filtered_result_list


def search_for_joint_elements_without_bracket(input: str) -> list[str]:
    if "," in input:
        return ["{" + input + "}"]

    return []


def get_integer_with_comma_regex() -> Combine:
    comma = ","
    not_num = ~Literal(NUMS)
    digit_first = Word(NUMS, max=3)
    digit_others = Word(NUMS, min=3, max=3)
    sign = Optional(Word("+-", exact=1))

    return Combine(sign + digit_first + OneOrMore(comma + digit_others) + not_num)


def remove_commas_from_integers(input: str) -> str:
    number_with_comma = get_integer_with_comma_regex()

    def replace_commas(tokens):
        return tokens[0].replace(",", "")

    number_with_comma.set_parse_action(replace_commas)
    return number_with_comma.transform_string(input)


def search_for_boxes(input: str) -> list[str]:
    element = original_text_for(nested_expr("{", "}"))
    parser = Literal("\\boxed") + element | Literal("\\mbox") + element
    results = parser.search_string(input)
    return [_[1][1:-1] for _ in results]


def search_for_numbers(input: str) -> list[str]:
    integer = Word("-"+NUMS, NUMS)
    fraction = Combine(Word("-"+NUMS, NUMS) + "/" + Word(NUMS))
    decimal = Combine(Optional(Word("-"+NUMS, NUMS)) + "." + Word(NUMS))
    scientific = Combine(Word("-"+NUMS, NUMS) + "e" + Word("-"+NUMS, NUMS))
    latex = Combine(Suppress("$") + SkipTo("$") + Suppress("$"))
    number_with_comma = get_integer_with_comma_regex()

    parser = latex | scientific | fraction | decimal | number_with_comma | integer

    return [_[0] for _ in parser.search_string(input)]


def remove_text_box_only(input: str) -> str:
    tex_expr = one_of(TEXT_BOX_CMDS) + nested_expr("{", "}") + Optional("^" + Char(NUMS))
    return "".join(tex_expr.suppress().transform_string(input))


def extract_content_from_cmds(input_string: str, cmds: list[str]) -> str:
    for cmd in cmds:
        while True:
            start = input_string.find(cmd)
            if start == -1: # cmd type not found
                break
            brace_start = input_string.find("{", start)
            if brace_start == -1: # "{" not found after cmd type
                break
            if not bool(re.fullmatch(r"\s*", input_string[start+len(cmd):brace_start])):
                # print(f"WARNING content between cmd {cmd} and first brace: {input_string[start:brace_start]}")
                break
            brace_count = 0
            for i in range(brace_start, len(input_string)):
                if input_string[i] == "{":
                    brace_count += 1
                elif input_string[i] == "}":
                    brace_count -= 1
                if brace_count == 0: # matching "}" found
                    brace_end = i
                    break
            else: # matching "}" not found
                break
            # remove cmd type but keep the content inside
            input_string = input_string[:start] + input_string[brace_start+1:brace_end] + input_string[brace_end+1:]
    return input_string


def remove_boxes_keep_content(input_string: str) -> str:
    box_types = ["\\box", "\\boxed"] + TEXT_BOX_CMDS
    return extract_content_from_cmds(input_string, box_types)


def remove_equals(input_string: str) -> str:
    if "=" in input_string and len(input_string.split("=")) == 2:
        left, right = input_string.split("=")
        if remove_prefix_and_suffix(right) == "0" and len(remove_prefix_and_suffix(left)) >= 2:
            return left
        else:
            return right
    return input_string


def split_tuple(ans: str) -> list[str] | None:
    """Split a tuple-like string into its components or return None
    
    Based of the implementation in https://github.com/openai/prm800k/blob/main/prm800k/grading/grader.py
    with some more specific sanity checks
    """
    # don't split on commas in integers
    ans = remove_commas_from_integers(ans)
    
    if len(ans) > 2 and ans[0] in "()[]" and ans[-1] in "()[]":
        paren_count = 0
        for i in range(len(ans)):
            if ans[i] in "([":
                paren_count += 1
            elif ans[i] in ")]":
                paren_count -= 1

            if paren_count < 1 and i != len(ans) - 1:
                # Starting and ending parens don't match
                return None
        
            if ans[i] == "," and paren_count > 1:
                # Found comma inside another set of parens,
                # fail and return None out of caution
                return None
            
        return [remove_prefix_and_suffix(elem) for elem in ans[1:-1].split(",")]
    return None
