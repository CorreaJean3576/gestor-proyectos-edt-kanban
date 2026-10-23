"""Traduce errores del core/persistencia a mensajes comprensibles para la interfaz."""
from app.domain.errores import (ErrorDuplicado, ErrorNoEncontrado, ErrorPersistencia,
                          ErrorTransicion, ErrorValidacion)


def mensaje_para_usuario(error) -> str:
    match error:
        case ErrorValidacion(_, mensaje):
            return mensaje
        case ErrorNoEncontrado(entidad, id_):
            return f"No se encontró {entidad} «{id_}»."
        case ErrorDuplicado(entidad, campo, valor):
            return f"Ya existe {entidad} con {campo} «{valor}»."
        case ErrorTransicion(origen, destino):
            return f"No se puede pasar una tarea de «{origen}» a «{destino}»."
        case ErrorPersistencia(_):
            return "No se pudo guardar o leer en la base de datos. Intenta de nuevo."
        case _:
            return "Ocurrió un error inesperado."
