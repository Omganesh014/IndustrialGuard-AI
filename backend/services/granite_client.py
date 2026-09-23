"""
backend/services/granite_client.py

IBM Granite / watsonx.ai client for IndustrialGuard AI.

Role of the LLM (Granite):
- Natural-language narration of ML analysis results
- RAG-based knowledge synthesis
- Explanation generation (grounded in ML evidence)
- Recommendation narrative (no invented numbers)
- Report generation
- Conversational assistant

What Granite must NOT do:
- Perform numerical calculations
- Make statistical decisions
- Generate defect predictions
- Invent parameter thresholds

All Granite calls include the structured ML/analysis context in the prompt.
The LLM is grounded — it cannot fabricate technical information when
the system prompt explicitly prohibits it.
"""

import logging
import os
from typing import Any
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# IBM watsonx.ai configuration — loaded from environment variables
# NEVER hard-code credentials here
def get_watsonx_config():
    return {
        "url": os.getenv("WATSONX_API_URL", ""),
        "api_key": os.getenv("WATSONX_API_KEY", ""),
        "project_id": os.getenv("WATSONX_PROJECT_ID", ""),
        "model_id": os.getenv("GRANITE_MODEL_ID", "ibm/granite-13b-instruct-v2"),
        "use_cached": os.getenv("USE_CACHED_GRANITE_RESPONSES", "false").lower() == "true",
    }

CACHED_RESPONSES_PATH = "data/synthetic/demo_granite_responses.json"


SYSTEM_PROMPT = """You are an industrial quality control assistant for IndustrialGuard AI.

You receive structured analysis results from ML models and anomaly detectors.
Your role is to narrate and synthesize these results in clear engineering language.

STRICT RULES:
1. Do NOT invent numerical values. Use only the numbers provided in the context.
2. Do NOT claim causation — use language like "associated with", "likely contributing", "may indicate".
3. Do NOT fabricate industrial standards or technical thresholds not present in the context.
4. Do NOT claim the system has been validated in a real industrial environment.
5. Always end recommendations with: "Human engineer review required before any process action."
6. If retrieved documentation is available, reference it by source name.
7. If context is insufficient to answer, say: "Insufficient evidence available from current data."

You are a decision-support tool, not an autonomous control system.
"""

TASK_PROMPTS = {
    "quality_analysis_narration": (
        "Briefly summarize the quality analysis findings in 2-3 sentences. "
        "Reference the anomaly severity, contributing factors, and any retrieved documentation."
    ),
    "optimization_recommendation_narrative": (
        "Write a 2-3 sentence recommendation summary based on the evidence provided. "
        "Reference what parameter change is suggested and the evidence basis. "
        "Do not invent numbers. End with the human review requirement."
    ),
    "defect_explanation": (
        "Explain why this process record was flagged as high-risk in 3-4 sentences. "
        "Reference the top contributing features and retrieved documentation. "
        "Distinguish between model evidence and retrieved documentation."
    ),
    "quality_report": (
        "Generate a structured quality incident report based on the provided data. "
        "Include: incident summary, detected anomalies, defect risk assessment, "
        "contributing factors, and recommended next steps. "
        "Label all values as coming from ML analysis. "
        "Mark the report as requiring engineer review."
    ),
    "chat_assistant": (
        "Answer the engineer's question using only the information provided in the context. "
        "If the information is not available, say so explicitly."
    ),
}


def _build_prompt(task: str, context: dict, instruction: str | None = None) -> str:
    """Build a grounded prompt for Granite."""
    import json

    task_instruction = instruction or TASK_PROMPTS.get(task, "Summarize the following information.")
    context_str = json.dumps(context, indent=2, default=str)

    return (
        f"{task_instruction}\n\n"
        f"Context from ML analysis:\n{context_str}\n\n"
        f"Response:"
    )


def _call_watsonx(prompt: str, config: dict | None = None) -> str:
    """Call IBM watsonx.ai API with the Granite model."""
    cfg = config or get_watsonx_config()
    try:
        from ibm_watsonx_ai.foundation_models import ModelInference
        from ibm_watsonx_ai.credentials import Credentials

        credentials = Credentials(
            url=cfg["url"],
            api_key=cfg["api_key"],
        )
        model = ModelInference(
            model_id=cfg["model_id"],
            credentials=credentials,
            project_id=cfg["project_id"],
        )

        response = model.generate_text(
            prompt=SYSTEM_PROMPT + "\n\n" + prompt,
            params={
                "max_new_tokens": 400,
                "temperature": 0.2,   # low temperature for factual narration
                "top_p": 0.9,
            },
        )
        return response.strip()

    except ImportError:
        raise ImportError(
            "ibm-watsonx-ai not installed. Run: pip install ibm-watsonx-ai"
        )


def _load_cached_response(task: str) -> str:
    """Load pre-cached Granite response for demo failure recovery."""
    import json
    try:
        with open(CACHED_RESPONSES_PATH) as f:
            cache = json.load(f)
        response = cache.get(task, f"[Cached response not available for task: {task}]")
        logger.info(f"Using cached Granite response for task: {task}")
        return f"[CACHED DEMO RESPONSE — IBM API unavailable]\n\n{response}"
    except FileNotFoundError:
        return f"[IBM API unavailable. Cached response not found for task: {task}]"


def generate_narrative(task: str, context: dict, instruction: str | None = None) -> str:
    """
    Generate an LLM narrative for a given task and context.

    Args:
        task:        task key from TASK_PROMPTS (or custom instruction provided)
        context:     structured dict from ML/agent analysis
        instruction: override instruction (optional)

    Returns:
        str: Granite-generated narrative, grounded in context
    """
    cfg = get_watsonx_config()
    if not cfg["api_key"] or not cfg["url"]:
        logger.warning(
            "IBM watsonx.ai credentials not configured. "
            "Set WATSONX_API_KEY, WATSONX_API_URL, WATSONX_PROJECT_ID in .env"
        )
        if cfg["use_cached"]:
            return _load_cached_response(task)
        return (
            "[IBM watsonx.ai not configured. "
            "Set credentials in .env to enable Granite-powered narration.]"
        )

    prompt = _build_prompt(task, context, instruction)

    try:
        response = _call_watsonx(prompt, config=cfg)
        logger.info(f"Granite response generated for task: {task}")
        return response
    except Exception as e:
        logger.error(f"Granite API call failed: {e}")
        if cfg["use_cached"]:
            return _load_cached_response(task)
        return f"[Granite API error: {e}]"
