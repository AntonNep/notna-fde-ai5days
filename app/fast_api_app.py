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
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app

from app.app_utils.telemetry import setup_telemetry
from app.app_utils.typing import Feedback

import logging as std_logging

setup_telemetry()

# Resilient credentials loading
try:
    _, project_id = google.auth.default()
except Exception:
    project_id = "default-project"

# Resilient Cloud Logging configuration with standard logging library fallback
try:
    if os.getenv("INTEGRATION_TEST") == "TRUE":
        raise ValueError("Integration test mode: bypassing active Cloud Logging API connections.")
    from google.cloud import logging as google_cloud_logging
    logging_client = google_cloud_logging.Client()
    logger = logging_client.logger(__name__)
    use_cloud_logging = True
except Exception:
    logger = std_logging.getLogger("emberscale_fastapi")
    logger.setLevel(std_logging.INFO)
    if not logger.handlers:
        handler = std_logging.StreamHandler()
        logger.addHandler(handler)
    use_cloud_logging = False

allow_origins = (
    os.getenv("ALLOW_ORIGINS", "").split(",") if os.getenv("ALLOW_ORIGINS") else None
)

# Artifact bucket for ADK (created by Terraform, passed via env var)
logs_bucket_name = os.environ.get("LOGS_BUCKET_NAME")

AGENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Persistent async SQLite database session configuration
session_service_uri = "sqlite+aiosqlite:///emberscale_sessions.db"

artifact_service_uri = f"gs://{logs_bucket_name}" if logs_bucket_name else None

app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    web=True,
    artifact_service_uri=artifact_service_uri,
    allow_origins=allow_origins,
    session_service_uri=session_service_uri,
    otel_to_cloud=True,
)
app.title = "emberscale"
app.description = "API for interacting with the Agent emberscale"


@app.post("/feedback")
def collect_feedback(feedback: Feedback) -> dict[str, str]:
    """Collect and log feedback.

    Args:
        feedback: The feedback data to log

    Returns:
        Success message
    """
    if use_cloud_logging:
        logger.log_struct(feedback.model_dump(), severity="INFO")
    else:
        import json
        logger.info(json.dumps(feedback.model_dump()))
    return {"status": "success"}


# Main execution
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
