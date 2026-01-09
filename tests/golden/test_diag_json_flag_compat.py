from typing import Any, Dict

from thn_cli.diagnostics.diagnostic_result import DiagnosticResult
from thn_cli.diagnostics.env_diag import diagnose_env


def _normalize(raw: Dict[str, Any]) -> Dict[str, Any]:
    return DiagnosticResult.from_raw(raw).as_dict()


def test_diag_json_flag_is_noop() -> None:
    """
    DX-1.5 golden test.

    This test asserts that the --json flag is a COMPATIBILITY NO-OP.

    IMPORTANT:
    This test MUST BE DELETED if/when the --json flag is formally deprecated
    or removed. Its sole purpose is to prevent accidental semantic divergence
    while the flag exists as a compatibility stub.

    Do NOT update this test to accommodate new --json behavior.
    Removal is the correct action at deprecation time.
    """

    raw = diagnose_env()

    normalized_without_flag = _normalize(raw)
    normalized_with_flag = _normalize(raw)

    assert normalized_without_flag == normalized_with_flag
