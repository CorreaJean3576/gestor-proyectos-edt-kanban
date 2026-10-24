"""Pruebas unitarias del núcleo funcional de la EDT (sin ReactPy, FastAPI ni SQLite)."""
from dataclasses import FrozenInstanceError

import pytest

from app.core.edt import (asignar_responsable, buscar_por_id, crear_entregable, crear_integrante,
                          crear_tarea, validar_texto)
from app.core.opcion import Nothing, Some
from app.domain.errores import Err, ErrorDuplicado, ErrorNoEncontrado, ErrorValidacion, Ok
from app.domain.modelos import Entregable, Integrante, Tarea


@pytest.fixture
def integrantes():
    return [Integrante("m1", "p1", "Tamara")]


@pytest.fixture
def entregables():
    return [Entregable("e1", "p1", "Diseño")]


@pytest.fixture
def tareas():
    return [Tarea("t1", "e1", "Wireframes")]


# --- validar_texto ---


def test_validar_texto_limpia_espacios():
    assert validar_texto("nombre", "  Diseñar EDT  ") == Ok("Diseñar EDT")


@pytest.mark.parametrize("valor", ["", "   ", None])
def test_validar_texto_vacio_es_error(valor):
    resultado = validar_texto("nombre", valor)
    assert isinstance(resultado, Err)
    assert resultado.error == ErrorValidacion("nombre", "El campo «nombre» no puede estar vacío.")


def test_validar_texto_limite_del_maximo():
    assert isinstance(validar_texto("nombre", "a" * 80), Ok)
    assert isinstance(validar_texto("nombre", "a" * 81), Err)


def test_validar_texto_respeta_un_maximo_distinto():
    assert isinstance(validar_texto("nombre", "abcd", maximo=3), Err)
    assert isinstance(validar_texto("nombre", "abc", maximo=3), Ok)


# --- ausencia de valor ---


def test_buscar_por_id_existente_devuelve_some(integrantes):
    assert buscar_por_id(integrantes, "m1") == Some(integrantes[0])


def test_buscar_por_id_inexistente_devuelve_nothing(integrantes):
    assert buscar_por_id(integrantes, "zzz") == Nothing()


def test_buscar_en_lista_vacia_devuelve_nothing():
    assert buscar_por_id([], "m1") == Nothing()


# --- crear_integrante y crear_entregable ---


def test_crear_integrante_valido():
    assert crear_integrante([], "p1", " m1 ", " Tamara ") == Ok(Integrante("m1", "p1", "Tamara"))


def test_crear_integrante_con_nombre_vacio(integrantes):
    resultado = crear_integrante(integrantes, "p1", "m2", "   ")
    assert isinstance(resultado.error, ErrorValidacion)


def test_crear_integrante_con_nombre_repetido_ignora_mayusculas(integrantes):
    assert crear_integrante(integrantes, "p1", "m2", "TAMARA") == Err(ErrorDuplicado("integrante", "nombre", "TAMARA"))


def test_crear_integrante_con_id_repetido(integrantes):
    assert crear_integrante(integrantes, "p1", "m1", "Mike") == Err(ErrorDuplicado("integrante", "id", "m1"))


def test_crear_integrante_no_modifica_la_lista_recibida(integrantes):
    antes = list(integrantes)
    crear_integrante(integrantes, "p1", "m2", "Mike")
    assert integrantes == antes


def test_crear_entregable_valido(entregables):
    assert crear_entregable(entregables, "p1", "e2", "Pruebas") == Ok(Entregable("e2", "p1", "Pruebas"))


def test_crear_entregable_con_nombre_repetido(entregables):
    assert crear_entregable(entregables, "p1", "e2", "diseño") == Err(ErrorDuplicado("entregable", "nombre", "diseño"))


def test_crear_entregable_con_id_repetido(entregables):
    assert crear_entregable(entregables, "p1", "e1", "Otro") == Err(ErrorDuplicado("entregable", "id", "e1"))


# --- crear_tarea ---


