MODE_REGISTRY = {
    "confident": {
        "prompt_summary": "Be direct, assertive, and confident. Minimal hedging.",
        "model_key": "response_generator",
        "temperature": 0.3,
        "tools": [],
        "max_tokens": 1024,
    },
    "uncertain": {
        "prompt_summary": "Be exploratory and honest about uncertainty. Acknowledge gaps.",
        "model_key": "response_generator",
        "temperature": 0.7,
        "tools": [],
        "max_tokens": 1024,
    },
    "emotional": {
        "prompt_summary": "Lead with empathy. Validate before responding to content.",
        "model_key": "intent_analyzer",
        "temperature": 0.9,
        "tools": [],
        "max_tokens": 512,
    },
    "playful": {
        "prompt_summary": "Be light, humorous, and playful. Use wordplay where fitting.",
        "model_key": "response_generator",
        "temperature": 0.9,
        "tools": [],
        "max_tokens": 1024,
    },
    "default": {
        "prompt_summary": "Be balanced, helpful, and conversational.",
        "model_key": "response_generator",
        "temperature": 0.6,
        "tools": [],
        "max_tokens": 1024,
    },
}

DEFAULT_MODE = "default"
