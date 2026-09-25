import io

import pandas as pd

from src.data_cleaner import normalize_posts
from src.data_validator import validate_frame
from src.utils import find_column
from config.config import ALIASES, BRANDS


def read_csv_bytes(data):
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin1"):
        for separator in (None, ";", ",", "\t"):
            try:
                return pd.read_csv(io.BytesIO(data), encoding=encoding, sep=separator, engine="python")
            except Exception:
                pass
    raise ValueError("No se pudo leer el CSV. Revisá codificación y separador.")


def read_uploads(uploads, brand):
    frames, errors, rejected = [], [], 0
    for upload in uploads:
        try:
            frame = read_csv_bytes(upload.getvalue())
            problems = validate_frame(frame)
            date_col = find_column(frame.columns, ALIASES["date"])
            if not date_col:
                rejected += len(frame)
                errors.append(f"{upload.name}: {problems[0]}")
                continue
            for problem in problems:
                errors.append(f"{upload.name}: {problem}")
            account_col = find_column(frame.columns, ALIASES["account"])
            fingerprint = (upload.name + " " + " ".join(frame[account_col].dropna().astype(str).head(20))).lower() if account_col else upload.name.lower()
            detected_brand = next(
                (key for key, config in BRANDS.items() if any(alias in fingerprint for alias in config["aliases"])),
                None,
            )
            if detected_brand and detected_brand != brand:
                errors.append(
                    f"{upload.name}: el contenido parece ser de {BRANDS[detected_brand]['name']}, "
                    f"pero se seleccionó {BRANDS[brand]['name']}; se cargó en la marca seleccionada."
                )
            # The chosen dashboard is the destination. Detection is used to flag
            # likely mismatches, never to silently send a file to another brand.
            normalized = normalize_posts(frame, brand, upload.name)
            invalid = normalized.date.isna()
            rejected += int(invalid.sum())
            normalized = normalized.loc[~invalid]
            if not normalized.empty:
                frames.append(normalized)
        except Exception as exc:
            errors.append(f"{upload.name}: {exc}")
    return {"data": pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(), "errors": errors, "rejected": rejected, "files": len(uploads)}
