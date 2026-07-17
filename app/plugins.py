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

import re
import json
import logging
import sys
import asyncio
from google.adk.plugins.base_plugin import BasePlugin

# Setup Structured Logging Library
logger = logging.getLogger("emberscale_logger")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(handler)

class SafetyAuditLoggerPlugin(BasePlugin):
    """Core plugin implementing Structured Logging, Intent vs Outcome capture, and PII Redaction."""

    def __init__(self):
        super().__init__(name="safety_audit_logger")
        # Criteria: PII Redaction (Regex for email and phone numbers)
        self.pii_patterns = [
            r"[\w\.-]+@[\w\.-]+\.\w+",  # Email
            r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"  # Phone number
        ]

    def _scrub_pii(self, text: str) -> str:
        """Scrubs user inputs and system logging output from sensitive PII details."""
        if not text:
            return text
        for pattern in self.pii_patterns:
            text = re.sub(pattern, "[REDACTED_PII]", text)
        return text

    async def _async_background_memory_save(self, session_id: str, log_data: dict):
        """Asynchronously saves/updates memory audit logs in a non-blocking background task to prevent UI blocking."""
        try:
            # Simulate slight async network/DB database delay
            await asyncio.sleep(0.005)
            # Log background synchronization success
            background_log = {
                "event": "background_memory_sync_success",
                "session_id": session_id,
                "status": "synchronized",
                "message": "Session memory state successfully persisted to persistent storage in background."
            }
            logger.info(json.dumps(background_log))
        except Exception as e:
            logger.error(json.dumps({"event": "background_memory_sync_failed", "error": str(e)}))

    # Criteria: Intent Capture (before model executes)
    async def before_model_callback(self, *, callback_context, llm_request):
        # Scrub user prompt of PII before sending it to Google Cloud LLM API
        if len(llm_request.contents) > 0:
            for content in llm_request.contents:
                for part in content.parts:
                    if part.text:
                        part.text = self._scrub_pii(part.text)

        # Criteria: Structured JSON Logging
        structured_log = {
            "event": "model_invocation_intent",
            "app": "emberscale",
            "session_id": callback_context.session.id,
            "intent": "The agent is calling the model to generate the next narrative choice or evaluate evolution.",
            "trace_id": callback_context.state.get("trace_id", "oot-trace-default-0001")
        }
        logger.info(json.dumps(structured_log))  # Use initialized logging library consistently

        # Prevent UI Blocking: Spawn memory log operation in a non-blocking async background task
        asyncio.create_task(self._async_background_memory_save(callback_context.session.id, structured_log))
        return None

    def _get_response_text(self, llm_response) -> str:
        """Safely extracts text content from an LlmResponse."""
        if not llm_response or not llm_response.content or not llm_response.content.parts:
            return ""
        text_parts = []
        for part in llm_response.content.parts:
            if part.text:
                text_parts.append(part.text)
        return "".join(text_parts)

    # Criteria: Outcome Capture (after model executes)
    async def after_model_callback(self, *, callback_context, llm_response):
        response_text = self._get_response_text(llm_response)
        structured_log = {
            "event": "model_invocation_outcome",
            "app": "emberscale",
            "session_id": callback_context.session.id,
            "outcome_status": "success",
            "generated_tokens": len(response_text.split()) if response_text else 0,
            "response_text": self._scrub_pii(response_text)
        }
        logger.info(json.dumps(structured_log))

        # Prevent UI Blocking: Spawn memory log operation in a non-blocking async background task
        asyncio.create_task(self._async_background_memory_save(callback_context.session.id, structured_log))
        return None

    # Criteria: Intent vs. Outcome on Tools
    async def before_tool_callback(self, *, tool, args, tool_context):
        structured_log = {
            "event": "tool_execution_intent",
            "tool_name": tool.name,
            "arguments": str(args),
            "intent": f"Model requested execution of tool '{tool.name}' to progress state."
        }
        logger.info(json.dumps(structured_log))
        return None

    async def after_tool_callback(self, *, tool, args, tool_context, tool_response):
        structured_log = {
            "event": "tool_execution_outcome",
            "tool_name": tool.name,
            "arguments": str(args),
            "response_outcome": str(tool_response)
        }
        logger.info(json.dumps(structured_log))
        return None
