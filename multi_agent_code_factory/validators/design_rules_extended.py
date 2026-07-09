"""DES-012 至 DES-034 等扩展设计 JSON 规则。"""

from __future__ import annotations

import re
from typing import Any

from multi_agent_code_factory.schemas.design import DesignArtifact, DiagramKind
from multi_agent_code_factory.schemas.spec import SpecArtifact
from multi_agent_code_factory.schemas.validation_report import Violation
from multi_agent_code_factory.validators._report import error, warn
from multi_agent_code_factory.validators.task_tier import (
    requires_table_schemas,
    requires_transaction_constraints,
)

_ERR_CODE_RE = re.compile(r"^ERR-[A-Z][A-Z0-9_]{1,11}-\d{3}$")
_TC_ID_RE = re.compile(r"^TC-(HAP|NEG|BND)-[A-Z][A-Z0-9_]{1,11}-\d{3}$")
_CODE_DOMAIN_RE = re.compile(r"^[A-Z][A-Z0-9_]{1,11}$")
_RELATIONAL_STORAGE = frozenset(
    {
        "postgres",
        "postgresql",
        "mysql",
        "mariadb",
        "sqlite",
        "sql",
        "relational",
        "rdbms",
    }
)

_MIDDLEWARE_KINDS = frozenset({"db", "cache", "mq", "rpc", "api", "blockchain"})


def _err_domain(code: str) -> str | None:
    parts = code.split("-")
    if len(parts) >= 3 and parts[0] == "ERR":
        return parts[1]
    return None


def _tc_domain(tc_id: str) -> str | None:
    parts = tc_id.split("-")
    if len(parts) >= 4 and parts[0] == "TC":
        return parts[2]
    return None


def _registered_domains(design: DesignArtifact) -> set[str]:
    domains = {module.code_domain for module in design.modules if module.code_domain}
    for dep in design.external_dependencies:
        if dep.kind == "none":
            continue
        if dep.code_domain:
            domains.add(dep.code_domain)
    return domains


def _is_relational_storage(storage: str) -> bool:
    normalized = storage.lower().replace("-", "_").replace(" ", "_")
    return any(token in normalized for token in _RELATIONAL_STORAGE)


