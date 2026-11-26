# Catálogo de libros con CI/CD

Aplicación web de la Evidencia de aprendizaje 3. Muestra el catálogo de
[Books to Scrape](https://books.toscrape.com/), un sitio de práctica cuyos
precios y calificaciones son ficticios.

Autores, en el orden de las evidencias anteriores:

- Juan Carlos Ardila Gómez
- Edwin Alberto Ruiz Guzmán
- Jorge Andrés Echavarría Pardo
- Yeison Padrón Higuita

El trabajo continúa la extracción de la Evidencia 2 y le agrega una interfaz,
pruebas automáticas y despliegue continuo en Render. La Evidencia 1 había
intentado extraer laptops de Mercado Libre; ese sitio dejó de entregar el
listado y por eso el catálogo de esta entrega es el de práctica.

El repositorio anterior del equipo queda como antecedente:
https://github.com/jardilag/ProgramacionAnaliticaDatos. El informe en Word no
forma parte de este repositorio.

## Archivos

- `scraper.py`: descarga y valida el catálogo.
- `analisis.py`: resumen, distribuciones y correlación.
- `app.py`: rutas de la aplicación.
- `autores.py`: nombres que muestra el pie de página.
- `iniciar.py`: arranque local y Gunicorn en Render.
- `templates/` y `static/`: interfaz.
- `test_*.py`: pruebas sin consultar el sitio.
- `data/libros_books_to_scrape.csv`: catálogo que publica el servicio.
- `.github/workflows/cicd.yml`: pruebas y despliegue.
- `render.yaml`: definición del servicio.

## Ejecución local

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -v
.\.venv\Scripts\python.exe scraper.py --paginas 50
.\.venv\Scripts\python.exe iniciar.py
```

La aplicación queda en `http://127.0.0.1:5000`. `scraper.py` espera un segundo
entre páginas. El CSV que publica el servicio ya está en
`data/libros_books_to_scrape.csv`, así el arranque no vuelve a consultar el sitio.

## Pipeline

El archivo `.github/workflows/cicd.yml` define dos trabajos:

1. **Pruebas automatizadas.** En cada push o pull request hacia `main`, GitHub
   Actions instala las dependencias en Ubuntu y ejecuta `pytest`. Las pruebas
   no visitan Books to Scrape.
2. **Despliegue continuo.** Solo corre en `main`, y solo si las pruebas
   pasaron. Render está configurado con `autoDeployTrigger: checksPass` en
   `render.yaml`: publica el servicio cuando ese check queda en verde. Si el
   repositorio tiene el secreto `RENDER_DEPLOY_HOOK_URL`, el mismo trabajo
   también llama ese deploy hook.

Un pull request queda en integración continua y no se publica.

## Despliegue

Render instala `requirements.txt` y ejecuta `python iniciar.py`. Ese archivo
lee `PORT` y arranca Gunicorn. La comprobación de estado es `/salud`.

El plan gratuito puede suspender el servicio tras un rato sin visitas. La
primera petición después de eso tarda un poco más en responder.
