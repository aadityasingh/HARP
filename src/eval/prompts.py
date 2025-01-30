"""
Prompts used for experiments
"""

import textwrap


gemini_sysprompt = 'You are a math expert. I am going to give you a series of demonstrations of math Problems and Solutions. When you respond, respond only with the Solution of the final Problem, thinking step by step. At the end of the Solution, when you give your final answer, write it in the form "Final Answer: The final answer is $answer$. I hope it is correct."'
gemini_0shot_sysprompt = 'You are a math expert. Solve the following math Problem, thinking step by step. At the end of the Solution, when you give your final answer, write it in the form "Final Answer: The final answer is $answer$. I hope it is correct."'

# We standardize the text to look *exactly* like that which appears in Hendrycks' MATH
# As Minerva did not release code, it's unclear where the newlines are actually placed.
# The format provided in their paper Appendix D.2 is truncated to 80 characters per line,
# but I believe this is just due to Google linting, not actually where newlines are placed
minerva_4shot_prompt = [
    # Hendrycks MATH train/algebra/943.json
    {
        "role": "user",
        "content": "Problem:\nFind the domain of the expression $\\frac{\\sqrt{x-2}}{\\sqrt{5-x}}$."
    },
    {
        "role": "assistant",
        "content": "Solution:\nThe expressions inside each square root must be non-negative. Therefore, $x-2 \\ge 0$, so $x\\ge2$, and $5 - x \\ge 0$, so $x \\le 5$. Also, the denominator cannot be equal to zero, so $5-x>0$, which gives $x<5$. Therefore, the domain of the expression is $\\boxed{[2,5)}$.\nFinal Answer: The final answer is $[2,5)$. I hope it is correct."
    },
    # Hendrycks MATH train/precalculus/372.json
    {
        "role": "user",
        "content": "Problem:\nIf $\\det \\mathbf{A} = 2$ and $\\det \\mathbf{B} = 12,$ then find $\\det (\\mathbf{A} \\mathbf{B}).$"
    },
    {
        "role": "assistant",
        "content": "Solution:\nWe have that $\\det (\\mathbf{A} \\mathbf{B}) = (\\det \\mathbf{A})(\\det \\mathbf{B}) = (2)(12) = \\boxed{24}.$\nFinal Answer: The final answer is $24$. I hope it is correct."
    },
    # Hendrycks MATH train/algebra/256.json
    {
        "role": "user",
        "content": "Problem:\nTerrell usually lifts two 20-pound weights 12 times. If he uses two 15-pound weights instead, how many times must Terrell lift them in order to lift the same total weight?"
    },
    {
        "role": "assistant",
        "content": "Solution:\nIf Terrell lifts two 20-pound weights 12 times, he lifts a total of $2\\cdot 12\\cdot20=480$ pounds of weight.  If he lifts two 15-pound weights instead for $n$ times, he will lift a total of $2\\cdot15\\cdot n=30n$ pounds of weight.  Equating this to 480 pounds, we can solve for $n$: \\begin{align*}\n30n&=480\\\\\n\\Rightarrow\\qquad n&=480/30=\\boxed{16}\n\\end{align*}\nFinal Answer: The final answer is $16$. I hope it is correct."
    },
    # Hendrycks MATH train/algebra/1951.json
    {
        "role": "user",
        "content": "Problem:\nIf the system of equations\n\n\\begin{align*}\n6x-4y&=a,\\\\\n6y-9x &=b.\n\\end{align*}has a solution $(x, y)$ where $x$ and $y$ are both nonzero, find $\\frac{a}{b},$ assuming $b$ is nonzero."
    },
    {
        "role": "assistant",
        "content": "Solution:\nIf we multiply the first equation by $-\\frac{3}{2}$, we obtain\n\n$$6y-9x=-\\frac{3}{2}a.$$Since we also know that $6y-9x=b$, we have\n\n$$-\\frac{3}{2}a=b\\Rightarrow\\frac{a}{b}=\\boxed{-\\frac{2}{3}}.$$\nFinal Answer: The final answer is $-\\frac{2}{3}$. I hope it is correct."
    }
]


# As seen in the Llama 3.1 70B Instruct evals in huggingface
# https://huggingface.co/datasets/meta-llama/Meta-Llama-3.1-70B-Instruct-evals/
llama3_prompt_template = textwrap.dedent(
    """\
    Solve the following math problem efficiently and clearly:

    - For simple problems (2 steps or fewer):
    Provide a concise solution with minimal explanation.

    - For complex problems (3 steps or more):
    Use this step-by-step format:

    ## Step 1: [Concise description]
    [Brief explanation and calculations]

    ## Step 2: [Concise description]
    [Brief explanation and calculations]

    ...

    Regardless of the approach, always conclude with:

    Therefore, the final answer is: $\\boxed{{answer}}$. I hope it is correct.

    Where [answer] is just the final number or expression that solves the problem.

    Problem: {problem}
    """
)


llama3_multiple_choice_prompt_template = textwrap.dedent(
    """\
    Solve the following math problem efficiently and clearly:

    - For simple problems (2 steps or fewer):
    Provide a concise solution with minimal explanation.

    - For complex problems (3 steps or more):
    Use this step-by-step format:

    ## Step 1: [Concise description]
    [Brief explanation and calculations]

    ## Step 2: [Concise description]
    [Brief explanation and calculations]

    ...

    Regardless of the approach, always conclude with:

    Therefore, the final answer is: ?. I hope it is correct.

    Where ? is replaced by one of the letters A, B, C, D or E.

    Problem: {problem}
    """
)


# As seen in https://github.com/openai/simple-evals/blob/main/math_eval.py#L18
openai_prompt_template = textwrap.dedent(
    """\
    Solve the following math problem step by step. The last line of your response should be of the form Answer: $ANSWER (without quotes) where $ANSWER is the answer to the problem.

    {problem}

    Remember to put your answer on its own line after "Answer:", and you do not need to use a \\boxed command.
    """
)


modified_openai_o1_prompt_template = textwrap.dedent(
    """Solve the following math problem. The last line of your response should be of the form "Answer:\n$ANSWER" (without quotes) where $ANSWER is the answer to the problem. Remember to put your answer on its own line after "Answer:", and you do not need to use a \\boxed command.

    {problem}"""
)


# https://github.com/openai/simple-evals/blob/main/sampler/chat_completion_sampler.py#L10
gpt4_system_instruction = "You are a helpful assistant."


# A custom system prompt that we use for standard evals. Adapted from the OpenAI prompt above
# Only change is to explicitly ask the model to use LaTeX, as Claude seems to prefer using unicode
# characters whenever possible.
custom_claude_sysprompt = textwrap.dedent(
    """Solve the following math problem using LaTeX. The last line of your response should be of the form "Answer:\n$ANSWER" (without quotes) where $ANSWER is the answer to the problem in LaTeX. Remember to put your answer on its own line after "Answer:", and you do not need to use a \\boxed command."""
)


# From the Gemini 1.5 AMC prompt
gemini_multiple_choice_sysprompt = """You are a math expert. I am going to give you a series of demonstrations of math Problems and Solutions. When you respond, respond only with the Solution of the final Problem, thinking step by step. End the Solution with the final answer in the form "Final Answer: The final answer is ?. I hope it is correct.", where ? is replaced by one of the letters A, B, C, D or E."""
gemini_multiple_choice_0shot_sysprompt = """You are a math expert. Solve the following math Problem, thinking step by step. End the Solution with the final answer in the form "Final Answer: The final answer is ?. I hope it is correct.", where ? is replaced by one of the letters A, B, C, D or E."""