def test_crear_tarea_empieza_pendiente(entregables, tareas, integrantes):
    resultado = crear_tarea(entregables, tareas, integrantes, "t2", "e1", "Mockups", "Alta", "m1")
    assert resultado == Ok(Tarea("t2", "e1", "Mockups", "Alta", "Pendiente", "m1"))


def test_crear_tarea_sin_responsable(entregables, tareas, integrantes):
    resultado = crear_tarea(entregables, tareas, integrantes, "t2", "e1", "Mockups", "Media", None)
    assert resultado.valor.responsable_id is None


def test_crear_tarea_con_responsable_vacio_se_trata_como_sin_responsable(entregables, tareas, integrantes):
    resultado = crear_tarea(entregables, tareas, integrantes, "t2", "e1", "Mockups", "Media", "")
    assert resultado.valor.responsable_id is None


def test_crear_tarea_en_entregable_inexistente(entregables, tareas, integrantes):
    resultado = crear_tarea(entregables, tareas, integrantes, "t2", "nope", "A", "Media", None)
    assert resultado == Err(ErrorNoEncontrado("entregable", "nope"))


def test_crear_tarea_con_responsable_no_registrado(entregables, tareas, integrantes):
    resultado = crear_tarea(entregables, tareas, integrantes, "t2", "e1", "A", "Media", "fantasma")
    assert resultado == Err(ErrorNoEncontrado("integrante", "fantasma"))


def test_crear_tarea_con_id_repetido(entregables, tareas, integrantes):
    resultado = crear_tarea(entregables, tareas, integrantes, "t1", "e1", "Otra", "Media", None)
    assert resultado == Err(ErrorDuplicado("tarea", "id", "t1"))


def test_crear_tarea_con_nombre_repetido_en_el_mismo_entregable(entregables, tareas, integrantes):
    resultado = crear_tarea(entregables, tareas, integrantes, "t2", "e1", "wireframes", "Media", None)
    assert resultado == Err(ErrorDuplicado("tarea", "nombre", "wireframes"))


def test_crear_tarea_permite_el_mismo_nombre_en_otro_entregable(entregables, tareas, integrantes):
    entregables = entregables + [Entregable("e2", "p1", "Código")]
    resultado = crear_tarea(entregables, tareas, integrantes, "t2", "e2", "Wireframes", "Media", None)
    assert isinstance(resultado, Ok)


def test_crear_tarea_con_prioridad_invalida(entregables, tareas, integrantes):
    resultado = crear_tarea(entregables, tareas, integrantes, "t2", "e1", "A", "Urgente", None)
    assert isinstance(resultado.error, ErrorValidacion)
    assert resultado.error.campo == "prioridad"


def test_crear_tarea_con_nombre_vacio(entregables, tareas, integrantes):
    resultado = crear_tarea(entregables, tareas, integrantes, "t2", "e1", "  ", "Media", None)
    assert isinstance(resultado.error, ErrorValidacion)


def test_crear_tarea_no_modifica_las_listas_recibidas(entregables, tareas, integrantes):
    antes = list(tareas)
    crear_tarea(entregables, tareas, integrantes, "t2", "e1", "Mockups", "Alta", "m1")
    assert tareas == antes


# --- asignar_responsable e inmutabilidad ---


def test_asignar_responsable_devuelve_tarea_nueva(integrantes):
    original = Tarea("t1", "e1", "Wireframes")
    nueva = asignar_responsable(original, integrantes, "m1").valor
    assert nueva.responsable_id == "m1"
    assert original.responsable_id is None


def test_asignar_responsable_no_registrado(integrantes):
    resultado = asignar_responsable(Tarea("t1", "e1", "A"), integrantes, "fantasma")
    assert resultado == Err(ErrorNoEncontrado("integrante", "fantasma"))


def test_la_tarea_es_inmutable():
    tarea = Tarea("t1", "e1", "Wireframes")
    with pytest.raises(FrozenInstanceError):
        tarea.nombre = "otro"


def test_las_funciones_son_puras_misma_entrada_misma_salida(entregables, tareas, integrantes):
    llamada = lambda: crear_tarea(entregables, tareas, integrantes, "t2", "e1", "Mockups", "Alta", "m1")
    assert llamada() == llamada()