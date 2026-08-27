"""Presentación educativa: formato, procedimiento, tablas e interpretación."""

import html
import math

import pandas as pd
import streamlit as st

from methods import IntervalCheck, MethodResult, RESIDUAL_THRESHOLD
from problems import Problem, cloud_cost, cloud_equilibrium_function, local_cost


def fmt(value: float | None, decimals: int = 6) -> str:
    if value is None or pd.isna(value):
        return "—"
    if value != 0 and abs(value) < 10 ** (-decimals):
        return f"{value:.{decimals}e}"
    return f"{value:.{decimals}f}"


def interval_text(interval: tuple[float, float], decimals: int = 6) -> str:
    return f"[{fmt(interval[0], decimals)}, {fmt(interval[1], decimals)}]"


def display_iterations(frame: pd.DataFrame, decimals: int) -> pd.DataFrame:
    """Solo esta copia se convierte en texto; los datos originales conservan float."""
    shown = frame.copy(deep=True)
    for column in shown.columns:
        if column == "Iteración":
            continue
        if column == "Nuevo intervalo":
            shown[column] = shown[column].map(lambda value: interval_text(value, decimals))
        else:
            shown[column] = shown[column].map(lambda value: fmt(value, decimals))
    return shown


def csv_bytes(frame: pd.DataFrame) -> bytes:
    # CSV con precisión original, BOM para acentos en Excel y error inicial vacío.
    return frame.to_csv(index=False, na_rep="").encode("utf-8-sig")


def summary_cards(problem: Problem, interval: tuple[float, float], tolerance: float,
                  result: MethodResult | None, decimals: int) -> None:
    cards = [
        ("MÉTODO", problem.method, "Implementación desde cero"),
        ("TOLERANCIA", f"{tolerance:g} %", "Error relativo aproximado"),
        ("INTERVALO INICIAL", interval_text(interval, min(decimals, 4)), f"{problem.variable} en {problem.unit}"),
        ("ITERACIONES", str(result.iterations) if result else "—", "Registro completo del cálculo"),
        ("RAÍZ APROXIMADA", fmt(result.root, decimals) if result else "—", problem.unit),
        ("ERROR FINAL", f"{fmt(result.error, decimals)} %" if result and result.error is not None else "—",
         "Por aproximaciones consecutivas"),
    ]
    markup = '<div class="summary-grid">'
    for label, value, note in cards:
        markup += (f'<div class="summary-card"><span>{html.escape(label)}</span>'
                   f'<strong>{html.escape(value)}</strong><small>{html.escape(note)}</small></div>')
    st.markdown(markup + "</div>", unsafe_allow_html=True)


def interval_verification(check: IntervalCheck, variable: str, decimals: int) -> None:
    st.markdown("#### Verificación del intervalo inicial")
    frame = pd.DataFrame([
        {"Punto": point, variable: fmt(x, decimals), f"f({variable})": fmt(fx, decimals),
         "Signo": "positivo" if fx > 0 else "negativo" if fx < 0 else "cero"}
        for point, x, fx in (("a", check.a, check.fa), ("b", check.b, check.fb))
    ])
    st.dataframe(frame, hide_index=True, width="stretch")
    st.latex(rf"f(a)\times f(b) = {check.product:.{decimals}g}")
    if check.product < 0:
        st.success("✅ Existe un cambio de signo. Por el teorema del valor intermedio, existe al menos una raíz en [a,b].")
        st.caption("Los modelos son continuos en sus dominios válidos. El cambio de signo por sí solo no demuestra unicidad.")
    elif check.fa == 0 or check.fb == 0:
        st.info("Un extremo ya satisface f(x) = 0. Elige otro intervalo con cambio de signo estricto para ejecutar el método.")
    else:
        st.warning("⚠️ El intervalo seleccionado no garantiza una raíz porque f(a) y f(b) tienen el mismo signo.")


def method_theory(problem: Problem) -> None:
    with st.expander("¿Cómo funciona este método?"):
        if problem.key == "network":
            st.markdown("**Bisección** requiere una función continua y un intervalo con cambio de signo. "
                        "Divide el intervalo por la mitad, conserva el subintervalo con cambio de signo "
                        "y repite hasta alcanzar el criterio de parada.")
        else:
            st.markdown("**Falsa Posición** requiere una función continua y un intervalo con cambio de signo. "
                        "Interpola una recta entre los extremos; su intersección con el eje X define la nueva "
                        "aproximación. Después conserva el subintervalo con cambio de signo. Un extremo puede "
                        "permanecer fijo durante varias iteraciones.")
        st.caption("La tolerancia controla el cambio relativo entre aproximaciones, no el error verdadero ni directamente |f(xr)|.")


