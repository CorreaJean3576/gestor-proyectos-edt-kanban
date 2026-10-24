"""Interfaz ReactPy (Imperative Shell).

Los callbacks solo recogen datos del formulario y llaman a app.servicio;
las reglas del dominio viven en core/. El estado visual (campos, aviso) es local.
"""
from reactpy import component, html, use_state

from app.domain.errores import Err, Ok
from app.core.kanban import (filtrar_tareas, ordenar_tareas, pendientes_por_integrante,
                             siguientes_estados)
from app.domain.modelos import ESTADOS, PRIORIDADES
from app import servicio
from app.adapters import sqlite as db
from app.ui.mensajes import mensaje_para_usuario

ESTILO_AVISO = {
    "ok": {"background": "#e6f4ea", "color": "#1e4620", "padding": "8px", "margin": "8px 0"},
    "error": {"background": "#fdecea", "color": "#611a15", "padding": "8px", "margin": "8px 0"},
}


def _campo(etiqueta, valor, set_valor, tipo="text"):
    return html.label(
        {"style": {"display": "block", "margin": "4px 0"}},
        f"{etiqueta}: ",
        html.input({"type": tipo, "value": valor,
                    "on_change": lambda e: set_valor(e["target"]["value"])}),
    )


def _select(etiqueta, valor, set_valor, opciones):
    """opciones: lista de (valor, texto)."""
    return html.label(
        {"style": {"display": "block", "margin": "4px 0"}},
        f"{etiqueta}: ",
        html.select(
            {"value": valor, "on_change": lambda e: set_valor(e["target"]["value"])},
            [html.option({"value": v, "key": v or "_vacio"}, t) for v, t in opciones],
        ),
    )


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

        banner = (html.div({"style": ESTILO_AVISO[aviso[0]]}, aviso[1]) if aviso else "")

        match db.listar_proyectos(con):
            case Err(error):
                return html.p(mensaje_para_usuario(error))
            case Ok([]):
                return html.div(html.h1("Gestor de proyectos"), banner,
                                FormProyecto(ejecutar))
            case Ok([proyecto, *_]):
                pass

        match servicio.cargar_tablero(con, proyecto.id):
            case Err(error):
                return html.p(mensaje_para_usuario(error))
            case Ok(tablero):
                pass

        return html.div(
            {"style": {"fontFamily": "sans-serif", "maxWidth": "1100px", "margin": "auto"}},
            html.h1(f"Proyecto: {proyecto.nombre}"),
            html.p(proyecto.descripcion) if proyecto.descripcion else "",
            banner,
            html.div({"style": {"display": "flex", "gap": "24px", "flexWrap": "wrap"}},
                     SeccionIntegrantes(proyecto.id, tablero, ejecutar),
                     SeccionEdt(proyecto.id, tablero, ejecutar)),
            html.h2("Tablero Kanban"),
            Kanban(tablero, ejecutar),
        )

    @component
    def FormProyecto(ejecutar):
        id_, set_id = use_state("")
        nombre, set_nombre = use_state("")
        desc, set_desc = use_state("")
        return html.div(
            html.h2("Crear proyecto"),
            _campo("Id", id_, set_id), _campo("Nombre", nombre, set_nombre),
            _campo("Descripción", desc, set_desc),
            html.button({"on_click": lambda e: ejecutar(
                servicio.crear_proyecto(con, id_, nombre, desc), "Proyecto creado.")}, "Crear"),
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

        return html.section(
            {"style": {"minWidth": "260px"}},
            html.h2("Integrantes"),
            html.ul([html.li({"key": m.id}, f"{m.nombre} ({m.id}) — {pendientes[m.id]} pendientes")
                     for m in tablero["integrantes"]])
            if tablero["integrantes"] else html.p("Aún no hay integrantes."),
            _campo("Id", id_, set_id), _campo("Nombre", nombre, set_nombre),
            html.button({"on_click": agregar}, "Agregar integrante"),
        )

    @component
    def SeccionEdt(proyecto_id, tablero, ejecutar):
        e_id, set_e_id = use_state("")
        e_nombre, set_e_nombre = use_state("")
        t_id, set_t_id = use_state("")
        t_nombre, set_t_nombre = use_state("")
        t_entregable, set_t_entregable = use_state("")
        t_prioridad, set_t_prioridad = use_state("Media")
        t_resp, set_t_resp = use_state("")

        entregables, tareas = tablero["entregables"], tablero["tareas"]
        entregable_sel = t_entregable or (entregables[0].id if entregables else "")

        def agregar_entregable(_):
            r = ejecutar(servicio.crear_entregable(con, proyecto_id, e_id, e_nombre),
                         "Entregable creado.")
            if isinstance(r, Ok):
                set_e_id(""); set_e_nombre("")

        def agregar_tarea(_):
            r = ejecutar(servicio.crear_tarea(con, proyecto_id, t_id, entregable_sel, t_nombre,
                                              t_prioridad, t_resp or None), "Tarea creada.")
            if isinstance(r, Ok):
                set_t_id(""); set_t_nombre("")

        arbol = [
            html.li({"key": e.id}, html.strong(f"{e.nombre} ({e.id})"),
                    html.ul([html.li({"key": t.id}, f"{t.nombre} — {t.prioridad} — {t.estado}")
                             for t in tareas if t.entregable_id == e.id]))
            for e in entregables
        ]
        nombres = {m.id: m.nombre for m in tablero["integrantes"]}

        return html.section(
            {"style": {"flex": "1", "minWidth": "320px"}},
            html.h2("EDT / WBS"),
            html.ul(arbol) if arbol else html.p("Aún no hay entregables."),
            html.h3("Nuevo entregable"),
            _campo("Id", e_id, set_e_id), _campo("Nombre", e_nombre, set_e_nombre),
            html.button({"on_click": agregar_entregable}, "Agregar entregable"),
            html.h3("Nueva tarea"),
            _campo("Id", t_id, set_t_id), _campo("Nombre", t_nombre, set_t_nombre),
            _select("Entregable", entregable_sel, set_t_entregable,
                    [(e.id, e.nombre) for e in entregables] or [("", "(crea un entregable)")]),
            _select("Prioridad", t_prioridad, set_t_prioridad, [(p, p) for p in PRIORIDADES]),
            _select("Responsable", t_resp, set_t_resp,
                    [("", "(sin responsable)")] + [(i, n) for i, n in nombres.items()]),
            html.button({"on_click": agregar_tarea}, "Agregar tarea"),
        )

    @component
    def Kanban(tablero, ejecutar):
        f_estado, set_f_estado = use_state("")
        f_resp, set_f_resp = use_state("")
        f_prio, set_f_prio = use_state("")

        nombres = {m.id: m.nombre for m in tablero["integrantes"]}
        entregables = {e.id: e.nombre for e in tablero["entregables"]}

        # La regla de filtrado es del core (función pura); aquí solo se pasan los criterios.
        visibles = ordenar_tareas(filtrar_tareas(
            tablero["tareas"],
            estado=f_estado or None,
            responsable_id=f_resp or None,
            prioridad=f_prio or None,
        ))

        def limpiar(_):
            set_f_estado(""); set_f_resp(""); set_f_prio("")

        filtros = html.div(
            {"style": {"display": "flex", "gap": "16px", "flexWrap": "wrap", "alignItems": "center"}},
            _select("Estado", f_estado, set_f_estado, [("", "(todos)")] + [(e, e) for e in ESTADOS]),
            _select("Responsable", f_resp, set_f_resp,
                    [("", "(todos)")] + [(i, n) for i, n in nombres.items()]),
            _select("Prioridad", f_prio, set_f_prio, [("", "(todas)")] + [(p, p) for p in PRIORIDADES]),
            html.button({"on_click": limpiar}, "Limpiar filtros"),
        )

        def tarjeta(t):
            botones = [
                html.button({"key": destino,
                             "on_click": lambda e, tid=t.id, d=destino: ejecutar(
                                 servicio.mover_tarea(con, tid, d), f"Tarea movida a «{d}».")},
                            f"→ {destino}")
                for destino in siguientes_estados(t.estado)
            ]
            return html.div(
                {"key": t.id, "style": {"border": "1px solid #ccc", "borderRadius": "6px",
                                        "padding": "8px", "margin": "6px 0"}},
                html.strong(t.nombre),
                html.div(f"{entregables.get(t.entregable_id, '?')} · {t.prioridad}"),
                html.div(f"Responsable: {nombres.get(t.responsable_id, 'sin asignar')}"),
                html.div(botones),
            )

        columnas = []
        for estado in ESTADOS:
            tareas = [t for t in visibles if t.estado == estado]
            columnas.append(html.div(
                {"key": estado, "style": {"flex": "1", "minWidth": "200px", "background": "#f6f6f6",
                                          "padding": "8px", "borderRadius": "6px"}},
                html.h3(f"{estado} ({len(tareas)})"),
                [tarjeta(t) for t in tareas] if tareas else html.p("Sin tareas."),
            ))

        if not tablero["tareas"]:
            aviso_vacio = html.p("Aún no hay tareas. Crea un entregable y agrega tareas.")
        elif not visibles:
            aviso_vacio = html.p({"style": {"fontWeight": "bold"}},
                                 "Ninguna tarea coincide con los filtros seleccionados.")
        else:
            aviso_vacio = ""

        return html.div(filtros, aviso_vacio,
                        html.div({"style": {"display": "flex", "gap": "12px", "flexWrap": "wrap"}}, columnas))

    return App
