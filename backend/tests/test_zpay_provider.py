import pytest

from app.core.providers.zpay import (
    format_amount,
    get_zpay_gateway,
    get_zpay_key,
    get_zpay_notify_url,
    get_zpay_pid,
    get_zpay_return_url,
    parse_amount_cents,
    sign_params,
)


def test_zpay_amount_conversion_uses_cents_boundary():
    assert format_amount(1) == "0.01"
    assert format_amount(12345) == "123.45"
    assert parse_amount_cents("123.45") == 12345
    assert parse_amount_cents("0.005") == 1
    assert parse_amount_cents(None) is None
    assert parse_amount_cents("invalid") is None


def test_zpay_signature_sorts_fields_and_ignores_signature_metadata():
    params = {
        "money": "10.00",
        "pid": "merchant-1",
        "empty": "",
        "sign_type": "MD5",
        "sign": "old-signature",
        "optional": None,
    }

    assert sign_params(params, "secret") == "103a3b53da5ff22547e23dee85bfb153"


def test_zpay_configuration_reads_environment(monkeypatch):
    monkeypatch.setenv("ZPAY_PID", "merchant-1")
    monkeypatch.setenv("ZPAY_KEY", "secret")
    monkeypatch.setenv("ZPAY_GATEWAY", "https://pay.example.test/")
    monkeypatch.setenv("ZPAY_NOTIFY_URL", "https://api.example.test/notify")
    monkeypatch.setenv("ZPAY_RETURN_URL", "https://app.example.test/return")

    assert get_zpay_pid() == "merchant-1"
    assert get_zpay_key() == "secret"
    assert get_zpay_gateway() == "https://pay.example.test"
    assert get_zpay_notify_url() == "https://api.example.test/notify"
    assert get_zpay_return_url() == "https://app.example.test/return"


def test_zpay_required_configuration_rejects_missing_values(monkeypatch):
    for name in ("ZPAY_PID", "ZPAY_KEY", "ZPAY_NOTIFY_URL", "ZPAY_RETURN_URL"):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(ValueError, match="ZPAY_PID 未配置"):
        get_zpay_pid()
    with pytest.raises(ValueError, match="ZPAY_KEY 未配置"):
        get_zpay_key()
    with pytest.raises(ValueError, match="ZPAY_NOTIFY_URL 未配置"):
        get_zpay_notify_url()
    with pytest.raises(ValueError, match="ZPAY_RETURN_URL 未配置"):
        get_zpay_return_url()