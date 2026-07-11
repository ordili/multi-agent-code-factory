"""Run 目录 Mermaid 路径规范化测试。"""

from __future__ import annotations

import pytest
from multi_agent_code_factory.agents.architect import (
    _normalize_design_diagram_paths,
    _write_mermaid_artifacts,
)
from multi_agent_code_factory.schemas.design import DesignArtifact
from multi_agent_code_factory.tools.run_artifacts import RunArtifactWriter
from multi_agent_code_factory.tools.run_artifacts.paths import (
    InvalidRunMmdPathError,
    normalize_run_mmd_path,
)


def test_normalize_run_mmd_path_strips_directory_prefix() -> None:
    assert normalize_run_mmd_path("docs/design.mmd") == "design.mmd"
    assert (
        normalize_run_mmd_path("docs/runs/arbitrage/architecture-arb.mmd")
        == "architecture-arb.mmd"
    )
    assert normalize_run_mmd_path("flow.mmd") == "flow.mmd"


def test_normalize_run_mmd_path_rejects_unsafe_paths() -> None:
    with pytest.raises(InvalidRunMmdPathError):
        normalize_run_mmd_path("../flow.mmd")
    with pytest.raises(InvalidRunMmdPathError):
        normalize_run_mmd_path("/tmp/flow.mmd")
    with pytest.raises(InvalidRunMmdPathError):
        normalize_run_mmd_path("flow.txt")


def test_normalize_design_diagram_paths_updates_design_json() -> None:
    design = DesignArtifact.model_validate(
        {
            "version": "1",
            "spec_ref": "x",
            "revision": 1,
            "modules": [
                {
                    "name": "Core",
                    "path": "src/core.py",
                    "responsibility": "logic",
                    "code_domain": "CORE",
                }
            ],
            "dev_tasks": [
                {
                    "id": "t1",
                    "path": "src/core.py",
                    "description": "implement",
                    "depends_on": [],
                }
            ],
            "diagrams": [
                {
                    "path": "docs/flow.mmd",
                    "kind": "sequence",
                    "title": "main",
                }
            ],
        }
    )

    normalized = _normalize_design_diagram_paths(design)

    assert normalized.diagrams[0].path == "flow.mmd"


def test_write_mermaid_artifacts_writes_flat_path(tmp_path) -> None:
    writer = RunArtifactWriter("mmd-path-test", base_dir=tmp_path)
    _write_mermaid_artifacts(
        writer,
        mmd_files=[{"path": "docs/design.mmd", "content": "flowchart LR\n  A --> B"}],
    )

    assert (tmp_path / "design.mmd").is_file()
    assert not (tmp_path / "docs").exists()
