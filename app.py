from __future__ import annotations

import hashlib

import streamlit as st
import pandas as pd

from config.config import BRANDS
from src.data_loader import read_uploads
from src.data_cleaner import normalize_posts, merge_deduplicate
from src.data_validator import validate_frame
from src.metrics import add_derived_metrics, summarize
from src.comparisons import compare_periods
from src.charts import render_dashboard

st.set_page_config(page_title="Social Insights", page_icon="📊", layout="wide")

if "posts" not in st.session_state:
    st.session_state.posts = pd.DataFrame()
if "load_report" not in st.session_state:
    st.session_state.load_report = None
if "loaded_signatures" not in st.session_state:
    st.session_state.loaded_signatures = set()

def clear_filter_state():
    for key in list(st.session_state.keys()):
        if any(key.startswith(prefix) for prefix in ("platform_filter_", "format_filter_", "type_filter_", "date_filter_", "period_filter_", "year_filter_", "quarter_filter_", "month_filter_")):
            st.session_state.pop(key, None)

st.sidebar.markdown("## Elegí el dashboard")
brand_key = st.sidebar.radio(
    "Marca activa",
    list(BRANDS),
    format_func=lambda k: BRANDS[k]["name"],
    horizontal=True,
)
brand = BRANDS[brand_key]
st.markdown(
    f"""<style>
    .stApp {{background:#f7f8fb}}
    [data-testid="stMetric"] {{background:#fff;border:1px solid #e6e9ef;padding:16px;border-radius:12px}}
    h1,h2,h3,p,label {{color:#20283a}}
    </style>""",
    unsafe_allow_html=True,
)
st.title(f"Dashboard · {brand['name']}")
st.caption(f"Estás viendo únicamente el dataset de {brand['name']}. ELEBAR y Punto Blu se cargan y analizan por separado.")
st.sidebar.markdown(f"### Cargar datos de {brand['name']}")
uploads = st.sidebar.file_uploader(
    f"CSV para {brand['name']}", type=["csv"], accept_multiple_files=True,
    key=f"uploader_{brand_key}",
    help="Al confirmar, los archivos se agregan al dataset de la marca activa.",
)
process_uploads = st.sidebar.button(
    f"Cargar archivos en {brand['name']}",
    type="primary",
    disabled=not uploads,
    help="Confirma y procesa los archivos seleccionados para el dashboard activo.",
)
if uploads and not process_uploads:
    st.sidebar.info(f"{len(uploads)} archivo(s) seleccionado(s). Presioná el botón para cargarlos en {brand['name']}.")

if uploads and process_uploads:
    fresh_uploads = []
    for upload in uploads:
        signature = hashlib.sha256(brand_key.encode("utf-8") + upload.name.encode("utf-8") + upload.getvalue()).hexdigest()
        if signature not in st.session_state.loaded_signatures:
            fresh_uploads.append(upload)
            st.session_state.loaded_signatures.add(signature)
    if fresh_uploads:
        report = read_uploads(fresh_uploads, brand_key)
        incoming, errors = report["data"], report["errors"]
        new_count = duplicate_count = 0
        if not incoming.empty:
            st.session_state.posts, new_count, duplicate_count = merge_deduplicate(
                st.session_state.posts, incoming
            )
        st.session_state.load_report = {
            "files": report["files"], "new": new_count, "duplicates": duplicate_count,
            "rejected": report["rejected"], "errors": errors,
        }
    else:
        st.session_state.load_report = {
            "files": len(uploads), "new": 0, "duplicates": len(uploads),
            "rejected": 0, "errors": ["Estos archivos ya se habían procesado en esta sesión."],
        }

counts = st.session_state.posts.groupby("brand").size().to_dict() if not st.session_state.posts.empty else {}
st.sidebar.markdown("**Datos cargados en esta sesión**")
st.sidebar.caption(f"ELEBAR: {counts.get('elebar', 0)} publicaciones")
st.sidebar.caption(f"Punto Blu: {counts.get('blu', 0)} publicaciones")
if not st.session_state.posts.empty:
    with st.sidebar.expander("Archivos procesados"):
        for filename in sorted(st.session_state.posts.source_file.dropna().unique()):
            st.caption(filename)

if st.session_state.load_report:
    r = st.session_state.load_report
    st.sidebar.success(
        f"Archivos: {r['files']} · Nuevos: {r['new']} · Duplicados: {r['duplicates']} · Rechazados: {r['rejected']}"
    )
    for error in r["errors"]:
        st.sidebar.warning(error)

