"""Punto de entrada: streamlit run app.py."""

from pathlib import Path

import pandas as pd
import streamlit as st

from charts import costs_figure, function_figure
from methods import NumericalError, bisection, false_position, inspect_interval
from presentation import (
    csv_bytes, display_iterations, fmt, interpretation, interval_verification,
    method_theory, procedure, result_status, result_summary, summary_cards,
)
from problems import PROBLEMS, cloud_exploration

st.set_page_config(
    page_title="Métodos Numéricos — Bisección y Falsa Posición",
    page_icon="∑", layout="wide", initial_sidebar_state="auto",
)
# Oculta herramientas de desarrollador como Deploy; conserva los controles de uso.
st.set_option("client.toolbarMode", "viewer")
st.markdown(f"<style>{Path(__file__).with_name('styles.css').read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown('<div class="brand"><span class="brand-mark">∑</span><div><b>NUMÉRICA</b><small>Laboratorio de ingeniería</small></div></div>', unsafe_allow_html=True)
    st.caption("ESPACIO DE TRABAJO")
    selected = st.selectbox("Problema y método", list(PROBLEMS), key="problem_selector")
    problem = PROBLEMS[selected]
    st.divider()
    st.markdown("#### Parámetros del método")
    st.caption("Configura el intervalo y pulsa Ejecutar. Los cambios no recalculan el resultado por sí solos.")
    saved_config = st.session_state.get(f"config_{problem.key}", {
        "a": problem.default_interval[0], "b": problem.default_interval[1],
        "tolerance": 0.5, "max_iterations": 50,
    })
    with st.form(f"parameters_{problem.key}"):
        st.markdown("**Intervalo inicial [a, b]**")
        a = st.number_input(f"Extremo a ({problem.unit})", value=saved_config["a"], step=0.1,
                            format="%.8f", key=f"a_{problem.key}")
        b = st.number_input(f"Extremo b ({problem.unit})", value=saved_config["b"], step=0.1,
                            format="%.8f", key=f"b_{problem.key}")
        tolerance = st.number_input("Tolerancia (%)", min_value=0.00000001, value=saved_config["tolerance"],
                                    step=0.1, format="%.8f", key=f"tolerance_{problem.key}",
                                    help="0.5 significa 0.5 %, no 50 %. Se usa el error relativo entre aproximaciones consecutivas.")
        max_iterations = st.number_input("Máximo de iteraciones", min_value=1, max_value=10000,
                                         value=saved_config["max_iterations"], step=1, key=f"max_{problem.key}")
        submitted = st.form_submit_button("▶ Ejecutar método", type="primary", width="stretch")
    decimals = st.select_slider("Decimales visibles", options=[4, 6, 8, 10], value=6, key="decimals")

if submitted:
    saved_config = dict(a=a, b=b, tolerance=tolerance, max_iterations=max_iterations)
    st.session_state[f"config_{problem.key}"] = saved_config
    # Un intento inválido elimina el resultado anterior de esta página.
    st.session_state.pop(f"result_{problem.key}", None)
    st.session_state.pop(f"error_{problem.key}", None)
    try:
        solver = bisection if problem.key == "network" else false_position
        st.session_state[f"result_{problem.key}"] = solver(problem.function, a, b, tolerance, max_iterations)
    except NumericalError as exc:
        st.session_state[f"error_{problem.key}"] = str(exc)

stored = st.session_state.get(f"result_{problem.key}")
result, frame = stored if stored else (None, None)
interval = (saved_config["a"], saved_config["b"])
check = None
validation_error = None
try:
    check = inspect_interval(problem.function, *interval)
except NumericalError as exc:
    validation_error = str(exc)

st.markdown('<div class="eyebrow">LABORATORIO INTERACTIVO <span>•</span> RAÍCES DE ECUACIONES</div>', unsafe_allow_html=True)
st.title("Métodos Numéricos — Bisección y Falsa Posición")
st.markdown('<p class="subtitle">Aplicación de métodos para raíces de ecuaciones no lineales</p>', unsafe_allow_html=True)
st.markdown(f'<div class="context-bar"><span class="context-dot"></span><b>{problem.navigation}</b><span>Modelo → Método → Decisión</span></div>', unsafe_allow_html=True)
summary_cards(problem, interval, saved_config["tolerance"], result, decimals)

error_message = st.session_state.get(f"error_{problem.key}", validation_error)
if error_message:
    st.warning(f"⚠️ {error_message}")
elif result:
    result_status(result)
else:
    st.info("Prepara tu análisis: revisa el modelo y el intervalo; luego pulsa ▶ Ejecutar método en la barra lateral.")

tab_problem, tab_procedure, tab_iterations, tab_graph, tab_interpretation = st.tabs([
    "📘 Problema", "🧮 Procedimiento", "📊 Iteraciones", "📈 Gráfica", "💡 Interpretación",
])

with tab_problem:
    left, right = st.columns([1.1, 1], gap="large")
    with left:
        st.markdown("### " + problem.title)
        st.write(problem.context)
        with st.container(border=True):
            st.caption("MODELO MATEMÁTICO")
            if problem.key == "cloud":
                st.latex(r"C_1(t)=45+12t,\qquad C_2(t)=20e^{0.4t}")
                st.latex(r"C_1(t)=C_2(t)\ \Longleftrightarrow\ f(t)=0")
            st.latex(problem.formula)
            st.caption("C: capacidad en Mbps · Dominio: C > 8.5" if problem.key == "network"
                       else "t: tiempo en años, t ≥ 0 · Costos: miles de soles (S/ mil)")
        if problem.key == "cloud":
            st.markdown("#### Exploración inicial")
            exploration = pd.DataFrame(cloud_exploration())
            for column in ("C1(t)", "C2(t)", "f(t)"):
                exploration[column] = exploration[column].map(lambda x: fmt(x, decimals))
            st.dataframe(exploration, hide_index=True, width="stretch")
            st.caption("La exploración muestra un cambio de signo entre 3 y 4 años: es el intervalo inicial sugerido. Puedes modificarlo en la barra lateral.")
        method_theory(problem)
    with right:
        with st.container(border=True):
            st.markdown("#### Una mirada al modelo")
            if check:
                st.plotly_chart(function_figure(problem, interval, result, decimals), width="stretch",
                                config={"displayModeBar": False}, key=f"preview_{problem.key}")
                st.caption("Franja: intervalo inicial · Línea discontinua: f(x) = 0" +
                           (" · Diamante: aproximación calculada" if result else ""))
            else:
                st.info("Corrige el intervalo para visualizar la función.")
    if check:
        interval_verification(check, problem.variable, decimals)

with tab_procedure:
    procedure(problem, frame, decimals)

with tab_iterations:
    st.markdown("### Registro de iteraciones")
    st.write("Una fila por aproximación, sin ocultar pasos. La tabla usa los extremos anteriores a la actualización.")
    if frame is not None:
        st.dataframe(display_iterations(frame, decimals), hide_index=True, width="stretch",
                     height=min(650, 36 * (len(frame) + 1) + 5))
        st.caption("— indica que el error relativo no está definido. «Nuevo intervalo» es el subintervalo resultante; "
                   "en la última fila se muestra aunque el criterio de parada evite otra iteración. "
                   "Desliza horizontalmente para ver todas las columnas en pantallas pequeñas.")
        st.download_button("⬇ Descargar tabla CSV", data=csv_bytes(frame),
                           file_name=f"iteraciones_{problem.key}.csv", mime="text/csv", key=f"csv_{problem.key}")
        with st.expander("📋 Copiar resumen del resultado"):
            st.caption("Usa el icono de copia en la esquina superior derecha del bloque.")
            st.code(result_summary(problem, result, decimals), language=None)
    else:
        st.info("Todavía no hay iteraciones. Ejecuta el método con un intervalo válido.")

with tab_graph:
    st.markdown("### La raíz en su contexto gráfico")
    if check:
        st.plotly_chart(function_figure(problem, interval, result, decimals), width="stretch",
                        config={"displaylogo": False}, key=f"function_{problem.key}")
        if problem.key == "cloud":
            st.markdown("#### Comparación de los dos modelos de costos")
            st.plotly_chart(costs_figure(interval, result, decimals), width="stretch",
                            config={"displaylogo": False}, key="costs_cloud")
        st.caption("Los gráficos evalúan las mismas funciones que el algoritmo. Los marcadores se ubican en los "
                   "valores calculados, sin forzarlos a y = 0 ni a un costo idéntico. Puedes ampliar el gráfico "
                   "y consultar los valores al pasar el cursor.")
    else:
        st.info("Corrige el intervalo para generar los gráficos.")

with tab_interpretation:
    if result:
        interpretation(problem, result, decimals)
    else:
        st.info("Ejecuta el método para obtener una interpretación basada en el resultado numérico.")

st.divider()
with st.expander("Bisección vs. Falsa Posición"):
    st.dataframe(pd.DataFrame({
        "Característica": ["Nuevo xr", "Cambio de signo", "Convergencia segura", "Velocidad"],
        "Bisección": ["Punto medio", "Sí", "Generalmente sí*", "Estable: reduce el intervalo a la mitad"],
        "Falsa Posición": ["Interpolación lineal", "Sí", "Generalmente sí*", "Puede ser más rápida; puede estancarse"],
    }), hide_index=True, width="stretch")
    st.caption("* Se requiere continuidad, un intervalo válido y conservar el cambio de signo. "
               "La aritmética finita y el máximo de iteraciones pueden impedir alcanzar la tolerancia. "
               "Como estos ejemplos resuelven problemas diferentes, sus conteos de iteraciones no son una comparación directa de velocidad.")
st.markdown('<div class="footer"><span>NUMÉRICA / MÉTODOS NUMÉRICOS</span><span>Dos problemas reales. Cada paso, verificable.</span></div>', unsafe_allow_html=True)
