"""Aplicación web del catálogo extraído de Books to Scrape."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from flask import Flask, abort, render_template, request

import analisis
import autores

POR_PAGINA = 20
RAIZ = Path(__file__).resolve().parent


def crear_aplicacion(catalogo: pd.DataFrame | None = None) -> Flask:
    aplicacion = Flask(__name__)
    if catalogo is not None:
        aplicacion.config["CATALOGO"] = catalogo

    def datos() -> pd.DataFrame:
        if "CATALOGO" not in aplicacion.config:
            aplicacion.config["CATALOGO"] = analisis.cargar_catalogo(
                RAIZ / analisis.ARCHIVO_CSV
            )
        return aplicacion.config["CATALOGO"]

    @aplicacion.context_processor
    def inyectar_autores():
        return {"autores": autores.texto_autores()}

    @aplicacion.get("/salud")
    def salud():
        return {"estado": "ok", "libros": int(len(datos()))}

    @aplicacion.get("/")
    def inicio():
        tabla = datos()
        calificaciones = analisis.por_calificacion(tabla)
        precios = analisis.por_precio(tabla)
        return render_template(
            "inicio.html",
            resumen=analisis.resumir(tabla),
            calificaciones=calificaciones,
            max_calificacion=max(fila["cantidad"] for fila in calificaciones) or 1,
            precios=precios,
            max_precio=max(fila["cantidad"] for fila in precios) or 1,
            extremos=analisis.extremos(tabla),
        )

    @aplicacion.get("/catalogo")
    def catalogo_vista():
        tabla = datos()
        consulta = request.args.get("q", "", type=str).strip()
        pagina = request.args.get("pagina", 1, type=int)
        if pagina < 1:
            pagina = 1
        filtrado = tabla
        if consulta:
            filtrado = tabla[
                tabla["Producto"].str.contains(consulta, case=False, na=False)
            ]
        total = int(len(filtrado))
        paginas = max(1, (total + POR_PAGINA - 1) // POR_PAGINA)
        if pagina > paginas:
            pagina = paginas
        inicio_fila = (pagina - 1) * POR_PAGINA
        filas = filtrado.iloc[inicio_fila : inicio_fila + POR_PAGINA].reset_index(names="indice")
        return render_template(
            "catalogo.html",
            filas=filas.to_dict(orient="records"),
            consulta=consulta,
            pagina=pagina,
            paginas=paginas,
            total=total,
            total_catalogo=int(len(tabla)),
        )

    @aplicacion.get("/flujo")
    def flujo():
        return render_template("flujo.html")

    @aplicacion.get("/libro/<int:indice>")
    def libro(indice: int):
        tabla = datos()
        if indice < 0 or indice >= len(tabla):
            abort(404)
        return render_template("libro.html", libro=tabla.iloc[indice].to_dict(), indice=indice)

    return aplicacion


app = crear_aplicacion()
