import html
import json
import os
import pickle as pkl
import re
from typing import Any

import numpy as np
import tiktoken
from requests import Response
from tqdm import tqdm

from eval.parsing_lib import (
    clean_aesthetic_latex_cmds,
    clean_latex_whitespace,
    clean_latex_leftright,
    remove_boxes_keep_content,
)
from scraping.aops_wiki.difficulty import map_difficulty
from scraping.aops_wiki.line_filters import (
    MANUAL_LINE_FILTERS,
    ASY_DOUBLE_SLASH_CREDIT_COMMENTS
)
from scraping.aops_wiki.utils import all_year_contest_problem_map, has_choices, has_answer, total_problems


def convert_ordered_list(s: str) -> str:
    converted = []
    for i, (tag, elem) in enumerate(re.findall(r"<(li|p)>(.*?)</\1>", s, flags=re.DOTALL)):
        elem: str = elem.strip()
        elem = re.sub(r'::marker\s*', '', elem)
        elem = re.sub(r'</?p>', '', elem)
        if tag == "li":
            converted.append(f"{i+1}. {elem}")
        else:
            converted.append(elem)
    return "<p>" + "\n".join(converted) + "</p>"


def replace_img_alt_text(s: str) -> str:
    """Extract img block alt text.
    
    For latex images, this contains the source latex code.
    For actual images, this is the file name or a caption. In this case, we return an empty string
    """
    def _replace_one(alt_text: str) -> str:
        if bool(re.fullmatch(r'^.*\.(png|jpeg|jpg|gif)$', alt_text, flags=re.IGNORECASE)):
            print("WARNING: Dropping image alt text that looks like image file name: {}".format(alt_text))
            return ""
        
        if (
            (alt_text.startswith("$") and alt_text.endswith("$")) or
            (alt_text.startswith("\\[") and alt_text.endswith("\\]")) or
            (alt_text.startswith("\\(") and alt_text.endswith("\\)")) or
            (alt_text.startswith("\\begin{")) or
            (alt_text.startswith("[asy]") and alt_text.endswith("[/asy]"))
        ):
            # TODO: Should we wrap \begin{...}...\end{...} and [asy] blocks in $...$?
            # They compile just fine on AoPS, hence why they aren't there in the first place
            if "$" in alt_text[1:-1] and not alt_text.startswith("[asy]"):
                print("Found $ in latex {}".format(alt_text))
                alt_text = alt_text[0] + re.sub(r"\$", r"\\textdollar", alt_text[1:-1]) + alt_text[-1]
            return alt_text
        
        print("WARNING: Dropping image alt text that doesn't look like latex: {}".format(alt_text))
        return ""

    return re.sub(r'<img[^>]*alt="([^"]*)"[^>]*>', lambda x: _replace_one(x.group(1)), s)


def standardize_boxed_command(text: str) -> str:
    text = re.sub(r'\\fbox', r'\\boxed', text) 
    text = re.sub(r'\\framebox(\[.*?\])?', r"\\boxed", text)
    text = re.sub(r'\\boxed +{', r'\\boxed{', text) 
    return text


def replace_unicode_chars(text: str) -> str:
    text = re.sub('\u00a0', ' ', text)
    text = re.sub('\u200b', '', text)
    text = re.sub('\u2018', "'", text)
    text = re.sub('\u2019', "'", text)
    text = re.sub('\u201c', "'", text)
    text = re.sub('\u201d', "'", text)
    text = re.sub('\uff0c', ', ', text)
    text = re.sub('\u2013', '-', text)
    text = re.sub('\u2014', '--', text)
    text = re.sub('\u301c', '~', text)
    text = re.sub('\u00a9', '(C)', text)  # happens in Solution 10 of 2017 AMC_12A #23
    return text


def remove_emails(text: str) -> str:
    return re.sub(r'\S+@\S+', '', text)


