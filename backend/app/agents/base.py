"""
Base Agent definition for AroMi 2.0 multi-agent system.

DESIGN PRINCIPLES:
- Each agent has a SINGLE bounded responsibility
- Agents communicate via structured typed outputs (not raw text)
- Every agent logs its reasoning for explainability
- Every agent respects hard safety constraints (medical filter)
- Agents can be unit-tested independently

WHY multi-agent over single prompt:
- Bounded responsibility → testable, debuggable, accountable
- Parallelism: Workout + Nutrition agents run concurrently
- Specialization: domain-specific few-shot examples per agent
- Error isolation: one bad prompt doesn't poison the whole plan
"""
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional
from sqlalchemy.orm import Session


@dataclass
class AgentContext:
    """Standardized input context passed to every agent."""
    user_id: int
    health_profile: dict           # from HealthProfile.to_agent_context()
    medical_conditions: list       # [{condition_name, restrictions}]
    injury_restrictions: list      # [{body_part, restrictions}]
    long_term_memory: dict         # {favorites, dislikes, patterns, injuries}
    week_number: int = 1           # weeks since user started
    db: Optional[Any] = None       # SQLAlchemy session


@dataclass
class AgentOutput:
    """Standardized output from every agent."""
    agent_name: str
    success: bool
    data: dict = field(default_factory=dict)
    reasoning: str = ""
    warnings: list = field(default_factory=list)
    latency_ms: int = 0
    token_count: int = 0


