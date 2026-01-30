from __future__ import annotations

from pathlib import Path

import pandas as pd
import numpy as np
import streamlit as st

from src.config import PATHS

st.set_page_config(page_title="Immobilier IDF — Dashboard", layout="wide")

@st.cache_data(show_spinner=False)
def load_ready() -> pd.DataFrame:
    if not PATHS.READY_PARQUET.exists():
        st.error(f"Fichier manquant: {PATHS.READY_PARQUET}\n\n➡️ Lance d'abord le notebook pipeline (ou exécute le script clean/analyse).")
        st.stop()
    df = pd.read_parquet(PATHS.READY_PARQUET)
    # types
    for c in ["price_eur", "surface_m2", "rooms", "price_per_m2"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    for c in ["dept", "zipcode", "property_type"]:
        if c in df.columns:
            df[c] = df[c].astype("string")
    return df

def kpi_row(df: pd.DataFrame):
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Annonces (filtrées)", f"{len(df):,}".replace(",", " "))
    col2.metric("Médiane prix (€)", f"{int(np.nanmedian(df['price_eur'])):,}".replace(",", " ") if "price_eur" in df else "—")
    col3.metric("Médiane surface (m²)", f"{np.nanmedian(df['surface_m2']):.1f}" if "surface_m2" in df else "—")
    col4.metric("Médiane €/m²", f"{int(np.nanmedian(df['price_per_m2'])):,}".replace(",", " ") if "price_per_m2" in df else "—")

def dept_stats(df: pd.DataFrame) -> pd.DataFrame:
    if "dept" not in df.columns:
        return pd.DataFrame()
    out = (
        df.groupby("dept", dropna=False)
          .agg(
              n=("dept", "size"),
              median_price=("price_eur", "median"),
              median_surface=("surface_m2", "median"),
              median_ppm2=("price_per_m2", "median"),
          )
          .reset_index()
          .sort_values("dept")
    )
    return out

def main():
    st.title("Immobilier IDF — Dashboard")

    df_all = load_ready()

    # On garde ton workflow: analyses principales sur df_immo (hors POI)
    if "is_poi_location" in df_all.columns:
        df_immo = df_all[~df_all["is_poi_location"].fillna(False)].copy()
    else:
        df_immo = df_all.copy()

    with st.sidebar:
        st.header("Filtres")
        depts = sorted([d for d in df_immo["dept"].dropna().unique()]) if "dept" in df_immo.columns else []
        selected_depts = st.multiselect("Départements", depts, default=depts)

        paris_only = st.selectbox("Zone", ["Tout", "Paris (75)", "Hors Paris"], index=0)

        # numeric sliders (safe)
        def slider_for(col, label):
            if col not in df_immo.columns or df_immo[col].dropna().empty:
                return None
            vmin = float(df_immo[col].quantile(0.01))
            vmax = float(df_immo[col].quantile(0.99))
            if not np.isfinite(vmin) or not np.isfinite(vmax) or vmin >= vmax:
                return None
            return st.slider(label, min_value=float(vmin), max_value=float(vmax), value=(float(vmin), float(vmax)))

        price_range = slider_for("price_eur", "Prix (€) — 1% à 99%")
        surf_range = slider_for("surface_m2", "Surface (m²) — 1% à 99%")
        ppm2_range = slider_for("price_per_m2", "€/m² — 1% à 99%")

        types = sorted([t for t in df_immo.get("property_type", pd.Series(dtype="string")).dropna().unique()])
        selected_types = st.multiselect("Type de bien", types, default=types) if types else []

    df_f = df_immo.copy()

    if selected_depts and "dept" in df_f.columns:
        df_f = df_f[df_f["dept"].isin(selected_depts)]

    if paris_only != "Tout" and "is_paris" in df_f.columns:
        if paris_only == "Paris (75)":
            df_f = df_f[df_f["is_paris"].fillna(False)]
        else:
            df_f = df_f[~df_f["is_paris"].fillna(False)]

    if selected_types and "property_type" in df_f.columns:
        df_f = df_f[df_f["property_type"].isin(selected_types)]

    if price_range and "price_eur" in df_f.columns:
        df_f = df_f[df_f["price_eur"].between(price_range[0], price_range[1])]
    if surf_range and "surface_m2" in df_f.columns:
        df_f = df_f[df_f["surface_m2"].between(surf_range[0], surf_range[1])]
    if ppm2_range and "price_per_m2" in df_f.columns:
        df_f = df_f[df_f["price_per_m2"].between(ppm2_range[0], ppm2_range[1])]

    kpi_row(df_f)

    st.divider()

    c1, c2 = st.columns([1.1, 0.9])

    with c1:
        st.subheader("€/m² médian par département")
        ds = dept_stats(df_f)
        if ds.empty:
            st.info("Pas assez de données (ou colonne dept manquante).")
        else:
            chart_df = ds.set_index("dept")["median_ppm2"]
            st.bar_chart(chart_df)

        st.subheader("Table annonces (échantillon)")
        cols_show = [c for c in ["title", "property_type", "price_eur", "surface_m2", "rooms", "zipcode", "address", "url"] if c in df_f.columns]
        st.dataframe(df_f[cols_show].head(500))

    with c2:
        st.subheader("Carte (si disponible)")
        if PATHS.MAP_HTML.exists():
            html = PATHS.MAP_HTML.read_text(encoding="utf-8", errors="ignore")
            st.components.v1.html(html, height=520, scrolling=True)
            st.caption("Carte chargée depuis data/processed/carte_idf_dept.html")
        else:
            st.info("Pas de carte HTML trouvée. Place un fichier carte_idf_dept.html dans data/processed/")

        st.subheader("Distribution €/m²")
        if "price_per_m2" in df_f.columns and not df_f["price_per_m2"].dropna().empty:
            st.line_chart(df_f["price_per_m2"].dropna().sort_values().reset_index(drop=True))

    st.divider()
    st.caption("Note: le dashboard analyse df_immo = df[~is_poi_location] pour éviter le biais des POI/lieux.")

if __name__ == "__main__":
    main()
