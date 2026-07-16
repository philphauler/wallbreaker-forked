import pytest

from wallbreaker.config import ConfigError, Endpoint, load_config


def test_load_example_config():
    cfg = load_config("config.example.toml")
    assert cfg.default_profile == "openrouter"
    assert "zai" in cfg.profiles
    assert cfg.profiles["zai"].protocol == "anthropic"
    assert cfg.target is not None


def test_profile_lookup_and_unknown():
    cfg = load_config("config.example.toml")
    assert cfg.profile("openrouter").base_url == "https://openrouter.ai/api/v1"
    with pytest.raises(ConfigError):
        cfg.profile("does-not-exist")


def test_require_key_errors_without_env(monkeypatch):
    monkeypatch.delenv("MISSING_KEY", raising=False)
    ep = Endpoint("t", "openai", "http://x", "m", api_key_env="MISSING_KEY")
    with pytest.raises(ConfigError):
        ep.require_key()


def test_resolved_key_from_env(monkeypatch):
    monkeypatch.setenv("SOME_KEY", "secret-123")
    ep = Endpoint("t", "openai", "http://x", "m", api_key_env="SOME_KEY")
    assert ep.require_key() == "secret-123"


def test_apply_target_overrides_model_and_profile():
    from argparse import Namespace

    from wallbreaker.cli import apply_target_overrides

    cfg = load_config("config.example.toml")
    apply_target_overrides(cfg, Namespace(target="zai", target_model=None))
    assert cfg.target.protocol == "anthropic" and cfg.target.model == "glm-4.6"

    apply_target_overrides(cfg, Namespace(target=None, target_model="x-ai/grok-2"))
    assert cfg.target.model == "x-ai/grok-2"
    assert cfg.target.base_url == "https://api.z.ai/api/anthropic"


def test_provider_profile_default_model_is_optional(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text(
        'default_profile = "ready"\n\n'
        '[profiles.ready]\nprotocol = "openai"\nbase_url = "https://ready.example/v1"\nmodel = "ready-model"\n\n'
        '[profiles.discovering]\nprotocol = "openai"\nbase_url = "https://models.example/v1"\n',
        encoding="utf-8",
    )

    config = load_config(path)
    assert config.profiles["discovering"].model == ""


def test_concrete_target_still_requires_model(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text(
        'default_profile = "ready"\n\n'
        '[profiles.ready]\nprotocol = "openai"\nbase_url = "https://ready.example/v1"\nmodel = "ready-model"\n\n'
        '[target]\nprotocol = "openai"\nbase_url = "https://target.example/v1"\n',
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="target.*model"):
        load_config(path)
