"""Interfaz ReactPy (Imperative Shell).

Los callbacks solo recogen datos del formulario y llaman a app.servicio;
las reglas del dominio viven en app/core. Aquí solo hay presentación.
"""
from reactpy import component, html, use_state

from app import servicio
from app.core.kanban import (filtrar_tareas, ordenar_tareas, pendientes_por_integrante,
                             siguientes_estados)
from app.domain.errores import Err, Ok
from app.domain.modelos import ESTADOS, PRIORIDADES
from app.adapters import sqlite as db
from app.ui.mensajes import mensaje_para_usuario

CSS = """
:root{--bg:#f4f6fb;--card:#fff;--txt:#1d2433;--mut:#66708a;--bor:#e1e5ef;--pri:#4f46e5;--pri-t:#fff;
--ok-b:#e7f6ec;--ok-t:#14532d;--er-b:#fdecec;--er-t:#7f1d1d;--col:#eef1f8}
@media (prefers-color-scheme:dark){:root{--bg:#0f1420;--card:#171e2e;--txt:#e7eaf3;--mut:#9aa4bd;--bor:#2a3347;
--pri:#818cf8;--pri-t:#0f1420;--ok-b:#12301f;--ok-t:#a7f3c0;--er-b:#3a1717;--er-t:#fecaca;--col:#121929}}
*{box-sizing:border-box}
.app{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--txt);
min-height:100vh;padding:24px}
.wrap{max-width:1200px;margin:0 auto}
.head h1{margin:0 0 4px;font-size:26px}.head p{margin:0;color:var(--mut)}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:18px 0}
.stat{background:var(--card);border:1px solid var(--bor);border-radius:12px;padding:12px 14px}
.stat b{display:block;font-size:24px}.stat span{color:var(--mut);font-size:13px}
.barra{height:8px;background:var(--bor);border-radius:99px;overflow:hidden;margin-top:8px}
.barra div{height:100%;background:var(--pri)}
.aviso{padding:10px 14px;border-radius:10px;margin:10px 0;font-weight:500}
.aviso.ok{background:var(--ok-b);color:var(--ok-t)}.aviso.error{background:var(--er-b);color:var(--er-t)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px;margin-bottom:8px}
.card{background:var(--card);border:1px solid var(--bor);border-radius:14px;padding:16px}
.card h2{margin:0 0 10px;font-size:17px}.card h3{margin:16px 0 6px;font-size:14px;color:var(--mut)}
.campo{display:block;margin:8px 0;font-size:13px;color:var(--mut)}
.campo input,.campo select{display:block;width:100%;margin-top:3px;padding:8px 10px;font-size:14px;
border:1px solid var(--bor);border-radius:8px;background:var(--bg);color:var(--txt)}
.btn{cursor:pointer;border:0;border-radius:8px;padding:8px 12px;font-size:13px;font-weight:600;
background:var(--pri);color:var(--pri-t)}
.btn.sec{background:transparent;color:var(--txt);border:1px solid var(--bor)}
.btn.mini{padding:4px 8px;font-size:12px}
.vacio{color:var(--mut);font-style:italic;margin:6px 0}
.lista{list-style:none;margin:0;padding:0}
.lista li{display:flex;align-items:center;gap:10px;padding:6px 0;border-bottom:1px solid var(--bor)}
.lista li:last-child{border-bottom:0}
.avatar{width:28px;height:28px;border-radius:50%;background:var(--pri);color:var(--pri-t);display:inline-flex;
align-items:center;justify-content:center;font-size:11px;font-weight:700;flex:none}
.sub{color:var(--mut);font-size:12px}
.entregable{margin:0 0 10px}.entregable>strong{display:block;margin-bottom:4px}
.tarea-mini{display:flex;justify-content:space-between;gap:8px;font-size:13px;padding:3px 0 3px 12px;
border-left:3px solid var(--bor)}
.badge{display:inline-block;border-radius:99px;padding:1px 8px;font-size:11px;font-weight:700}
.prio-alta{background:#fee2e2;color:#991b1b}.prio-media{background:#fef3c7;color:#92400e}
.prio-baja{background:#dcfce7;color:#166534}
.filtros{display:flex;flex-wrap:wrap;gap:12px;align-items:flex-end;margin-bottom:12px}
.filtros .campo{margin:0;min-width:150px}
.tablero{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px}
.columna{background:var(--col);border-radius:14px;padding:10px;border-top:4px solid var(--bor)}
.columna h3{margin:2px 4px 8px;font-size:14px;display:flex;justify-content:space-between}
.col-pendiente{border-top-color:#94a3b8}.col-progreso{border-top-color:#3b82f6}
.col-revision{border-top-color:#f59e0b}.col-terminada{border-top-color:#22c55e}
.tarjeta{background:var(--card);border:1px solid var(--bor);border-radius:10px;padding:10px;margin-bottom:8px}
.tarjeta strong{display:block;margin:4px 0}
.resp{display:flex;align-items:center;gap:6px;margin:6px 0;font-size:12px;color:var(--mut)}
.acciones{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px}
"""

