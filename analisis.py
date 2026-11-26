"""Resúmenes del catálogo extraído. No estima ventas ni convierte la moneda."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ARCHIVO_CSV = Path("data/libros_books_to_scrape.csv")
TRAMOS = [
    (0, 20, "Menos de £20"),
    (20, 30, "£20 a £30"),
    (30, 40, "£30 a £40"),
    (40, 50, "£40 a £50"),
    (50, 60, "£50 a £60"),
    (60, 10_000, "£60 o más"),
]


def cargar_catalogo(ruta: Path | str = ARCHIVO_CSV) -> pd.DataFrame:
    origen = Path(ruta)
    if not origen.exists():
        raise FileNotFoundError(
            f"No existe el catálogo {origen}. Ejecuta scraper.py antes de publicar."
        )
    datos = pd.read_csv(origen, encoding="utf-8-sig")
    esperadas = {
        "Producto",
        "Precio_Numerico",
        "Moneda",
        "Disponibilidad",
        "Calificacion",
        "Enlace",
    }
    faltantes = esperadas.difference(datos.columns)
    if faltantes:
        raise ValueError(f"El catálogo no tiene las columnas {sorted(faltantes)}.")
    if datos.empty:
        raise ValueError("El catálogo está vacío.")
    if datos["Precio_Numerico"].isna().any() or (datos["Precio_Numerico"] < 0).any():
        raise ValueError("Hay precios vacíos o negativos.")
    return datos


def resumir(datos: pd.DataFrame) -> dict:
    precios = datos["Precio_Numerico"]
    en_stock = int(
        datos["Disponibilidad"]
        .fillna("")
        .str.contains(r"\bin stock\b", case=False, regex=True)
        .sum()
    )
    correlacion = datos["Precio_Numerico"].corr(datos["Calificacion"])
    return {
        "libros": int(len(datos)),
        "precio_minimo": round(float(precios.min()), 2),
        "precio_maximo": round(float(precios.max()), 2),
        "precio_promedio": round(float(precios.mean()), 2),
        "precio_mediana": round(float(precios.median()), 2),
        "en_stock": en_stock,
        "correlacion_precio_calificacion": round(float(correlacion), 2),
        "moneda": "GBP",
    }


def por_calificacion(datos: pd.DataFrame) -> list[dict]:
    conteo = datos["Calificacion"].value_counts(dropna=False)
    filas = []
    for estrellas in range(1, 6):
        cantidad = int(conteo.get(estrellas, 0))
        filas.append(
            {
                "calificacion": estrellas,
                "cantidad": cantidad,
                "porcentaje": round(100 * cantidad / len(datos), 1),
            }
        )
    return filas


def por_precio(datos: pd.DataFrame) -> list[dict]:
    precios = datos["Precio_Numerico"]
    filas = []
    for minimo, maximo, etiqueta in TRAMOS:
        if maximo >= 10_000:
            cantidad = int((precios >= minimo).sum())
        else:
            cantidad = int(((precios >= minimo) & (precios < maximo)).sum())
        filas.append(
            {
                "etiqueta": etiqueta,
                "cantidad": cantidad,
                "porcentaje": round(100 * cantidad / len(datos), 1),
            }
        )
    return filas


def extremos(datos: pd.DataFrame, n: int = 5) -> dict[str, list[dict]]:
    columnas = [
        "indice",
        "Producto",
        "Precio_Numerico",
        "Calificacion",
        "Disponibilidad",
        "Enlace",
    ]
    preparado = datos.reset_index(names="indice")
    ordenado = preparado.sort_values("Precio_Numerico", kind="mergesort")
    return {
        "mas_economicos": ordenado.head(n)[columnas].to_dict(orient="records"),
        "mas_costosos": ordenado.tail(n).iloc[::-1][columnas].to_dict(orient="records"),
    }
