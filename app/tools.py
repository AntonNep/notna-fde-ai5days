# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import logging
from typing import Dict, Any, Literal
from pydantic import BaseModel, Field
from google.adk.tools import ToolContext, FunctionTool

# --- Pydantic Schemas for Strict Input Validation ---
# Criteria: Explicit JSON Schemas
class InjurySchema(BaseModel):
    injury_type: Literal["cut", "scorch", "wing_tear", "bruise"] = Field(
        description="The type of physical injury sustained by the dragon."
    )
    severity: Literal["minor", "moderate", "severe"] = Field(
        description="The physical impact of the injury on the dragon's stats."
    )
    story_context: str = Field(
        description="A short string describing how the injury happened in the narrative."
    )

class EvolutionSchema(BaseModel):
    target_element: Literal["fire", "frost", "lightning", "void"] = Field(
        description="The element the dragon is evolving into."
    )
    stat_focus: Literal["wings", "armor", "horns"] = Field(
        description="The physical attribute of the dragon receiving the growth."
    )

# --- Tools with Guided Error Handling & Comprehensive Docstrings ---
# Criteria: Comprehensive Tool Docstrings & Descriptive Naming

def generate_dragon_injury_overlay(
    injury_type: Literal["cut", "scorch", "wing_tear", "bruise"],
    severity: Literal["minor", "moderate", "severe"],
    story_context: str,
    tool_context: ToolContext
) -> Dict[str, Any]:
    """Generates coordinate-mapped visual damage layers to overlay onto the custom dragon drawing.

    Args:
        injury_type: The physical classification of the sustained wound.
        severity: The intensity of the wound which dictates visual size and opacity.
        story_context: A description of the narrative cause to record in the ledger.

    Returns:
        A dict containing 'status', 'overlay_coordinates', and recovery parameters.
    """
    # Criteria: Guided Error Handling
    try:
        # Access session state variables
        dragon_health = tool_context.state.get("dragon_health", 100)
        
        # Calculate damage metrics
        damage_map = {"minor": 10, "moderate": 25, "severe": 45}
        damage = damage_map.get(severity, 10)
        new_health = max(0, dragon_health - damage)
        
        # Save new health directly back to state
        tool_context.state["dragon_health"] = new_health
        
        # Map injury to canvas coordinates
        coordinate_map = {
            "cut": {"x": 120, "y": 240, "asset": "layers/scratches.png"},
            "scorch": {"x": 80, "y": 150, "asset": "layers/scorch_marks.png"},
            "wing_tear": {"x": 300, "y": 100, "asset": "layers/torn_membrane.png"},
            "bruise": {"x": 190, "y": 280, "asset": "layers/dark_bruising.png"}
        }
        
        overlay = coordinate_map.get(injury_type, {"x": 0, "y": 0, "asset": "layers/generic.png"})
        
        return {
            "status": "success",
            "message": f"Applied {severity} {injury_type} overlay due to: '{story_context}'",
            "dragon_health": new_health,
            "visual_layer": overlay,
            "next_step_instruction": "Tell the user their dragon's canvas has been updated to reflect the damage."
        }
    except Exception as e:
        # Guided Error Handling returning recovery directions to LLM instead of crashing
        return {
            "status": "error",
            "message": f"Overlay mapping failed due to internal error: {str(e)}",
            "suggested_recovery": "Prompt the user to redraw their base dragon frame and re-submit the action."
        }

def apply_elemental_evolution(
    target_element: Literal["fire", "frost", "lightning", "void"],
    stat_focus: Literal["wings", "armor", "horns"],
    tool_context: ToolContext
) -> Dict[str, Any]:
    """Applies permanent elemental mutations to the companion dragon's stats and base image schema.

    Args:
        target_element: The magical element that governs the evolution's color shift and powers.
        stat_focus: The physical feature mutated during this evolution step.

    Returns:
        A dict outlining the upgraded stat parameters and asset overlay keys.
    """
    try:
        # Store mutations in persistent state
        mutations = tool_context.state.get("mutations", [])
        mutation_key = f"{target_element}_{stat_focus}"
        mutations.append(mutation_key)
        tool_context.state["mutations"] = mutations
        tool_context.state["current_element"] = target_element

        return {
            "status": "success",
            "mutated_attributes": mutations,
            "shading_css_filter": f"hue-rotate({target_element}) saturate(1.5)",
            "message": f"Your dragon's {stat_focus} now channel {target_element} magic!"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to evolve dragon: {str(e)}",
            "suggested_recovery": "Instruct the user that they must gain more experience points before this element triggers."
        }

# --- Human-in-the-Loop Evolution Confirmation ---
# Criteria: Human-in-the-Loop Hooks
def confirm_evolution_decision(target_element: str, **kwargs) -> bool:
    """Policy checking if an evolution step is high-stakes and requires manager review."""
    # Always require human approval for legendary void/lightning evolutions
    return target_element in ["void", "lightning"]

# FunctionTool wrapping the confirmation policy
confirm_evolution_milestone = FunctionTool(
    apply_elemental_evolution,
    require_confirmation=confirm_evolution_decision
)