CLASE_ESTADO = {"Pendiente": "col-pendiente", "En progreso": "col-progreso",
                "En revisión": "col-revision", "Terminada": "col-terminada"}


# ---------------- ayudas de presentación (sin reglas del dominio) ----------------
def _iniciales(nombre):
    partes = (nombre or "?").split()
    return "".join(p[0] for p in partes[:2]).upper() or "?"


def _badge(prioridad):
    return html.span({"class_name": f"badge prio-{prioridad.lower()}"}, prioridad)


def _avatar(nombre):
    return html.span({"class_name": "avatar"}, _iniciales(nombre))


def _campo(etiqueta, valor, set_valor, placeholder=""):
    return html.label(
        {"class_name": "campo"}, etiqueta,
        html.input({"type": "text", "value": valor, "placeholder": placeholder,
                    "on_change": lambda e: set_valor(e["target"]["value"])}),
    )


def _select(etiqueta, valor, set_valor, opciones):
    """opciones: lista de (valor, texto)."""
    return html.label(
        {"class_name": "campo"}, etiqueta,
        html.select(
            {"value": valor, "on_change": lambda e: set_valor(e["target"]["value"])},
            [html.option({"value": v, "key": v or "_vacio"}, t) for v, t in opciones],
        ),
    )


def _estadisticas(tareas):
    total = len(tareas)
    por_estado = {e: sum(1 for t in tareas if t.estado == e) for e in ESTADOS}
    avance = round(100 * por_estado["Terminada"] / total) if total else 0
    return total, por_estado, avance


