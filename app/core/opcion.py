"""Ausencia de valor explícita: Some(valor) si existe, Nothing() si no existe"""
from dataclasses import dataclass
from typing import Generic, TypeVar, Union

T = TypeVar("T")


@dataclass(frozen=True)
class Some(Generic[T]):
    valor: T


@dataclass(frozen=True)
class Nothing:
    pass


Option = Union[Some[T], Nothing]