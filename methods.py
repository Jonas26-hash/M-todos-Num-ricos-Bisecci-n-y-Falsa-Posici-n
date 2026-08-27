"""Bisección y Regula Falsi clásicos, sin solucionadores de raíces externos.

Todas las operaciones se realizan con float, sin redondeo intermedio.
Cada fila conserva los extremos usados para calcular su aproximación.
"""

import math
from dataclasses import dataclass
from numbers import Integral
from typing import Callable

import pandas as pd

Function = Callable[[float], float]
RESIDUAL_THRESHOLD = 1e-12
COLUMNS = [
    "Iteración", "a", "b", "xr", "f(a)", "f(b)", "f(xr)",
    "f(a)·f(xr)", "Error aproximado (%)", "Nuevo intervalo",
]


class NumericalError(ValueError):
    """Error de entrada o aritmética que puede mostrarse directamente en la UI."""


@dataclass(frozen=True)
class IntervalCheck:
    a: float
    b: float
    fa: float
    fb: float
    product: float


@dataclass(frozen=True)
class MethodResult:
    root: float
    residual: float
    error: float | None
    iterations: int
    converged: bool
    reason: str
    initial_interval: tuple[float, float]
    final_interval: tuple[float, float]
    tolerance: float
    max_iterations: int


def evaluate(func: Function, x: float) -> float:
    try:
        value = float(func(x))
    except (ValueError, TypeError, ZeroDivisionError, OverflowError) as exc:
        raise NumericalError(f"No se puede evaluar la función en x = {x}: {exc}") from exc
    if not math.isfinite(value):
        raise NumericalError(f"La función produce NaN o infinito en x = {x}. Revisa el dominio y el intervalo.")
    return value


def inspect_interval(func: Function, a: float, b: float) -> IntervalCheck:
    """Evalúa extremos válidos aun si no hay cambio de signo, para explicarlo."""
    try:
        a, b = float(a), float(b)
    except (TypeError, ValueError, OverflowError) as exc:
        raise NumericalError("Los extremos deben ser números reales finitos.") from exc
    if not all(math.isfinite(x) for x in (a, b)):
        raise NumericalError("Los extremos deben ser finitos, no NaN ni infinito.")
    if a >= b:
        raise NumericalError("El intervalo debe cumplir a < b.")
    fa, fb = evaluate(func, a), evaluate(func, b)
    product = fa * fb
    if not math.isfinite(product):
        raise NumericalError("El producto f(a) × f(b) excede la precisión numérica. Usa un intervalo más cercano a la raíz.")
    return IntervalCheck(a, b, fa, fb, product)


def validate_interval(func: Function, a: float, b: float) -> IntervalCheck:
    checked = inspect_interval(func, a, b)
    if checked.fa == 0 or checked.fb == 0:
        raise NumericalError("Un extremo ya es una raíz exacta. Para demostrar el método, elige un intervalo con f(a) × f(b) < 0.")
    if checked.product >= 0:
        raise NumericalError(
            "El intervalo seleccionado no garantiza una raíz porque f(a) y f(b) tienen el mismo signo."
            if (checked.fa > 0) == (checked.fb > 0)
            else "El producto de los extremos es demasiado pequeño para representarse. Reescala la función."
        )
    return checked


def approximate_error(current: float, previous: float | None) -> float | None:
    """Error porcentual. None significa que el error relativo no está definido."""
    if previous is None or current == 0:
        return None
    error = abs((current - previous) / current) * 100
    if not math.isfinite(error):
        raise NumericalError("El error relativo excede la precisión numérica; revisa el intervalo.")
    return error


def _solve(func: Function, a: float, b: float, tolerance: float,
           max_iterations: int, method: str) -> tuple[MethodResult, pd.DataFrame]:
    if not isinstance(tolerance, (int, float)) or not math.isfinite(tolerance) or tolerance <= 0:
        raise NumericalError("La tolerancia porcentual debe ser un número finito mayor que cero.")
    if isinstance(max_iterations, bool) or not isinstance(max_iterations, Integral) or max_iterations < 1:
        raise NumericalError("El máximo de iteraciones debe ser un entero mayor o igual que 1.")
    checked = validate_interval(func, a, b)
    a, b, fa, fb = checked.a, checked.b, checked.fa, checked.fb
    initial = (a, b)
    previous = None
    rows = []
    reason = "max_iterations"
    converged = False

    for iteration in range(1, max_iterations + 1):
        if method == "bisection":
            # Equivale a (a+b)/2, evitando que la suma desborde.
            xr = a / 2 + b / 2
        else:
            denominator = fa - fb
            if denominator == 0 or not math.isfinite(denominator):
                raise NumericalError("Falsa Posición no puede dividir entre f(a) − f(b). Revisa el intervalo o reescala la función.")
            xr = b - (fb * (a - b)) / denominator

        if not math.isfinite(xr) or not a <= xr <= b:
            raise NumericalError("La nueva aproximación no es finita o salió del intervalo por pérdida de precisión.")
        fxr = evaluate(func, xr)
        error = approximate_error(xr, previous)
        product = fa * fxr
        if not math.isfinite(product):
            raise NumericalError("El producto f(a) × f(xr) excede la precisión numérica. Reescala la función.")

        # Decidimos el subintervalo, pero todavía NO modificamos los extremos.
        if fxr == 0:
            next_interval = (xr, xr)
        elif (fa < 0) != (fxr < 0):
            next_interval = (a, xr)
        else:
            next_interval = (xr, b)
        rows.append({
            "Iteración": iteration, "a": a, "b": b, "xr": xr,
            "f(a)": fa, "f(b)": fb, "f(xr)": fxr, "f(a)·f(xr)": product,
            "Error aproximado (%)": error, "Nuevo intervalo": next_interval,
        })

        if abs(fxr) <= RESIDUAL_THRESHOLD:
            reason, converged = "residual", True
            break
        # Un valor repetido por redondeo de máquina no demuestra convergencia.
        if xr == previous or xr == a or xr == b:
            reason = "stagnation"
            break
        if error is not None and error <= tolerance:
            reason, converged = "tolerance", True
            break

        if next_interval[0] == a:
            b, fb = xr, fxr
        else:
            a, fa = xr, fxr
        previous = xr

    result = MethodResult(
        root=xr, residual=fxr, error=error, iterations=len(rows),
        converged=converged, reason=reason, initial_interval=initial,
        final_interval=next_interval, tolerance=tolerance, max_iterations=max_iterations,
    )
    return result, pd.DataFrame(rows, columns=COLUMNS)


def bisection(func: Function, a: float, b: float, tolerance: float = 0.5,
              max_iterations: int = 50) -> tuple[MethodResult, pd.DataFrame]:
    """Divide el intervalo por la mitad y conserva el cambio de signo."""
    return _solve(func, a, b, tolerance, max_iterations, "bisection")


def false_position(func: Function, a: float, b: float, tolerance: float = 0.5,
                   max_iterations: int = 50) -> tuple[MethodResult, pd.DataFrame]:
    """Regula Falsi clásica: xr = b − f(b)(a − b)/(f(a) − f(b))."""
    return _solve(func, a, b, tolerance, max_iterations, "false_position")
