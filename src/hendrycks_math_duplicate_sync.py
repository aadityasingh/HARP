"""
Given a threshold for what counts as a duplicate, determine the actual matches from our prefix matches
"""

import json

from eval.utils import read_jsonl, write_jsonl


if __name__ == "__main__":
    data = read_jsonl('data/processed/hendrycks_math_ours.jsonl')
    our_data = read_jsonl('data/processed_with_dup_info/aops_wiki_final_prefix_matched_MATH_raw.jsonl')

    # I chose these thresholds by doing the following:
    # Try some combination, inspect samples. 
    # If we find samples that are flagged as duplicate but aren't, make these thresholds more strict. 
    # Otherwise, loosen the thresholds. 
    # Repeat this process until the number of duplicates roughly converges.
    # We find just under 800 duplicates.
    frac_thresh = 0.9
    thresh = 60
    ctr = 0

    # We also considered if a problem matched multiple MATH problems given redundancy. However, we
    # found this only happened in 3 cases. In one, we had a misparse. In the other two, the two MATH
    # problems were duplicates/one was the subset of the other (due to newline and "Express answer as blah")
    # matches_multi_math = 0
    for p in our_data:
        if (p['MATH_match']['depth']/len(p[' ']) > frac_thresh) or (p['MATH_match']['depth'] > thresh):
            ctr += 1
            print(p['problem'])
            print('-'*10)
            for i in p['MATH_match']['matched_inds']:
                print(data[i]['problem'])
                print('-')
            print('-'*20)
            # if len(p['MATH_match']['matched_inds']) > 1:
            #     matches_multi_math += 1
            p['MATH_match'] = data[p['MATH_match']['matched_inds'][0]]
        else:
            p['MATH_match'] = None

    print("total", ctr)
    # print("multi match", matches_multi_math)

    write_jsonl(our_data, 'data/processed_with_dup_info/aops_wiki_final_with_MATH_match.jsonl')