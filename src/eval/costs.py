"""
A library of functions to compute costs
"""

import re

import tiktoken

from eval.pricing import PRICING

def count_tokens(text: str, model: str) -> str:
    if model.startswith("o1"):
        # TODO: using tiktoken.encoding_for_model once it supports o1
        tokenizer = tiktoken.get_encoding("o200k_base")
        return len(tokenizer.encode(text))
    elif model.startswith("gpt"):
        tokenizer = tiktoken.encoding_for_model(model)
        return len(tokenizer.encode(text))
    elif model.startswith("claude"):
        # The Claude 3 tokenizer isn't publicly available,
        # but OAI tokenizers seem to roughly approximate the right token count
        # Could also use the Claude 2 tokenizer, but it is much slower
        tokenizer = tiktoken.get_encoding("o200k_base")
        return len(tokenizer.encode(text))
    elif model.startswith("gemini"):
        # "tokens" as in non-whitespace characters
        # since that's how billing is computing for Vertex API
        return len(re.sub(r"\s+", "", text))
    else:
        raise NotImplementedError(model)


def get_pricing(model: str) -> dict[str, float]:
    """Get price per token (or non-whitespace char for Gemini) for a given model
    
    If you plan to run using Batch API, make sure to adjust pricing by 1/2
    """
    if model in PRICING:
        return PRICING[model]
    
    if model.startswith("gemini"):
        return PRICING[model.rsplit("-", maxsplit=1)[0]]
    else:
        return PRICING[re.sub(r'-(?:\d{4}-?\d{2}-?\d{2})$', '', model)]
