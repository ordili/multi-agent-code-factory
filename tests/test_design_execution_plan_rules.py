"""DES-104 / DES-105～107 design_validate 规则测试。"""

from __future__ import annotations

from pathlib import Path

import pytest
from multi_agent_code_factory.nodes.design_validate import run_design_validate
from multi_agent_code_factory.profile_config import (
    ProfileConfig,
    load_profile,
)
from multi_agent_code_factory.schemas.design import DesignArtifact
from multi_agent_code_factory.schemas.prd import PrdArtifact
from multi_agent_code_factory.validators.design_execution_plan_rules import (
    validate_execution_plan_rules,
)
from multi_agent_code_factory.validators.design_rules import validate_design_rules

from tests.conftest import load_snippet_json


def _minimal_design(**overrides: object) -> DesignArtifact:
    base: dict = {
        "version": "1",
        "spec_ref": "x",
        "revision": 1,
        "summary": "s",
        "design_goals": ["g"],
        "non_goals": ["n"],
        "context_view": {"actors": ["user"]},
        "architecture": {
            "solution_strategy": "cli",
            "code_delta": {"summary": "greenfield"},
        },
        "cross_cutting": {},
        "modules": [
            {
                "name": "Store",
                "path": "src/store.py",
                "responsibility": "store",
                "code_domain": "STORE",
            }
        ],
        "external_dependencies": [
            {
                "name": "fs",
                "kind": "filesystem",
                "code_domain": "STORE",
                "purpose": "persist",
            }
        ],
        "interfaces": [
            {
                "name": "Store",
                "module_ref": "Store",
                "file": "src/store.py",
                "operations": [
                    {
                        "name": "save",
                        "summary": "save",
                        "inputs": [],
                        "outputs": [],
                    }
                ],
            }
        ],
        "traceability": [{"spec_ref_id": "AC-1", "spec_ref_kind": "AC"}],
        "error_catalog": [
            {
                "code": "ERR-STORE-001",
                "http_status": 500,
                "message": "fail",
            }
        ],
        "test_cases": [
            {
                "id": "TC-HAP-STORE-001",
                "kind": "happy",
                "covers": ["AC-1"],
                "error_code": None,
            },
            {
                "id": "TC-NEG-STORE-001",
                "kind": "negative",
                "error_code": "ERR-STORE-001",
            },
            {
                "id": "TC-BND-STORE-001",
                "kind": "boundary",
                "covers": ["AC-1"],
            },
        ],
        "dev_tasks": [
            {
                "id": "T1",
                "path": "pyproject.toml",
                "description": "framework",
                "depends_on": [],
            },
            {
                "id": "T2",
                "path": "src/store.py",
                "description": "store",
                "depends_on": ["T1"],
                "covers": ["AC-1"],
            },
        ],
        "file_plan": [
            {"path": "pyproject.toml", "action": "create"},
            {"path": "src/store.py", "action": "create"},
        ],
    }
    base.update(overrides)
    return DesignArtifact.model_validate(base)


@pytest.fixture
def python_profile() -> ProfileConfig:
    return load_profile("python")


def test_des_104_rejects_file_plan_path_not_in_dev_tasks(python_profile) -> None:
    design = _minimal_design(
        file_plan=[
            {"path": "src/store.py", "action": "create"},
            {"path": "src/__init__.py", "action": "create"},
        ],
    )
    violations, _ = validate_design_rules(design, python_profile)
    des104 = [v for v in violations if v.rule_id == "DES-104"]
    assert len(des104) == 1
    assert "__init__.py" in des104[0].message


def test_des_104_skipped_when_file_plan_empty(python_profile) -> None:
    design = _minimal_design(file_plan=[])
    violations, _ = validate_design_rules(design, python_profile)
    assert "DES-104" not in {v.rule_id for v in violations}


def test_des_105_warns_multiple_roots(python_profile) -> None:
    design = _minimal_design(
        dev_tasks=[
            {
                "id": "T1",
                "path": "pyproject.toml",
                "description": "a",
                "depends_on": [],
            },
            {
                "id": "T2",
                "path": "src/store.py",
                "description": "b",
                "depends_on": [],
            },
        ],
        file_plan=[
            {"path": "pyproject.toml", "action": "create"},
            {"path": "src/store.py", "action": "create"},
        ],
    )
    violations = validate_execution_plan_rules(design, python_profile)
    assert any(
        v.rule_id == "DES-105" and "exactly one root" in v.message for v in violations
    )


