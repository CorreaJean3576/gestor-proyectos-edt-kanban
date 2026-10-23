"""Modelo de datos compartido (inmutable). CONTRATO acordado entre los tres."""
from dataclasses import dataclass
from typing import Optional

PENDIENTE = "Pendiente"
EN_PROGRESO = "En progreso"
EN_REVISION = "En revisión"
TERMINADA = "Terminada"
ESTADOS = (PENDIENTE, EN_PROGRESO, EN_REVISION, TERMINADA)

PRIORIDADES = ("Baja", "Media", "Alta")


@dataclass(frozen=True)
class Proyecto:
    id: str
    nombre: str
    descripcion: str = ""


@dataclass(frozen=True)
class Integrante:
    id: str
    proyecto_id: str
    nombre: str


@dataclass(frozen=True)
class Entregable:
    id: str
    proyecto_id: str
    nombre: str


@dataclass(frozen=True)
class Tarea:
    id: str
    entregable_id: str
    nombre: str
    prioridad: str = "Media"
    estado: str = PENDIENTE
    responsable_id: Optional[str] = None
