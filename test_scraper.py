"""Pruebas del scraper con HTML local. No consultan Books to Scrape."""

from unittest.mock import Mock, patch

import pandas as pd
import pytest
import requests

import scraper

HTML = """
<html><body>
<article class="product_pod">
  <p class="star-rating Three"></p>
  <h3><a href="catalogue/libro-de-prueba_1/index.html" title="Libro de prueba: edición completa">Libro...</a></h3>
  <p class="price_color">£19.99</p>
  <p class="availability">In stock</p>
</article>
</body></html>
"""
PAGINACION = '<li class="next"><a href="catalogue/page-2.html">next</a></li>'


def respuesta_html(html: str):
    respuesta = Mock()
    respuesta.content = html.encode("utf-8")
    respuesta.raise_for_status.return_value = None
    return respuesta


def test_extrae_titulo_completo_precio_moneda_y_enlace():
    with patch("scraper.requests.get", return_value=respuesta_html(HTML)) as get:
        datos = scraper.ejecutar_scraping(pausa=0)
    get.assert_called_once_with(
        scraper.URL_BASE,
        headers={"User-Agent": scraper.USER_AGENT},
        timeout=30,
    )
    assert list(datos.columns) == scraper.COLUMNAS
    assert datos.iloc[0].to_dict() == {
        "Producto": "Libro de prueba: edición completa",
        "Precio": "£19.99",
        "Precio_Numerico": 19.99,
        "Moneda": "GBP",
        "Disponibilidad": "In stock",
        "Calificacion": 3,
        "Enlace": "https://books.toscrape.com/catalogue/libro-de-prueba_1/index.html",
    }


def test_sigue_paginacion_y_se_detiene_al_final():
    primera = HTML.replace("</body>", PAGINACION + "</body>")
    segunda = HTML.replace("libro-de-prueba_1", "otro-libro_2")
    with patch(
        "scraper.requests.get",
        side_effect=[respuesta_html(primera), respuesta_html(segunda)],
    ) as get:
        datos = scraper.ejecutar_scraping(max_paginas=5, pausa=0)
    assert get.call_count == 2
    assert get.call_args_list[1].args[0] == "https://books.toscrape.com/catalogue/page-2.html"
    assert len(datos) == 2


def test_respeta_el_limite_de_paginas():
    html = HTML.replace("</body>", PAGINACION + "</body>")
    with patch("scraper.requests.get", return_value=respuesta_html(html)) as get:
        scraper.ejecutar_scraping(max_paginas=1, pausa=0)
    assert get.call_count == 1


def test_no_oculta_errores_http():
    respuesta = respuesta_html(HTML)
    respuesta.raise_for_status.side_effect = requests.HTTPError("403 Forbidden")
    with patch("scraper.requests.get", return_value=respuesta):
        with pytest.raises(requests.HTTPError, match="403"):
            scraper.ejecutar_scraping(pausa=0)


def test_pagina_sin_libros_falla():
    with patch("scraper.requests.get", return_value=respuesta_html("<html>Acceso restringido</html>")):
        with pytest.raises(RuntimeError, match="No se encontraron libros"):
            scraper.ejecutar_scraping(pausa=0)


@pytest.mark.parametrize("precio", ["USD 19.99", "£sin precio", "£-1.00", "£NaN"])
def test_rechaza_precios_invalidos(precio):
    html = HTML.replace("£19.99", precio)
    with patch("scraper.requests.get", return_value=respuesta_html(html)):
        with pytest.raises(ValueError):
            scraper.ejecutar_scraping(pausa=0)


def test_rechaza_limite_invalido_sin_consultar_la_red():
    with patch("scraper.requests.get") as get:
        with pytest.raises(ValueError):
            scraper.ejecutar_scraping(max_paginas=0)
    get.assert_not_called()


def test_elimina_duplicados_por_enlace():
    repetido = HTML.replace("</body>", HTML + "</body>")
    with patch("scraper.requests.get", return_value=respuesta_html(repetido)):
        datos = scraper.ejecutar_scraping(pausa=0)
    assert len(datos) == 1


def test_cli_exporta_csv(tmp_path):
    salida = tmp_path / "data" / "libros.csv"
    with patch("scraper.requests.get", return_value=respuesta_html(HTML)):
        scraper.main(["--salida", str(salida), "--pausa", "0"])
    datos = pd.read_csv(salida, encoding="utf-8-sig")
    assert datos.iloc[0]["Producto"] == "Libro de prueba: edición completa"
    assert datos.iloc[0]["Precio_Numerico"] == 19.99
