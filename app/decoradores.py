"""Decorador pequeño (Jean Pierre): registra una operación y mide su duración.

No contiene reglas del dominio: solo observa la llamada (efecto de logging).
"""
import logging
import time
from functools import wraps

log = logging.getLogger("gestor")


def medir_duracion(funcion):
    @wraps(funcion)
    def envoltura(*args, **kwargs):
        inicio = time.perf_counter()
        try:
            return funcion(*args, **kwargs)
        finally:
            log.info("%s tardó %.4f s", funcion.__name__, time.perf_counter() - inicio)

    return envoltura
