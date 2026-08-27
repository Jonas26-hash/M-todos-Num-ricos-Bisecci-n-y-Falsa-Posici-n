"""Figuras Plotly construidas a partir de los mismos modelos y resultados."""

import math

import numpy as np
import plotly.graph_objects as go

from methods import MethodResult, NumericalError, evaluate
from problems import Problem, cloud_cost, local_cost

GREEN = "#137C66"
BLUE = "#4775B7"
AMBER = "#C4812A"


def _base(fig: go.Figure, xlabel: str, ylabel: str) -> go.Figure:
    fig.update_layout(
        template="plotly_white", height=370,
        margin=dict(l=20, r=25, t=40, b=25),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial, sans-serif", color="#465B66", size=12),
        hovermode="x unified",
        legend=dict(orientation="h", y=1.14, x=0),
        xaxis=dict(title=xlabel, gridcolor="#E7ECEF", zeroline=False),
        yaxis=dict(title=ylabel, gridcolor="#E7ECEF", zeroline=False),
    )
    return fig


def _sample(problem: Problem, interval: tuple[float, float]) -> np.ndarray:
    a, b = interval
    padding = max((b - a) * 0.2, 0.1)
    lower = max(math.nextafter(8.5, math.inf), a - padding) if problem.key == "network" else max(0, a - padding)
    upper = b + padding
    # No acercar innecesariamente la curva a la asíntota fuera del intervalo.
    if problem.key == "network":
        lower = max(lower, 8.5 + (a - 8.5) * 0.55)
    return np.linspace(lower, upper, 450)


def _values(func, xs) -> list[float | None]:
    values = []
    for x in xs:
        try:
            values.append(evaluate(func, float(x)))
        except NumericalError:
            values.append(None)
    return values


def function_figure(problem: Problem, interval: tuple[float, float],
                    result: MethodResult | None = None, decimals: int = 6) -> go.Figure:
    xs = _sample(problem, interval)
    if result:
        xs = np.sort(np.append(xs, result.root))
    fig = go.Figure()
    fig.add_vrect(x0=interval[0], x1=interval[1], fillcolor=GREEN, opacity=0.055,
                  line_width=0, annotation_text="Intervalo inicial", annotation_position="top left")
    fig.add_hline(y=0, line_width=1, line_color="#637783", line_dash="dash")
    fig.add_trace(go.Scatter(x=xs.tolist(), y=_values(problem.function, xs), name=f"f({problem.variable})",
                             mode="lines", line=dict(color=GREEN, width=3)))
    endpoints = list(interval)
    fig.add_trace(go.Scatter(x=endpoints, y=_values(problem.function, endpoints),
                             mode="markers", name="Extremos a, b",
                             marker=dict(color=BLUE, size=8)))
    if result:
        fig.add_vline(x=result.root, line_color=AMBER, line_dash="dot", line_width=1)
        fig.add_trace(go.Scatter(x=[result.root], y=[problem.function(result.root)],
                                 name="Raíz aproximada", mode="markers",
                                 marker=dict(color=AMBER, size=12, symbol="diamond")))
        fig.add_annotation(x=result.root, y=problem.function(result.root),
                           text=f"{problem.variable}* ≈ {result.root:.{decimals}f}",
                           showarrow=True, arrowcolor=AMBER, ax=45, ay=-48,
                           bgcolor="white", bordercolor="#E3E9ED", borderpad=6)
    return _base(fig, f"{problem.variable} ({problem.unit})",
                 f"f({problem.variable})" + (" · miles de soles" if problem.key == "cloud" else ""))


def costs_figure(interval: tuple[float, float], result: MethodResult | None = None,
                 decimals: int = 6) -> go.Figure:
    upper = max(5, interval[1] + 0.2 * (interval[1] - interval[0]))
    xs = np.linspace(0, upper, 450)
    if result:
        xs = np.sort(np.append(xs, result.root))
    fig = go.Figure()
    for func, color, name in ((local_cost, BLUE, "Sistema local · C₁(t)"),
                               (cloud_cost, GREEN, "Sistema cloud · C₂(t)")):
        fig.add_trace(go.Scatter(x=xs.tolist(), y=_values(func, xs), name=name,
                                 mode="lines", line=dict(color=color, width=3)))
    if result:
        fig.add_vline(x=result.root, line_color=AMBER, line_dash="dot")
        for func, color in ((local_cost, BLUE), (cloud_cost, GREEN)):
            fig.add_trace(go.Scatter(x=[result.root], y=[func(result.root)], showlegend=False,
                                     name="Costo evaluado en t*", mode="markers",
                                     marker=dict(color=color, size=10, line=dict(color="white", width=2))))
        fig.add_annotation(x=result.root, y=local_cost(result.root),
                           text=f"Equilibrio aproximado<br>t* ≈ {result.root:.{decimals}f} años",
                           showarrow=True, ax=-55, ay=-60, bgcolor="white", borderpad=6,
                           bordercolor="#E3E9ED", arrowcolor=AMBER)
    return _base(fig, "Tiempo (años)", "Costo (miles de soles)")
