"""Errores esperados del dominio y el tipo Resultado (manejo funcional de errores).

CONTRATO COMPARTIDO: lo usan app/core (Tamara/Mike) y la shell (Jean Pierre).
"""
from dataclasses import dataclass
from typing import Generic, TypeVar, Union

T = TypeVar("T")


@dataclass(frozen=True)
class ErrorValidacion:
    campo: str
    mensaje: str


@dataclass(frozen=True)
class ErrorNoEncontrado:
    entidad: str
    id: str


@dataclass(frozen=True)
class ErrorTransicion:
    origen: str
    destino: str


@dataclass(frozen=True)
class ErrorDuplicado:
    entidad: str
    campo: str
    valor: str


@dataclass(frozen=True)
class ErrorPersistencia:
    detalle: str


Error = Union[ErrorValidacion, ErrorNoEncontrado, ErrorTransicion, ErrorDuplicado, ErrorPersistencia]


@dataclass(frozen=True)
class Ok(Generic[T]):
    valor: T


@dataclass(frozen=True)
class Err:
    error: Error


Resultado = Union[Ok[T], Err]