def line_level_filter(text: str) -> str:
    """Remove last lines that are unrelated to the actual math content, like links and usernames"""
    prefix_pattern = r'(By|Solution( Edited| Written)?|Edited|(Minor )?(clarity |LaTeX |)?Edits?( made)?|(Second )?Editor|Proposed|Credit|(Original )?Diagram|Written|Latex)( (By|To))?:?'
    username_pattern = r'[a-z|A-Z][-_\w]*?( [a-z|A-Z][-_\w]*?)?'
    main_pattern = rf'^(-\s*)?\(?{prefix_pattern} ?{username_pattern}(,? and {username_pattern})?\.?\)?:?\s*$'

    lines = text.split('\n')

    manual_filters = set([m.strip().lower() for m in MANUAL_LINE_FILTERS])
    new_lines = []
    for line in lines:
        if line.strip().lower() in manual_filters:
            print("WARNING: removing line from manual match. Raw: {}".format(line))
        else:
            new_lines.append(line)
    lines = new_lines
    
    while len(lines) > 0:
        if len(lines[-1]) == 0:
            lines.pop()
            continue
        if len(lines[0]) == 0:
            lines = lines[1:]
            continue
        
        # Delete ending lines with links
        if 'http' in lines[-1]:
            print("WARNING: removing line due to http. Raw:\n{}".format(lines[-1]))
            lines.pop()
            continue

        if lines[-1] == '<a class="mw-selflink selflink">Solution</a>':
            # Some problems have a self-link to the solution section.
            # This is likely just a mistake from copy-pasting from the full problems page
            # and either way we can remove it
            print("WARNING: removing self-link. Raw: {}".format(lines[-1]))
            lines.pop()
            continue
        
        # Delete ending lines with usernames. Users commonly sign at the end of their solutions
        if bool(re.match(r'^\s*[-~][-~]?[-~]? ?[a-z|A-Z][-_\w]*?.?\s*', lines[-1])):
            print("WARNING: removing line due to username. Raw: {}".format(lines[-1]))
            lines.pop()
            continue
        if bool(re.match(main_pattern, lines[-1], flags=re.IGNORECASE)):
            print("WARNING: removing line due to username. Raw: {}".format(lines[-1]))
            lines.pop()
            continue
        # additional manually added username filter that isn't handled by regexes above
        if bool(re.fullmatch(r'^\s*vvsss\s*(</b>)?\s*$', lines[-1])):
            print("WARNING: removing line due to username vvsss. Raw: {}".format(lines[-1]))
            lines.pop()
            continue
        if bool(re.fullmatch(r'^<i>Credit( to|:) Math1331Math</i>$', lines[-1])):
            print("WARNING: removing line due to username Math1331Math. Raw: {}".format(lines[-1]))
            lines.pop()
            continue
        if bool(re.fullmatch(r'^Solution by \$(.+?)\$\.?S', lines[-1])):
            # e.g. 1970 AHSME #19: "Solution by $\\underline{\\textbf{Invoker}}$"
            print("WARNING: removing line due to username. Raw: {}".format(lines[-1]))
            lines.pop()
            continue

        # Sometimes users sign at the start of a solution
        if bool(re.match(main_pattern, lines[0], flags=re.IGNORECASE)):
            print("WARNING: removing first line due to username. Raw: {}".format(lines[0]))
            lines = lines[1:]
            continue
        if lines[0].startswith("[asy]") and len(lines) > 1 and bool(re.match(main_pattern, lines[1], flags=re.IGNORECASE)):
            print("WARNING: removing first line due to username. Raw: {}".format(lines[1]))
            lines = [lines[0]] + lines[2:]
            continue
        
        break

    return '\n'.join(lines) + '\n'


def clean_asymptote(asy: str) -> str:
    # This has a couple false positives, but they aren't that important as comments
    # False positives are "/* scale down by 100x */" and "/* to force rendering by using a white line */"
    asy = re.sub(r'/\*[^*]*by[^*]*\*/', '', asy)
    asy = re.sub(r'/\*[^*]*[Aa]zjps[^*]*\*/', '', asy)
    # asymptote uses newlines, but those aren't preserved in the html
    # so it's hard to isolate the comment text... so remove common credit comments by hand
    for pattern in ASY_DOUBLE_SLASH_CREDIT_COMMENTS:
        asy = re.sub(pattern, '', asy)
    return asy


