"""Flujo principal shell + core + SQLite (en memoria).

Necesita el core de Tamara y Mike: si aún no existe, estas pruebas se omiten."""
import pytest

pytest.importorskip("app.core.edt")
pytest.importorskip("app.core.kanban")

from app.domain.errores import Err, ErrorDuplicado, ErrorNoEncontrado, ErrorTransicion, ErrorValidacion, Ok
from app import servicio
from app.adapters import sqlite as db
from app.ui.mensajes import mensaje_para_usuario


def _con():
    con = db.conectar(":memory:")
    assert isinstance(servicio.crear_proyecto(con, "p1", "Gestor"), Ok)
    return con


def test_flujo_completo():
    con = _con()
    assert isinstance(servicio.registrar_integrante(con, "p1", "m1", "Tamara"), Ok)
    assert isinstance(servicio.crear_entregable(con, "p1", "e1", "Diseño"), Ok)
    assert isinstance(servicio.crear_tarea(con, "p1", "t1", "e1", "Wireframes", "Alta", "m1"), Ok)
    assert isinstance(servicio.mover_tarea(con, "t1", "En progreso"), Ok)
    tablero = servicio.cargar_tablero(con, "p1").valor
    assert tablero["tareas"][0].estado == "En progreso"


def test_nombre_vacio_es_error_de_validacion():
    con = _con()
    r = servicio.registrar_integrante(con, "p1", "m1", "   ")
    assert isinstance(r.error, ErrorValidacion)


def test_integrante_duplicado_sin_distinguir_mayusculas():
    con = _con()
    servicio.registrar_integrante(con, "p1", "m1", "Tamara")
    r = servicio.registrar_integrante(con, "p1", "m2", "TAMARA")
    assert isinstance(r.error, ErrorDuplicado)
    assert len(db.listar_integrantes(con, "p1").valor) == 1


def test_tarea_con_entregable_inexistente():
    con = _con()
    r = servicio.crear_tarea(con, "p1", "t1", "nope", "A", "Media", None)
    assert r.error == ErrorNoEncontrado("entregable", "nope")


def test_tarea_con_responsable_no_registrado():
    con = _con()
    servicio.crear_entregable(con, "p1", "e1", "Diseño")
    r = servicio.crear_tarea(con, "p1", "t1", "e1", "A", "Media", "fantasma")
    assert r.error == ErrorNoEncontrado("integrante", "fantasma")


def test_transicion_invalida_no_cambia_la_tarea():
    con = _con()
    servicio.crear_entregable(con, "p1", "e1", "Diseño")
    servicio.crear_tarea(con, "p1", "t1", "e1", "A", "Media", None)
    r = servicio.mover_tarea(con, "t1", "Terminada")
    assert isinstance(r.error, ErrorTransicion)
    assert db.obtener_tarea(con, "t1").valor.estado == "Pendiente"


def test_mover_tarea_inexistente():
    con = _con()
    assert servicio.mover_tarea(con, "x", "En progreso").error == ErrorNoEncontrado("tarea", "x")


def test_estado_vacio_del_tablero():
    con = _con()
    t = servicio.cargar_tablero(con, "p1").valor
    assert t == {"integrantes": [], "entregables": [], "tareas": []}


def test_mensajes_comprensibles():
    assert "Terminada" in mensaje_para_usuario(ErrorTransicion("Pendiente", "Terminada"))
    assert "t9" in mensaje_para_usuario(ErrorNoEncontrado("tarea", "t9"))
