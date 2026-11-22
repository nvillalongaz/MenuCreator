import os
import json
from io import BytesIO

import pandas as pd
import streamlit as st

from tools.calculate_shopping import main as aggregate_ingredients
from tools.manual_cocinero import generar_manual

st.set_page_config(
    page_title="Menú Campamento",
    page_icon="🏕️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Estilo "Salvia" (los colores y la fuente están en .streamlit/config.toml;
# aquí solo lo que el tema no cubre: tarjetas, filas de comida y barra lateral)
# ---------------------------------------------------------------------------
TIENDA = (
    '<svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="#8FB09A" '
    'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    '<path d="M3 20 12 4l9 16"/><path d="M12 4v16"/><path d="M9 20l3-6 3 6"/><path d="M2 20h20"/></svg>'
)

st.markdown(
    """
<style>
/* Área principal */
.block-container { padding-top: 2.5rem; padding-bottom: 3rem; max-width: 1400px; }

/* Días: dos por fila, uno por fila si la zona principal es estrecha */
[class*="st-key-par_"] > [data-testid="stLayoutWrapper"]:first-child > [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; row-gap: 1rem; }
[class*="st-key-par_"] > [data-testid="stLayoutWrapper"]:first-child > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { flex: 1 1 430px !important; min-width: 0 !important; width: auto !important; }
/* Tarjetas de cada día y de la lista de compra */
[class*="st-key-dia_"], .st-key-compra {
    background: #FFFFFF;
    border: 0 !important;
    border-radius: 12px;
    box-shadow: 0 1px 2px rgba(30, 36, 33, .06), 0 0 0 1px rgba(30, 36, 33, .06);
    padding: 22px !important;
}
.titulo-dia { margin: 0; padding-bottom: 10px; font-size: 1.15rem; font-weight: 800; letter-spacing: -0.01em; color: #1E2421; }
.titulo-seccion { margin: 0; font-size: 1.25rem; font-weight: 800; letter-spacing: -0.01em; color: #1E2421; }

/* Filas de comida: una línea con nombre, plato y ajuste, separadas por una raya fina */
[class*="st-key-fila_"] { border-top: 1px solid #EEF0ED; padding-top: 8px; gap: 0.4rem; }
.comida { font-size: .85rem; font-weight: 700; color: #4C6B57; }
/* Filas de comida: anchos fijos para nombre, −, casilla y +; el desplegable ocupa el resto */
[class*="st-key-fila_"] > [data-testid="stLayoutWrapper"]:first-child > [data-testid="stHorizontalBlock"],
[class*="st-key-enc_"] > [data-testid="stLayoutWrapper"]:first-child > [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; gap: .5rem; }
[class*="st-key-fila_"] > [data-testid="stLayoutWrapper"]:first-child > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"],
[class*="st-key-enc_"] > [data-testid="stLayoutWrapper"]:first-child > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { min-width: 0 !important; width: auto !important; }
[class*="st-key-fila_"] > [data-testid="stLayoutWrapper"]:first-child > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(1),
[class*="st-key-enc_"] > [data-testid="stLayoutWrapper"]:first-child > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(1) { flex: 0 0 84px !important; }
[class*="st-key-fila_"] > [data-testid="stLayoutWrapper"]:first-child > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(2),
[class*="st-key-enc_"] > [data-testid="stLayoutWrapper"]:first-child > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(2) { flex: 1 1 auto !important; }
[class*="st-key-fila_"] > [data-testid="stLayoutWrapper"]:first-child > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(3),
[class*="st-key-enc_"] > [data-testid="stLayoutWrapper"]:first-child > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(3) { flex: 0 0 40px !important; }
[class*="st-key-fila_"] > [data-testid="stLayoutWrapper"]:first-child > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(4),
[class*="st-key-enc_"] > [data-testid="stLayoutWrapper"]:first-child > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(4) { flex: 0 0 52px !important; }
[class*="st-key-fila_"] > [data-testid="stLayoutWrapper"]:first-child > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(5),
[class*="st-key-enc_"] > [data-testid="stLayoutWrapper"]:first-child > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(5) { flex: 0 0 40px !important; }
[class*="st-key-enc_"] { margin-bottom: -0.6rem; }
/* Botones − / + del ajuste */
[class*="st-key-menos_"] button, [class*="st-key-mas_"] button {
    min-height: 40px; height: 40px; padding: 0; border-radius: 8px;
    border: 1px solid #C9D6C8; background: #FFFFFF; color: #4C6B57;
}
[class*="st-key-menos_"] button p, [class*="st-key-mas_"] button p { font-size: 1.15rem; font-weight: 800; line-height: 1; }
[class*="st-key-menos_"] button:hover, [class*="st-key-mas_"] button:hover { border-color: #4C6B57; background: #EEF3EF; color: #2F4637; }
[class*="st-key-ajuste_"] input { text-align: center; padding-left: 4px; padding-right: 4px; }
.enc { font-size: .7rem; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; color: #5E6B63; }
.enc-ajuste { display: block; white-space: nowrap; letter-spacing: .02em; text-align: center; cursor: help; border-bottom: 1px dotted #8FA096; width: fit-content; margin: 0 auto; }

/* Números sin los botones +/- para que quepan en la fila */
[data-testid="stNumberInputStepUp"], [data-testid="stNumberInputStepDown"] { display: none; }
[data-testid="stNumberInput"] input { font-weight: 700; }

/* Etiquetas pequeñas de los números del día */
[class*="st-key-dia_"] [data-testid="stWidgetLabel"] p { font-size: .75rem; font-weight: 600; color: #5E6B63; }

/* Barra lateral */
[data-testid="stSidebar"] .lateral-titulo { margin: 14px 0 6px; font-size: 1.6rem; font-weight: 700; line-height: 1.2; letter-spacing: -0.02em; color: #EEF1EE; }
[data-testid="stSidebar"] .lateral-texto { margin: 0 0 8px; font-size: .9rem; line-height: 1.6; color: #AEB8B1; }
.resumen { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1px; background: #343C37;
           border: 1px solid #343C37; border-radius: 10px; overflow: hidden; margin: 8px 0 14px; }
.resumen div { background: #1E2421; padding: 12px 14px; display: flex; flex-direction: column; gap: 2px; }
.resumen span { font-size: .75rem; color: #AEB8B1; }
.resumen strong { font-size: 1.35rem; font-weight: 700; color: #EEF1EE; }
.etiqueta-lateral { margin: 18px 0 6px; font-size: .72rem; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; color: #AEB8B1; }

/* Botón principal de la barra lateral: texto oscuro sobre salvia para que se lea bien */
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] { color: #14201A; font-weight: 800; min-height: 50px; }
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] p { font-weight: 800; font-size: 1rem; }
/* Descargas: el manual destacado con borde salvia */
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] { background: transparent; justify-content: flex-start; min-height: 46px; }
.st-key-dl_manual [data-testid="stBaseButton-secondary"] { border-color: #8FB09A; }
.st-key-dl_manual_m [data-testid="stBaseButton-secondary"] { border-color: #4C6B57; }
/* Móvil: las filas de comida y la cabecera del día no se apilan, y aparece un botón de generar abajo */
.st-key-generar_movil, .st-key-descargas_movil { display: none; }
@media (max-width: 640px) {
  [class*="st-key-cab_"] > [data-testid="stLayoutWrapper"]:first-child > [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; gap: .35rem; }
  [class*="st-key-cab_"] > [data-testid="stLayoutWrapper"]:first-child > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { min-width: 0 !important; width: auto !important; }
  [class*="st-key-fila_"] > [data-testid="stLayoutWrapper"]:first-child > [data-testid="stHorizontalBlock"],
  [class*="st-key-enc_"] > [data-testid="stLayoutWrapper"]:first-child > [data-testid="stHorizontalBlock"] { gap: .35rem; }
  [class*="st-key-fila_"] > [data-testid="stLayoutWrapper"]:first-child > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(1),
  [class*="st-key-enc_"] > [data-testid="stLayoutWrapper"]:first-child > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(1) { flex: 0 0 66px !important; }
  [class*="st-key-fila_"] > [data-testid="stLayoutWrapper"]:first-child > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(3),
  [class*="st-key-enc_"] > [data-testid="stLayoutWrapper"]:first-child > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(3),
  [class*="st-key-fila_"] > [data-testid="stLayoutWrapper"]:first-child > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(5),
  [class*="st-key-enc_"] > [data-testid="stLayoutWrapper"]:first-child > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(5) { flex: 0 0 36px !important; }
  [class*="st-key-fila_"] > [data-testid="stLayoutWrapper"]:first-child > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(4),
  [class*="st-key-enc_"] > [data-testid="stLayoutWrapper"]:first-child > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(4) { flex: 0 0 44px !important; }
  [class*="st-key-cab_"] > [data-testid="stLayoutWrapper"]:first-child > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { flex: 1 1 0 !important; }
  .comida { font-size: .78rem; }
  [class*="st-key-dia_"], .st-key-compra { padding: 16px !important; }
  .st-key-generar_movil, .st-key-descargas_movil { display: block; }
}
</style>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Datos
# ---------------------------------------------------------------------------
@st.cache_data
def load_data():
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_dir, "Maestro_Ingredientes.json")
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("No se encontró el archivo Maestro_Ingredientes.json")
        return []


maestro = load_data()

NINGUNO = "-- Ninguno --"
opciones_comida = {t: [NINGUNO] for t in ["Desayuno", "Comida", "Merienda", "Cena", "Excursión"]}
for plato in maestro:
    tipo = plato.get("tipo_comida")
    if tipo in opciones_comida:
        opciones_comida[tipo].append(plato["plato"])

# El almuerzo usa las mismas opciones que la merienda
opciones_comida["Almuerzo"] = list(opciones_comida["Merienda"])
TIPOS_COMIDA = ["Desayuno", "Almuerzo", "Comida", "Merienda", "Cena", "Excursión"]
DIAS = ["Día 1", "Día 2", "Día 3", "Día 4"]


# ---------------------------------------------------------------------------
# Barra lateral (parte superior)
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        f"""{TIENDA}
<p class="lateral-titulo">Planificador de menús</p>
<p class="lateral-texto">Campamento de 4 días. Elige los platos y genera la compra y el manual del cocinero.</p>
<p class="lateral-texto">Con <b>−</b> y <b>+</b> (o escribiendo en la casilla <b>± pers.</b>) sumas o restas personas solo en esa comida.</p>""",
        unsafe_allow_html=True,
    )
    resumen_slot = st.empty()


# ---------------------------------------------------------------------------
# Días (dos por fila)
# ---------------------------------------------------------------------------
def sumar(clave: str, delta: int):
    """Botones − / + del ajuste de personas de una comida."""
    st.session_state[clave] = int(st.session_state.get(clave, 0)) + delta


def tarjeta_dia(i: int) -> dict:
    with st.container(key=f"dia_{i}"):
        cab = st.container(key=f"cab_{i}")
        h0, h1, h2, h3 = cab.columns([2.2, 1.1, 1, 1], vertical_alignment="bottom")
        with h0:
            st.markdown(f'<p class="titulo-dia">{DIAS[i]}</p>', unsafe_allow_html=True)
        with h1:
            personas = st.number_input("Personas", min_value=1, value=50, key=f"pax_{i}")
        with h2:
            celiacos = st.number_input("Celíacos", min_value=0, value=0, key=f"cel_{i}")
        with h3:
            lactosos = st.number_input("Sin lact.", min_value=0, value=0, key=f"lac_{i}")

        dia_plan = {
            "dia": DIAS[i],
            "personas": personas + 3,
            "celiacos": celiacos,
            "lactosos": lactosos,
            "comidas": {},
        }

        # Encabezado de las columnas de comidas
        with st.container(key=f"enc_{i}"):
            k0, k1, _, k2, _ = st.columns([1.15, 3.3, 0.5, 0.75, 0.5], gap="small", vertical_alignment="bottom")
            with k1:
                st.markdown('<span class="enc">Plato</span>', unsafe_allow_html=True)
            with k2:
                st.markdown(
                    '<span class="enc enc-ajuste" title="Suma (+) o resta (−) personas solo en esta comida. '
                    'Ej.: 5 si vienen 5 monitores más a cenar, −10 si 10 no comen en el campamento.">± pers.</span>',
                    unsafe_allow_html=True,
                )

        for tipo in TIPOS_COMIDA:
            with st.container(key=f"fila_{i}_{tipo}"):
                c0, c1, c_menos, c2, c_mas = st.columns([1.15, 3.3, 0.5, 0.75, 0.5], gap="small", vertical_alignment="center")
                with c0:
                    st.markdown(f'<span class="comida">{tipo}</span>', unsafe_allow_html=True)
                with c1:
                    seleccion = st.selectbox(
                        f"Plato de {tipo}", options=opciones_comida[tipo],
                        key=f"sel_{i}_{tipo}", label_visibility="collapsed",
                    )
                if tipo == "Excursión":
                    if seleccion != NINGUNO:
                        e1, e2, e3 = st.columns(3)
                        with e1:
                            exc_pax = st.number_input("Pers. excursión", min_value=0, value=0, key=f"exc_pax_{i}")
                        with e2:
                            exc_cel = st.number_input("Celíacos", min_value=0, value=0, key=f"exc_cel_{i}")
                        with e3:
                            exc_lac = st.number_input("Sin lactosa", min_value=0, value=0, key=f"exc_lac_{i}")
                        dia_plan["comidas"][tipo] = {
                            "plato": seleccion,
                            "personas": exc_pax,
                            "celiacos": exc_cel,
                            "lactosos": exc_lac,
                            "ajuste": 0,
                        }
                else:
                    clave = f"ajuste_{i}_{tipo}"
                    if clave not in st.session_state:
                        st.session_state[clave] = 0
                    with c_menos:
                        st.button("−", key=f"menos_{i}_{tipo}", on_click=sumar, args=(clave, -1),
                                  width="stretch", help=f"Una persona menos en {tipo.lower()}")
                    with c2:
                        ajuste = st.number_input(
                            f"± personas en {tipo}", key=clave, step=1,
                            label_visibility="collapsed",
                        )
                    with c_mas:
                        st.button("+", key=f"mas_{i}_{tipo}", on_click=sumar, args=(clave, 1),
                                  width="stretch", help=f"Una persona más en {tipo.lower()}")
                    if seleccion != NINGUNO:
                        dia_plan["comidas"][tipo] = {"plato": seleccion, "ajuste": ajuste}
    return dia_plan


plan = []
for fila in range(2):
    # Dos días por fila; si no caben (pantallas medianas) pasan a uno por fila
    cols = st.container(key=f"par_{fila}").columns(2, gap="medium")
    for j, col in enumerate(cols):
        with col:
            plan.append(tarjeta_dia(fila * 2 + j))


# En el móvil la barra lateral va plegada: botón de generar también aquí (solo visible en pantallas pequeñas)
if st.button("Generar lista de compra", type="primary", width="stretch", key="generar_movil"):
    st.session_state["generado"] = True

# ---------------------------------------------------------------------------
# Barra lateral: resumen, botón y descargas
# ---------------------------------------------------------------------------
def rango(valores):
    lo, hi = min(valores), max(valores)
    return f"{lo}" if lo == hi else f"{lo}–{hi}"


n_platos = sum(len(p["comidas"]) for p in plan)
resumen_slot.markdown(
    f"""<div class="resumen">
<div><span>Personas</span><strong>{rango([p['personas'] - 3 for p in plan])}</strong></div>
<div><span>Platos</span><strong>{n_platos}</strong></div>
<div><span>Celíacos</span><strong>{rango([p['celiacos'] for p in plan])}</strong></div>
<div><span>Sin lactosa</span><strong>{rango([p['lactosos'] for p in plan])}</strong></div>
</div>""",
    unsafe_allow_html=True,
)

with st.sidebar:
    if st.button("Generar lista de compra", type="primary", width="stretch", key="generar"):
        st.session_state["generado"] = True
    st.markdown('<p class="etiqueta-lateral">Descargas</p>', unsafe_allow_html=True)
    descargas = st.container()

# ---------------------------------------------------------------------------
# Resultado
# ---------------------------------------------------------------------------
if not st.session_state.get("generado"):
    descargas.caption("Genera la lista para descargar el manual, el Excel y el CSV.")
else:
    resultado = aggregate_ingredients(plan, maestro)
    if resultado["status"] != "success":
        st.error(f"Error en el cálculo: {resultado['message']}")
    elif not resultado["data"]:
        st.info("No se han seleccionado platos con ingredientes válidos.")
    else:
        desglose = resultado.get("desglose", {})
        df = pd.DataFrame(resultado["data"])
        df["Cantidad Total"] = df["Cantidad Total"].apply(lambda x: round(x, 2) if isinstance(x, float) else x)
        df_dietas = pd.DataFrame([{
            "Día": p["dia"],
            "Personas Base": p["personas"],
            "Celíacos": p["celiacos"],
            "Lactosos": p["lactosos"],
        } for p in plan])

        compra = st.container(key="compra")
        with compra:
            t0, t1 = st.columns([3, 1], vertical_alignment="bottom")
            with t0:
                st.markdown('<p class="titulo-seccion">Lista de compra</p>', unsafe_allow_html=True)
            with t1:
                st.caption(f"{len(df)} ingredientes")
            # La columna Notas solo se muestra si algún ingrediente tiene nota
            vista = df.drop(columns=["Notas"]) if (df["Notas"] == "").all() else df
            st.dataframe(vista, width="stretch", hide_index=True)

        # Ficheros a descargar (se generan una vez y se ofrecen en la barra lateral y, en el móvil, bajo la tabla)
        ficheros = []
        try:
            ficheros.append(("manual", "Manual del cocinero", ":material/description:", generar_manual(plan, desglose),
                             "Manual_del_cocinero.docx",
                             "application/vnd.openxmlformats-officedocument.wordprocessingml.document"))
        except Exception as e:
            st.warning(f"No se pudo generar el manual: {e}")
        try:
            salida = BytesIO()
            with pd.ExcelWriter(salida, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False, sheet_name="Compra")
                df_dietas.to_excel(writer, index=False, sheet_name="Dietas")
            ficheros.append(("excel", "Lista en Excel", ":material/table_chart:", salida.getvalue(),
                             "lista_compra_campamento.xlsx",
                             "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"))
        except Exception:
            st.warning("Exportación a Excel no disponible (falta xlsxwriter). Usa CSV.")
        ficheros.append(("csv", "Lista en CSV", ":material/download:", df.to_csv(index=False).encode("utf-8"),
                         "lista_compra_campamento.csv", "text/csv"))

        def botones_descarga(sufijo=""):
            for clave, texto, icono, datos, nombre, mime in ficheros:
                with st.container(key=f"dl_{clave}{sufijo}"):
                    st.download_button(texto, data=datos, file_name=nombre, mime=mime,
                                       icon=icono, width="stretch", key=f"btn_{clave}{sufijo}")

        with descargas:
            botones_descarga()
        with compra:
            with st.container(key="descargas_movil"):
                botones_descarga("_m")
