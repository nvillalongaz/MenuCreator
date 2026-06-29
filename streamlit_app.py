import streamlit as st
import json
import pandas as pd
from tools.calculate_shopping import main as aggregate_ingredients
from io import BytesIO

st.set_page_config(page_title="Menú Campamento", page_icon="🏕️", layout="wide")

st.title("🏕️ Planificador de Menús de Campamento")

import os

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

opciones_comida = {"Desayuno": ["-- Ninguno --"], "Comida": ["-- Ninguno --"], "Merienda": ["-- Ninguno --"], "Cena": ["-- Ninguno --"], "Excursión": ["-- Ninguno --"]}
if maestro:
    for plato in maestro:
        tipo = plato.get("tipo_comida")
        if tipo in opciones_comida:
            opciones_comida[tipo].append(plato["plato"])

st.write("Configura los menús indicando el número de personas base, dietas especiales y los ajustes excepcionales por cada comida.")

plan = []

dias = ["Día 1", "Día 2", "Día 3", "Día 4"]
cols = st.columns(4)

for i, col in enumerate(cols):
    with col:
        with st.container(border=True):
            st.subheader(dias[i])
            c1, c2, c3 = st.columns(3)
            with c1:
                personas = st.number_input("Base", min_value=1, value=50, key=f"pax_{i}", help="Personas base del día")
            with c2:
                celiacos = st.number_input("Celí.", min_value=0, value=0, key=f"cel_{i}", help="Nº Celíacos")
            with c3:
                lactosos = st.number_input("Lact.", min_value=0, value=0, key=f"lac_{i}", help="Nº Lactosos")
            
            dia_plan = {
                "dia": dias[i], 
                "personas": personas+3, 
                "celiacos": celiacos,
                "lactosos": lactosos,
                "comidas": {}
            }
            
            st.markdown("<hr style='margin: 0.5rem 0'>", unsafe_allow_html=True)
            for tipo in ["Desayuno", "Comida", "Merienda", "Cena", "Excursión"]:
                with st.expander(f"🍽️ {tipo}", expanded=(tipo=="Comida")):
                    seleccion = st.selectbox("Plato", options=opciones_comida[tipo], key=f"sel_{i}_{tipo}", label_visibility="collapsed")
                    if tipo == "Excursión":
                        e1, e2, e3 = st.columns(3)
                        with e1:
                            exc_pax = st.number_input("Base Exc.", min_value=0, value=0, key=f"exc_pax_{i}")
                        with e2:
                            exc_cel = st.number_input("Celíacos", min_value=0, value=0, key=f"exc_cel_{i}")
                        with e3:
                            exc_lac = st.number_input("Lactosos", min_value=0, value=0, key=f"exc_lac_{i}")
                        ajuste = 0
                    else:
                        ajuste = st.number_input("Ajuste (extra/ausentes)", value=0, key=f"ajuste_{i}_{tipo}", help="Personas adicionales (+) o ausentes (-) para esta comida")
                    
                    if seleccion != "-- Ninguno --":
                        if tipo == "Excursión":
                            dia_plan["comidas"][tipo] = {
                                "plato": seleccion,
                                "personas": exc_pax,
                                "celiacos": exc_cel,
                                "lactosos": exc_lac,
                                "ajuste": 0
                            }
                        else:
                            dia_plan["comidas"][tipo] = {
                                "plato": seleccion,
                                "ajuste": ajuste
                            }
                    
            plan.append(dia_plan)

st.markdown("<br>", unsafe_allow_html=True)
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    generar = st.button("🛒 Generar Lista de Compra", use_container_width=True, type="primary")

if generar:
    st.divider()
    st.header("📊 Resultado del Campamento")
    
    # Mostrar resumen de dietas
    st.subheader("⚠️ Resumen de Dietas Especiales por Día")
    df_dietas = pd.DataFrame([{
        "Día": p["dia"], 
        "Personas Base": p["personas"],
        "Celíacos": p["celiacos"], 
        "Lactosos": p["lactosos"]
    } for p in plan])
    st.dataframe(df_dietas, hide_index=True)
    
    st.subheader("🛒 Lista de Compra Consolidada")
    resultado = aggregate_ingredients(plan, maestro)
    
    if resultado["status"] == "success":
        data = resultado["data"]
        desglose = resultado.get("desglose", {})
        
        if data:
            df = pd.DataFrame(data)
            df["Cantidad Total"] = df.apply(lambda row: round(row["Cantidad Total"], 2) if pd.notnull(row["Cantidad Total"]) and isinstance(row["Cantidad Total"], float) else row["Cantidad Total"], axis=1)
            
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            export_cols = st.columns([1, 1, 4])
            csv = df.to_csv(index=False).encode('utf-8')
            with export_cols[0]:
                st.download_button(label="📥 Exportar a CSV", data=csv, file_name='lista_compra_campamento.csv', mime='text/csv', use_container_width=True)
                
            try:
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='Compra')
                    df_dietas.to_excel(writer, index=False, sheet_name='Dietas')
                with export_cols[1]:
                    st.download_button(label="📥 Exportar a Excel", data=output.getvalue(), file_name="lista_compra_campamento.xlsx", mime="application/vnd.ms-excel", use_container_width=True)
            except Exception as e:
                st.warning("Exportación a Excel no disponible (falta xlsxwriter). Usa CSV.")

            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander("Ver desglose detallado por día e ingrediente"):
                for dia, detalles in desglose.items():
                    if detalles:
                        st.write(f"### {dia}")
                        df_desglose = pd.DataFrame(detalles)
                        st.dataframe(df_desglose, use_container_width=True, hide_index=True)
        else:
            st.info("No se han seleccionado platos con ingredientes válidos.")
    else:
        st.error(f"Error en el cálculo: {resultado['message']}")
