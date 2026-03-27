"""
Planning utilities for multi-step DM reasoning.
"""

from course_project.models import PlanStep, TurnPlan


def build_turn_plan(user_message: str, scenario: str) -> TurnPlan:
    """
    Build a simple multi-step plan before generating an answer.

    Inputs:
        user_message (str): Player instruction/question.
        scenario (str): Current scenario category.
    Outputs:
        TurnPlan: Structured plan object used by the engine.
    """
    objective = "Respond as DM while preserving game continuity"

    steps = [
        PlanStep(step_id=1, action="Classify intent", reason=f"Identify whether the player asked for action, lore, or rules: '{user_message[:80]}'"),
        PlanStep(step_id=2, action="Retrieve support context", reason="Use memory and RAG context to ground response"),
        PlanStep(step_id=3, action="Choose tools if needed", reason="Use dice or helper tools when deterministic outcomes are needed"),
        PlanStep(step_id=4, action="Generate DM narration", reason="Produce clear narrative and next choices for the party"),
    ]

    return TurnPlan(
        scenario=scenario,
        objective=objective,
        steps=steps,
    )
