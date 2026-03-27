"""
Tool functions used by the AI Dungeon Master.

This module intentionally reuses patterns from lab05 and util/llm_utils.
"""

import random
from typing import Dict

try:
    from util.llm_utils import tool_tracker
except Exception:
    def tool_tracker(func):
        return func


@tool_tracker
def roll_d20(skill: str, dc: int, player: str) -> Dict[str, str]:
    """
    Roll a d20 skill check and return a structured result.

    Inputs:
        skill (str): Skill name (e.g., stealth, persuasion).
        dc (int): Difficulty class.
        player (str): Player character name.
    Outputs:
        Dict[str, str]: Result payload with roll, outcome, and narration.
    """
    roll = random.randint(1, 20)
    success = roll >= int(dc)
    outcome = "success" if success else "failure"
    narration = f"{player} rolled {roll} for {skill} against DC {dc} and got a {outcome}."

    return {
        "player": player,
        "skill": skill,
        "dc": str(dc),
        "roll": str(roll),
        "outcome": outcome,
        "narration": narration,
    }


@tool_tracker
def coin_flip() -> Dict[str, str]:
    """
    Flip a coin and return heads/tails.
    """
    side = random.choice(["heads", "tails"])
    return {"result": side, "narration": f"The coin lands on {side}."}


def parse_roll_request(user_text: str) -> Dict[str, str]:
    """
    Parse a lightweight roll request format from player text.

    Supported mini-format:
        /roll player=Aria skill=stealth dc=14

    Inputs:
        user_text (str): Raw user message.
    Outputs:
        Dict[str, str]: Parsed values or empty dict.
    """
    if not user_text.startswith("/roll"):
        return {}

    parts = user_text.split()
    payload = {}
    for token in parts[1:]:
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        payload[key.strip().lower()] = value.strip()

    if {"player", "skill", "dc"}.issubset(payload):
        return payload

    return {}
