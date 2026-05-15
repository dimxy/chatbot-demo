from bot.state import PersonaConfig


def persona_to_description(persona: PersonaConfig) -> str:
    """
    Translate a PersonaConfig into a natural-language description under 80 words,
    covering all 6 PersonaConfig fields (name, gender, emotional_distance,
    warmth, sexuality, playfulness).
    """
    dist = (
        "close and intimate"
        if persona.emotional_distance < 0.35
        else "formal and professional"
        if persona.emotional_distance > 0.65
        else "friendly but respectful"
    )
    warmth = (
        "very warm and nurturing"
        if persona.warmth > 0.7
        else "cool and transactional"
        if persona.warmth < 0.3
        else "genuinely caring"
    )
    sexuality = (
        "personally engaged and attentive to the human"
        if persona.sexuality == "interested"
        else "focused on topics rather than personal connection"
    )
    play = (
        "very playful and humorous"
        if persona.playfulness > 0.7
        else "serious and earnest"
        if persona.playfulness < 0.3
        else "occasionally light-hearted"
    )
    return (
        f"You are {persona.name}, presenting as {persona.gender}. "
        f"Your emotional distance is {dist}. "
        f"You are {warmth}, {play}, and {sexuality}."
    )
