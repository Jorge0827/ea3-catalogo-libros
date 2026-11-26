"""Pruebas de las rutas con un catálogo en memoria."""

import pandas as pd

from app import crear_aplicacion

CATALOGO = pd.DataFrame(
    [
        {
            "Producto": "A Light in the Attic",
            "Precio": "£51.77",
            "Precio_Numerico": 51.77,
            "Moneda": "GBP",
            "Disponibilidad": "In stock",
            "Calificacion": 3,
            "Enlace": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
        },
        {
            "Producto": "The Black Maria",
            "Precio": "£52.15",
            "Precio_Numerico": 52.15,
            "Moneda": "GBP",
            "Disponibilidad": "In stock",
            "Calificacion": 1,
            "Enlace": "https://books.toscrape.com/catalogue/the-black-maria_991/index.html",
        },
    ]
)


def cliente():
    aplicacion = crear_aplicacion(CATALOGO.copy())
    aplicacion.config["TESTING"] = True
    return aplicacion.test_client()


def test_salud_reporta_la_cantidad_de_libros():
    respuesta = cliente().get("/salud")
    assert respuesta.status_code == 200
    assert respuesta.get_json() == {"estado": "ok", "libros": 2}


def test_inicio_muestra_el_promedio_y_un_titulo():
    respuesta = cliente().get("/")
    assert respuesta.status_code == 200
    texto = respuesta.get_data(as_text=True)
    assert "£51.96" in texto
    assert "A Light in the Attic" in texto
    assert "ficticios" in texto


def test_busqueda_filtra_por_titulo():
    respuesta = cliente().get("/catalogo?q=black")
    texto = respuesta.get_data(as_text=True)
    assert respuesta.status_code == 200
    assert "The Black Maria" in texto
    assert "A Light in the Attic" not in texto


def test_busqueda_sin_resultados():
    respuesta = cliente().get("/catalogo?q=no-existe")
    assert "No hay títulos con ese texto." in respuesta.get_data(as_text=True)


def test_ficha_y_ruta_inexistente():
    navegador = cliente()
    ficha = navegador.get("/libro/0")
    assert ficha.status_code == 200
    assert "£51.77" in ficha.get_data(as_text=True)
    assert navegador.get("/libro/9").status_code == 404


def test_el_pie_nombra_al_equipo():
    texto = cliente().get("/").get_data(as_text=True)
    for nombre in (
        "Juan Carlos Ardila Gómez",
        "Edwin Alberto Ruiz Guzmán",
        "Jorge Andrés Echavarría Pardo",
        "Yeison Padrón Higuita",
    ):
        assert nombre in texto


def test_flujo_describe_el_pipeline():
    texto = cliente().get("/flujo").get_data(as_text=True)
    assert "GitHub Actions" in texto
    assert "Render" in texto
