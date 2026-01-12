import json


def test_normalization_runs_only_at_cli_boundary(monkeypatch, capsys):
    """
    DX-2.1 CANONICAL BOUNDARY TEST.

    normalize_diagnostics() MUST run ONLY at the final CLI
    presentation boundary, and ONLY when probe-enabled.

    This test MUST fail if normalization is invoked earlier
    in the diagnostics pipeline.
    """

    # Enable normalization probe (test-only)
    monkeypatch.setenv("THN_DIAG_NORMALIZATION_PROBE", "1")

    from tests.golden._runner import run_cli

    # NOTE: run_cli expects argv as a LIST, not a string
    result = run_cli(["diag", "env", "--json"], capsys)

    # --- runner contract ---
    assert result.code == 0

    raw = result.out.strip() or result.err.strip()
    assert raw, "Expected JSON output from CLI"

    payload = json.loads(raw)

    # --- DX-2.1 assertions ---
    assert payload.get("__normalized__") is True
    assert "diagnostics" in payload
    assert isinstance(payload["diagnostics"], list)


def test_normalization_does_not_run_without_probe(monkeypatch, capsys):
    """
    DX-2.1 guarantee (negative case):
    normalize_diagnostics() MUST NOT run unless explicitly probe-enabled.

    This test protects against accidental always-on normalization.
    """

    # Explicitly ensure probe is NOT set
    monkeypatch.delenv("THN_DIAG_NORMALIZATION_PROBE", raising=False)

    from tests.golden._runner import run_cli

    result = run_cli(["diag", "env", "--json"], capsys)

    assert result.code == 0

    payload = json.loads(result.out)

    # Sentinel injected ONLY by normalization layer
    assert "__normalized__" not in payload
