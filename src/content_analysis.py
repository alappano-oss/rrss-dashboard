import pandas as pd


def top_posts(posts, metric, n=10, ascending=False):
    if metric not in posts or posts[metric].notna().sum() == 0:
        return posts.iloc[0:0]
    return posts.sort_values(metric, ascending=ascending, na_position="last").head(n)


def insights(posts, previous=None):
    notes = []
    by_format = posts.groupby("format").agg(reach=("reach", "mean"), er=("er_reach", "mean"), count=("date", "count"))
    by_format = by_format[by_format["count"] > 0]
    if len(by_format) >= 2 and by_format.reach.notna().sum() >= 2:
        best = by_format.reach.idxmax()
        notes.append(f"{best} registró el mayor alcance promedio entre los formatos disponibles.")
    if previous and pd.notna(previous.get("er_reach")) and posts.er_reach.notna().any():
        old = previous["er_reach"]
        now = posts.er_reach.mean()
        if old:
            change = (now - old) / abs(old) * 100
            notes.append(f"El engagement promedio varió {change:+.1f}% frente al período anterior equivalente.")
    if not notes:
        notes.append("Se necesitan más períodos o métricas disponibles para generar comparaciones adicionales.")
    return notes
