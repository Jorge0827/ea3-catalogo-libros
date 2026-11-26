"""Extrae el catálogo de demostración de Books to Scrape.

Continuación de la Evidencia 2: requests y BeautifulSoup, sin navegador.
El sitio publica precios y calificaciones ficticios para practicar scraping.
"""

from __future__ import annotations

import argparse
import time
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

URL_BASE = "https://books.toscrape.com/"
ARCHIVO_CSV = Path("data/libros_books_to_scrape.csv")
USER_AGENT = (
    "EA3-CatalogoLibros/1.0 "
    "(ejercicio academico IU Digital; una peticion por pagina)"
)
COLUMNAS = [
    "Producto",
    "Precio",
    "Precio_Numerico",
    "Moneda",
    "Disponibilidad",
    "Calificacion",
    "Enlace",
]
CALIFICACIONES = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


def _encabezados() -> dict[str, str]:
    return {"User-Agent": USER_AGENT}


def _extraer_producto(tarjeta, url_pagina: str) -> dict:
    titulo = tarjeta.select_one("h3 a")
    precio = tarjeta.select_one(".price_color")
    disponibilidad = tarjeta.select_one(".availability")
    calificacion = tarjeta.select_one(".star-rating")
    if titulo is None or precio is None or not titulo.get("href"):
        raise ValueError("Tarjeta de libro sin título, precio o enlace.")

    precio_texto = precio.get_text(strip=True)
    if not precio_texto.startswith("£"):
        raise ValueError(f"Moneda inesperada: {precio_texto!r}")
    try:
        precio_numero = Decimal(precio_texto[1:])
    except InvalidOperation as error:
        raise ValueError(f"Precio inválido: {precio_texto!r}") from error
    if not precio_numero.is_finite() or precio_numero < 0:
        raise ValueError(f"Precio inválido: {precio_texto!r}")

    estrellas = None
    if calificacion is not None:
        estrellas = next(
            (
                CALIFICACIONES[clase]
                for clase in calificacion.get("class", [])
                if clase in CALIFICACIONES
            ),
            None,
        )

    return {
        "Producto": titulo.get("title") or titulo.get_text(strip=True),
        "Precio": precio_texto,
        "Precio_Numerico": float(precio_numero),
        "Moneda": "GBP",
        "Disponibilidad": (
            disponibilidad.get_text(" ", strip=True)
            if disponibilidad is not None
            else "No disponible"
        ),
        "Calificacion": estrellas,
        "Enlace": urljoin(url_pagina, titulo["href"]),
    }


def ejecutar_scraping(max_paginas: int = 1, pausa: float = 1.0) -> pd.DataFrame:
    """Descarga hasta max_paginas y falla si la fuente no devuelve libros."""
    if max_paginas < 1:
        raise ValueError("max_paginas debe ser mayor que cero.")
    if pausa < 0:
        raise ValueError("pausa no puede ser negativa.")

    datos = []
    url = URL_BASE
    for pagina in range(max_paginas):
        respuesta = requests.get(url, headers=_encabezados(), timeout=30)
        respuesta.raise_for_status()
        soup = BeautifulSoup(respuesta.content, "html.parser")
        tarjetas = soup.select("article.product_pod")
        if not tarjetas:
            raise RuntimeError(f"No se encontraron libros en {url}.")
        datos.extend(_extraer_producto(tarjeta, url) for tarjeta in tarjetas)
        print(f"Página {pagina + 1}: {len(tarjetas)} libros en {url}", flush=True)

        siguiente = soup.select_one("li.next a")
        if siguiente is None or not siguiente.get("href") or pagina + 1 >= max_paginas:
            break
        url = urljoin(url, siguiente["href"])
        if pausa:
            time.sleep(pausa)

    return pd.DataFrame(datos, columns=COLUMNAS).drop_duplicates(
        subset="Enlace", ignore_index=True
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paginas", type=int, default=1)
    parser.add_argument("--pausa", type=float, default=1.0)
    parser.add_argument("--salida", type=Path, default=ARCHIVO_CSV)
    argumentos = parser.parse_args(argv)
    if argumentos.paginas < 1:
        parser.error("--paginas debe ser mayor que cero")
    resultados = ejecutar_scraping(
        max_paginas=argumentos.paginas, pausa=argumentos.pausa
    )
    argumentos.salida.parent.mkdir(parents=True, exist_ok=True)
    resultados.to_csv(argumentos.salida, index=False, encoding="utf-8-sig")
    print(f"Se extrajeron {len(resultados)} libros de {URL_BASE}")
    print(f"CSV guardado en: {argumentos.salida.resolve()}")
    print("Catálogo de demostración: los precios son ficticios.")


if __name__ == "__main__":
    main()
