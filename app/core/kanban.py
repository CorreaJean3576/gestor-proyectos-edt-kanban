"""Functional Core (Mike): reglas del tablero Kanban.

Todo es PURO: no hay I/O, no se muta nada; cada función devuelve valores nuevos.
No importa ReactPy, FastAPI ni sqlite3.
"""
from collections import Counter
from dataclasses import dataclass, replace
from typing import Optional

from app.domain.errores import Err, ErrorNoEncontrado, ErrorTransicion, ErrorValidacion, Ok
from app.domain.modelos import (EN_PROGRESO, EN_REVISION, PENDIENTE, PRIORIDADES, TERMINADA, Tarea)

# --- Reglas de transición (datos explícitos, fáciles de explicar y probar) ------------
TRANSICIONES = {
    PENDIENTE: (EN_PROGRESO,),
    EN_PROGRESO: (PENDIENTE, EN_REVISION),
    EN_REVISION: (EN_PROGRESO, TERMINADA),
    TERMINADA: (EN_REVISION,),  # se puede reabrir
}


def siguientes_estados(estado):
    """Estados a los que se puede pasar desde `estado`. Estado desconocido -> ()."""
    return TRANSICIONES.get(estado, ())


def cambiar_estado(tarea, nuevo_estado):
    """Ok(tarea nueva) si la transición es válida; Err(ErrorTransicion) si no.
    La tarea original NO se modifica (dataclass frozen + replace)."""
    if nuevo_estado in siguientes_estados(tarea.estado):
        return Ok(replace(tarea, estado=nuevo_estado))
    return Err(ErrorTransicion(tarea.estado, nuevo_estado))


# --- Ausencia de valor: «no existe» es None, nunca un valor falso ---------------------
def buscar_tarea(tareas, tarea_id) -> Optional[Tarea]:
    return next((t for t in tareas if t.id == tarea_id), None)


# --- Comandos + pattern matching estructural ----------------------------------------
@dataclass(frozen=True)
class CambiarEstado:
    tarea_id: str
    nuevo_estado: str


@dataclass(frozen=True)
class CambiarPrioridad:
    tarea_id: str
    prioridad: str


def aplicar_comando(tareas, comando):
    """Procesa un comando sobre una colección de tareas y devuelve la tarea actualizada
    (Ok) o el error (Err). No modifica `tareas`."""
    match buscar_tarea(tareas, comando.tarea_id):
        case None:
            return Err(ErrorNoEncontrado("tarea", comando.tarea_id))
        case tarea:
            pass
    match comando:
        case CambiarEstado(_, nuevo_estado):
            return cambiar_estado(tarea, nuevo_estado)
        case CambiarPrioridad(_, prioridad) if prioridad in PRIORIDADES:
            return Ok(replace(tarea, prioridad=prioridad))
        case CambiarPrioridad(_, prioridad):
            return Err(ErrorValidacion("prioridad", f"La prioridad «{prioridad}» no es válida."))
        case _:
            return Err(ErrorValidacion("comando", "Comando desconocido."))


# --- Closures: funciones configurables que capturan UN criterio inmutable -------------
def por_estado(estado):
    return lambda t: t.estado == estado


def por_responsable(responsable_id):
    return lambda t: t.responsable_id == responsable_id


def por_prioridad(prioridad):
    return lambda t: t.prioridad == prioridad


# --- Función de orden superior: recibe criterios (funciones) y devuelve otra función --
def combinar(*criterios):
    """Une criterios con AND. Sin criterios, todo pasa."""
    return lambda t: all(c(t) for c in criterios)


def filtrar_tareas(tareas, estado=None, responsable_id=None, prioridad=None):
    """None = «no filtrar por ese criterio» (distinto de un criterio que no encuentra nada)."""
    criterios = [
        c for c in (
            por_estado(estado) if estado is not None else None,
            por_responsable(responsable_id) if responsable_id is not None else None,
            por_prioridad(prioridad) if prioridad is not None else None,
        ) if c is not None
    ]
    return list(filter(combinar(*criterios), tareas))


# --- Ordenamiento y consultas del avance --------------------------------------------
_ORDEN_PRIORIDAD = {"Alta": 0, "Media": 1, "Baja": 2}


def ordenar_tareas(tareas):
    """Primero las de mayor prioridad; a igual prioridad, por nombre. Devuelve lista nueva."""
    return sorted(tareas, key=lambda t: (_ORDEN_PRIORIDAD.get(t.prioridad, 99), t.nombre.lower()))


def pendientes_por_integrante(tareas, integrantes):
    """{id_integrante: cantidad de tareas no terminadas}; incluye 0 para quien no tiene."""
    cuenta = Counter(t.responsable_id for t in tareas if t.estado != TERMINADA)
    return {i.id: cuenta.get(i.id, 0) for i in integrantes}
