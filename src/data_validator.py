from config.config import ALIASES
from src.utils import find_column


def validate_frame(frame):
    problems = []
    date_col = find_column(frame.columns, ALIASES["date"])
    if not date_col:
        problems.append("Falta una columna de fecha de publicación.")
    if not find_column(frame.columns, ALIASES["reach"]):
        problems.append("No se encontró Alcance; se conservarán los registros con alcance no disponible.")
    if not any(find_column(frame.columns, ALIASES[key]) for key in ("post_id", "url", "copy")):
        problems.append("No se encontró ID, URL ni texto para identificar publicaciones.")
    return problems
