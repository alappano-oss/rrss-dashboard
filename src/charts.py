import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from src.content_analysis import insights, top_posts
from src.comparisons import variation


def fmt(value, percent=False):
    if pd.isna(value):
        return "N/D"
    return f"{value:,.2f}%" if percent else f"{value:,.0f}"


def render_dashboard(posts, previous, summary, brand):
    posts = posts.copy()
    posts["month"] = posts.date.dt.to_period("M").dt.to_timestamp()
    posts["month_label"] = posts.month.dt.strftime("%b %Y")
    st.caption(f"Período analizado: {posts.date.min():%d/%m/%Y} – {posts.date.max():%d/%m/%Y} · {len(posts):,} publicaciones")

    # Executive cards, with comparisons in each metric's delta.
    reach_mean = posts.reach.mean() if posts.reach.notna().any() else np.nan
    er_mean = posts.er_reach.mean() if posts.er_reach.notna().any() else np.nan
    views_total = posts.views.sum(min_count=1) if posts.views.notna().any() else np.nan
    shares_total = posts.shares.sum(min_count=1) if posts.shares.notna().any() else np.nan
    saves_total = posts.saves.sum(min_count=1) if posts.saves.notna().any() else np.nan
    comments_total = posts.comments.sum(min_count=1) if posts.comments.notna().any() else np.nan
    followers_total = posts.followers_gained.sum(min_count=1) if posts.followers_gained.notna().any() else np.nan
    best_day = posts.assign(weekday=posts.date.dt.day_name()).groupby("weekday").reach.mean().idxmax() if posts.reach.notna().any() else "N/D"
    weekday_names = {"Monday":"Lun", "Tuesday":"Mar", "Wednesday":"Mié", "Thursday":"Jue", "Friday":"Vie", "Saturday":"Sáb", "Sunday":"Dom"}
    cards = [
        ("Alcance total", summary["reach"], False, "reach"),
        ("Visualizaciones", views_total, False, "views"),
        ("Interacciones", summary["interactions"], False, "interactions"),
        ("Me gusta", posts.likes.sum(min_count=1) if posts.likes.notna().any() else np.nan, False, None),
        ("Compartidos", shares_total, False, None),
        ("Guardados", saves_total, False, None),
        ("Engagement rate", er_mean, True, "er_reach"),
        ("Alcance promedio", reach_mean, False, None),
        ("Mejor día", weekday_names.get(best_day, best_day), False, None),
        ("Comentarios", comments_total, False, None),
        ("Seguidores atribuidos", followers_total, False, "followers_gained"),
        ("Publicaciones", summary["posts"], False, "posts"),
    ]
    st.subheader("Resumen ejecutivo")
    for start in range(0, len(cards), 4):
        columns = st.columns(4)
        for column, (label, value, percent, key) in zip(columns, cards[start:start + 4]):
            delta = None
            if previous and key:
                prev_value = previous.get(key, np.nan)
                if isinstance(value, (int, float, np.number)) and not pd.isna(value):
                    result = variation(value, prev_value)
                    delta = f"{result[1]:+.1f}% vs. período anterior" if result else None
            column.metric(label, fmt(value, percent) if label != "Mejor día" else value, delta)

    st.markdown("---")
    st.subheader("Tendencia mes a mes")
    monthly = posts.groupby(["month", "month_label"], as_index=False).agg(
        Alcance=("reach", lambda series: series.sum(min_count=1)),
        Interacciones=("interactions", lambda series: series.sum(min_count=1)),
        Visualizaciones=("views", lambda series: series.sum(min_count=1)),
        Publicaciones=("date", "count"),
    )
    left, right = st.columns(2)
    with left:
        trend = monthly.melt(id_vars=["month", "month_label"], value_vars=["Alcance", "Interacciones"], var_name="Métrica", value_name="Total")
        fig = px.line(trend, x="month_label", y="Total", color="Métrica", markers=True,
                      title="Alcance e interacciones acumuladas", template="plotly_white",
                      color_discrete_map={"Alcance": brand["color"], "Interacciones": brand["accent"]})
        fig.update_layout(xaxis_title="", yaxis_title="", legend_title="")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        by_format = posts.groupby("format", as_index=False).agg(
            **{"Alcance promedio": ("reach", "mean"), "Interacciones promedio": ("interactions", "mean")}
        )
        fmt_long = by_format.melt(id_vars="format", var_name="Métrica", value_name="Promedio")
        fig = px.bar(fmt_long, x="format", y="Promedio", color="Métrica", barmode="group",
                     title="Rendimiento por formato · promedio por publicación", template="plotly_white",
                     color_discrete_sequence=[brand["color"], brand["accent"]])
        fig.update_layout(xaxis_title="", yaxis_title="", legend_title="")
        st.plotly_chart(fig, use_container_width=True)

    left, right = st.columns(2)
    with left:
        net = posts.groupby("platform", as_index=False).reach.sum(min_count=1).dropna()
        if not net.empty:
            fig = px.pie(net, names="platform", values="reach", hole=0.55,
                         title="Distribución del alcance por red", template="plotly_white",
                         color_discrete_sequence=[brand["color"], brand["accent"], "#8A8F9C"])
            st.plotly_chart(fig, use_container_width=True)
    with right:
        mix = posts.groupby("format", as_index=False).size().rename(columns={"size":"Publicaciones"})
        fig = px.pie(mix, names="format", values="Publicaciones", hole=0.55,
                     title="Mix de formatos · cantidad de publicaciones", template="plotly_white",
                     color_discrete_sequence=[brand["color"], brand["accent"], "#8A8F9C", "#B9C2D0"])
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Actividad por día")
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    day = posts.assign(weekday=posts.date.dt.day_name()).groupby("weekday", as_index=False).agg(
        **{"Alcance promedio": ("reach", "mean"), "Engagement promedio": ("er_reach", "mean"), "Publicaciones": ("date", "count")}
    )
    day["weekday"] = pd.Categorical(day.weekday, categories=day_order, ordered=True)
    day = day.sort_values("weekday")
    day["Día"] = day.weekday.map({k: weekday_names[k] for k in day_order})
    fig = px.bar(day, x="Día", y="Alcance promedio", title="Alcance promedio por día", template="plotly_white",
                 color_discrete_sequence=[brand["color"]])
    fig.update_layout(xaxis_title="", yaxis_title="")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Top publicaciones")
    metric_labels = {"reach": "Alcance", "interactions": "Interacciones", "views": "Visualizaciones", "er_reach": "ER%", "shares": "Compartidos", "saves": "Guardados"}
    metric = st.radio("Ordenar por", list(metric_labels), format_func=lambda key: metric_labels[key], horizontal=True)
    top = top_posts(posts, metric)
    columns = [c for c in ["date", "platform", "format", "copy", "reach", "interactions", "er_reach", "shares", "saves", "url"] if c in top]
    display = top[columns].rename(columns={"date":"Fecha", "platform":"Red", "format":"Formato", "copy":"Publicación", "reach":"Alcance", "interactions":"Interacciones", "er_reach":"ER %", "shares":"Compartidos", "saves":"Guardados", "url":"Enlace"})
    st.dataframe(display, use_container_width=True, hide_index=True)
    st.caption("ER% = interacciones / alcance × 100. Los KPIs solo se calculan cuando la exportación contiene la métrica.")

    st.subheader("Insights")
    for insight in insights(posts, previous):
        st.write(f"• {insight}")
