"""Structured LLM invocation with budget tracking."""

from __future__ import annotations

import json
from typing import Any, TypeVar

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from multi_agent_code_factory.config import FactoryConfig
from multi_agent_code_factory.llm import create_chat_model
from multi_agent_code_factory.profiles import ProfileConfig
from multi_agent_code_factory.schemas.run_meta import BudgetUsage
from multi_agent_code_factory.tools.write_artifact import RunArtifactWriter

T = TypeVar("T", bound=BaseModel)


class LlmRunner:
    """Invoke role prompts with structured output and run_meta budget updates."""

    def __init__(
        self,
        writer: RunArtifactWriter,
        profile: ProfileConfig,
        *,
        factory_config: FactoryConfig | None = None,
    ) -> None:
        self.writer = writer
        self.profile = profile
        self.factory_config = factory_config
        self._model = create_chat_model()

    def load_role_prompt(self, role_id: str) -> str:
        path = self.profile.prompts_dir / f"{role_id}.txt"
        if path.is_file():
            return path.read_text(encoding="utf-8")
        fallback = self.profile.prompts_dir / "python-style-snippet.txt"
        if fallback.is_file():
            return fallback.read_text(encoding="utf-8")
        return (
            f"You are the {role_id} agent. Output must match the requested JSON schema."
        )

    def _check_budget(self) -> None:
        if self.factory_config is None or self.factory_config.budget is None:
            return
        meta = self.writer.read_meta()
        if meta is None or meta.budget is None:
            return
        max_calls = meta.budget.max_llm_calls
        used = meta.budget.used_llm_calls or 0
        if max_calls is not None and used >= max_calls:
            msg = f"LLM call budget exceeded ({used}/{max_calls})"
            raise RuntimeError(msg)

    def _record_call(self) -> None:
        meta = self.writer.read_meta()
        if meta is None:
            return
        budget = meta.budget
        if budget is None and self.factory_config and self.factory_config.budget:
            budget = BudgetUsage(
                max_llm_calls=self.factory_config.budget.max_llm_calls,
                max_tokens=self.factory_config.budget.max_tokens,
                used_llm_calls=0,
                used_tokens=0,
            )
        if budget is None:
            budget = BudgetUsage(used_llm_calls=1, used_tokens=0)
        else:
            budget = budget.model_copy(
                update={"used_llm_calls": (budget.used_llm_calls or 0) + 1}
            )
        self.writer.update_meta(budget=budget)

    def invoke_structured(
        self,
        *,
        role_id: str,
        schema: type[T],
        context: dict[str, Any],
        extra_system: str | None = None,
    ) -> T:
        self._check_budget()
        system_parts = [self.load_role_prompt(role_id)]
        style = self.profile.prompts_dir / "python-style-snippet.txt"
        if role_id in {"developer", "architect", "pm"} and style.is_file():
            system_parts.append(style.read_text(encoding="utf-8"))
        if extra_system:
            system_parts.append(extra_system)
        system_prompt = "\n\n".join(
            part.strip() for part in system_parts if part.strip()
        )
        user_prompt = json.dumps(context, ensure_ascii=False, indent=2)
        structured = self._model.with_structured_output(schema)
        result = structured.invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]
        )
        if not isinstance(result, schema):
            result = schema.model_validate(result)
        self._record_call()
        return result
