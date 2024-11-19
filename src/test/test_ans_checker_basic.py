import json

import numpy as np

from eval.latex_answer_check import check_one_latex_answer


def main() -> None:
    candidate_answers = [r'\frac{\sqrt{7}}{12}',
                            r'12\pi',
                            r'13/8',
                            r'168+48\sqrt{7}',
                            r'6\sqrt{3}',
                            r'\frac{5}{2}',
                            r'-3193'
                        ]

    correct_pairs = dict()
    incorrect_pairs = dict()
    unclear_pairs = dict()
    np.random.seed(1)
    for answer in candidate_answers:
        correct_pairs[answer] = [answer]
        unclear_pairs[answer] = []
        # None of our answers are positive integers
        incorrect_pairs[answer] = [str(np.random.randint(100))]

    # \frac{\sqrt{7}}{12}
    correct_pairs[r'\frac{\sqrt{7}}{12}'].extend([r'\sqrt{7}/12',
                                                r'\sqrt{7/144}',
                                                r'\sqrt{\frac{7}{144}}',
                                                r'\sqrt{7} / 12',
                                                r'\dfrac{\sqrt{7}}{12 }',
                                                r'1/12 * \sqrt{7}',
                                                r'\frac{7^\frac{1}{2}}{12}'])
    incorrect_pairs[r'\frac{\sqrt{7}}{12}'].extend(['7/12',
                                                    r'\frac{\sqrt{7}}{\sqrt{12}}',
                                                    r'\sqrt{\frac{7}{12}}',
                                                    r'\frac{1}{4}',
                                                    r'0.22048'])
    unclear_pairs[r'\frac{\sqrt{7}}{12}'].extend([r'\sqrt{7}\12',
                                                r'sqrt(7)/12'])
    # 12\pi
    correct_pairs[r'12\pi'].extend([r'12 * \pi', r'12 \cdot \pi',
                                    r'\pi \cdot 12'])
    incorrect_pairs[r'12\pi'].extend([r'12\phi', r'11\pi', '36', '48',
                                    r'10\pi', r'12'])
    unclear_pairs[r'12\pi'].extend([r'6\tau', r'12pi'])
    # 13/8
    correct_pairs[r'13/8'].extend([r'\frac{13}{8}', r'\dfrac{13}{8}',
                                r'1 \frac{5}{8}', r'1 + \frac{5}{8}', 
                                r'1 + 5/8', r'1.625'])
    incorrect_pairs[r'13/8'].extend([r'1 \frac{3}{8}', r'1.6', '13', '8'])
    unclear_pairs[r'13/8'].extend([r'1 5/8', r'1 3/8', r'13\8'])
    # r'168+48\sqrt{7}'
    correct_pairs[r'168+48\sqrt{7}'].extend([r'24(7+2\sqrt{7})', 
                                            r'24\cdot(7+2\sqrt{7})',
                                            r'168+24\sqrt{28}',
                                            r'168+48\cdot\sqrt{7}'])
    incorrect_pairs[r'168+48\sqrt{7}'].extend([r'168', 
                                            r'216\sqrt{7}'])
    unclear_pairs[r'168+48\sqrt{7}'].extend([r'168+48sqrt(7)'])
    # r'6\sqrt{3}'
    correct_pairs[r'6\sqrt{3}'].extend([r'\sqrt{108}', r'6\cdot\sqrt{3}'])
    incorrect_pairs[r'6\sqrt{3}'].extend([r'18', r'-6\sqrt{3}'])
    unclear_pairs[r'6\sqrt{3}'].extend([r'sqrt(108)'])
    # r'\frac{5}{2}',
    correct_pairs[r'\frac{5}{2}'].extend([r'\frac{10}{4}', r'2.5', r'5/2'])
    incorrect_pairs[r'\frac{5}{2}'].extend([r'2', r'2.25', r'52'])
    unclear_pairs[r'\frac{5}{2}'].extend([r'5\2'])
    # r'-3193'
    correct_pairs[r'-3193'].extend([])
    incorrect_pairs[r'-3193'].extend([r'3193'])
    unclear_pairs[r'-3193'].extend([r'--3193', r'- 3193'])

    for gt in candidate_answers:
        print('-'*50)
        print("Testing for", gt)
        for pairs, title in zip([correct_pairs, incorrect_pairs, unclear_pairs],
                                ['Correct', 'Incorrect', 'Unclear']):
            print(title)
            for v in pairs[gt]:
                model_ans = f"The final answer is ${v}$. "
                match = check_one_latex_answer(model_ans, gt)
                print(f'{match["is_correct"]} || {gt} || {v} -> {match["predict"]}')
            print()

    # interesting_answers = [r'\left(1009,2^{1009}-2\right)']


if __name__ == "__main__":
    main()
