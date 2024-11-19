"""
Deduplicate problems from aops_wiki.jsonl, adding a metadata field when we find duplicates.
When we find duplicates, we use the harder contest for the main contest and problem number,
e.g. AMC 12 over AMC 10.

Example cmd:
    python scraping/aops_wiki/dedupe.py
"""

import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from eval.utils import read_jsonl, write_jsonl, get_uid

END_SUBSTR = '<END>'


def find_duplicate_problems(data: list[dict[str, Any]], max_trie_depth: int = 800) -> dict[str, list[str]]:
    print(f"Dataset has length {len(data)}")

    trie: dict[str, dict | list[str]] = {}
    duplicate_uids = defaultdict(list)

    for i, info in enumerate(data):
        problem_text = re.sub(r'\s+', ' ', info['problem']).strip()
        if info['choices']:
            choice_text = ' '.join([f"{c}. {ans}" for c, ans in info['choices'].items()])
            problem_text = problem_text + " " + choice_text

        uid = get_uid(info)
        current = trie
        steps = min(max_trie_depth, len(problem_text))
        for c in problem_text[:steps]:
            if END_SUBSTR in current:
                print("Found a problem {uid} that's a superset of a different problem")
            current = current.setdefault(c, dict())

        if END_SUBSTR in current:
            # Found a prefix duplicate in the dataset

            if len(current) > 1:
                print("Actually, found a problem that's a subset of a different problem!")
            exact_dup = False
            for el in current[END_SUBSTR]:
                if data[el]['problem'] == info['problem']:
                    exact_dup = True
                    duplicate_uids[get_uid(data[el])].append(uid)
                    break
            
            if not exact_dup:
                # Found a near duplicate
                # This happens for a few AMC_8 problems that use the same common data
                # e.g. 2002/3 AMC_8 #8-10
                current[END_SUBSTR].append(i)
                # print("******************")
                # print("Found a near duplicate that's not exact")
                # print(info["year"], info["contest"], info["number"])
                # print(info["problem"])
                # print("--------")
                # for el in current[END_SUBSTR]:
                #     print(data[el]["year"], data[el]["contest"], data[el]["number"])
                #     print(data[el]["problem"])
                #     print("--------")
                # print()
        else:
            if len(current) > 0:
                print(f"Found a problem {uid} that's a subset of a different problem!")
            current[END_SUBSTR] = [i]
    return dict(duplicate_uids)


def main() -> None:
    fname = "data/processed/aops_wiki.jsonl"
    out_fname = "data/processed/aops_wiki_deduped.jsonl"
    dataset: list[dict[str, Any]] = read_jsonl(fname)
    dataset_map = {get_uid(prob): prob for prob in dataset}

    # At 800, we only get 3 near duplicates
    # These come from cases in 2002/2003 AMC_8 where the problems used common data across a few problems
    duplicate_uids = find_duplicate_problems(dataset, max_trie_depth=800)
    print(f"Found {len(duplicate_uids)} duplicates using trie.")

    # Manually add some duplicates that we found that have slightly different wording and fail the trie method
    duplicate_uids["1965/AHSME/24"] = ["1971/AHSME/29"]
    duplicate_uids["2004/AMC_12B/1"] = ["2004/AMC_10B/3"]
    duplicate_uids["2013/AMC_12A/18"] = ["2013/AMC_10A/22"]
    duplicate_uids["2017/AMC_12A/3"] = ["2017/AMC_10A/6"]
    duplicate_uids["2017/AMC_12B/10"] = ["2017/AMC_10B/11"]
    duplicate_uids["2018/AMC_12B/5"] = ["2018/AMC_10B/5"]
    duplicate_uids["2022/USAMO/4"] = ["2022/USAJMO/5"]
    duplicate_uids["2022/USAMO/1"] = ["2022/USAJMO/2"]
    duplicate_uids["2020/USAMO/4"] = ["2020/USAJMO/5"]
    duplicate_uids["2020/USAMO/2"] = ["2020/USAJMO/3"]
    duplicate_uids["2019/USAMO/2"] = ["2019/USAJMO/3"]
    duplicate_uids["2015/USAMO/4"] = ["2015/USAJMO/6"]

    # An exception to the rule. Sometimes duplicate problems have their own wiki pages
    # and one's solutions are incomplete vs another. We remap here.
    other_solns_map = {
        "2022/USAMO/1": "2022/USAJMO/2",
    }

    # print("Got AoPS dataset duplicates:", duplicate_uids)

    # This is currently true
    assert all(len(v) == 1 for v in duplicate_uids.values())
    duplicate_uids = {k: v[0] for k, v in duplicate_uids.items()}

    contest_order = ["USAMO", "USAJMO", "AIME", "AMC_12", "AHSME", "AMC_10", "AJHSME", "AMC_8"]
    dupe_remove_to_main = {}
    dupe_main_to_remove = defaultdict(list)
    for k, v in duplicate_uids.items():
        k_year, k_contest, _ = k.split("/")
        v_year, v_contest, _ = v.split("/")

        k_order = None
        v_order = None
        for i, c in enumerate(contest_order):
            if k_contest.startswith(c):
                k_order = (i, k_year)
            if v_contest.startswith(c):
                v_order = (i, v_year)
        assert k_order is not None and v_order is not None

        if k_order < v_order:
            dupe_remove_to_main[v] = k
            dupe_main_to_remove[k].append(v)
        elif k_order > v_order:
            dupe_remove_to_main[k] = v
            dupe_main_to_remove[v].append(k)
        else:
            raise Exception(f"Found duplicates with the same year and contest: {k}, {v}")
    
    assert len(set(dupe_remove_to_main.keys()) & set(dupe_main_to_remove.keys())) == 0
        
    deduped_problems = []
    for prob in read_jsonl(fname):
        uid = get_uid(prob)
        if uid in dupe_remove_to_main:
            continue

        if uid in other_solns_map:
            prob = dataset_map[other_solns_map[uid]].copy()
            year, contest, number = uid.split("/")
            prob["year"] = year
            prob["contest"] = contest
            prob["number"] = int(number)
        
        dupe_metadata = None
        if uid in dupe_main_to_remove:
            dupe_metadata = []
            for u in dupe_main_to_remove[uid]:
                year, contest, number = u.split("/")
                dupe_metadata.append({"year": year, "contest": contest, "number": int(number)})
        prob["other_appearances"] = dupe_metadata
        deduped_problems.append(prob)

    write_jsonl(deduped_problems, out_fname)


if __name__ == "__main__":
    main()

