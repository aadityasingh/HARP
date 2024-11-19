# HARD-Math

Human Annotated Reasoning Dataset for Math (**HARD-Math**) is a math reasoning dataset consisting of 4,780 short answer questions from US national math competitions, spanning from 1950 to Sept. 2024. The paper can be found at [HARD_Math.pdf](HARD_Math.pdf).

We release a few splits of our dataset: 
- [HARD-Math.jsonl.zip](HARD-Math.zip) consists of 4,780 short answer questions and is the **default** split for running the evaluation.
- [HARD-Math_mcq.jsonl.zip](HARD-Math_mcq.zip) consists of 4,110 multiple choice questions.
- [HARD-Math_proof-based.jsonl.zip](HARD-Math_proof-based.zip) consists of 310 proof-based problems.
- [HARD-Math_raw.jsonl.zip](HARD-Math_raw.zip) consists of all 5,409 problems we scraped and processed.

We provide all jsonl files in zip format, to avoid leaking the data in plain text (and thus hopefully mitigate contamination).

In addition to the dataset and paper, this repo also include all our code for constructing the dataset, running evaluations, checking answers, and various other analyses that we did in the paper.

## Fields in the main dataset

- `problem`: Problem text
- `answer`: Ground truth answer
- `solution_{i}`: Human-written solution(s) (at least 1 per problem)
- `year`/`contest`/`number`: Three fields that jointly uniquely identify the source problem
- `level`: Difficulty level
- `subject`: Subject label for the problem -- one of `['prealgebra', 'algebra', 'number_theory', 'geometry', 'counting_and_probability', 'precalculus']`
