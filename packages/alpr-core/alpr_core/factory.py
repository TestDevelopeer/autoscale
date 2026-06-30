"""Фабрика ALPR providers."""

from __future__ import annotations

from alpr_core.demo import DemoAlprProvider, MockAlprProvider


def create_alpr_provider(provider_type: str, **kwargs):
    if provider_type in ("demo",):
        return DemoAlprProvider()
    if provider_type in ("mock",):
        return MockAlprProvider(**kwargs)
    if provider_type in ("nomeroff", "nomeroff_net"):
        try:
            from alpr_core.nomeroff import NomeroffNetProvider  # noqa: WPS433

            return NomeroffNetProvider()
        except ImportError as exc:
            raise RuntimeError(
                "nomeroff-net не установлен. pip install alpr-core[nomeroff]"
            ) from exc
    raise ValueError(f"Unknown ALPR provider: {provider_type}")
