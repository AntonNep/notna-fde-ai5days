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

import os
import google.auth
from google.adk.agents import Agent
from google.adk.apps import App, ResumabilityConfig
from google.adk.apps.app import EventsCompactionConfig
from google.adk.apps.llm_event_summarizer import LlmEventSummarizer
from google.adk.models import Gemini
from google.genai import types

from app.tools import (
    generate_dragon_injury_overlay,
    apply_elemental_evolution,
    confirm_evolution_milestone
)
from app.plugins import SafetyAuditLoggerPlugin

# --- Preserve Standard GCP Environment Settings ---
try:
    _, project_id = google.auth.default()
    os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
except Exception:
    project_id = "default-project"
    os.environ["GOOGLE_CLOUD_PROJECT"] = project_id

os.environ["GOOGLE_CLOUD_LOCATION"] = "global"

# Setup API key authentication fallback if present
key_path = "/home/notna/agy-projs/gemini_key.txt"
if os.path.exists(key_path):
    with open(key_path, "r") as f:
        api_key = f.read().strip()
    os.environ["GEMINI_API_KEY"] = api_key
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"
else:
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

# --- Model Definitions (Strategic Model Routing) ---
fast_model = Gemini(
    model="gemini-flash-latest",
    retry_options=types.HttpRetryOptions(attempts=3)
)
smart_model = Gemini(
    model="gemini-pro-latest",
    retry_options=types.HttpRetryOptions(attempts=3)
)

# --- Sub-Agent 1: Narrative Storyteller ---
narrative_writer = Agent(
    name="narrative_writer",
    model=fast_model,
    instruction="""
    You are EmberScale's Narrative Writer. Your role is to write immersive, rich text adventure descriptions.
    - Keep story options dramatic, branching, and engaging.
    - If the user decides on a dangerous path, ensure they encounter physical trials where their dragon gets hurt.
    - When injuries occur, you must invoke the generate_dragon_injury_overlay tool.
    """,
    description="Writes story text and narrates choices."
)

# --- Sub-Agent 2: Evolution Designer ---
evolution_designer = Agent(
    name="evolution_designer",
    model=smart_model,
    instruction="""
    You are EmberScale's Evolution Designer. Your role is to plan how the dragon changes physically.
    - When the dragon accumulates enough experience or choice points, coordinate their physical evolution.
    - You must invoke confirm_evolution_milestone to ask the player for permission before completing the evolution.
    """,
    description="Handles dragon evolution calculations and coordinates.",
    tools=[confirm_evolution_milestone]
)

# --- Root Coordinator Agent ---
# Criteria: Multi-Agent Pattern (Coordinator delegation)
root_agent = Agent(
    name="emberscale_coordinator",
    model=smart_model,
    instruction="""
    You are the EmberScale Coordinator. You oversee the player's dragon storytelling journey.
    - Delegate narrative generation and branching choices to narrative_writer.
    - Delegate physical changes, stat upgrades, and form upgrades to evolution_designer.
    - Maintain a highly supportive, fantasy game-master tone.
    """,
    sub_agents=[narrative_writer, evolution_designer],
    tools=[generate_dragon_injury_overlay]
)

# --- History Compaction & App Config ---
# Criteria: History Compaction & Persistent Session State
app = App(
    name="app", # Must match agent directory name
    root_agent=root_agent,
    resumability_config=ResumabilityConfig(is_resumable=True), # Enable Human-in-the-Loop stops
    events_compaction_config=EventsCompactionConfig(
        compaction_interval=15,  # Compact context history every 15 turns
        overlap_size=3,          # Keep last 3 events for dialogue context continuity
        summarizer=LlmEventSummarizer(llm=fast_model)
    ),
    plugins=[
        SafetyAuditLoggerPlugin()  # Core plugin handling logging, PII scrub, intent-vs-outcome
    ]
)
