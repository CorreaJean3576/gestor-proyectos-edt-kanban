"""Casos de uso (Imperative Shell): leer de SQLite -> función pura del core -> guardar.

Aquí se coordinan los efectos; las reglas viven en core/. Cada caso de uso
devuelve Resultado para que la interfaz solo decida qué mostrar.
"""
from app.core import edt, kanban
from app.domain.errores import Err, ErrorValidacion, Ok
from app.domain.modelos import Proyecto
from app.adapters import sqlite as db


def _con(*resultados):
    """Si alguno falló devuelve ese Err; si no, None."""
    return next((r for r in resultados if isinstance(r, Err)), None)


def crear_proyecto(con, id_, nombre, descripcion=""):
    match edt.validar_texto("nombre", nombre):
        case Err() as e:
            return e
        case Ok(n):
            if not (id_ or "").strip():
                return Err(ErrorValidacion("id", "El campo «id» no puede estar vacío."))
            return db.guardar_proyecto(con, Proyecto(id_.strip(), n, (descripcion or "").strip()))


def registrar_integrante(con, proyecto_id, id_, nombre):
    match db.obtener_proyecto(con, proyecto_id), db.listar_integrantes(con, proyecto_id):
        case (Err() as e, _) | (_, Err() as e):
            return e
        case (Ok(_), Ok(existentes)):
            match edt.crear_integrante(existentes, proyecto_id, id_, nombre):
                case Ok(nuevo):
                    return db.guardar_integrante(con, nuevo)
                case Err() as e:
                    return e


def crear_entregable(con, proyecto_id, id_, nombre):
    match db.obtener_proyecto(con, proyecto_id), db.listar_entregables(con, proyecto_id):
        case (Err() as e, _) | (_, Err() as e):
            return e
        case (Ok(_), Ok(existentes)):
            match edt.crear_entregable(existentes, proyecto_id, id_, nombre):
                case Ok(nuevo):
                    return db.guardar_entregable(con, nuevo)
                case Err() as e:
                    return e


def crear_tarea(con, proyecto_id, id_, entregable_id, nombre, prioridad, responsable_id):
    datos = (db.listar_entregables(con, proyecto_id), db.listar_tareas(con, proyecto_id),
             db.listar_integrantes(con, proyecto_id))
    if (fallo := _con(*datos)):
        return fallo
    entregables, tareas, integrantes = (r.valor for r in datos)
    match edt.crear_tarea(entregables, tareas, integrantes, id_, entregable_id, nombre,
                          prioridad, responsable_id):
        case Ok(nueva):
            return db.guardar_tarea(con, nueva)
        case Err() as e:
            return e


def mover_tarea(con, tarea_id, nuevo_estado):
    match db.obtener_tarea(con, tarea_id):
        case Err() as e:
            return e
        case Ok(tarea):
            match kanban.cambiar_estado(tarea, nuevo_estado):
                case Ok(actualizada):
                    return db.guardar_tarea(con, actualizada)
                case Err() as e:
                    return e


def cargar_tablero(con, proyecto_id):
    """Lee todo lo necesario para pintar EDT y Kanban con los mismos datos."""
    datos = (db.listar_integrantes(con, proyecto_id), db.listar_entregables(con, proyecto_id),
             db.listar_tareas(con, proyecto_id))
    if (fallo := _con(*datos)):
        return fallo
    integrantes, entregables, tareas = (r.valor for r in datos)
    return Ok({"integrantes": integrantes, "entregables": entregables, "tareas": tareas})