def get_parsed_lines_from_html(http_resp: Response) -> str:
    retval = []
    raw_html = http_resp.text

    # Remove the table of contents element if it's there, as it will mess with later regexes
    if bool(toc_match := re.search(r'<div [^>]*?"toc"[^>]?>', raw_html)):
        start_idx = toc_match.span()[1]
        cnt = 1
        for i, c in enumerate(raw_html[start_idx:]):
            if c == "<":
                if raw_html[start_idx+i:start_idx+i+4] == "<div":
                    cnt += 1
                elif raw_html[start_idx+i:start_idx+i+6] == "</div>":
                    cnt -= 1
                if cnt == 0:
                    break
        raw_html = raw_html[:start_idx].strip() + raw_html[start_idx+i+6:].strip()

    raw_html = re.sub(r'\s*<hr />\s*', '', raw_html)
    raw_html = re.sub(r'<p class="mw-empty-elt">\s*</p>', '', raw_html)
    raw_html = re.sub(r'center>', 'p>', raw_html) # replace <center> tag with <p> tag
    raw_html = re.sub(r'(<div class="(center|(float(right|left|none)))">)+(.+?)(</div>)+', r'<p>\5</p>', raw_html)
    raw_html = re.sub(r'(<div style="text-align:center;?">)+(.+?)(</div>)+', r'<p>\2</p>', raw_html)
    
    raw_html = re.sub(r'<ol([^>]*?)>(.+?)</ol>', lambda x: convert_ordered_list(x.group(2)), raw_html, flags=re.DOTALL)
    raw_html = re.sub(r'<(/)?[du]l([^>]*?)>', r'<\1p>', raw_html)
    raw_html = re.sub(r'<li>(.+?)</li>', r'* \1\n', raw_html)
    raw_html = re.sub(r'<dd>(.+?)</dd>', r'\1\n', raw_html)
    raw_html = re.sub(r'<dt>(.+?)</dt>', r'\1\n', raw_html)
    raw_html = re.sub(r'::marker\s*', '', raw_html)

    # Collapse nested <p> blocks, e.g. 2011 AMC12B #20 Solution 5
    raw_html = re.sub(r'<p>\s*<p>', r'<p>', raw_html)
    raw_html = re.sub(r'</p>\s*</p>', r'</p>', raw_html)
    # Combine adjacent <p> blocks
    raw_html = re.sub(r'</p><p>', '', raw_html)
    raw_html = re.sub(r'</p>\n+<p>', '\n', raw_html)
    raw_html = re.sub(r'</p>\s+<p>', ' ', raw_html)

    raw_html = re.sub(r'<br />', '\n', raw_html)
    raw_html = re.sub('<a (.*?)href=".+?>(.+?)</a>', r'\2', raw_html)  #re.sub(r'<a href.*>(.*)</a>', '', raw_html)
    for a, b in re.findall(r'>([^<]*Problem ?#?\d*|Solution[^<]*)<[^\n]*\n<p>(.*?)</p>', raw_html, re.DOTALL):
    # for a, b in re.findall(r'>([^<]*Problem|Solution[^<]*)<[^\n]*\n<p>(.*)\n', raw_html):
        if a.startswith('Problem'):
            a = 'Problem'
        retval.append('# '+a)
        # print('-'*100)
        # print(b)
        parsed = replace_img_alt_text(b)
        parsed = re.sub(r'\[asy\](.*?)\[/asy\]', lambda x: "[asy]" + clean_asymptote(x.group(1)) + "[/asy]", parsed)
        # gets rid of usernames, which tend to appear on newlines starting with '~'
        # or at the end of lines
        parsed = re.sub(r'^~.*', '', parsed, flags=re.MULTILINE)
        parsed = re.sub(r'\s[~|-][a-z|A-Z][-_\w]*?$', '', parsed, flags=re.MULTILINE)
        # gets rid of alternate solutions prompt
        parsed = re.sub(r'<i>Alternate solutions.*?</i>', '', parsed)
        parsed = standardize_boxed_command(parsed)
        parsed = html.unescape(parsed)
        parsed = replace_unicode_chars(parsed)
        parsed = remove_emails(parsed)
        parsed = re.sub(r'\\\[\\\]', '', parsed)  # sometimes used and is empty
        # replace mathjax with latex dollar signs
        parsed = re.sub(r"\[mathjax display=true\](.*?)\[/mathjax\]", r"\[\1\]", parsed)
        parsed = re.sub(r"\[mathjax\](.*?)\[/mathjax\]", r"$\1$", parsed)
        parsed = line_level_filter(parsed)
        if a == 'Problem':
            # Some olympiad problems start with the author
            parsed = re.sub(r'^\(<i>([^<>]+?)</i>\)\s*', '', parsed)
            parsed = re.sub(r'^\([a-zA-Z]+ [a-zA-Z]+\)\s*', '', parsed)
        if a.startswith("Solution"):
            if parsed.startswith("$\\boxed{") and parsed.count("\\boxed{") == 1:
                end_idx = len("$\\boxed{") + find_closing_brace(parsed[len("$\\boxed{"):]) + 2
                if len(parsed[end_idx:].strip()) > 0:
                    print("WARNING: moving only boxed value to end of solution.")
                    parsed = parsed[end_idx:].strip() + "\n" + parsed[:end_idx]

        parsed = re.sub('\n+', '\n', parsed)
        # print(parsed)
        # print('-'*100)
        retval.append(parsed)
    return '\n'.join(retval)


