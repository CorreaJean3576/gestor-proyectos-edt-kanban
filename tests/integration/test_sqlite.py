"""Pruebas de integración del adaptador SQLite (base en memoria, nunca la real)."""
import sqlite3

from app.domain.errores import Err, ErrorNoEncontrado, ErrorPersistencia, Ok
from app.domain.modelos import Entregable, Integrante, Proyecto, Tarea
from app.adapters import sqlite as db


def _base():
    con = db.conectar(":memory:")
    db.guardar_proyecto(con, Proyecto("p1", "Proyecto 1", "desc"))
    return con


def test_esquema_se_crea():
    con = db.conectar(":memory:")
    tablas = {f["name"] for f in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"proyectos", "integrantes", "entregables", "tareas"} <= tablas


def test_inicializar_dos_veces_no_falla():
    con = db.conectar(":memory:")
    con.executescript(db.ESQUEMA)  # idempotente (IF NOT EXISTS)


def test_guardar_y_obtener_proyecto():
    con = _base()
    assert db.obtener_proyecto(con, "p1") == Ok(Proyecto("p1", "Proyecto 1", "desc"))


def test_proyecto_inexistente_devuelve_no_encontrado():
    con = _base()
    assert db.obtener_proyecto(con, "zzz") == Err(ErrorNoEncontrado("proyecto", "zzz"))


def test_guardar_y_listar_integrantes_entregables_tareas():
    con = _base()
    db.guardar_integrante(con, Integrante("m1", "p1", "Tamara"))
    db.guardar_entregable(con, Entregable("e1", "p1", "Diseño"))
    t = Tarea("t1", "e1", "Wireframes", "Alta", "Pendiente", "m1")
    assert db.guardar_tarea(con, t) == Ok(t)
    assert db.listar_integrantes(con, "p1") == Ok([Integrante("m1", "p1", "Tamara")])
    assert db.listar_entregables(con, "p1") == Ok([Entregable("e1", "p1", "Diseño")])
    assert db.listar_tareas(con, "p1") == Ok([t])


def test_guardar_tarea_actualiza_si_ya_existe():
    con = _base()
    db.guardar_entregable(con, Entregable("e1", "p1", "Diseño"))
    db.guardar_tarea(con, Tarea("t1", "e1", "A"))
    db.guardar_tarea(con, Tarea("t1", "e1", "A", estado="En progreso"))
    assert db.obtener_tarea(con, "t1").valor.estado == "En progreso"
    assert len(db.listar_tareas(con, "p1").valor) == 1


def test_tarea_inexistente_devuelve_no_encontrado():
    con = _base()
    assert db.obtener_tarea(con, "nada") == Err(ErrorNoEncontrado("tarea", "nada"))


def test_clave_foranea_invalida_devuelve_error_persistencia():
    con = _base()
    r = db.guardar_tarea(con, Tarea("t1", "no-existe", "A"))
    assert isinstance(r, Err) and isinstance(r.error, ErrorPersistencia)


def test_id_duplicado_devuelve_error_y_no_altera_datos():
    con = _base()
    db.guardar_integrante(con, Integrante("m1", "p1", "Tamara"))
    r = db.guardar_integrante(con, Integrante("m1", "p1", "Otro"))
    assert isinstance(r, Err)
    assert db.listar_integrantes(con, "p1").valor == [Integrante("m1", "p1", "Tamara")]


def test_rollback_no_deja_cambios_parciales():
    con = _base()
    try:
        with db.transaccion(con):
            con.execute("INSERT INTO integrantes VALUES ('m1','p1','Tamara')")
            con.execute("INSERT INTO integrantes VALUES ('m1','p1','Repetido')")  # falla
    except sqlite3.IntegrityError:
        pass
    assert db.listar_integrantes(con, "p1") == Ok([])
