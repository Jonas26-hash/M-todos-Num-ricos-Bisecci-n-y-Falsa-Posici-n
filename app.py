"""Entrada ASGI para Vercel y Uvicorn, sin ejecutar la interfaz al importar.

Uso local: streamlit run app.py
Alternativa: python -m uvicorn app:app --host 127.0.0.1 --port 8501
"""

from pathlib import Path

import streamlit as st

# Vercel importa esta variable. Streamlit ejecuta la interfaz por sesión,
# no durante la detección del punto de entrada del servidor.
app = st.App(Path(__file__).resolve().with_name("streamlit_app.py"))

if __name__ == "__main__":
    app.run()
