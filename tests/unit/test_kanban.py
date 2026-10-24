"""Pruebas del núcleo Kanban (Mike). No usan ReactPy, FastAPI ni archivos."""
import pytest

from app.core.kanban import (CambiarEstado, CambiarPrioridad, aplicar_comando, buscar_tarea,
                             cambiar_estado, combinar, filtrar_tareas, ordenar_tareas,
                             pendientes_por_integrante, por_estado, por_responsable,
                             siguientes_estados)
from app.domain.errores import Err, ErrorNoEncontrado, ErrorTransicion, ErrorValidacion, Ok
from app.domain.modelos import (EN_PROGRESO, EN_REVISION, PENDIENTE, TERMINADA, Integrante, Tarea)


def t(id_, nombre="x", estado=PENDIENTE, prio="Media", resp=None):
    return Tarea(id_, "e1", nombre, prio, estado, resp)


# --- transiciones ---
@pytest.mark.parametrize("origen,destino", [
    (PENDIENTE, EN_PROGRESO), (EN_PROGRESO, PENDIENTE), (EN_PROGRESO, EN_REVISION),
    (EN_REVISION, EN_PROGRESO), (EN_REVISION, TERMINADA), (TERMINADA, EN_REVISION)])
def test_transiciones_validas(origen, destino):
    r = cambiar_estado(t("1", estado=origen), destino)
    assert isinstance(r, Ok) and r.valor.estado == destino


@pytest.mark.parametrize("origen,destino", [
    (PENDIENTE, TERMINADA), (PENDIENTE, EN_REVISION), (PENDIENTE, PENDIENTE),
    (EN_PROGRESO, TERMINADA), (TERMINADA, PENDIENTE), (PENDIENTE, "Inventado")])
def test_transiciones_invalidas(origen, destino):
    assert cambiar_estado(t("1", estado=origen), destino) == Err(ErrorTransicion(origen, destino))


def test_cambiar_estado_no_muta_la_original():
    original = t("1")
    nueva = cambiar_estado(original, EN_PROGRESO).valor
    assert original.estado == PENDIENTE and nueva.estado == EN_PROGRESO


def test_siguientes_estados():
    assert siguientes_estados(PENDIENTE) == (EN_PROGRESO,)
    assert siguientes_estados(TERMINADA) == (EN_REVISION,)
    assert siguientes_estados("Raro") == ()


# --- ausencia de valor y comandos (match/case) ---
def test_buscar_tarea():
    assert buscar_tarea([t("1")], "1").id == "1"
    assert buscar_tarea([t("1")], "9") is None
    assert buscar_tarea([], "1") is None


def test_comando_cambiar_estado():
    tareas = [t("1"), t("2")]
    r = aplicar_comando(tareas, CambiarEstado("1", EN_PROGRESO))
    assert r.valor.estado == EN_PROGRESO and tareas[0].estado == PENDIENTE


def test_comando_transicion_invalida():
    r = aplicar_comando([t("1")], CambiarEstado("1", TERMINADA))
    assert isinstance(r.error, ErrorTransicion)


def test_comando_tarea_inexistente():
    assert aplicar_comando([], CambiarEstado("9", EN_PROGRESO)).error == ErrorNoEncontrado("tarea", "9")


def test_comando_prioridad():
    assert aplicar_comando([t("1")], CambiarPrioridad("1", "Alta")).valor.prioridad == "Alta"
    assert isinstance(aplicar_comando([t("1")], CambiarPrioridad("1", "Urgente")).error, ErrorValidacion)


# --- filtros: closures + HOF ---
TAREAS = [t("1", resp="m1"), t("2", resp="m2", prio="Alta"),
          t("3", resp="m1", estado=TERMINADA), t("4")]


def test_closures_capturan_su_criterio():
    assert por_estado(TERMINADA)(TAREAS[2]) and not por_estado(TERMINADA)(TAREAS[0])
    assert por_responsable("m1")(TAREAS[0]) and not por_responsable("m1")(TAREAS[1])


def test_combinar_sin_criterios_deja_pasar_todo():
    assert combinar()(TAREAS[0]) is True


def test_filtrar_sin_criterios_devuelve_todo():
    assert filtrar_tareas(TAREAS) == TAREAS


def test_filtrar_por_cada_criterio_y_combinados():
    assert [x.id for x in filtrar_tareas(TAREAS, estado=TERMINADA)] == ["3"]
    assert [x.id for x in filtrar_tareas(TAREAS, responsable_id="m1")] == ["1", "3"]
    assert [x.id for x in filtrar_tareas(TAREAS, prioridad="Alta")] == ["2"]
    assert [x.id for x in filtrar_tareas(TAREAS, responsable_id="m1", estado=PENDIENTE)] == ["1"]


def test_filtrar_sin_resultados_y_lista_vacia():
    assert filtrar_tareas(TAREAS, prioridad="Baja") == []
    assert filtrar_tareas([], estado=PENDIENTE) == []


# --- orden y pendientes ---
def test_ordenar_por_prioridad_y_nombre():
    tareas = [t("1", "b"), t("2", "a", prio="Baja"), t("3", "z", prio="Alta"), t("4", "a")]
    assert [x.id for x in ordenar_tareas(tareas)] == ["3", "4", "1", "2"]
    assert ordenar_tareas([]) == []


def test_pendientes_por_integrante():
    ints = [Integrante("m1", "p1", "Ana"), Integrante("m2", "p1", "Luis"), Integrante("m3", "p1", "Eva")]
    assert pendientes_por_integrante(TAREAS, ints) == {"m1": 1, "m2": 1, "m3": 0}
    assert pendientes_por_integrante([], ints) == {"m1": 0, "m2": 0, "m3": 0}
