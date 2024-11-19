"""
This file contains constants tracking the price of running on various models.
All costs are in dollars
"""

# Acculumated cost factors. Most are per token, but not always.
# Namely, Gemini is per character
PRICING = {
    # Gemini on Vertex AI is charged by 1K characters, ignoring whitespaces
    # These are costs on <= 128K context window. Over is 2x as expensive.
    # Batch mode has a 50% discount
    "gemini-1.5-flash": {
        "input_tokens":  0.00001875 / 1000, # per character
        "output_tokens": 0.000075 / 1000, # per character
    },
    "gemini-1.5-pro": {
        # starting 2024-10-07
        "input_tokens":  0.0003125 / 1000, # per character
        "output_tokens": 0.00125 / 1000, # per character
        # before 2024-10-07
        # "input_tokens":  0.00125 / 1000, # per character
        # "output_tokens": 0.00375 / 1000, # per character
    },

    # Anthropic API pricing.
    # Batches API (beta) has a 50% cost reduction
    "claude-3-5-sonnet": {
        "input_tokens":  3 / 1e6,  # $3 per 1M tokens
        "output_tokens": 15 / 1e6,  # $15 per 1M tokens
    },
    "claude-3-5-haiku": {
        "input_tokens":  1 / 1e6,  # $1 per 1M tokens
        "output_tokens": 5 / 1e6,  # $5 per 1M tokens
    },
    "claude-3-opus": {
        "input_tokens":  15 / 1e6,  # $15 per 1M tokens
        "output_tokens": 75 / 1e6,  # $75 per 1M tokens
    },
    "claude-3-haiku": {
        "input_tokens":  0.25 / 1e6,  # $0.25 per 1M tokens
        "output_tokens": 1.25 / 1e6,  # $1.25 per 1M tokens
    },

    # OpenAI API pricing. Batch mode has a 50% discount
    # Prompt caching is automatically enabled where available
    # (aka recent model snapshots) but can't be used with Batch API
    # Batch API is a 50% discount and is not supported for o1 models
    "gpt-4o-2024-05-13": {
        "input_tokens":  5 / 1e6,  # $5 per 1M tokens
        "output_tokens": 15 / 1e6,  # $15 per 1M tokens
    },
    "gpt-4o-2024-08-06": {
        "input_tokens":  2.5 / 1e6,  # $2.5 per 1M tokens
        "cached_input_tokens":  1.25 / 1e6,  # $1.25 per 1M tokens
        "output_tokens": 10 / 1e6,  # $10 per 1M tokens
    },
    "gpt-4o-mini-2024-07-18": {
        "input_tokens":  0.15 / 1e6,  # $0.15 per 1M tokens
        "output_tokens": 0.6 / 1e6,  # $0.6 per 1M tokens
        "cached_input_tokens": 0.075 / 1e6,  # $0.075 per 1M tokens
    },
    "gpt-4-turbo-2024-04-09": {
        "input_tokens":  10 / 1e6,  # $10 per 1M tokens
        "output_tokens": 30 / 1e6,  # $30 per 1M tokens
    },
    "o1-preview-2024-09-12": {
        "input_tokens":  15 / 1e6,  # $15 per 1M tokens
        "output_tokens": 60 / 1e6,  # $60 per 1M tokens, includes not visible internal reasoning
        "cached_input_tokens": 7.5 / 1e6,  # $7.5 per 1M tokens
    },
    "o1-mini-2024-09-12": {
        "input_tokens":  3 / 1e6,  # $3 per 1M tokens
        "output_tokens": 12 / 1e6,  # $12 per 1M tokens, includes not visible internal reasoning
        "cached_input_tokens": 1.5 / 1e6,  # $1.5 per 1M tokens
    },

    # Llama models hosted on Together AI
    "meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo": {
        "input_tokens":  3.5 / 1e6,  # $3.50 per 1M tokens
        "output_tokens": 3.5 / 1e6,
    },
    "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo": {
        "input_tokens":  0.88 / 1e6,  # $0.88 per 1M tokens
        "output_tokens": 0.88 / 1e6,
    },
    "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo": {
        "input_tokens":  0.18 / 1e6,  # $0.18 per 1M tokens
        "output_tokens": 0.18 / 1e6,
    },
    "meta-llama/Llama-3.2-90B-Vision-Instruct-Turbo": {
        "input_tokens":  1.20 / 1e6,  # $1.20 per 1M tokens
        "output_tokens": 1.20 / 1e6,
    },
    "meta-llama/Llama-3.2-3B-Instruct-Turbo": {
        "input_tokens":  0.06 / 1e6,  # $0.06 per 1M tokens
        "output_tokens": 0.06 / 1e6,
    },
}
