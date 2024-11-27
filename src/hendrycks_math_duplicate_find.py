"""
Use a trie to get prefix matches between Hendryck's MATH and our dataset
"""
import re
import numpy as np
from functools import partial

import matplotlib.pyplot as plt

from eval.utils import read_jsonl, write_jsonl


def apply_fn_to_trie(node, fn, flatten=True):
    if isinstance(node, list):
        return fn(node)
    else:
        if flatten:
            retval = []
        else:
            retval = dict()
        for c in node:
            if flatten:
                retval.extend(apply_fn_to_trie(node[c], fn))
            else:
                retval[c] = apply_fn_to_trie(node[c], fn)
        return retval


flatten_trie = partial(apply_fn_to_trie, fn=(lambda x: x))


def get_starting_with_str(current, s):
    for c in s:
        if c in current:
            current = current[c]
        else:
            print("Found no problems!")
            return []
    return flatten_trie(current)


def get_max_depth_and_p_inds(current, s):
    for d, c in enumerate(s):
        if c in current:
            current = current[c]
        else:
            return {"depth": d, "matched_inds": flatten_trie(current)}
    return {"depth": len(s), "matched_inds": flatten_trie(current)}


with __name__ == "__main__":
    end_substr = '<END>'

    data = read_jsonl('data/processed/hendrycks_math_ours.jsonl')

    # At 800, we only get 5 near duplicates
    # At 1000, we can no longer traverse our trie effectively due to recursion depth in python
    #   could resolve by switching to iterative traversal but I'm lazy
    max_trie_depth = 200
    trie = {}

    print(len(data))

    for i, info in enumerate(data):
        problem_text = re.sub(r'\s+', ' ', info['problem']).strip()
        current = trie
        steps = min(max_trie_depth, len(problem_text))
        for ind, c in enumerate(problem_text[:steps]):
            if end_substr in current:
                print("Found a problem that's a superset of a different problem")
            current = current.setdefault(c, dict())

        if end_substr in current:
            print("Found a near duplicate in MATH!")
            if len(current) > 1:
                print("Actually, found a problem that's a subset of a different problem!")
            exact_dup = False
            for el in current[end_substr]:
                if data[el]['problem'] == info['problem']:
                    exact_dup = True
                # print(el)
            if exact_dup:
                print("Actually, it's an EXACT duplicate")
                # Verified there are no exact duplicates when script runs
            else:
                current[end_substr].append(i)
        else:
            if len(current) > 0:
                print("Found a problem that's a subset of a different problem!")
            current[end_substr] = [i]

    print("Built MATH json trie")

    print(len(apply_fn_to_trie(trie, lambda x: x)))

    print(np.unique(apply_fn_to_trie(trie, lambda x: [len(x)]), return_counts=True))

    our_data = read_jsonl("data/datasets/full_dataset.jsonl")

    depths = []
    fracs = []
    # matches = []
    for info in our_data:
        # We don't have to strip the problem text in our data since we do that in preproc
        info['MATH_match'] = get_max_depth_and_p_inds(trie, info['problem'])
        depths.append(info['MATH_match']['depth'])
        fracs.append(info['MATH_match']['depth']/len(info['problem']))

    write_jsonl(our_data, 'data/processed_with_dup_info/aops_wiki_final_prefix_matched_MATH_raw.jsonl')

    fig, axs = plt.subplots(1,2, sharey=True)
    fig.set_size_inches(10, 5)
    axs[0].hist(depths)
    axs[0].set_xlabel('Length of matching prefix')
    axs[0].set_ylabel('# Problems')
    axs[0].set_title('Maximum prefix match of HARP problems to any\nMATH problem')

    axs[1].hist(fracs)
    axs[1].set_title('Maximum prefix match of HARP problems to any,\nMATH problemnormalized by problem length')
    axs[1].set_xlabel('Length of matching prefix / Length of HARP problem')

    fig.savefig('duplicate_stats.png')

    plt.show()
