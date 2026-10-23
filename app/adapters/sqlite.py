"""Adaptador SQLite (Imperative Shell). Sin reglas del dominio: solo guardar y leer.

Todas las operaciones devuelven Resultado (Ok/Err); los errores de SQLite se
convierten en ErrorPersistencia y las escrituras usan transacción con rollback.
"""
import sqlite3
from contextlib import contextmanager

from app.domain.errores import Err, ErrorNoEncontrado, ErrorPersistencia, Ok
from app.domain.modelos import Entregable, Integrante, Proyecto, Tarea
from app.decoradores import medir_duracion

ESQUEMA = """
CREATE TABLE IF NOT EXISTS proyectos (
    id TEXT PRIMARY KEY, nombre TEXT NOT NULL, descripcion TEXT NOT NULL DEFAULT '');
CREATE TABLE IF NOT EXISTS integrantes (
    id TEXT PRIMARY KEY,
    proyecto_id TEXT NOT NULL REFERENCES proyectos(id),
    nombre TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS entregables (
    id TEXT PRIMARY KEY,
    proyecto_id TEXT NOT NULL REFERENCES proyectos(id),
    nombre TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS tareas (
    id TEXT PRIMARY KEY,
    entregable_id TEXT NOT NULL REFERENCES entregables(id),
    nombre TEXT NOT NULL,
    prioridad TEXT NOT NULL,
    estado TEXT NOT NULL,
    responsable_id TEXT REFERENCES integrantes(id));
"""


def conectar(ruta: str = "gestor.db") -> sqlite3.Connection:
    """Abre la conexión e inicializa el esquema de forma controlada."""
    con = sqlite3.connect(ruta, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(ESQUEMA)
    con.commit()
    return con


@contextmanager
def transaccion(con: sqlite3.Connection):
    """Confirma si todo sale bien; si algo falla, revierte (sin cambios parciales)."""
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise


def _escribir(con, sql: str, params: tuple, valor):
    try:
        with transaccion(con):
            con.execute(sql, params)
        return Ok(valor)
    except sqlite3.Error as e:
        return Err(ErrorPersistencia(str(e)))


def _leer(con, sql: str, params: tuple, construir):
    try:
        return Ok([construir(f) for f in con.execute(sql, params).fetchall()])
    except sqlite3.Error as e:
        return Err(ErrorPersistencia(str(e)))


# ------------------------------ proyectos ------------------------------
@medir_duracion
def guardar_proyecto(con, p: Proyecto):
    return _escribir(
        con,
        "INSERT INTO proyectos(id, nombre, descripcion) VALUES (?,?,?) "
        "ON CONFLICT(id) DO UPDATE SET nombre=excluded.nombre, descripcion=excluded.descripcion",
        (p.id, p.nombre, p.descripcion), p)


@medir_duracion
def listar_proyectos(con):
    return _leer(con, "SELECT * FROM proyectos ORDER BY rowid", (),
                 lambda f: Proyecto(f["id"], f["nombre"], f["descripcion"]))


@medir_duracion
def obtener_proyecto(con, id_: str):
    match listar_proyectos(con):
        case Err() as e:
            return e
        case Ok(lista):
            encontrado = next((p for p in lista if p.id == id_), None)
            return Ok(encontrado) if encontrado else Err(ErrorNoEncontrado("proyecto", id_))


# ------------------------------ integrantes ------------------------------
@medir_duracion
def guardar_integrante(con, m: Integrante):
    return _escribir(con, "INSERT INTO integrantes(id, proyecto_id, nombre) VALUES (?,?,?)",
                     (m.id, m.proyecto_id, m.nombre), m)


@medir_duracion
def listar_integrantes(con, proyecto_id: str):
    return _leer(con, "SELECT * FROM integrantes WHERE proyecto_id=? ORDER BY rowid", (proyecto_id,),
                 lambda f: Integrante(f["id"], f["proyecto_id"], f["nombre"]))


# ------------------------------ entregables ------------------------------
@medir_duracion
def guardar_entregable(con, e: Entregable):
    return _escribir(con, "INSERT INTO entregables(id, proyecto_id, nombre) VALUES (?,?,?)",
                     (e.id, e.proyecto_id, e.nombre), e)


@medir_duracion
def listar_entregables(con, proyecto_id: str):
    return _leer(con, "SELECT * FROM entregables WHERE proyecto_id=? ORDER BY rowid", (proyecto_id,),
                 lambda f: Entregable(f["id"], f["proyecto_id"], f["nombre"]))


# ------------------------------ tareas ------------------------------
def _tarea(f) -> Tarea:
    return Tarea(f["id"], f["entregable_id"], f["nombre"], f["prioridad"], f["estado"], f["responsable_id"])


@medir_duracion
def guardar_tarea(con, t: Tarea):
    """Inserta o actualiza (upsert) una tarea."""
    return _escribir(
        con,
        "INSERT INTO tareas(id, entregable_id, nombre, prioridad, estado, responsable_id) "
        "VALUES (?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET "
        "nombre=excluded.nombre, prioridad=excluded.prioridad, "
        "estado=excluded.estado, responsable_id=excluded.responsable_id",
        (t.id, t.entregable_id, t.nombre, t.prioridad, t.estado, t.responsable_id), t)


@medir_duracion
def listar_tareas(con, proyecto_id: str):
    return _leer(
        con,
        "SELECT t.* FROM tareas t JOIN entregables e ON e.id = t.entregable_id "
        "WHERE e.proyecto_id=? ORDER BY t.rowid", (proyecto_id,), _tarea)


@medir_duracion
def obtener_tarea(con, id_: str):
    match _leer(con, "SELECT * FROM tareas WHERE id=?", (id_,), _tarea):
        case Err() as e:
            return e
        case Ok([t]):
            return Ok(t)
        case Ok(_):
            return Err(ErrorNoEncontrado("tarea", id_))