def clean_choice_format(text: str) -> str:
    for i in range(5):
        c = chr(65+i)
        # Manual check for 2005 AMC12A
        if f'(\\mathrm{{{c}}})' in text:
            text = re.sub(r'\(\\mathrm{(\w)}\)', r'\\mathrm{(\1)}', text)
        # Manual check for 1951 AHSME
        if f'(\\mathrm {{{c}}})' in text:
            text = re.sub(r'\(\\mathrm {(\w)}\)', r'\\mathrm{(\1)}', text)
        # Manual check for 2014 AMC10B
        if f'\\textbf {{({c})' in text:
            text = re.sub(r'\\textbf {\((\w)\)', r'\\textbf{(\1)', text)
        # Manual check for 1982 AHSME
        if f'\\text {{({c})' in text:
            text = re.sub(r'\\text {\((\w)\)', r'\\text{(\1)', text)
    return text


def clean_choice(text: str) -> str:
    text = clean_latex_whitespace(text)
    text = clean_latex_leftright(text)
    text = clean_aesthetic_latex_cmds(text)
    return text


def find_closing_brace(text: str) -> int:
    cnt = 1
    for i, c in enumerate(text):
        if c == "{":
            cnt += 1
        if c == "}":
            cnt -= 1
            if cnt == 0:
                return i
    return -1


def extract_choices(text: str) -> str:
    # GPT4 was not useful for a regex here...
    # choices = re.findall(r'\((\w)\)[.*?\W*\\text*](.*?)(?=\\qquad|$)', text)
    # return {choice[0]: choice[1] for choice in choices}

    format_str = None
    choices_start = -1
    for poss in ['\\textbf{', '\\text{', '\\mathrm{']:
        poss_start = text.find('$'+poss+'(A)')
        if poss_start >= 0:
            format_str = poss
            choices_start = poss_start
            break
    if format_str is None:
        print("ERROR: could not find choices in:\n{}".format(text))
        return None
    choices_end = text.find('\n', text.find(format_str+'(E)'))
    if choices_end == -1:
        choices_end = len(text)-1
    assert choices_end > choices_start, f"Got choices_end {choices_end} <= choices_start {choices_start}"

    remaining_text = text
    retval = dict()
    for c in range(5):
        look_for = format_str+'({choice})'.format(choice=chr(65+c))
        index = text.find(look_for)
        if index == -1:
            print("ERROR: Didn't find choice {} using format_str {} in:\n{}".format(chr(65+c), format_str, text))
            return None

        index += len(look_for)
        remaining_text = text[index:]

        brace_idx = find_closing_brace(remaining_text)
        if brace_idx == -1:
            print("ERROR: Couldn't find closing brace for choice {} in remaining text:\n{}".format(chr(65+c), remaining_text))
            return None
        raw_before_brace = clean_choice(remaining_text[:brace_idx]).lstrip()
        if raw_before_brace and format_str.startswith("\\text"):
            raw_before_brace = "\\text{" + raw_before_brace + "}"
        if c < 4:
            next_look = format_str+'({choice})'.format(choice=chr(65+c+1))
            end = remaining_text.find(next_look)
            raw_after_brace = remaining_text[brace_idx+1:end]
            # Check an alternate char (\n) that indicates the end of an answer choice
            alt_end = remaining_text.find("\n", brace_idx+3)
            if alt_end != -1 and alt_end < end:
                if not bool(re.fullmatch(r"^\s*\$?\s*(\\q?quad)?\s*", remaining_text[alt_end:end])):
                    print("ERROR: Found non-trivial value between alt_end and end! {}".format(remaining_text[alt_end:end]))
                    return None
                end = alt_end
                raw_after_brace = remaining_text[brace_idx+1:alt_end]
        else:
            # There may be problem content after the answer choices, e.g. a diagram or footnote
            # So we check for newlines and split on that
            end = remaining_text.find("\n", brace_idx+3)
            if end == -1:
                raw_after_brace = remaining_text[brace_idx+1:]
            else:
                raw_after_brace = remaining_text[brace_idx+1:end]
        raw_choice = raw_before_brace + " " + raw_after_brace.strip()

        choice = clean_choice(raw_choice)
        choice = re.sub(r'[\s\$]*$', '', choice).strip()

        if choice.startswith('$'):
            print("WARNING: Found non-latex choice {} answer text for problem text:\n{}".format(chr(65+c), text))
            # In this case, each answer choice letter is formatted with '$', which means
            # the remaining text is *not in latex*
            # We thus set the choice to be
            choice = choice[1:].rstrip('$').strip()
            if choice.count('$') % 2 == 1:
                choice = choice + '$'
            if '[asy]' in choice:
                print("ERROR: Found asymptote in choice {}:\n{}".format(chr(65+c), text))
                return None
            retval[chr(65+c)] = choice
            continue
        choice = '${}$'.format(choice)
        if '$' in choice[1:-1]:
            choice = re.sub(r'\$\$', '', choice).strip()
            print("WARNING: Weirdly found latex in choice {} for problem text:\n{}".format(chr(65+c), text))
            print("Choice: {}".format(choice))
        if '[asy]' in choice:
            print("ERROR: Found asymptote in choice {}:\n{}".format(chr(65+c), text))
            return None
        if len(choice) <= 2:
            print("ERROR: Found empty choice {} -- raw: {}, full:\n{}".format(chr(65+c), raw_choice, text))
            return None
        retval[chr(65+c)] = choice
            
    return {'choices': retval, 'choices_start_ind': choices_start, 'choices_end_ind': choices_end+1}


