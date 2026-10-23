"""Ensamble e inicio de la aplicación (Imperative Shell).

FastAPI solo integra y sirve la app ReactPy; no hay endpoints REST propios.
Ejecutar con:  python -m app.main
"""
import logging

import uvicorn
from fastapi import FastAPI
from reactpy.backend.fastapi import configure

from app.adapters import sqlite as db
from app.ui.componentes import crear_componente


def crear_app(ruta_db: str = "gestor.db") -> FastAPI:
    con = db.conectar(ruta_db)
    app = FastAPI(title="Gestor de proyectos con EDT y Kanban")
    configure(app, crear_componente(con))
    return app


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    uvicorn.run(crear_app(), host="127.0.0.1", port=8000)
