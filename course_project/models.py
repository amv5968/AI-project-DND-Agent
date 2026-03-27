"""
Structured models used for planning and scenario tracking.
"""

from typing import List

from pydantic import BaseModel, Field


class PlanStep(BaseModel):
    """Single planning step for a DM turn."""

    step_id: int = Field(..., ge=1)
    action: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)


class TurnPlan(BaseModel):
    """Multi-step plan for how the DM should answer a player turn."""

    scenario: str = Field(..., min_length=1)
    objective: str = Field(..., min_length=1)
    steps: List[PlanStep] = Field(..., min_length=1)


class ScenarioRecord(BaseModel):
    """Tracks a scenario and whether it is active/complete."""

    scenario_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)
    notes: str = Field(default="")