def extract_last_boxed_from_text(text: str) -> str | None:
    prefix = "\\boxed{"

    ind = text.rfind(prefix)
    if ind == -1:
        return None
    
    close_idx = find_closing_brace(text[ind+len(prefix):])
    if close_idx == -1:
        print("ERROR: Failed to extract boxed due to no closing }")
        return None
    return text[ind+len(prefix):ind+len(prefix)+close_idx]


def standardize_answer(boxed: str, choices: dict[str, str] | None, logging_prob_text: str = "") -> str | None:
    """Standardize boxed answer for the different contests
    
    Args:
        - boxed: str inside a \\boxed{...} cmd
        - choices: dict of answer choice letters to value. None for non-multiple choice problems
        - logging_prob_text: some identifying information about the text that `boxed` was extracted from
    
    Returns: the answer choice or integer answer, depending on multiple-choice or AIME.
        Returns None if 1) couldn't determine the unique answer choice for multiple choice
        or 2) the boxed value is not an interger for AIME problems
    """
    # If choices, look to extract just the letter of the answer
    # We'll then use the letter to get the actual choice
    if choices is not None:
        answers = [choice for choice in choices if "({})".format(choice) in boxed]
        if len(answers) == 0:
            # Try looking for answer choice without parens
            answers = [choice for choice in choices if "{}".format(choice) in boxed]
            if len(answers) > 0:
                print(f"WARNING: Found non-standard letter answer format in boxed in {logging_prob_text}")
            else:
                # Try looking for exact match with answer value, e.g. 2011 AMC12B #20
                # This is purposely exact to avoid false positives
                # TODO: add some basic standardization like \\frac == \\dfrac
                boxed = clean_choice(boxed)
                answers = [
                    choice
                    for choice, choice_val in choices.items() 
                    if choice_val == boxed or choice_val == "$" + boxed + "$"
                ]
                if len(answers) > 0:
                    print(f"WARNING: Found non-standard answer value format in boxed in {logging_prob_text}")

        if len(answers) != 1:
            print(f"WARNING: Skipping solution with != 1 answer in boxed in {logging_prob_text}")
            return None
        return answers[0]
    else:
        # An AIME problem
        try:
            boxed = clean_choice(boxed)
            boxed = remove_boxes_keep_content(boxed)
            boxed = boxed.strip("()[]{} \n\r\t\f\v")
            return "${}$".format(int(boxed))
        except ValueError:
            print(f"WARNING: Found AIME solution with non-integer solution in {logging_prob_text}")
            return None


