"""Pruebas del resumen. Usan un catálogo pequeño en memoria."""

import pandas as pd
import pytest

import analisis

CATALOGO = pd.DataFrame(
    [
        ["Libro A", "£10.00", 10.0, "GBP", "In stock", 5, "https://ejemplo/a"],
        ["Libro B", "£30.00", 30.0, "GBP", "In stock", 5, "https://ejemplo/b"],
        ["Libro C", "£20.00", 20.0, "GBP", "In stock", 1, "https://ejemplo/c"],
        ["Libro D", "£40.00", 40.0, "GBP", "Out of stock", 3, "https://ejemplo/d"],
    ],
    columns=[
        "Producto",
        "Precio",
        "Precio_Numerico",
        "Moneda",
        "Disponibilidad",
        "Calificacion",
        "Enlace",
    ],
)


def test_resumen_calcula_promedio_mediana_y_existencia():
    resumen = analisis.resumir(CATALOGO)
    assert resumen["libros"] == 4
    assert resumen["precio_minimo"] == 10.0
    assert resumen["precio_maximo"] == 40.0
    assert resumen["precio_promedio"] == 25.0
    assert resumen["precio_mediana"] == 25.0
    assert resumen["en_stock"] == 3
    assert resumen["moneda"] == "GBP"
    assert -1 <= resumen["correlacion_precio_calificacion"] <= 1


def test_calificaciones_incluyen_las_cinco_categorias():
    filas = analisis.por_calificacion(CATALOGO)
    assert [fila["calificacion"] for fila in filas] == [1, 2, 3, 4, 5]
    cantidades = {fila["calificacion"]: fila["cantidad"] for fila in filas}
    assert cantidades[5] == 2
    assert cantidades[2] == 0
    assert cantidades[1] == 1


def test_tramos_de_precio_cubren_todo_el_catalogo():
    filas = analisis.por_precio(CATALOGO)
    assert sum(fila["cantidad"] for fila in filas) == 4
    etiquetas = {fila["etiqueta"]: fila["cantidad"] for fila in filas}
    assert etiquetas["Menos de £20"] == 1
    assert etiquetas["£20 a £30"] == 1
    assert etiquetas["£30 a £40"] == 1
    assert etiquetas["£40 a £50"] == 1


def test_extremos_ordenan_por_precio():
    extremos = analisis.extremos(CATALOGO, n=2)
    assert [libro["Producto"] for libro in extremos["mas_economicos"]] == ["Libro A", "Libro C"]
    assert [libro["Producto"] for libro in extremos["mas_costosos"]] == ["Libro D", "Libro B"]


def test_catalogo_vacio_falla(tmp_path):
    ruta = tmp_path / "vacio.csv"
    CATALOGO.head(0).to_csv(ruta, index=False, encoding="utf-8-sig")
    with pytest.raises(ValueError, match="vacío"):
        analisis.cargar_catalogo(ruta)
