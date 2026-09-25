# Social Insights · ELEBAR y Punto Blu

Dashboard modular de Instagram y Facebook para archivos CSV exportados desde Meta. No contiene datos ficticios. Cada publicación se normaliza a un esquema común y se deduplica por marca e identificador de contenido.

## Ejecutar en Streamlit Cloud

1. Subí todo el contenido de esta carpeta a la raíz de un repositorio GitHub.
2. En Streamlit Community Cloud seleccioná el repositorio y `app.py`.
3. Streamlit instalará `requirements.txt` y ejecutará la aplicación.
4. Seleccioná la marca y cargá los CSV de Meta desde la barra lateral.

También se puede ejecutar localmente con `streamlit run app.py`. La aplicación no requiere rutas locales ni credenciales.

## Arquitectura

- `app.py`: interfaz, filtros, sesión y exportación.
- `src/data_loader.py`: lectura CSV y resumen de ingestión.
- `src/data_validator.py`: comprobaciones de estructura.
- `src/data_cleaner.py`: modelo normalizado, formatos y deduplicación.
- `src/metrics.py`: métricas derivadas y KPIs.
- `src/comparisons.py`: comparación con período anterior equivalente.
- `src/content_analysis.py`: rankings e insights descriptivos.
- `src/charts.py`: visualizaciones y tablas.
- `config/config.py`: marcas, colores y alias de columnas.

La lógica de negocio recibe y devuelve DataFrames, de modo que la capa de ingestión puede reemplazarse posteriormente por almacenamiento persistente sin rehacer los componentes de visualización.

## Datos y privacidad

Los CSV se cargan en memoria de la sesión de Streamlit. La aplicación no los escribe a disco ni a una base de datos. En Streamlit Cloud esto significa que los datos pasan por el servidor mientras la sesión está activa; al reiniciarse la app o terminar la sesión, hay que volver a cargarlos. No es almacenamiento periódico permanente. Para retener archivos entre sesiones se necesitaría almacenamiento persistente autorizado (por ejemplo, un bucket privado).

El usuario selecciona marca, elige los CSV y confirma con `Cargar archivos en [marca]`. Los archivos se agregan al dataset de la marca activa. La app avisa si el contenido parece corresponder a la otra marca. Métricas no incluidas permanecen vacías y se presentan como no disponibles. Se informan archivos rechazados y problemas de estructura. Para exportaciones de Meta donde `Fecha` dice `Total`, se usa primero `Hora de publicación`.

La barra lateral ofrece filtros de red, formato, año, trimestre y mes. Los KPIs incluyen comparación con el período anterior equivalente; al seleccionar un mes, trimestre o año completo se compara con el mes, trimestre o año calendario anterior. El dashboard presenta tendencias mensuales, rendimiento por formato, distribución por red, actividad semanal y publicaciones ordenadas por métrica.

## Columnas y limitaciones

Se reconocen alias en español e inglés para fechas, alcance, impresiones, interacciones, likes, comentarios, compartidos, guardados, reproducciones y seguidores atribuidos. Los CSV pueden variar; revisá los avisos de carga. El campo Meta `Seguidores` de exportaciones por publicación se interpreta como seguidores atribuidos, no como el total histórico de seguidores de la cuenta. No se calcula crecimiento inicial/final sin una serie explícita de seguidores de cuenta.

Los períodos comparan el rango seleccionado contra el rango inmediatamente anterior de igual duración. Al cargar nuevos períodos, volvé a cargarlos en la sesión para actualizar el dashboard. Los filtros y la deduplicación evitan duplicar publicaciones dentro de la sesión.

## Personalización

Editá `config/config.py` para cambiar colores o agregar alias y nombres de marca. Agregar una marca implica definir su clave, nombre, colores y alias; el selector y el mismo pipeline reutilizable la mostrarán automáticamente.

## Tests

Los tests unitarios están en `tests/`. Para ejecutarlos en un entorno Python: `pytest`.
