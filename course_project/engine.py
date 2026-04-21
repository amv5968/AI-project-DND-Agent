"""
Main AI Dungeon Master engine.
"""

import uuid
from typing import Dict, List, Optional

import ollama

from course_project import config
from course_project.database import GameStateDB
from course_project.planner import build_turn_plan
from course_project.prompts import load_system_prompt
from course_project.rag import LoreRetriever
from course_project.rl_agent import DMRLAgent
from course_project.tools import coin_flip, parse_roll_request, roll_d20


class DungeonMasterEngine:
    """Coordinates planning, retrieval, tools, and model generation."""

    def __init__(self):
        self.db = GameStateDB(config.SQLITE_DB_PATH)
        self.retriever = LoreRetriever(
            persist_directory=config.RAG_PERSIST_DIR,
            collection_name=config.RAG_COLLECTION,
            embedding_model=config.EMBEDDING_MODEL,
        )
        self.rl_agent = DMRLAgent()
        self._session_turns: Dict[str, List[str]] = {}

    def start_session(self, player_name: str) -> str:
        session_id = str(uuid.uuid4())
        self.db.log_turn(session_id, "system", f"Session started for {player_name}", "session")
        self._session_turns[session_id] = []
        return session_id

    def end_session(self, session_id: str) -> None:
        self.rl_agent.end_session()
        self._session_turns.pop(session_id, None)

    def index_default_lore(self) -> int:
        return self.retriever.rebuild_from_directory(config.DEFAULT_DATA_DIR)

    def _build_chat_messages(self, session_id: str, user_message: str, scenario: str, context_chunks: List[str]) -> List[Dict[str, str]]:
        recent = self.db.get_recent_turns(session_id=session_id, limit=8)
        recent_history = "\n".join([f"{role}: {message}" for role, message in recent])
        context_text = "\n\n".join(context_chunks) if context_chunks else "No additional lore retrieved."

        system_prompt = load_system_prompt(
            config.SYSTEM_TEMPLATE_FILE,
            scenario=scenario,
            recent_history=recent_history,
            context_text=context_text,
        )

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

    def _run_tools(self, user_message: str) -> List[str]:
        notes: List[str] = []
        roll_request = parse_roll_request(user_message)
        if roll_request:
            result = roll_d20(
                skill=roll_request["skill"],
                dc=int(roll_request["dc"]),
                player=roll_request["player"],
            )
            notes.append("Tool[roll_d20]: " + result["narration"])

        if user_message.strip().lower() == "/flip":
            result = coin_flip()
            notes.append("Tool[coin_flip]: " + result["narration"])

        return notes

    def process_turn(
        self,
        session_id: str,
        user_message: str,
        scenario: str = "general_adventure",
        temperature: Optional[float] = None,
        max_tokens: int = config.DEFAULT_MAX_TOKENS,
    ) -> Dict[str, object]:
        """
        Process one player turn and produce a DM response.

        Returns:
            Dict with response text, plan, context, tool notes, and rl_temperature.
        """
        history = self._session_turns.setdefault(session_id, [])
        if history:
            prev_len = len(history[-1])
            reward = 1.0 if len(user_message) >= prev_len else 0.0
            self.rl_agent.record_reward(reward)

        turn_count = len(history)
        rl_temperature = self.rl_agent.choose_temperature(scenario, turn_count)
        effective_temperature = temperature if temperature is not None else rl_temperature
        history.append(user_message)

        plan = build_turn_plan(user_message=user_message, scenario=scenario)
        context_chunks = self.retriever.query(user_message, n_results=config.DEFAULT_NUM_CONTEXT_CHUNKS)
        tool_notes = self._run_tools(user_message)

        combined_user_message = user_message
        if tool_notes:
            combined_user_message += "\n\n" + "\n".join(tool_notes)

        messages = self._build_chat_messages(
            session_id=session_id,
            user_message=combined_user_message,
            scenario=scenario,
            context_chunks=context_chunks,
        )

        self.db.log_turn(session_id, "user", user_message, scenario)

        try:
            response = ollama.chat(
                model=config.MODEL_NAME,
                messages=messages,
                options={
                    "temperature": effective_temperature,
                    "top_p": config.DEFAULT_TOP_P,
                    "num_predict": max_tokens,
                },
            )
            dm_text = response["message"]["content"]
        except Exception as e:
            dm_text = (
                "[Fallback DM Response] I could not reach Ollama right now. "
                "Your action is recorded, and the party advances one beat in the story. "
                f"(error: {e})"
            )

        self.db.log_turn(session_id, "assistant", dm_text, scenario)

        return {
            "response": dm_text,
            "plan": plan.model_dump(),
            "context": context_chunks,
            "tool_notes": tool_notes,
            "rl_temperature": rl_temperature,
        }