def validate_design_extended_rules(
    design: DesignArtifact,
    spec: SpecArtifact | None = None,
) -> list[Violation]:
    """DES-012 至 DES-034 扩展 JSON 规则。"""
    violations: list[Violation] = []

    if not design.external_dependencies:
        violations.append(
            error(
                "DES-012",
                "external_dependencies must not be empty "
                "(use kind=filesystem or kind=none with purpose)",
                field="external_dependencies",
            )
        )

    if requires_table_schemas(design, spec):
        has_table_schemas = bool(design.table_schemas)
        has_data_model_columns = bool(design.data_model) and any(
            isinstance(table.get("columns"), list) and table.get("columns")
            for table in design.table_schemas
        )
        if not has_table_schemas and not has_data_model_columns:
            violations.append(
                error(
                    "DES-013",
                    "table_schemas must not be empty, or data_model with column defs",
                    field="table_schemas",
                )
            )

    if (
        requires_transaction_constraints(design, spec)
        and not design.transaction_constraints
    ):
        violations.append(
            error(
                "DES-014",
                "transaction_constraints must not be empty",
                field="transaction_constraints",
            )
        )

    if not design.error_catalog:
        violations.append(
            error(
                "DES-015",
                "error_catalog must not be empty",
                field="error_catalog",
            )
        )

    if not design.test_cases:
        violations.append(
            error(
                "DES-016",
                "test_cases must not be empty",
                field="test_cases",
            )
        )
    elif spec is not None:
        covered_by_tests: set[str] = set()
        for tc in design.test_cases:
            covers = tc.get("covers")
            if isinstance(covers, list):
                covered_by_tests.update(str(item) for item in covers)
            elif isinstance(covers, str):
                covered_by_tests.add(covers)
        for ac in spec.acceptance_criteria:
            if ac.id not in covered_by_tests:
                violations.append(
                    warn(
                        "DES-016",
                        f"acceptance criterion {ac.id} not covered by test_cases",
                        field="test_cases",
                    )
                )

    diagram_kinds = {
        diagram.kind.value if hasattr(diagram.kind, "value") else str(diagram.kind)
        for diagram in design.diagrams
    }
    if DiagramKind.SEQUENCE.value not in diagram_kinds:
        violations.append(
            error(
                "DES-017",
                "diagrams must include kind=sequence",
                field="diagrams",
            )
        )
    if DiagramKind.FLOWCHART.value not in diagram_kinds:
        violations.append(
            error(
                "DES-017",
                "diagrams must include kind=flowchart",
                field="diagrams",
            )
        )

    for table in design.table_schemas:
        for col in table.get("columns") or []:
            if not isinstance(col, dict):
                continue
            name = col.get("name", "?")
            if not isinstance(col.get("nullable"), bool):
                violations.append(
                    error(
                        "DES-018",
                        f"column {name!r} must declare nullable as boolean",
                        field="table_schemas",
                    )
                )
            description = col.get("description")
            if not isinstance(description, str) or not description.strip():
                violations.append(
                    error(
                        "DES-018",
                        f"column {name!r} must have non-empty description",
                        field="table_schemas",
                    )
                )

        storage = str(table.get("storage", ""))
        if _is_relational_storage(storage):
            column_names = {
                str(col.get("name"))
                for col in table.get("columns") or []
                if isinstance(col, dict) and col.get("name")
            }
            for required_col in ("created_at", "updated_at"):
                if required_col not in column_names:
                    violations.append(
                        error(
                            "DES-019",
                            f"relational table {table.get('name', '?')!r} "
                            f"missing {required_col}",
                            field="table_schemas",
                        )
                    )
            audit = table.get("audit_policy") or {}
            if audit.get("require_version") and "version" not in column_names:
                violations.append(
                    error(
                        "DES-019",
                        f"table {table.get('name', '?')!r} requires version column",
                        field="table_schemas",
                    )
                )
            indexes = table.get("indexes") or []
            notes = table.get("notes") or ""
            if not indexes and not str(notes).strip():
                violations.append(
                    error(
                        "DES-019",
                        f"relational table {table.get('name', '?')!r} needs indexes "
                        f"or notes explaining PK-only",
                        field="table_schemas",
                    )
                )

        for idx in table.get("indexes") or []:
            if not isinstance(idx, dict):
                continue
            purpose = idx.get("purpose")
            if not isinstance(purpose, str) or not purpose.strip():
                violations.append(
                    warn(
                        "DES-020",
                        f"index {idx.get('name', '?')!r} should include purpose",
                        field="table_schemas",
                    )
                )

    catalog_codes = {item.code for item in design.error_catalog if item.code}
    for err_item in design.error_catalog:
        code = err_item.code
        if not _ERR_CODE_RE.match(code):
            violations.append(
                error(
                    "DES-023",
                    f"error_catalog code {code!r} must match ERR-{{DOMAIN}}-{{NNN}}",
                    field="error_catalog",
                )
            )

    negative_by_code: dict[str, list[dict[str, Any]]] = {}
    kinds_present: set[str] = set()
    for tc in design.test_cases:
        tc_id = tc.get("id")
        if not isinstance(tc_id, str) or not _TC_ID_RE.match(tc_id):
            violations.append(
                error(
                    "DES-024",
                    (
                        f"test_cases id {tc_id!r} must match "
                        "TC-{HAP|NEG|BND}-{DOMAIN}-{NNN}"
                    ),
                    field="test_cases",
                )
            )
        kind = tc.get("kind")
        if isinstance(kind, str):
            kinds_present.add(kind)
        if isinstance(kind, str) and isinstance(tc_id, str):
            segment = tc_id.split("-")[1].lower()
            expected = {"hap": "happy", "neg": "negative", "bnd": "boundary"}.get(
                segment
            )
            if expected and kind != expected:
                violations.append(
                    warn(
                        "DES-026",
                        f"test case {tc_id} kind {kind!r} should match id segment",
                        field="test_cases",
                    )
                )
        error_code = tc.get("error_code")
        if isinstance(error_code, str) and error_code:
            if error_code not in catalog_codes:
                violations.append(
                    error(
                        "DES-025",
                        f"test_cases error_code {error_code!r} not in error_catalog",
                        field="test_cases",
                    )
                )
            if kind == "negative":
                negative_by_code.setdefault(error_code, []).append(tc)
            tc_domain = _tc_domain(tc_id) if isinstance(tc_id, str) else None
            err_domain = _err_domain(error_code)
            if (
                kind == "negative"
                and tc_domain
                and err_domain
                and tc_domain != err_domain
            ):
                violations.append(
                    warn(
                        "DES-031",
                        f"test case {tc_id} domain {tc_domain} differs from "
                        f"error_code domain {err_domain}",
                        field="test_cases",
                    )
                )

    for code in catalog_codes:
        negatives = negative_by_code.get(code, [])
        if not negatives:
            violations.append(
                error(
                    "DES-021",
                    f"error_catalog code {code} lacks negative test_cases entry",
                    field="test_cases",
                )
            )

    if design.test_cases:
        for required_kind in ("happy", "negative", "boundary"):
            if required_kind not in kinds_present:
                violations.append(
                    warn(
                        "DES-022",
                        f"test_cases should include kind={required_kind}",
                        field="test_cases",
                    )
                )

    module_domains: dict[str, str] = {}
    for module in design.modules:
        domain = module.code_domain
        if not _CODE_DOMAIN_RE.match(domain):
            violations.append(
                error(
                    "DES-027",
                    f"module {module.name!r} code_domain {domain!r} invalid",
                    field="modules",
                )
            )
        if domain in module_domains.values():
            violations.append(
                error(
                    "DES-027",
                    f"duplicate code_domain {domain!r} across modules",
                    field="modules",
                )
            )
        module_domains[module.name] = domain

    registered = _registered_domains(design)
    module_domain_set = {module.code_domain for module in design.modules}

    for dep in design.external_dependencies:
        kind = dep.kind
        domain = dep.code_domain
        if kind == "none":
            continue
        if kind != "filesystem" and (not domain or not _CODE_DOMAIN_RE.match(domain)):
            violations.append(
                error(
                    "DES-028",
                    f"external dependency {dep.name!r} requires code_domain",
                    field="external_dependencies",
                )
            )
        if kind in _MIDDLEWARE_KINDS and domain and domain in module_domain_set:
            violations.append(
                error(
                    "DES-028",
                    f"external dependency {dep.name!r} code_domain {domain!r} "
                    f"conflicts with module domain",
                    field="external_dependencies",
                )
            )
        if kind == "filesystem" and domain and domain not in module_domain_set:
            violations.append(
                error(
                    "DES-028",
                    f"filesystem dependency {dep.name!r} code_domain {domain!r} "
                    f"must match encapsulating module",
                    field="external_dependencies",
                )
            )

    for code in catalog_codes:
        domain = _err_domain(code)
        if domain and domain not in registered:
            violations.append(
                error(
                    "DES-029",
                    f"error_catalog code {code} domain {domain!r} not registered",
                    field="error_catalog",
                )
            )

    for tc in design.test_cases:
        tc_id = tc.get("id")
        if isinstance(tc_id, str):
            domain = _tc_domain(tc_id)
            if domain and domain not in registered:
                violations.append(
                    error(
                        "DES-030",
                        f"test_cases id {tc_id} domain {domain!r} not registered",
                        field="test_cases",
                    )
                )

    interfaces_by_module: dict[str, list[dict[str, Any]]] = {}
    for iface in design.interfaces:
        module_ref = iface.get("module_ref") or iface.get("name")
        if isinstance(module_ref, str):
            interfaces_by_module.setdefault(module_ref, []).append(iface)

    for module in design.modules:
        if module.code_domain == "SYS":
            continue
        module_ifaces = interfaces_by_module.get(module.name, [])
        if not module_ifaces:
            violations.append(
                error(
                    "DES-032",
                    f"module {module.name!r} lacks interfaces[] entry",
                    field="interfaces",
                )
            )
        for iface in module_ifaces:
            operations = iface.get("operations") or []
            if not operations:
                violations.append(
                    error(
                        "DES-033",
                        f"interface for module {module.name!r} has empty operations",
                        field="interfaces",
                    )
                )
            for op in operations:
                if not isinstance(op, dict):
                    continue
                summary = op.get("summary")
                if not isinstance(summary, str) or not summary.strip():
                    violations.append(
                        error(
                            "DES-033",
                            f"operation {op.get('name', '?')!r} requires summary",
                            field="interfaces",
                        )
                    )
                if "inputs" not in op or not isinstance(op.get("inputs"), list):
                    violations.append(
                        error(
                            "DES-033",
                            f"operation {op.get('name', '?')!r} requires inputs array",
                            field="interfaces",
                        )
                    )
                if "outputs" not in op or not isinstance(op.get("outputs"), list):
                    violations.append(
                        error(
                            "DES-033",
                            f"operation {op.get('name', '?')!r} requires outputs array",
                            field="interfaces",
                        )
                    )
                for err_code in op.get("errors") or []:
                    if isinstance(err_code, str) and err_code not in catalog_codes:
                        violations.append(
                            warn(
                                "DES-034",
                                f"operation {op.get('name', '?')!r} references "
                                f"unknown error {err_code!r}",
                                field="interfaces",
                            )
                        )

    return violations
