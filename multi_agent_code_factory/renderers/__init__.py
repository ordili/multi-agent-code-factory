"""结构化 JSON 转人类可读 Markdown 的渲染器。"""

from multi_agent_code_factory.renderers.design_md import render_design_md
from multi_agent_code_factory.renderers.review_md import render_review_md
from multi_agent_code_factory.renderers.spec_md import render_spec_md

__all__ = ["render_design_md", "render_review_md", "render_spec_md"]