def procedure(problem: Problem, frame: pd.DataFrame | None, decimals: int) -> None:
    st.markdown("### Del intervalo a la raíz")
    st.write("Cada aproximación se obtiene con la fórmula del método. Los extremos mostrados son los valores usados antes de actualizar el intervalo.")
    formula = r"x_r=\frac{a+b}{2}" if problem.key == "network" else r"x_r=b-\frac{f(b)(a-b)}{f(a)-f(b)}"
    st.latex(formula)
    st.latex(r"f(a)f(x_r)<0\ \Rightarrow\ b=x_r,\qquad f(a)f(x_r)>0\ \Rightarrow\ a=x_r")
    st.caption("Si f(xr) = 0, se encontró una raíz exacta y el algoritmo se detiene.")
    st.latex(r"E_a=\left|\frac{x_r^{(i)}-x_r^{(i-1)}}{x_r^{(i)}}\right|100")
    st.caption(f"Parada: Ea ≤ tolerancia, |f(xr)| ≤ {RESIDUAL_THRESHOLD:g} o máximo de iteraciones. "
               "La primera iteración no tiene error anterior (—). Si xr = 0, el error relativo no está definido; "
               "se comprueba el residuo sin dividir por cero.")
    if frame is None:
        st.info("Ejecuta el método para ver las primeras tres iteraciones con los valores calculados.")
        return
    st.markdown("#### Primeras 3 iteraciones · desarrollo manual")
    st.caption("En pantallas pequeñas, desliza las fórmulas horizontalmente para ver la sustitución completa.")
    if len(frame) < 3:
        st.caption(f"El método se detuvo tras {len(frame)} iteración(es); se muestran todas las disponibles.")
    for position, row in frame.head(3).iterrows():
        with st.expander(f"Iteración {int(row['Iteración'])}  ·  xr ≈ {fmt(row['xr'], decimals)}", expanded=True):
            a, b, xr, fa, fb, fxr = [row[key] for key in ("a", "b", "xr", "f(a)", "f(b)", "f(xr)")]
            st.latex(rf"a={a:.{decimals}f},\qquad b={b:.{decimals}f}")
            if problem.key == "network":
                st.latex(rf"x_r=\frac{{{a:.{decimals}f}+{b:.{decimals}f}}}{{2}}={xr:.{decimals}f}")
            else:
                st.latex(rf"x_r={b:.{decimals}f}-\frac{{({fb:.{decimals}f})({a:.{decimals}f}-{b:.{decimals}f})}}{{({fa:.{decimals}f})-({fb:.{decimals}f})}}={xr:.{decimals}f}")
            st.write(f"f(a) = {fmt(fa, decimals)}  ·  f(b) = {fmt(fb, decimals)}  ·  f(xr) = {fmt(fxr, decimals)}")
            st.write(f"f(a)·f(xr) = {fmt(row['f(a)·f(xr)'], decimals)}")
            if fxr == 0:
                st.success("f(xr) = 0: se encontró una raíz exacta; no hace falta otro intervalo.")
            else:
                sign = "negativo" if (fa < 0) != (fxr < 0) else "positivo"
                change = "b = xr" if sign == "negativo" else "a = xr"
                st.write(f"Como el producto es {sign}, se toma **{change}**. Nuevo intervalo: **{interval_text(row['Nuevo intervalo'], decimals)}**.")
            if position == 0:
                st.caption("Error aproximado: — (no existe una aproximación anterior).")
            elif xr == 0:
                st.caption("Error aproximado: — (xr = 0; no se divide entre cero).")
            else:
                previous = frame.iloc[position - 1]["xr"]
                st.latex(rf"E_a=\left|\frac{{{xr:.{decimals}f}-({previous:.{decimals}f})}}{{{xr:.{decimals}f}}}\right|100={row['Error aproximado (%)']:.{decimals}f}\%")
    st.caption("Las sustituciones se redondean solo para lectura. El algoritmo conserva la precisión interna de Python.")


def result_status(result: MethodResult) -> None:
    if result.converged:
        st.success("✅ Convergencia alcanzada")
        criterion = (f"|f(xr)| ≤ {RESIDUAL_THRESHOLD:g}" if result.reason == "residual"
                     else f"error aproximado ≤ {result.tolerance:g} %")
        st.caption(f"Criterio satisfecho: {criterion}. Comprueba también el residuo en la tarjeta de verificación.")
    elif result.reason == "max_iterations":
        st.warning("⚠️ Se alcanzó el número máximo de iteraciones")
        st.caption("La última aproximación es provisional. Aumenta el máximo o revisa el intervalo y la tolerancia.")
    else:
        st.warning("⚠️ La aproximación dejó de cambiar por precisión de máquina, pero el residuo no es suficientemente pequeño.")
        st.caption("No se declara convergencia por un error relativo artificialmente nulo. Revisa el intervalo o la escala de la función.")


def verification(problem: Problem, result: MethodResult, decimals: int) -> None:
    with st.container(border=True):
        st.markdown("#### Verificación del resultado")
        st.code(f"f({problem.variable}*) = {fmt(result.residual, decimals)}\n|f({problem.variable}*)| = {fmt(abs(result.residual), decimals)}", language=None)
        if problem.key == "cloud":
            st.latex(r"C_1(t^*)\approx C_2(t^*)")
            st.write(f"C₁(t*) = S/ {fmt(local_cost(result.root), decimals)} mil")
            st.write(f"C₂(t*) = S/ {fmt(cloud_cost(result.root), decimals)} mil")
            st.caption("La diferencia entre los costos es exactamente f(t*). La igualdad es aproximada; una menor tolerancia puede reducir el residuo.")
        else:
            st.caption("El residuo mide cuánto se aparta la aproximación de f(C) = 0. No es el mismo valor que el error porcentual entre iteraciones.")


