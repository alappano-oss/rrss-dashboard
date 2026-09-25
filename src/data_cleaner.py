import hashlib

import pandas as pd

from config.config import ALIASES
from src.utils import find_column, norm, numeric

OPTIONAL = ("post_id", "account", "copy", "url", "format", "reach", "impressions", "likes", "comments", "shares", "saves", "interactions", "views", "followers_gained", "duration")


def normalize_format(value):
    value = norm(value)
    if "reel" in value:
        return "Reel"
    if "carrusel" in value or "carousel" in value or "secuencia" in value:
        return "Carrusel"
    if "video" in value:
        return "Video"
    if "foto" in value or "imagen" in value or "image" in value:
        return "Imagen"
    return "Post" if value else "No disponible"


def normalize_posts(frame, brand, filename):
    columns = {key: find_column(frame.columns, ALIASES[key]) for key in OPTIONAL}
    date_col = find_column(frame.columns, ALIASES["date"])
    date = pd.to_datetime(frame[date_col], errors="coerce", dayfirst=False)
    platform_text = f"{filename} {' '.join(map(str, frame.columns))}".lower()
    headers = " ".join(norm(c) for c in frame.columns)
    platform = "Instagram" if "instagram" in platform_text or "ig-" in filename.lower() or "nombre_de_usuario_de_la_cuenta" in headers else "Facebook" if "facebook" in platform_text or "fb-" in filename.lower() or "nombre_de_la_pagina" in headers else "Sin identificar"

    out = pd.DataFrame(index=frame.index)
    out["date"] = date
    out["brand"] = brand
    out["platform"] = platform
    for key in OPTIONAL:
        col = columns[key]
        target = {"post_id": "post_id", "account": "account", "copy": "copy", "url": "url", "format": "format_raw", "reach": "reach", "impressions": "impressions", "likes": "likes", "comments": "comments", "shares": "shares", "saves": "saves", "interactions": "interactions_source", "views": "views", "followers_gained": "followers_gained", "duration": "video_seconds"}[key]
        out[target] = frame[col] if col else pd.NA

    for key in ("reach", "impressions", "likes", "comments", "shares", "saves", "interactions_source", "views", "followers_gained", "video_seconds"):
        out[key] = numeric(out[key])
    out["format"] = out["format_raw"].map(normalize_format)
    out["content_type"] = out["format"]
    out["source_file"] = filename
    identity = out["post_id"].fillna("").astype(str)
    fallback = out["url"].fillna("").astype(str) + out["date"].astype(str) + out["copy"].fillna("").astype(str)
    out["dedupe_key"] = [hashlib.sha256((a if a else b).encode("utf-8")).hexdigest() for a, b in zip(identity, fallback)]
    return out


def merge_deduplicate(existing, incoming):
    existing_keys = set(existing.get("brand", pd.Series(dtype=str)).astype(str) + ":" + existing.get("dedupe_key", pd.Series(dtype=str)).astype(str))
    incoming_keys = incoming["brand"].astype(str) + ":" + incoming["dedupe_key"].astype(str)
    unique_incoming = ~incoming_keys.duplicated(keep="first")
    new_count = int((unique_incoming & ~incoming_keys.isin(existing_keys)).sum())
    duplicate_count = int(len(incoming) - new_count)
    combined = pd.concat([existing, incoming], ignore_index=True) if not existing.empty else incoming.copy()
    combined = combined.drop_duplicates(subset=["brand", "dedupe_key"], keep="last").reset_index(drop=True)
    return combined, new_count, duplicate_count