if st.session_state.posts.empty:
    st.info(f"Todavía no hay datos cargados. Usá el panel lateral para subir los CSV de {brand['name']}.")
    st.caption("Elegí ELEBAR o Punto Blu en ‘Elegí el dashboard’. La carga y los resultados quedan separados por marca.")
    st.stop()

# La marca seleccionada controla qué dataset se analiza; la carga la conserva en su propio grupo.
all_posts = st.session_state.posts
brand_posts = all_posts[all_posts["brand"] == brand_key].copy()
if brand_posts.empty:
    st.info(f"No hay publicaciones de {brand['name']} cargadas todavía. Subí sus CSV desde ‘Cargar datos de {brand['name']}’ en el panel lateral.")
    st.stop()

brand_posts = add_derived_metrics(brand_posts)
with st.sidebar:
    st.markdown("### Filtros")
    platforms = sorted(brand_posts.platform.dropna().unique())
    selected_platforms = st.multiselect("Plataforma", platforms, default=platforms, key=f"platform_filter_{brand_key}")
    formats = sorted(brand_posts.format.dropna().unique())
    selected_formats = st.multiselect("Formato", formats, default=formats, key=f"format_filter_{brand_key}")
    years = sorted(brand_posts.date.dt.year.dropna().unique().tolist())
    year_options = ["Todos los años", *[str(year) for year in years]]
    selected_year = st.selectbox("Año", year_options, key=f"year_filter_{brand_key}")
    quarter_options = ["Todos los trimestres", "Q1", "Q2", "Q3", "Q4"]
    selected_quarter = st.selectbox("Trimestre", quarter_options, key=f"quarter_filter_{brand_key}")
    month_names = {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"}
    month_source = brand_posts
    if selected_year != "Todos los años":
        month_source = month_source[month_source.date.dt.year == int(selected_year)]
    available_month_numbers = sorted(month_source.date.dt.month.dropna().unique().tolist())
    month_options = ["Todos los meses", *[month_names[m] for m in available_month_numbers]]
    selected_month = st.selectbox("Mes", month_options, key=f"month_filter_{brand_key}")
    st.button("Limpiar filtros", on_click=clear_filter_state)

period_mask = pd.Series(True, index=brand_posts.index)
if selected_year != "Todos los años":
    period_mask &= brand_posts.date.dt.year == int(selected_year)
if selected_quarter != "Todos los trimestres":
    period_mask &= brand_posts.date.dt.quarter == int(selected_quarter[-1])
if selected_month != "Todos los meses":
    month_number = next(number for number, name in month_names.items() if name == selected_month)
    period_mask &= brand_posts.date.dt.month == month_number

filtered = brand_posts[
    period_mask
    & brand_posts.platform.isin(selected_platforms)
    & brand_posts.format.isin(selected_formats)
].copy()

if filtered.empty:
    st.warning("No hay publicaciones con los filtros seleccionados.")
    st.stop()

comparison_base = brand_posts[
    brand_posts.platform.isin(selected_platforms)
    & brand_posts.format.isin(selected_formats)
]
comparison_start = comparison_end = None
if selected_year != "Todos los años" and selected_month != "Todos los meses":
    month_number = next(number for number, name in month_names.items() if name == selected_month)
    comparison_start = pd.Timestamp(int(selected_year), month_number, 1)
    comparison_end = comparison_start + pd.offsets.MonthEnd(0)
elif selected_year != "Todos los años" and selected_quarter != "Todos los trimestres":
    first_month = (int(selected_quarter[-1]) - 1) * 3 + 1
    comparison_start = pd.Timestamp(int(selected_year), first_month, 1)
    comparison_end = comparison_start + pd.offsets.MonthEnd(2)
elif selected_year != "Todos los años":
    comparison_start = pd.Timestamp(int(selected_year), 1, 1)
    comparison_end = pd.Timestamp(int(selected_year), 12, 31)
previous = compare_periods(comparison_base, filtered, comparison_start, comparison_end)
summary = summarize(filtered)
render_dashboard(filtered, previous, summary, brand)

with st.sidebar:
    st.markdown("### Exportar")
    st.download_button("Descargar publicaciones CSV", filtered.to_csv(index=False).encode("utf-8-sig"), "publicaciones.csv", "text/csv")
    st.download_button("Descargar KPIs CSV", pd.DataFrame([summary]).to_csv(index=False).encode("utf-8-sig"), "kpis.csv", "text/csv")
    if st.button("Vaciar datos de esta sesión"):
        st.session_state.posts = pd.DataFrame()
        st.session_state.load_report = None
        st.session_state.loaded_signatures = set()
        st.rerun()

st.caption("Los datos cargados viven en la sesión activa de Streamlit. No se guardan de forma permanente.")
