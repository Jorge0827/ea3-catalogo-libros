"""Autores del trabajo, en el orden de las evidencias anteriores."""

AUTORES = (
    "Juan Carlos Ardila Gómez",
    "Edwin Alberto Ruiz Guzmán",
    "Jorge Andrés Echavarría Pardo",
    "Yeison Padrón Higuita",
)


def texto_autores() -> str:
    return ", ".join(AUTORES[:-1]) + " y " + AUTORES[-1]
