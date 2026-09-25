import re
import unicodedata

import pandas as pd


def norm(value):
    value = unicodedata.normalize("NFKD", str(value).lower().strip())
    value = "".join(c for c in value if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "_", value).strip("_")


def numeric(series):
    if series is None:
        return pd.Series(dtype="float64")
    text = series.astype("string").str.strip().str.replace(r"[^\d,.\-]", "", regex=True)
    comma_decimal = text.str.contains(",", na=False) & ~text.str.contains(".", regex=False)
    text.loc[comma_decimal] = text.loc[comma_decimal].str.replace(",", ".", regex=False)
    text.loc[~comma_decimal] = text.loc[~comma_decimal].str.replace(",", "", regex=False)
    return pd.to_numeric(text, errors="coerce")


def find_column(columns, aliases):
    lookup = {norm(c): c for c in columns}
    return next((lookup[norm(a)] for a in aliases if norm(a) in lookup), None)
