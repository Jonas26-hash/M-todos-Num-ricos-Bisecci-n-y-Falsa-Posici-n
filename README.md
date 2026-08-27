# Métodos Numéricos — Bisección y Falsa Posición

Aplicación educativa en **Python 3.11+ y Streamlit** para resolver dos problemas de ingeniería, mostrar el desarrollo matemático e interpretar las raíces. Los algoritmos están implementados desde cero: no se usa SciPy ni ninguna función automática de búsqueda de raíces.

## Ejecución local

Abre una terminal en la carpeta que contiene `app.py`.

```bash
python -m venv .venv
```

En Windows (Símbolo del sistema):

```bat
.venv\Scripts\activate
```

En PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

En macOS/Linux:

```bash
source .venv/bin/activate
```

Instala las dependencias y ejecuta:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Abre [http://localhost:8501](http://localhost:8501). Detén el servidor con `Ctrl+C`.

**Windows sin activar el entorno:** si PowerShell bloquea `Activate.ps1`, no es necesario cambiar la política del sistema:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

El entorno `.venv` preparado en esta máquina ya permite usar el último comando. Si copias el proyecto a otro equipo, crea su propio entorno virtual; no copies `.venv`. Si `python` no se reconoce, instala Python 3.11 o superior y habilita su acceso desde la terminal (o utiliza `py -3`).

## Publicación: GitHub y Streamlit Community Cloud

El código puede alojarse en un repositorio de GitHub, pero **GitHub Pages no ejecuta directamente esta aplicación**: solo publica archivos estáticos y no proporciona el servidor Python que necesita Streamlit. Véase la [documentación de GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site).

Para conservar Python + Streamlit, la opción propuesta es **GitHub para el código y Streamlit Community Cloud para ejecutar la aplicación**:

1. Sube al repositorio los archivos fuente, `requirements.txt` y `.streamlit/config.toml`. No subas `.venv`, cachés ni secretos; `.gitignore` ya los excluye.
2. Conecta tu cuenta de GitHub en [Streamlit Community Cloud](https://share.streamlit.io/).
3. Elige **Create app**, selecciona el repositorio y su rama, e indica **`app.py`** como archivo de entrada.
4. Selecciona una versión compatible de Python (por ejemplo, 3.12) en las opciones avanzadas y publica.
5. Comparte la dirección `https://…streamlit.app` que entregue el servicio.

Consulta la [guía oficial de despliegue](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy). Esto es una guía de preparación; no significa que el proyecto ya esté publicado.

Usar exclusivamente GitHub Pages requeriría adaptar la aplicación para ejecutarse en el navegador, cambiando su arquitectura. No basta con subir `app.py` ni exportar una captura HTML de los resultados.

### Si vas a utilizar Vercel

Subir este proyecto a GitHub **no lo deja listo para desplegarse directamente en Vercel**. La versión actual se inicia con `streamlit run app.py`; no expone un `handler` HTTP ni una aplicación WSGI/ASGI como punto de entrada, que son las interfaces descritas en la [documentación del runtime Python de Vercel](https://vercel.com/docs/functions/runtimes/python).

Antes de importar el repositorio en Vercel habría que adaptar y verificar su integración o separar la interfaz de los algoritmos Python. Este proyecto conserva la aplicación Streamlit solicitada y no incluye una adaptación ni un despliegue en Vercel. Los algoritmos de `methods.py` y los modelos de `problems.py` pueden reutilizarse en esa adaptación.

## Cómo utilizar la aplicación

1. Selecciona el problema en la barra lateral.
2. Revisa el modelo, el dominio, la exploración de costos y la verificación del intervalo.
3. Ajusta `a`, `b`, la tolerancia porcentual y el máximo de iteraciones.
4. Pulsa **▶ Ejecutar método**. La aplicación no ejecuta los algoritmos por cambiar un campo.
5. Recorre **Problema**, **Procedimiento**, **Iteraciones**, **Gráfica** e **Interpretación**.
6. Descarga el CSV o abre **📋 Copiar resumen del resultado** y utiliza el icono de copia del bloque.

Las tarjetas superiores corresponden a la última configuración enviada, no a campos aún sin confirmar. Los resultados de cada problema se conservan durante la sesión al navegar entre ellos. Un intento inválido limpia el resultado anterior de esa página para no mostrar cifras obsoletas. Los decimales visibles (4, 6, 8 o 10) no modifican los cálculos.

## Problema 1 · Bisección: enlace de red

Una empresa necesita la capacidad `C` (Mbps) que satisface:

```text
f(C) = 1/(C − 8.5) − 0.35 ln(C − 2) = 0
Dominio: C > 8.5
Intervalo inicial: [9, 10]
```

La función es continua en el intervalo válido. Se exige `f(a) × f(b) < 0`. Por el teorema del valor intermedio existe al menos una raíz; ese argumento por sí solo no afirma unicidad.

Bisección calcula `xr = (a + b)/2` y conserva el subintervalo con cambio de signo. El código usa la expresión equivalente `a/2 + b/2` para evitar desbordamiento al sumar extremos.

La recomendación práctica es `ceil(C*)` Mbps, para no contratar por debajo de la aproximación obtenida. Si `C*` está cerca de un entero, conviene afinar la tolerancia antes de decidir. No se hacen afirmaciones sobre proveedores ni restricciones no presentes en el modelo.

## Problema 2 · Falsa Posición: migración a la nube

```text
C1(t) = 45 + 12t       (sistema local)
C2(t) = 20 exp(0.4t)   (sistema cloud)
f(t)  = C1(t) − C2(t)
```

El tiempo se mide en años y los costos en **miles de soles**. Se usa `t ≥ 0`, por ser tiempo transcurrido. La exploración evalúa `t = 0, 1, 2, 3, 4, 5`. El cambio de signo entre 3 y 4 años justifica `[3, 4]` como intervalo predeterminado.

Regula Falsi usa consistentemente:

```text
xr = b − f(b)(a − b)/(f(a) − f(b))
```

Después conserva el subintervalo con cambio de signo. Es el algoritmo clásico, sin modificaciones Illinois/Pegasus ni solucionadores externos.

La interpretación calcula realmente los costos en la aproximación y antes/después. El muestreo empieza con `delta = max(0.1, 0.02 |t*|)` y lo amplía si hace falta observar signos opuestos; no calcula otra raíz. Con la configuración inicial, **cloud cuesta menos en el punto anterior y local cuesta menos en el posterior**. No se presume que migrar a cloud sea ventajoso después del equilibrio.

La fila del equilibrio aproximado muestra la alternativa numéricamente menor cuando aún existe un residuo. No se oculta la diferencia ni se fuerza la igualdad. Las conclusiones se limitan al modelo y los tiempos evaluados.

## Precisión, criterios de parada y límites

Valores iniciales: **tolerancia = 0.5 %**, **máximo = 50 iteraciones**, **6 decimales visibles**.

```text
Ea = abs((xr_actual − xr_anterior) / xr_actual) × 100
```

- El primer error es indefinido y se muestra como `—`.
- Si `xr = 0`, no se divide entre cero: se comprueba el residuo y, de ser necesario, se continúa.
- Se declara convergencia si `Ea ≤ tolerancia` o `|f(xr)| ≤ 1e−12`.
- Llegar al máximo produce una advertencia y una aproximación provisional, sin recomendación final.
- Una aproximación repetida por precisión de máquina, sin residuo pequeño, se informa como estancamiento.
- Un extremo que ya es una raíz exacta se informa, pero no se ejecuta el algoritmo: se solicita otro intervalo con cambio de signo estricto.
- Se controlan dominios inválidos, orden de extremos, NaN/infinitos, división entre cero y desbordamientos.
- La UI admite hasta 10 000 iteraciones para evitar ejecuciones accidentales excesivas.

**Ea mide el cambio relativo entre iteraciones; no es el error verdadero respecto de una raíz desconocida.** Una tolerancia de 0.5 % no implica `|f(xr)| ≤ 0.005`. Por eso se informa también el residuo. Regula Falsi puede avanzar lentamente con intervalos poco favorables.

No hay redondeos intermedios. La tabla visual usa los decimales elegidos y notación científica cuando un número pequeño quedaría oculto como cero. El CSV conserva los valores originales, la primera celda de error vacía y UTF-8 con BOM para acentos en Excel.

Cada fila se guarda **antes de modificar a o b**, con estas columnas:

```text
Iteración | a | b | xr | f(a) | f(b) | f(xr) | f(a)·f(xr)
Error aproximado (%) | Nuevo intervalo
```

`Nuevo intervalo` es internamente una tupla sin redondear. La última fila muestra el subintervalo resultante aunque ya no vaya a ejecutarse otra iteración.

## Resultados reproducibles predeterminados

| Método | Intervalo | Raíz aproximada | Iteraciones | Ea final (%) | f(raíz) |
|---|---|---:|---:|---:|---:|
| Bisección | [9, 10] | 9.9062500000 Mbps | 5 | 0.3154574132 | −0.0125676440 |
| Falsa Posición | [3, 4] | 3.7650110929 años | 3 | 0.0992158726 | 0.0065322663 |

Para el enlace: **ceil(C*) = 10 Mbps**. Para el equilibrio: costo local ≈ **S/ 90.180133 mil** y costo cloud ≈ **S/ 90.173601 mil**. La diferencia residual es esperable con el criterio de parada solicitado.

Los gráficos llaman a los mismos modelos que los algoritmos. El marcador se coloca en `(xr, f(xr))`, no artificialmente en `(xr, 0)`. El gráfico de costos marca cada costo real evaluado en `t*`.

## Estructura

```text
metodos-numericos/
├── app.py                 # Navegación, formulario y coordinación
├── methods.py             # Bisección, Regula Falsi y validación
├── problems.py            # Funciones, dominios y problemas
├── presentation.py        # Tablas, pasos, interpretación y exportación
├── charts.py              # Gráficos Plotly
├── styles.css             # Diseño adaptable
├── requirements.txt
├── README.md
├── .streamlit/config.toml  # Tema y configuración
└── tests/
    ├── test_methods.py
    ├── test_presentation.py
    └── test_app.py
```

La carpeta puede tener otro nombre, como `App_de_Met_Num`; ejecuta los comandos desde su raíz.

### Algoritmos sin la interfaz

```python
from methods import bisection, false_position
from problems import network_function, cloud_equilibrium_function

result, dataframe = bisection(network_function, 9, 10)
print(result.root, result.error, result.converged)

result, dataframe = false_position(cloud_equilibrium_function, 3, 4)
print(dataframe)
```

`MethodResult` incluye raíz, residuo, error, iteraciones, estado, motivo de parada, intervalo inicial/final y parámetros usados.

## Pruebas

Se utilizan `unittest` y `streamlit.testing.v1.AppTest`, sin dependencias de desarrollo adicionales.

```bash
python -m unittest discover -s tests -v
```

En Windows sin activar el entorno:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Se comprueban convergencia, residuo, fórmula de cada fila, error consecutivo, cambio de signo, orden de actualizaciones, casos inválidos, dominio, desbordamiento, error en cero, límite de iteraciones, estancamiento, CSV, precisión de presentación, muestras de los gráficos y flujo de las dos páginas.

La revisión visual adicional comprueba pestañas, fórmulas, gráficos y barra lateral en escritorio y una pantalla estrecha. No se necesita Internet para calcular una vez instaladas las dependencias.

## Documentación de las herramientas

- [Formularios de Streamlit](https://docs.streamlit.io/develop/api-reference/execution-flow/st.form).
- [Pruebas con AppTest](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest).
- [Referencia de Streamlit](https://docs.streamlit.io/develop/api-reference).

Finalidad académica: las conclusiones dependen de los modelos proporcionados y las condiciones de los métodos.
