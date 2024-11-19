"""
In this file, we consider trickier answers,
such as those containing ordered pairs, intervals, double exponents
or capital letters (as a check for non-numeric answers)
More inspection would likely reveal more tough cases, but
we start with these

TODO: some of these tests don't pass right now! We have to improve the answer checker for this
"""

import numpy as np

from eval.latex_answer_check import check_one_latex_answer


def main() -> None:
    candidate_answers = [r'24, 28, 3200',
                        r'(12/5, 8/5)',
                        r'\left[\frac{\left(\sqrt{30}\right)}{3},\frac{\sqrt{30}}{4},\frac{2\sqrt{30}}{5} \right),\left(\frac{\sqrt{30}}{3},\frac{\sqrt{30}}{2},\frac{\sqrt{30}}{5} \right)\right]',
                        r'\frac{2^{2009}-1}{3\cdot 2^{2008}-1}',
                        r'x^{4}-2x^{3}-13x^{2}+14x+24',
                        r'2011^{2009}\cdot(1005^{2011}-1004^{2011})',
                        r'\pm\sqrt{3}',
                        r'{40 \choose 10} {40 \choose 20}^3',
                        # TODO write more tests later if needed.
                        #  r'\frac{1\pm i\sqrt{7}}{2}), (\frac{-1\pm i\sqrt{11}}{2}', # unordered
                        #  r'\pm\frac{9}{4}'
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

    # 24, 28, 3200 -- this one is an unordered list
    correct_pairs[r'24, 28, 3200'].extend([r'4\cdot 6, 4\cdot 7, 40 \cdot 80', r'24, 28, 3,\!200'])
    incorrect_pairs[r'24, 28, 3200'].extend([r'24', r'28', r'32', r"3200", r'24, 28', r'84', r'6, 7, 8'])
    unclear_pairs[r'24, 28, 3200'].extend([r'3200, 24, 28'])

    # (12/5, 8/5) -- this one is an ordered pair
    correct_pairs[r'(12/5, 8/5)'].extend([r'(2.4, 1.6)', r'(2+2/5, 1+3/5)', r'(12/5,8/5)',
                                        r'(\frac{12}{5}, \frac{8}{5})', r'(2 \frac{2}{5}, 1 \frac{3}{5})'])
    incorrect_pairs[r'(12/5, 8/5)'].extend([r'(8/5, 12/5)', '4', r'(2, 2)', r'(12/5, 8/5]'])
    unclear_pairs[r'(12/5, 8/5)'].extend([r'[12/5, 8/5]', r'1 + (7/5, 3/5)', r'(2 2/5, 1 3/5)'])

    # \frac{2^{2009}-1}{3\cdot 2^{2008}-1}
    correct_pairs[r'\frac{2^{2009}-1}{3\cdot 2^{2008}-1}'].extend([r'1 - \frac{2^{2008}}{3\cdot 2^{2008}-1}',
                                                                r'\frac{2^{2009}-1}{3\cdot 2^{2008}-1} + 1 - 1'])
    incorrect_pairs[r'\frac{2^{2009}-1}{3\cdot 2^{2008}-1}'].extend(['2/3', '0.67',r'\frac{2^{2008}-1}{3\cdot 2^{2007}-1}'])
    unclear_pairs[r'\frac{2^{2009}-1}{3\cdot 2^{2008}-1}'].extend([])

    # x^{4}-2x^{3}-13x^{2}+14x+24
    correct_pairs[r'x^{4}-2x^{3}-13x^{2}+14x+24'].extend([r'x^{4} - 2x^{3} - 13x^{2} + 14x + 24',
                                                        r'x^4 - 2x^3 - 13x^2 + 14x + 24',
                                                        r'x^4 - x^3 - 13x^2 + 14x + 24 - x^3',
                                                        r'x^{4} - 2x^{3} - 13x^{2} + 14x + 16 + 8',
                                                        r'x^2 (x - 1)^2 - 14x(x-1) + 24'])  # fails bc sympy don't manage to simply the different of expressions to 0
    incorrect_pairs[r'x^{4}-2x^{3}-13x^{2}+14x+24'].extend([r'x^{4}-2x^{3}-13x^{2}+14x+25', 
                                                            r'x^{4}+2x^{3}-13x^{2}+14x+25'])
    unclear_pairs[r'x^{4}-2x^{3}-13x^{2}+14x+24'].extend([])

    # 2011^{2009}\cdot(1005^{2011}-1004^{2011}) -- this one overflows if evaluated
    correct_pairs[r'2011^{2009}\cdot(1005^{2011}-1004^{2011})'].extend([
        r'2011^{2009} * (1005^{2011}-1004^{2011})',
        r'\frac{2021055^{2011} - 2019044^{2011}}{2011^2}'])
    incorrect_pairs[r'2011^{2009}\cdot(1005^{2011}-1004^{2011})'].extend([
        r'2011^{2009}\cdot(1005^{2011}-1004^{2011}) + 1',
        r'2011^{2009}\cdot(1004^{2011}-1003^{2011})',
        r'2011^{2009} * (1004^{2011}-1004^{2011})',
        r'2010^{2009}\cdot(1005^{2011}-1004^{2011})',])
    unclear_pairs[r'2011^{2009}\cdot(1005^{2011}-1004^{2011})'].extend([])

    # TODO: add better support for unordered pairs and with it, +/- notation
    correct_pairs[r'\pm\sqrt{3}'].extend([r'\sqrt{3}, -\sqrt{3}',
                                        r'-\sqrt{3}, \sqrt{3}',
                                        r'\sqrt{3} or -\sqrt{3}'])
    incorrect_pairs[r'\pm\sqrt{3}'].extend([r'\sqrt{3}', r'-\sqrt{3}', r'\pm 3',
                                            r'+-\sqrt{3}'])
    unclear_pairs[r'\pm\sqrt{3}'].extend([])

    # TODO: sympy doesn't understand \choose indicates a binom coef
    correct_pairs[r'{40 \choose 10} {40 \choose 20}^3'].extend([
        r'{40 \choose 10} {40 \choose 20}^{3}',
        r'{40 \choose 20}^3 {40 \choose 10}',
        r'\frac{(40!)^4}{(20!)^6 \cdot 10! \cdot 30!}',
        # From wolfram alpha
        r'2.220288776331226273985899246597440607104 \cdot 10^42',])
    incorrect_pairs[r'{40 \choose 10} {40 \choose 20}^3'].extend([
        r'2.220288776331226 \cdot 10^42',
        r'{40 \choose 20}^4',
        r'{40 \choose 10} {40 \choose 20}^3 + 1'])
    unclear_pairs[r'{40 \choose 10} {40 \choose 20}^3'].extend([
        r'(40 \choose 10) (40 \choose 20)^3',
        r'\begin{pmatrix} 40 \\ 10 \end{pmatrix} \begin{pmatrix} 40 \\ 20 \end{pmatrix}^3',
        r'\left(\begin{smallmatrix}40\\ 10\end{smallmatrix}\right)\left(\begin{smallmatrix}40\\ 20\end{smallmatrix}\right)^{3}'])

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


if __name__ == "__main__":
    main()
