"""
Gemini integration for pre-visit and post-visit AI summaries.

FAILURE HANDLING (per brief's requirement: "LLM failures must be handled
gracefully, system should not break"):
- Every call is wrapped with tenacity retry (configurable attempts) for
  transient errors (timeouts, 5xx, rate limits).
- If all retries fail, we DO NOT raise — we return a structured fallback
  payload and flag `failed=True`. Callers store the fallback text in the DB
  and set the *_failed integer flag so the UI can show "AI summary
  unavailable, please review symptoms/notes manually" instead of breaking
  the booking or visit-completion flow.
- JSON parsing of the model's response is defensive: if the model wraps the
  JSON in markdown fences or adds preamble, we strip and recover before
  giving up.
"""
import json
import re
import logging
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import google.generativeai as genai
from app.core.config import settings

logger = logging.getLogger("llm_service")

if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)


class LLMError(Exception):
    pass


def _extract_json(text: str) -> dict:
    """Strips markdown code fences / preamble and parses JSON defensively."""
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(0)
    return json.loads(cleaned)


@retry(
    stop=stop_after_attempt(settings.LLM_MAX_RETRIES + 1),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type(LLMError),
    reraise=True,
)
def _call_gemini(prompt: str) -> str:
    if not settings.GEMINI_API_KEY:
        raise LLMError("GEMINI_API_KEY not configured")
    try:
        model = genai.GenerativeModel(settings.GEMINI_MODEL)
        response = model.generate_content(
            prompt,
            request_options={"timeout": settings.LLM_TIMEOUT_SECONDS},
        )
        if not response or not response.text:
            raise LLMError("Empty response from Gemini")
        return response.text
    except Exception as exc:  # noqa: BLE001 — any provider error becomes a retryable LLMError
        raise LLMError(str(exc)) from exc


PRE_VISIT_PROMPT_TEMPLATE = """You are a clinical triage assistant helping a doctor prepare for a patient visit.
Analyse the symptoms below and respond with STRICT JSON only, no markdown, no preamble, in exactly this shape:
{{
  "urgency_level": "Low" | "Medium" | "High",
  "chief_complaint": "<one sentence summary of the main problem>",
  "suggested_questions": ["<question 1>", "<question 2>", "<question 3>"]
}}

Symptoms: {symptoms}
"""

POST_VISIT_PROMPT_TEMPLATE = """You are a medical assistant converting clinical notes into a patient-friendly summary.
Respond with STRICT JSON only, no markdown, no preamble, in exactly this shape:
{{
  "summary": "<plain-language explanation of what was found and what it means, 3-5 sentences>",
  "medication_schedule": "<plain-language description of how and when to take each medication>",
  "follow_up_steps": "<plain-language description of what the patient should do next, including when to return or seek urgent care>"
}}

Clinical notes: {notes}
Prescriptions (structured): {prescriptions}
"""


def generate_pre_visit_summary(symptoms: str) -> dict:
    """
    Returns: {
      "urgency_level": str, "chief_complaint": str, "suggested_questions": list[str],
      "failed": bool, "raw": Optional[str]
    }
    """
    prompt = PRE_VISIT_PROMPT_TEMPLATE.format(symptoms=symptoms)
    try:
        raw = _call_gemini(prompt)
        parsed = _extract_json(raw)
        return {
            "urgency_level": parsed.get("urgency_level", "Medium"),
            "chief_complaint": parsed.get("chief_complaint", ""),
            "suggested_questions": parsed.get("suggested_questions", [])[:3],
            "failed": False,
            "raw": raw,
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("Pre-visit LLM summary failed after retries: %s", exc)
        return {
            "urgency_level": "Medium",
            "chief_complaint": "AI summary unavailable — please review the patient's symptoms below manually.",
            "suggested_questions": [],
            "failed": True,
            "raw": None,
        }


def generate_post_visit_summary(notes: str, prescriptions: list) -> dict:
    """
    Returns: {"summary": str, "medication_schedule": str, "follow_up_steps": str, "failed": bool}
    """
    prompt = POST_VISIT_PROMPT_TEMPLATE.format(notes=notes, prescriptions=json.dumps(prescriptions))
    try:
        raw = _call_gemini(prompt)
        parsed = _extract_json(raw)
        return {
            "summary": parsed.get("summary", ""),
            "medication_schedule": parsed.get("medication_schedule", ""),
            "follow_up_steps": parsed.get("follow_up_steps", ""),
            "failed": False,
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("Post-visit LLM summary failed after retries: %s", exc)
        return {
            "summary": "Your doctor's notes are available below. An AI-simplified summary could not be generated this time.",
            "medication_schedule": "Please refer to the prescription details below for dosage and timing.",
            "follow_up_steps": "Contact the clinic if you have questions about your visit or next steps.",
            "failed": True,
        }