class BaseAgent(ABC):
    """Abstract base class for all AroMi agents."""

    name: str = "base_agent"

    def __init__(self, groq_api_key: str, model: str = "llama-3.3-70b-versatile"):
        self.groq_api_key = groq_api_key
        self.model = model

    @classmethod
    def build_context(
        cls,
        user_id: int,
        profile_data: dict,
        planner_state_or_memory: Optional[Any] = None,
        memory_context: Optional[dict] = None,
        db: Optional[Any] = None
    ) -> AgentContext:
        """Construct standard AgentContext from raw profile data and memory context."""
        planner_state = None
        long_term_mem = memory_context

        if isinstance(planner_state_or_memory, str):
            planner_state = planner_state_or_memory
        elif isinstance(planner_state_or_memory, dict) and long_term_mem is None:
            long_term_mem = planner_state_or_memory

        medical_conds = profile_data.get("medical_conditions", [])
        formatted_conds = []
        if isinstance(medical_conds, list):
            for c in medical_conds:
                if isinstance(c, dict):
                    formatted_conds.append({
                        "condition": str(c.get("condition") or c.get("condition_name") or ""),
                        "restrictions": [str(r) for r in c.get("restrictions", []) if isinstance(r, str)]
                    })
                elif isinstance(c, str):
                    formatted_conds.append({
                        "condition": c,
                        "restrictions": [c.lower()]
                    })

        injuries = profile_data.get("injuries", [])
        formatted_injuries = []
        if isinstance(injuries, list):
            for i in injuries:
                if isinstance(i, dict):
                    formatted_injuries.append({
                        "body_part": str(i.get("body_part") or i.get("name") or ""),
                        "restrictions": [str(r) for r in i.get("restrictions", []) if isinstance(r, str)]
                    })
                elif isinstance(i, str):
                    formatted_injuries.append({
                        "body_part": i,
                        "restrictions": [i.lower()]
                    })

        health_profile = dict(profile_data)
        if planner_state:
            health_profile["planner_state"] = planner_state

        return AgentContext(
            user_id=user_id,
            health_profile=health_profile,
            medical_conditions=formatted_conds,
            injury_restrictions=formatted_injuries,
            long_term_memory=long_term_mem or {},
            week_number=1,
            db=db
        )

    @abstractmethod
    async def run(self, context: AgentContext, **kwargs) -> AgentOutput:
        """Execute the agent's task and return a structured output."""
        pass

    def _get_groq_client(self):
        from groq import Groq
        return Groq(api_key=self.groq_api_key)

    async def _call_llm(self, system_prompt: str, user_prompt: str,
                        temperature: float = 0.3, max_tokens: int = 4096) -> tuple[str, int]:
        """Call the LLM and return (response_text, token_count) with graceful fallback on network error."""
        import asyncio
        import json as _json

        if not self.groq_api_key or len(self.groq_api_key.strip()) < 5 or self.groq_api_key == "dummy_key" or not self.groq_api_key.startswith("gsk_"):
            return "", 0

        try:
            client = self._get_groq_client()

            def _sync_call():
                return client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

            loop = asyncio.get_event_loop()
            completion = await loop.run_in_executor(None, _sync_call)
            content = completion.choices[0].message.content.strip()
            tokens = completion.usage.total_tokens if completion.usage else 0
            return content, tokens
        except Exception as e:
            print(f"[{self.name}] Groq connection warning: {e}. Engaging offline fallback generator.")
            return "", 0

    def _parse_json_response(self, raw: str) -> dict:
        """Robustly extract JSON from LLM response."""
        import json
        import re

        start = raw.find('{')
        end = raw.rfind('}')
        if start != -1 and end != -1:
            candidate = raw[start:end + 1]
            candidate = re.sub(r',\s*}', '}', candidate)
            candidate = re.sub(r',\s*]', ']', candidate)
            try:
                return json.loads(candidate)
            except Exception:
                pass
        # Fallback: try full response
        try:
            return json.loads(raw)
        except Exception:
            return {}

    def _medical_safety_check(self, context: AgentContext, exercise_name: str) -> tuple[bool, str]:
        """
        HARD SAFETY FILTER — cannot be overridden by LLM.
        Returns (is_safe, reason).
        This is rule-based, not LLM-based, because safety requires determinism.
        """
        exercise_lower = exercise_name.lower()

        # Check injury restrictions
        for injury in context.injury_restrictions:
            if not isinstance(injury, dict):
                continue
            restrictions = [str(r) for r in injury.get("restrictions", []) if isinstance(r, str)]
            body_part = str(injury.get("body_part", "")).lower()

            if "no_squats" in restrictions and any(w in exercise_lower for w in ["squat", "lunge"]):
                return False, f"Excluded due to {body_part} restriction: no_squats"
            if "no_running" in restrictions and any(w in exercise_lower for w in ["run", "sprint", "jog"]):
                return False, f"Excluded due to {body_part} restriction: no_running"
            if "no_overhead_press" in restrictions and any(w in exercise_lower for w in ["press", "shoulder"]):
                return False, f"Excluded due to {body_part} restriction: no_overhead_press"
            if "no_deep_knee_flexion" in restrictions and any(w in exercise_lower for w in ["squat", "lunge", "leg press"]):
                return False, f"Excluded due to {body_part} restriction: no_deep_knee_flexion"
            if "no_pull_ups" in restrictions and "pull" in exercise_lower:
                return False, f"Excluded due to {body_part} restriction: no_pull_ups"

        # Check medical condition restrictions
        for condition in context.medical_conditions:
            if not isinstance(condition, dict):
                continue
            restrictions = [str(r) for r in condition.get("restrictions", []) if isinstance(r, str)]
            name = str(condition.get("condition", "")).lower()

            if "no_hiit" in restrictions and any(w in exercise_lower for w in ["hiit", "burpee", "jump", "sprint"]):
                return False, f"Excluded due to {name}: high-intensity contraindicated"
            if "no_high_impact" in restrictions and any(w in exercise_lower for w in ["jump", "run", "hop", "sprint"]):
                return False, f"Excluded due to {name}: high-impact contraindicated"
            if "no_valsalva" in restrictions and any(w in exercise_lower for w in ["deadlift", "heavy squat", "heavy press"]):
                return False, f"Excluded due to {name}: Valsalva maneuver contraindicated"

        return True, ""
