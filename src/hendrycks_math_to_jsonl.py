"""
Converts the raw Hendryck's MATH dataset, saved in `data/raw/MATH/`,
into a single JSONL file for future use
"""

import json
import os

if __name__ == "__main__":
    with open('data/processed/hendrycks_math_ours.jsonl', 'w') as f:
        for split in ['test', 'train']:
            for subject in os.listdir('/'.join(['data', 'raw', 'MATH', split])):
                base_f = '/'.join(['data', 'raw', 'MATH', split, subject])
                if os.path.isdir(base_f):
                    for fname in os.listdir(base_f):
                        if fname.endswith('.json'):
                            number = int(fname[:-5])
                            with open('/'.join([base_f, fname]), 'r') as math_f:
                                data = json.loads(math_f.read())
                            data['number'] = number
                            data['split'] = split
                            f.write(json.dumps(data)+'\n')