def get_problem_solution_choices(d: dict[str, Any]) -> dict[str, Any]:
    retval = dict()
    retval['choices'] = dict() if has_choices(d['contest']) else None
    full_text: str = d["full_text"]
    pieces: list[str] = re.split(r'\n{2,}#', full_text)
    pieces = [("#" + p if i > 0 else p) for i, p in enumerate(pieces)]

    # Problem processing
    if pieces[0].startswith("# Problem"):
        # Strip header
        problem_text = '\n'.join(pieces[0].split('\n')[1:]).strip()
        problem_text = re.sub(r'^\$(\*)\$\s*', '', problem_text)  # indicator in olympiad questions to include a diagram
        if has_choices(d['contest']):
            problem_text = clean_choice_format(problem_text)
            extracted_choices = extract_choices(problem_text)
            if extracted_choices is not None:
                retval['choices'] = extracted_choices['choices']
                if problem_text[extracted_choices['choices_end_ind']:]:
                    print(f"INFO: Found ending text: {problem_text[extracted_choices['choices_end_ind']:]}")
                problem_text = problem_text[:extracted_choices['choices_start_ind']] + problem_text[extracted_choices['choices_end_ind']:]
            else:
                print(f"ERROR: didn't parse choices properly for year={d['year']}, contest={d['contest']}, number={d['number']}:\n{problem_text}")
                print("********************\n")
                return None
        retval['problem'] = re.sub(r'\s+', ' ', problem_text).strip()
    else:
        print(f"ERROR: didn't find problem in year={d['year']}, contest={d['contest']}, number={d['number']}:\n{pieces[0]}")
        print("********************\n")
        return None

    # Solutions processing/answer extraction
    solution_num = 1
    for piece in pieces[1:]:
        if piece.startswith("# Solution"):
            # Get header/solution annotation
            lines = piece.split('\n')
            candidate_metadata = re.sub(r'[^a-zA-Z\s]', '', re.sub(r'# Solution ?\d? ?', '', lines[0])).strip()
            logging_prob_text = f"year={d['year']}, contest={d['contest']}, number={d['number']}:\n{piece}"

            solution_text = '\n'.join(lines[1:]).strip()
            if has_answer(d['contest']):
                if bool(re.fullmatch(r'^\$\\boxed{((?:[^{}]*|\{[^{}]*\})*)}\$$', solution_text)):
                    print(f"WARNING: Skipping solution with only boxed answer and no explanation in {logging_prob_text}")
                    continue

                boxed_ans = extract_last_boxed_from_text(solution_text)
                if boxed_ans is None:
                    print(f"WARNING: Skipping solution with no boxed answer in {logging_prob_text}")
                    continue

                answer = standardize_answer(
                    boxed_ans, 
                    retval["choices"], 
                    logging_prob_text=logging_prob_text
                )
                if answer is None:
                    # Couldn't determine answer in solution. Skip this solution.
                    print(f"WARNING: Skipping solution with unparsed boxed answer in {logging_prob_text}")
                    continue

                if retval["choices"] is not None:
                    if 'answer_choice' in retval:
                        if answer != retval['answer_choice']:
                            print(f"ERROR: Found solutions with inconsistent answers in {logging_prob_text}")
                            print("********************\n")
                            return None
                    else:
                        retval['answer_choice'] = answer
                        retval['answer'] = retval['choices'][retval['answer_choice']]
                else:
                    if 'answer' in retval:
                        if answer != retval['answer']:
                            print(f"ERROR: Found solutions with inconsistent answers in {logging_prob_text}")
                            print("********************\n")
                            return None
                    else:
                        retval['answer_choice'] = None
                        retval['answer'] = answer
            else:
                if all(bool(re.fullmatch(r"\s*", l)) for l in lines[1:]):
                    print(f"WARNING: Skipping empty solution in {logging_prob_text}")
                    continue
                # USAMO Problems, we assume have no answer
                retval['answer'] = None
                retval['answer_choice'] = None

            if solution_num > 1:
                if ('as above' in solution_text) or ('see above solution' in solution_text):
                    print(f"WARNING: Skipping solution that references prior solution in year={d['year']}, contest={d['contest']}, number={d['number']}:\n{piece}\n")
                    continue
                if bool(re.search(r'Solution \d', solution_text)):
                    print(f"WARNING: Skipping solution that references prior solution in year={d['year']}, contest={d['contest']}, number={d['number']}:\n{piece}\n")
                    continue

            # Only add solution metadata + text if we reach this far
            if len(re.sub(r'\s', '', candidate_metadata)) > 0:
                retval['solution_{}_metadata'.format(solution_num)] = candidate_metadata
            else:
                retval['solution_{}_metadata'.format(solution_num)] = ''

            # Sometimes, solutions have multiple whitespaces. We normalize this
            retval['solution_{}'.format(solution_num)] = re.sub(' +', ' ', solution_text).strip()
            solution_num += 1
        else:
            print(f"WARNING: skipping non solution piece in year={d['year']}, contest={d['contest']}, number={d['number']}")
            continue
    if solution_num == 1:
        print(f"ERROR: Did not find any valid solution in year={d['year']}, contest={d['contest']}, number={d['number']}")
        print("********************\n")
        return None

    retval['num_solutions'] = solution_num - 1

    return retval


