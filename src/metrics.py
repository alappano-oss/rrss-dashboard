import numpy as np
import pandas as pd


def add_derived_metrics(posts):
    df = posts.copy()
    parts = [df[c] for c in ("likes", "comments", "shares", "saves")]
    calculated = sum(parts).where(pd.concat(parts, axis=1).notna().any(axis=1))
    df["interactions"] = df["interactions_source"].where(df["interactions_source"].notna(), calculated)
    df["er_reach"] = (df["interactions"] / df["reach"] * 100).where(df["reach"] > 0)
    df["er_impressions"] = (df["interactions"] / df["impressions"] * 100).where(df["impressions"] > 0)
    df["frequency"] = (df["impressions"] / df["reach"]).where(df["reach"] > 0)
    df["performance_relative"] = (df["reach"] / df["reach"].mean()).where(df["reach"].mean() > 0)
    return df


def summarize(posts):
    def total(col):
        return float(posts[col].sum(min_count=1)) if posts[col].notna().any() else np.nan
    return {
        "posts": int(len(posts)), "reach": total("reach"), "impressions": total("impressions"),
        "interactions": total("interactions"), "er_reach": float(posts.er_reach.mean()) if posts.er_reach.notna().any() else np.nan,
        "followers_gained": total("followers_gained"), "views": total("views"),
    }