def crear_componente(con):
    """Devuelve el componente raíz con la conexión SQLite capturada (closure)."""

    @component
    def App():
        version, set_version = use_state(0)
        aviso, set_aviso = use_state(None)  # (tipo, texto) | None

        def ejecutar(resultado, texto_ok):
            match resultado:
                case Ok(_):
                    set_aviso(("ok", texto_ok))
                case Err(error):
                    set_aviso(("error", mensaje_para_usuario(error)))
            set_version(version + 1)
            return resultado

        banner = html.div({"class_name": f"aviso {aviso[0]}"}, aviso[1]) if aviso else ""

        match db.listar_proyectos(con):
            case Err(error):
                return html.div({"class_name": "app"}, html.style(CSS),
                                html.div({"class_name": "aviso error"}, mensaje_para_usuario(error)))
            case Ok([]):
                return html.div({"class_name": "app"}, html.style(CSS),
                                html.div({"class_name": "wrap"},
                                         html.div({"class_name": "head"}, html.h1("Gestor de proyectos"),
                                                  html.p("Crea tu primer proyecto para empezar.")),
                                         banner, FormProyecto(ejecutar)))
            case Ok([proyecto, *_]):
                pass

        match servicio.cargar_tablero(con, proyecto.id):
            case Err(error):
                return html.div({"class_name": "app"}, html.style(CSS),
                                html.div({"class_name": "aviso error"}, mensaje_para_usuario(error)))
            case Ok(tablero):
                pass

        total, por_estado, avance = _estadisticas(tablero["tareas"])
        stats = html.div(
            {"class_name": "stats"},
            html.div({"class_name": "stat"}, html.b(f"{avance}%"), html.span("Avance"),
                     html.div({"class_name": "barra"}, html.div({"style": {"width": f"{avance}%"}}))),
            html.div({"class_name": "stat"}, html.b(str(total)), html.span("Tareas")),
            [html.div({"class_name": "stat", "key": e}, html.b(str(n)), html.span(e))
             for e, n in por_estado.items()],
        )

        return html.div(
            {"class_name": "app"}, html.style(CSS),
            html.div(
                {"class_name": "wrap"},
                html.div({"class_name": "head"}, html.h1(proyecto.nombre),
                         html.p(proyecto.descripcion or "Sin descripción")),
                stats, banner,
                html.div({"class_name": "grid"},
                         SeccionIntegrantes(proyecto.id, tablero, ejecutar),
                         PanelEdt(proyecto.id, tablero, ejecutar),
                         FormTarea(proyecto.id, tablero, ejecutar)),
                html.div({"class_name": "card"}, html.h2("Tablero Kanban"), Kanban(tablero, ejecutar)),
            ),
        )

    @component
    def FormProyecto(ejecutar):
        id_, set_id = use_state("")
        nombre, set_nombre = use_state("")
        desc, set_desc = use_state("")
        return html.div(
            {"class_name": "card"}, html.h2("Crear proyecto"),
            _campo("Id", id_, set_id, "p1"), _campo("Nombre", nombre, set_nombre),
            _campo("Descripción", desc, set_desc),
            html.button({"class_name": "btn", "on_click": lambda e: ejecutar(
                servicio.crear_proyecto(con, id_, nombre, desc), "Proyecto creado.")}, "Crear proyecto"),
        )

    @component
    def SeccionIntegrantes(proyecto_id, tablero, ejecutar):
        id_, set_id = use_state("")
        nombre, set_nombre = use_state("")

        def agregar(_):
            r = ejecutar(servicio.registrar_integrante(con, proyecto_id, id_, nombre),
                         "Integrante registrado.")
            if isinstance(r, Ok):
                set_id(""); set_nombre("")

        pendientes = pendientes_por_integrante(tablero["tareas"], tablero["integrantes"])
        integrantes = tablero["integrantes"]
        return html.section(
            {"class_name": "card"}, html.h2("Equipo"),
            html.ul({"class_name": "lista"}, [
                html.li({"key": m.id}, _avatar(m.nombre),
                        html.div(html.div(m.nombre),
                                 html.div({"class_name": "sub"}, f"{m.id} · {pendientes[m.id]} pendientes")))
                for m in integrantes])
            if integrantes else html.p({"class_name": "vacio"}, "Aún no hay integrantes."),
            html.h3("Nuevo integrante"),
            _campo("Id", id_, set_id, "m1"), _campo("Nombre", nombre, set_nombre),
            html.button({"class_name": "btn", "on_click": agregar}, "Agregar integrante"),
        )

    @component
    def PanelEdt(proyecto_id, tablero, ejecutar):
        e_id, set_e_id = use_state("")
        e_nombre, set_e_nombre = use_state("")
        entregables, tareas = tablero["entregables"], ordenar_tareas(tablero["tareas"])

        def agregar(_):
            r = ejecutar(servicio.crear_entregable(con, proyecto_id, e_id, e_nombre), "Entregable creado.")
            if isinstance(r, Ok):
                set_e_id(""); set_e_nombre("")

        arbol = [
            html.div(
                {"class_name": "entregable", "key": e.id},
                html.strong(f"{e.nombre} ", html.span({"class_name": "sub"}, f"({e.id})")),
                [html.div({"class_name": "tarea-mini", "key": t.id},
                          html.span(t.nombre), html.span(_badge(t.prioridad), f" {t.estado}"))
                 for t in tareas if t.entregable_id == e.id]
                or html.div({"class_name": "tarea-mini sub"}, "Sin tareas"),
            )
            for e in entregables
        ]
        return html.section(
            {"class_name": "card"}, html.h2("Estructura del trabajo (EDT)"),
            arbol or html.p({"class_name": "vacio"}, "Aún no hay entregables."),
            html.h3("Nuevo entregable"),
            _campo("Id", e_id, set_e_id, "e1"), _campo("Nombre", e_nombre, set_e_nombre),
            html.button({"class_name": "btn", "on_click": agregar}, "Agregar entregable"),
        )

    @component
    def FormTarea(proyecto_id, tablero, ejecutar):
        t_id, set_t_id = use_state("")
        t_nombre, set_t_nombre = use_state("")
        t_entregable, set_t_entregable = use_state("")
        t_prioridad, set_t_prioridad = use_state("Media")
        t_resp, set_t_resp = use_state("")
        entregables = tablero["entregables"]
        entregable_sel = t_entregable or (entregables[0].id if entregables else "")

        def agregar(_):
            r = ejecutar(servicio.crear_tarea(con, proyecto_id, t_id, entregable_sel, t_nombre,
                                              t_prioridad, t_resp or None), "Tarea creada.")
            if isinstance(r, Ok):
                set_t_id(""); set_t_nombre("")

        return html.section(
            {"class_name": "card"}, html.h2("Nueva tarea"),
            _campo("Id", t_id, set_t_id, "t1"), _campo("Nombre", t_nombre, set_t_nombre),
            _select("Entregable", entregable_sel, set_t_entregable,
                    [(e.id, e.nombre) for e in entregables] or [("", "(crea un entregable)")]),
            _select("Prioridad", t_prioridad, set_t_prioridad, [(p, p) for p in PRIORIDADES]),
            _select("Responsable", t_resp, set_t_resp,
                    [("", "(sin responsable)")] + [(m.id, m.nombre) for m in tablero["integrantes"]]),
            html.button({"class_name": "btn", "on_click": agregar}, "Agregar tarea"),
        )

    @component
    def Kanban(tablero, ejecutar):
        f_estado, set_f_estado = use_state("")
        f_resp, set_f_resp = use_state("")
        f_prio, set_f_prio = use_state("")

        nombres = {m.id: m.nombre for m in tablero["integrantes"]}
        entregables = {e.id: e.nombre for e in tablero["entregables"]}

        # La regla de filtrado y de orden es del core (funciones puras).
        visibles = ordenar_tareas(filtrar_tareas(
            tablero["tareas"], estado=f_estado or None,
            responsable_id=f_resp or None, prioridad=f_prio or None))

        def limpiar(_):
            set_f_estado(""); set_f_resp(""); set_f_prio("")

        filtros = html.div(
            {"class_name": "filtros"},
            _select("Estado", f_estado, set_f_estado, [("", "Todos")] + [(e, e) for e in ESTADOS]),
            _select("Responsable", f_resp, set_f_resp, [("", "Todos")] + list(nombres.items())),
            _select("Prioridad", f_prio, set_f_prio, [("", "Todas")] + [(p, p) for p in PRIORIDADES]),
            html.button({"class_name": "btn sec", "on_click": limpiar}, "Limpiar filtros"),
        )

        def tarjeta(t):
            botones = [
                html.button(
                    {"key": destino, "class_name": "btn sec mini",
                     "on_click": lambda e, tid=t.id, d=destino: ejecutar(
                         servicio.mover_tarea(con, tid, d), f"Tarea movida a «{d}».")},
                    f"{'→' if ESTADOS.index(destino) > ESTADOS.index(t.estado) else '←'} {destino}")
                for destino in siguientes_estados(t.estado)
            ]
            responsable = nombres.get(t.responsable_id)
            return html.div(
                {"key": t.id, "class_name": "tarjeta"},
                _badge(t.prioridad), html.strong(t.nombre),
                html.div({"class_name": "sub"}, entregables.get(t.entregable_id, "?")),
                html.div({"class_name": "resp"},
                         _avatar(responsable) if responsable else "",
                         responsable or "Sin asignar"),
                html.div({"class_name": "acciones"}, botones),
            )

        columnas = []
        for estado in ESTADOS:
            tareas = [t for t in visibles if t.estado == estado]
            columnas.append(html.div(
                {"key": estado, "class_name": f"columna {CLASE_ESTADO[estado]}"},
                html.h3(html.span(estado), html.span({"class_name": "sub"}, str(len(tareas)))),
                [tarjeta(t) for t in tareas] if tareas else html.p({"class_name": "vacio"}, "Sin tareas"),
            ))

        if not tablero["tareas"]:
            vacio = html.p({"class_name": "vacio"}, "Aún no hay tareas. Crea un entregable y agrega tareas.")
        elif not visibles:
            vacio = html.p({"class_name": "aviso error"}, "Ninguna tarea coincide con los filtros seleccionados.")
        else:
            vacio = ""
        return html.div(filtros, vacio, html.div({"class_name": "tablero"}, columnas))

    return App
