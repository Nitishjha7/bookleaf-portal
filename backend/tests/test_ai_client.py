from types import SimpleNamespace

import pytest

from app.ai import client


class FakeModels:
    def __init__(self, behaviour):
        self.behaviour = behaviour
        self.tried = []

    def generate_content(self, model, contents, config):
        self.tried.append(model)
        result = self.behaviour[model]
        if isinstance(result, Exception):
            raise result
        return SimpleNamespace(text=result)


def _use(monkeypatch, behaviour):
    fake = SimpleNamespace(models=FakeModels(behaviour))
    monkeypatch.setattr(client, "_get_client", lambda: fake)
    monkeypatch.setattr(client.settings, "ai_model", "main")
    monkeypatch.setattr(client.settings, "ai_fallback_models", "backup")
    return fake.models


def test_falls_back_to_next_model_on_quota_error(monkeypatch):
    models = _use(monkeypatch, {"main": RuntimeError("429 quota"), "backup": " hello "})
    assert client.complete(system="s", user="u") == "hello"
    assert models.tried == ["main", "backup"]


def test_raises_when_every_model_fails(monkeypatch):
    _use(monkeypatch, {"main": RuntimeError("429"), "backup": RuntimeError("503")})
    with pytest.raises(client.AIUnavailable):
        client.complete(system="s", user="u")
