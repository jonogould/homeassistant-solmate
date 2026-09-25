"""Solmate solar inverter telemetry providers package."""

from __future__ import annotations

from typing import Any

import aiohttp

try:
    from ..const import (
        PROVIDER_DEMO,
        PROVIDER_ENPHASE,
        PROVIDER_FOXESS,
        PROVIDER_GOODWE,
        PROVIDER_GROWATT,
        PROVIDER_SOLAREDGE,
        PROVIDER_SOLARMAN,
        PROVIDER_SUNSYNK,
        PROVIDER_TESLA,
        PROVIDER_VICTRON,
    )
except (ImportError, ValueError):
    from const import (
        PROVIDER_DEMO,
        PROVIDER_ENPHASE,
        PROVIDER_FOXESS,
        PROVIDER_GOODWE,
        PROVIDER_GROWATT,
        PROVIDER_SOLAREDGE,
        PROVIDER_SOLARMAN,
        PROVIDER_SUNSYNK,
        PROVIDER_TESLA,
        PROVIDER_VICTRON,
    )
from .base import BaseSolarProvider
from .demo import DemoProvider
from .enphase import EnphaseProvider
from .foxess import FoxEssProvider
from .goodwe import GoodWeProvider
from .growatt import GrowattProvider
from .solaredge import SolarEdgeProvider
from .solarman import SolarmanProvider
from .sunsynk import SunsynkProvider
from .tesla import TeslaProvider
from .victron import VictronProvider

PROVIDER_CLASSES: dict[str, type[BaseSolarProvider]] = {
    PROVIDER_SUNSYNK: SunsynkProvider,
    PROVIDER_SOLAREDGE: SolarEdgeProvider,
    PROVIDER_VICTRON: VictronProvider,
    PROVIDER_TESLA: TeslaProvider,
    PROVIDER_FOXESS: FoxEssProvider,
    PROVIDER_GOODWE: GoodWeProvider,
    PROVIDER_GROWATT: GrowattProvider,
    PROVIDER_ENPHASE: EnphaseProvider,
    PROVIDER_SOLARMAN: SolarmanProvider,
    PROVIDER_DEMO: DemoProvider,
}


def get_provider(
    provider_type: str, session: aiohttp.ClientSession, config: dict[str, Any]
) -> BaseSolarProvider:
    """Instantiate and return the appropriate solar inverter provider."""
    cls = PROVIDER_CLASSES.get(provider_type, SunsynkProvider)
    return cls(session=session, config=config)


__all__ = [
    "BaseSolarProvider",
    "DemoProvider",
    "EnphaseProvider",
    "FoxEssProvider",
    "GoodWeProvider",
    "GrowattProvider",
    "PROVIDER_CLASSES",
    "SolarEdgeProvider",
    "SolarmanProvider",
    "SunsynkProvider",
    "TeslaProvider",
    "VictronProvider",
    "get_provider",
]
