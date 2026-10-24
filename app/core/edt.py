"""Functional Core de la EDT/WBS: validaciones y creación de integrantes, entregables y tareas."""
from dataclasses import replace

from app.core.opcion import Nothing, Option, Some
from app.domain.errores import Err, ErrorDuplicado, ErrorNoEncontrado, ErrorValidacion, Ok
from app.domain.modelos import PENDIENTE, PRIORIDADES, Entregable, Integrante, Tarea


def validar_texto(campo, valor, maximo=80):
    """Devuelve Ok(texto sin espacios sobrantes) o Err(ErrorValidacion)."""
    limpio = (valor or "").strip()
    if not limpio:
        return Err(ErrorValidacion(campo, f"El campo «{campo}» no puede estar vacío."))
    if len(limpio) > maximo:
        return Err(ErrorValidacion(campo, f"El campo «{campo}» no puede superar {maximo} caracteres."))
    return Ok(limpio)


def buscar_por_id(elementos, id_) -> Option:
    return next((Some(e) for e in elementos if e.id == id_), Nothing())


def crear_integrante(existentes, proyecto_id, id_, nombre):
    match _validar_id_y_nombre(id_, nombre):
        case Err() as error:
            return error
        case Ok((id_limpio, nombre_limpio)):
            if isinstance(buscar_por_id(existentes, id_limpio), Some):
                return Err(ErrorDuplicado("integrante", "id", id_limpio))
            if _nombre_repetido(existentes, nombre_limpio):
                return Err(ErrorDuplicado("integrante", "nombre", nombre_limpio))
            return Ok(Integrante(id_limpio, proyecto_id, nombre_limpio))


def crear_entregable(existentes, proyecto_id, id_, nombre):
    match _validar_id_y_nombre(id_, nombre):
        case Err() as error:
            return error
        case Ok((id_limpio, nombre_limpio)):
            if isinstance(buscar_por_id(existentes, id_limpio), Some):
                return Err(ErrorDuplicado("entregable", "id", id_limpio))
            if _nombre_repetido(existentes, nombre_limpio):
                return Err(ErrorDuplicado("entregable", "nombre", nombre_limpio))
            return Ok(Entregable(id_limpio, proyecto_id, nombre_limpio))


def crear_tarea(entregables, tareas, integrantes, id_, entregable_id, nombre, prioridad, responsable_id):
    match _validar_id_y_nombre(id_, nombre):
        case Err() as error:
            return error
        case Ok((id_limpio, nombre_limpio)):
            if prioridad not in PRIORIDADES:
                return Err(ErrorValidacion("prioridad", f"La prioridad debe ser una de: {', '.join(PRIORIDADES)}."))
            match buscar_por_id(entregables, entregable_id):
                case Nothing():
                    return Err(ErrorNoEncontrado("entregable", entregable_id))
                case Some():
                    pass
            if isinstance(buscar_por_id(tareas, id_limpio), Some):
                return Err(ErrorDuplicado("tarea", "id", id_limpio))
            del_entregable = [t for t in tareas if t.entregable_id == entregable_id]
            if _nombre_repetido(del_entregable, nombre_limpio):
                return Err(ErrorDuplicado("tarea", "nombre", nombre_limpio))
            match _verificar_responsable(integrantes, responsable_id):
                case Err() as error:
                    return error
                case Ok(responsable):
                    return Ok(Tarea(id_limpio, entregable_id, nombre_limpio, prioridad, PENDIENTE, responsable))


def asignar_responsable(tarea, integrantes, responsable_id):
    """Devuelve una tarea nueva con otro responsable; la original no se modifica."""
    match _verificar_responsable(integrantes, responsable_id):
        case Err() as error:
            return error
        case Ok(responsable):
            return Ok(replace(tarea, responsable_id=responsable))


# --- Funciones auxiliares (también puras) ---


def _validar_id_y_nombre(id_, nombre):
    match validar_texto("id", id_):
        case Err() as error:
            return error
        case Ok(id_limpio):
            match validar_texto("nombre", nombre):
                case Err() as error:
                    return error
                case Ok(nombre_limpio):
                    return Ok((id_limpio, nombre_limpio))


def _nombre_repetido(elementos, nombre) -> bool:
    return any(e.nombre.lower() == nombre.lower() for e in elementos)


def _verificar_responsable(integrantes, responsable_id):

    if not responsable_id:
        return Ok(None)
    match buscar_por_id(integrantes, responsable_id):
        case Some():
            return Ok(responsable_id)
        case Nothing():
            return Err(ErrorNoEncontrado("integrante", responsable_id))