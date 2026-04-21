"""
Console runner for the AI Dungeon Master project.
"""

import os
import sys


if __package__ is None or __package__ == "":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from course_project.engine import DungeonMasterEngine


def main() -> None:
    """Run a simple console session."""
    engine = DungeonMasterEngine()
    chunks = engine.index_default_lore()

    player_name = input("Player name: ").strip() or "Adventurer"
    session_id = engine.start_session(player_name=player_name)

    print(f"Loaded {chunks} lore chunks into ChromaDB.")
    print("Type /exit to quit, /flip for a coin flip, or /roll player=Name skill=stealth dc=14")

    while True:
        user_message = input("You: ").strip()
        if user_message == "/exit":
            break

        result = engine.process_turn(
            session_id=session_id,
            user_message=user_message,
            scenario="console_campaign",
        )
        print("DM:", result["response"])
        print(f"[RL temperature used: {result['rl_temperature']:.1f}]")

    engine.end_session(session_id)


if __name__ == "__main__":
    main()