def cost_comparison(root: float) -> tuple[pd.DataFrame, float]:
    """Muestrea ambos lados, ampliando delta si la aproximación aún es poco precisa.

    No refina la raíz ni presupone cuál alternativa es más económica.
    """
    delta = max(0.1, abs(root) * 0.02)
    for _ in range(20):
        before, after = max(0.0, root - delta), root + delta
        if cloud_equilibrium_function(before) * cloud_equilibrium_function(after) < 0:
            break
        delta *= 2
    rows = []
    for label, t in (("Antes del equilibrio", before), ("En el equilibrio (aproximado)", root),
                      ("Después del equilibrio", after)):
        c1, c2 = local_cost(t), cloud_cost(t)
        cheaper = "Iguales" if c1 == c2 else "Local" if c1 < c2 else "Cloud"
        rows.append({"Momento": label, "t (años)": t, "Costo local": c1, "Costo cloud": c2,
                     "Alternativa de menor costo": cheaper})
    return pd.DataFrame(rows), delta


def interpretation(problem: Problem, result: MethodResult, decimals: int) -> None:
    st.markdown("### Del resultado a la decisión")
    if not result.converged:
        st.warning("Resultado provisional: no se alcanzó la convergencia. No debe usarse como recomendación final.")
        verification(problem, result, decimals)
        return
    if problem.key == "network":
        left, right = st.columns(2)
        with left:
            st.metric("Capacidad matemática aproximada", f"{fmt(result.root, decimals)} Mbps")
        with right:
            st.metric("Capacidad práctica recomendada", f"{math.ceil(result.root)} Mbps")
        st.write("La raíz representa la capacidad que satisface el modelo matemático. En una implementación real "
                 "es razonable contratar una capacidad inmediatamente superior: redondear hacia arriba proporciona "
                 "margen y evita contratar por debajo del valor calculado.")
        st.caption("La recomendación usa ceil(C*) sobre la aproximación. Si el resultado está muy cerca de un entero, "
                   "conviene reducir la tolerancia antes de decidir. No sustituye un dimensionamiento completo de red.")
    else:
        st.metric("Punto de equilibrio", f"{fmt(result.root, decimals)} años")
        left, right = st.columns(2)
        left.metric("Costo local", f"S/ {fmt(local_cost(result.root), decimals)} mil")
        right.metric("Costo cloud", f"S/ {fmt(cloud_cost(result.root), decimals)} mil")
        table, delta = cost_comparison(result.root)
        st.markdown("#### ¿Qué alternativa cuesta menos?")
        st.caption(f"Se evalúan las funciones a ambos lados de t*: delta = {fmt(delta, decimals)} años "
                   "(el tiempo inferior se limita a cero). Todos los costos están en miles de soles.")
        shown = table.copy()
        for column in ("t (años)", "Costo local", "Costo cloud"):
            shown[column] = shown[column].map(lambda x: fmt(x, decimals))
        st.dataframe(shown, hide_index=True, width="stretch")
        before, after = table.iloc[0], table.iloc[-1]
        st.info(f"En el punto anterior evaluado, {before['Alternativa de menor costo']} tiene menor costo. "
                f"En el punto posterior evaluado, {after['Alternativa de menor costo']} tiene menor costo. "
                "La conclusión se obtiene de los costos calculados, no de una suposición sobre cloud.")
        st.caption("En la fila del equilibrio aproximado puede persistir una diferencia residual; se indica "
                   "la alternativa realmente menor. Estos puntos de comparación no prueban por sí solos una "
                   "ventaja para todo tiempo ni incluyen riesgos, calidad o costos de migración no modelados.")
    verification(problem, result, decimals)


def result_summary(problem: Problem, result: MethodResult, decimals: int) -> str:
    lines = [f"Método: {problem.method}", f"Problema: {problem.title}",
             f"Intervalo inicial: {interval_text(result.initial_interval, decimals)}",
             f"Tolerancia: {result.tolerance:g} %", f"Máximo de iteraciones: {result.max_iterations}",
             f"Iteraciones realizadas: {result.iterations}",
             f"{problem.variable}* ≈ {fmt(result.root, decimals)} {problem.unit}",
             f"Error aproximado: {fmt(result.error, decimals)}" + (" %" if result.error is not None else ""),
             f"f({problem.variable}*) = {fmt(result.residual, decimals)}",
             f"Estado: {'Convergencia alcanzada' if result.converged else 'Sin convergencia; aproximación provisional'}",
             f"Criterio de parada: {result.reason}"]
    if problem.key == "network" and result.converged:
        lines.append(f"Capacidad práctica recomendada: {math.ceil(result.root)} Mbps")
    if problem.key == "cloud":
        lines.extend([f"Costo local: S/ {fmt(local_cost(result.root), decimals)} mil",
                      f"Costo cloud: S/ {fmt(cloud_cost(result.root), decimals)} mil"])
    return "\n".join(lines)