def main() -> None:
    raw_save_path = 'data/raw/aops_wiki/{year}_{contest}_{number}.pkl'

    years = [str(y) for y in range(1950, 2022)] + ["2021_Fall"] + [str(y) for y in range(2022, 2025)]
    test_year_contest_problem_map = {year: dict() for year in years}

    # test_year_contest_problem_map["2017"] = dict()
    # test_year_contest_problem_map["1951"]['AHSME'] = range(1,50)
    # test_year_contest_problem_map["1952"]['AHSME'] = [23]
    # test_year_contest_problem_map["1964"]['AHSME'] = [29]
    # test_year_contest_problem_map["1961"]['AHSME'] = [11]
    # test_year_contest_problem_map["1973"]['AHSME'] = [24]
    # test_year_contest_problem_map["2003"]['AMC_10A'] = [6]
    # test_year_contest_problem_map["1993"]['AIME'] = [13]  # latex alt_text is "\begin{align}...\end{align}."
    # test_year_contest_problem_map["2007"]['AMC_8'] = [16]  # answer choices are (A)\n[asy]...[/asy]

    # for year in range(1983, 2000):
    #     test_year_contest_problem_map[year]['AIME'] = range(1, 16)

    test_year_contest_problem_map["2019"]['AMC_12B'] = [3]
    year_contest_problem_map = test_year_contest_problem_map
    year_contest_problem_map = all_year_contest_problem_map

    write = True

    if write:
        os.makedirs('data/processed', exist_ok = True)
        raw_text_path = 'data/processed/aops_wiki_all_text.jsonl'
        valid_path = 'data/processed/aops_wiki.jsonl'

        raw_f = open(raw_text_path, 'w') 
        valid_f = open(valid_path, 'w') 

    gpt4_tokenizer = tiktoken.get_encoding('cl100k_base')

    # np.random.seed(0)
    with tqdm(total=total_problems) as pbar:
        for y in year_contest_problem_map:
            for c in year_contest_problem_map[y]:
                for n in year_contest_problem_map[y][c]:
                    print("\n********************")
                    print("Processing year={year} contest={contest} number={number}".format(year=y, contest=c, number=n))
                    
                    with open(raw_save_path.format(year=y, contest=c, number=n), 'rb') as f:
                        r: Response = pkl.load(f)
                    
                    datum = {
                        'year': y,
                        'contest': c,
                        'number': n,
                        'url': r.url,
                        'level': map_difficulty(y, c, n),
                        'full_text': get_parsed_lines_from_html(r)
                    }
                    datum['num_gpt4_tokens'] = len(gpt4_tokenizer.encode(datum['full_text']))
                    if write:
                        raw_f.write(json.dumps(datum)+'\n')

                    # print(datum['full_text'])
                    problem_solution_dict = get_problem_solution_choices(datum)
                    if problem_solution_dict is not None:
                        datum.update(problem_solution_dict)
                        if write:
                            valid_f.write(json.dumps(datum)+'\n')
                    # for k in datum:
                    #     print(k+':\n', datum[k])
                    # print('-'*100)
                    pbar.update(1)
                    # datum.update(get_problem_solution_choices(datum))
                    # all_data.append()

    if write:
        raw_f.close()
        valid_f.close()


if __name__ == "__main__":
    main()
