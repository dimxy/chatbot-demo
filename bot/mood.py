from bot.state import EmotionalState


def mood_to_description(mood: EmotionalState) -> str:
    """
    Translate numeric PAD mood state to a natural-language description.
    Returns a string under 50 words covering at least 6 PAD space regions.
    """
    v, a, d = mood.valence, mood.arousal, mood.dominance

    if v > 0.5 and a > 0.6 and d > 0.2:
        return "feeling genuinely excited, upbeat, and confident right now"
    if v > 0.4 and a < 0.4:
        return "feeling calm, content, and at ease"
    if v > 0.2 and d > 0.3:
        return "feeling positive and in control of the conversation"
    if v < -0.5 and a > 0.5:
        return "feeling anxious, frustrated, or unsettled"
    if v < -0.5 and a < 0.4:
        return "feeling sad, withdrawn, and a bit low"
    if v < -0.2:
        return "feeling a bit down or displeased with how things are going"
    if a > 0.7:
        return "feeling alert, energized, and very engaged"
    if d < -0.3:
        return "feeling uncertain, a bit hesitant, and somewhat unsure"
    if a < 0.2:
        return "feeling quiet, contemplative, and low-energy"
    return "feeling relatively neutral and balanced"