def test_des_105_warns_orphan_dependency_chain(python_profile) -> None:
    design = _minimal_design(
        dev_tasks=[
            {
                "id": "T1",
                "path": "pyproject.toml",
                "description": "framework",
                "depends_on": [],
            },
            {
                "id": "T2",
                "path": "src/a.py",
                "description": "orphan branch",
                "depends_on": [],
            },
            {
                "id": "T3",
                "path": "src/store.py",
                "description": "store",
                "depends_on": ["T1"],
            },
        ],
        file_plan=[
            {"path": "pyproject.toml", "action": "create"},
            {"path": "src/a.py", "action": "create"},
            {"path": "src/store.py", "action": "create"},
        ],
        modules=[
            {
                "name": "A",
                "path": "src/a.py",
                "responsibility": "a",
                "code_domain": "A",
            },
            {
                "name": "Store",
                "path": "src/store.py",
                "responsibility": "store",
                "code_domain": "STORE",
            },
        ],
    )
    violations = validate_execution_plan_rules(design, python_profile)
    assert any(
        v.rule_id == "DES-105" and "exactly one root" in v.message for v in violations
    )


def test_des_106_warns_dev_task_path_missing_from_modules(python_profile) -> None:
    design = _minimal_design(
        modules=[
            {
                "name": "Store",
                "path": "src/store.py",
                "responsibility": "store",
                "code_domain": "STORE",
            }
        ],
        dev_tasks=[
            {
                "id": "T1",
                "path": "pyproject.toml",
                "description": "framework",
                "depends_on": [],
            },
            {
                "id": "T2",
                "path": "src/extra.py",
                "description": "extra",
                "depends_on": ["T1"],
            },
        ],
        file_plan=[
            {"path": "pyproject.toml", "action": "create"},
            {"path": "src/extra.py", "action": "create"},
        ],
    )
    violations = validate_execution_plan_rules(design, python_profile)
    assert any(v.rule_id == "DES-106" for v in violations)


def test_des_107_warns_non_manifest_root_path(python_profile) -> None:
    design = _minimal_design(
        dev_tasks=[
            {
                "id": "T1",
                "path": "src/store.py",
                "description": "wrong root",
                "depends_on": [],
            },
            {
                "id": "T2",
                "path": "src/cli.py",
                "description": "cli",
                "depends_on": ["T1"],
            },
        ],
        modules=[
            {
                "name": "Store",
                "path": "src/store.py",
                "responsibility": "store",
                "code_domain": "STORE",
            },
            {
                "name": "Cli",
                "path": "src/cli.py",
                "responsibility": "cli",
                "code_domain": "CLI",
            },
        ],
        file_plan=[
            {"path": "src/store.py", "action": "create"},
            {"path": "src/cli.py", "action": "create"},
        ],
    )
    violations = validate_execution_plan_rules(design, python_profile)
    assert any(
        v.rule_id == "DES-107" and "pyproject.toml" in v.message for v in violations
    )


def test_execution_plan_aligned_has_no_warns(python_profile) -> None:
    violations = validate_execution_plan_rules(_minimal_design(), python_profile)
    assert not violations


def test_design_todo_valid_warns_execution_plan(
    python_profile, snippets_dir: Path
) -> None:
    """现有 fixture 缺 T1 框架步 → DES-107 warn，但不阻断 passed。"""
    spec = PrdArtifact.model_validate(
        load_snippet_json(snippets_dir, "prd-default.json")
    )
    design = DesignArtifact.model_validate(
        load_snippet_json(Path(__file__).parent / "fixtures", "design-todo-valid.json")
    )
    report = run_design_validate(design, python_profile, spec=spec)
    warn_ids = {v.rule_id for v in report.violations if v.severity.value == "warn"}
    assert "DES-107" in warn_ids
    assert report.passed is True
