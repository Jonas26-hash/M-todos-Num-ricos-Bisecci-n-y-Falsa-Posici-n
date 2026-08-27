"""Modelos de ingeniería. Las unidades y dominios son parte del modelo."""

import math
from dataclasses import dataclass
from typing import Callable


def _finite(value: float, name: str) -> float:
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{name} debe ser un número finito, no NaN ni infinito.")
    return value


def network_function(C: float) -> float:
    C = _finite(C, "C")
    if C <= 8.5:
        raise ValueError("La capacidad debe cumplir C > 8.5 Mbps: fuera de este dominio el modelo no es válido.")
    return 1 / (C - 8.5) - 0.35 * math.log(C - 2)


def _time(t: float) -> float:
    t = _finite(t, "t")
    if t < 0:
        raise ValueError("El tiempo debe ser t ≥ 0 años en este modelo de costos.")
    return t


def local_cost(t: float) -> float:
    cost = 45 + 12 * _time(t)
    if not math.isfinite(cost):
        raise ValueError("El costo local excede la precisión numérica. Usa un tiempo menor.")
    return cost


def cloud_cost(t: float) -> float:
    try:
        cost = 20 * math.exp(0.4 * _time(t))
    except OverflowError as exc:
        raise ValueError("El costo cloud excede la precisión numérica. Usa un tiempo menor.") from exc
    if not math.isfinite(cost):
        raise ValueError("El costo cloud no es finito. Usa un tiempo menor.")
    return cost


def cloud_equilibrium_function(t: float) -> float:
    return local_cost(t) - cloud_cost(t)


@dataclass(frozen=True)
class Problem:
    key: str
    navigation: str
    title: str
    method: str
    variable: str
    unit: str
    default_interval: tuple[float, float]
    function: Callable[[float], float]
    formula: str
    context: str


NETWORK = Problem(
    "network", "1. Bisección — Enlace de red", "Dimensionamiento de un enlace de red",
    "Bisección", "C", "Mbps", (9.0, 10.0), network_function,
    r"f(C)=\frac{1}{C-8.5}-0.35\ln(C-2)=0",
    "Una empresa de telecomunicaciones necesita determinar la capacidad de un enlace "
    "de datos que satisface su modelo de operación. Buscamos el valor de C donde f(C) = 0.",
)

CLOUD = Problem(
    "cloud", "2. Falsa Posición — Migración a la nube", "Punto de equilibrio: local y cloud",
    "Falsa Posición", "t", "años", (3.0, 4.0), cloud_equilibrium_function,
    r"f(t)=45+12t-20e^{0.4t}=0",
    "Una empresa compara un sistema local con una alternativa en la nube. "
    "El punto de equilibrio ocurre cuando ambos modelos de costos toman el mismo valor.",
)

PROBLEMS = {p.navigation: p for p in (NETWORK, CLOUD)}


def cloud_exploration() -> list[dict]:
    return [
        {"t": t, "C1(t)": local_cost(t), "C2(t)": cloud_cost(t),
         "f(t)": cloud_equilibrium_function(t),
         "Signo": "positivo" if cloud_equilibrium_function(t) > 0 else "negativo"
         if cloud_equilibrium_function(t) < 0 else "cero"}
        for t in range(6)
    ]
