# Contrato entre la shell (Jean Pierre) y el core (Tamara y Mike)

La shell **no implementa reglas**: llama a estas funciones puras. Si cambian un nombre o una firma,
avisen para ajustar `app/servicio.py` y `app/ui/componentes.py`.

Todas devuelven `Ok(valor)` / `Err(error)` de `app/domain/errores.py`, salvo donde se indica.

## `app/domain/` (compartido: acordar entre los tres)
- `modelos.py`: `Proyecto`, `Integrante`, `Entregable`, `Tarea` (dataclasses `frozen=True`), `ESTADOS`, `PRIORIDADES`.
- `errores.py`: `Ok`, `Err`, `ErrorValidacion`, `ErrorNoEncontrado`, `ErrorDuplicado`, `ErrorTransicion`, `ErrorPersistencia`.

## `app/core/edt.py` (Tamara)
| Función | Devuelve |
|---|---|
| `validar_texto(campo, valor, maximo=80)` | `Ok(texto_limpio)` / `Err(ErrorValidacion)` |
| `crear_integrante(existentes, proyecto_id, id_, nombre)` | `Ok(Integrante)` / `Err(...)` |
| `crear_entregable(existentes, proyecto_id, id_, nombre)` | `Ok(Entregable)` / `Err(...)` |
| `crear_tarea(entregables, tareas, integrantes, id_, entregable_id, nombre, prioridad, responsable_id)` | `Ok(Tarea)` / `Err(...)` |

Reglas acordadas: ids únicos; nombres únicos sin distinguir mayúsculas (tarea: dentro de su entregable);
el entregable debe existir; el responsable, si se indica, debe ser un integrante registrado;
lo que no existe → `ErrorNoEncontrado`.

## `app/core/kanban.py` (Mike)
| Función | Devuelve |
|---|---|
| `cambiar_estado(tarea, nuevo_estado)` | `Ok(Tarea)` / `Err(ErrorTransicion)` |
| `siguientes_estados(estado)` | tupla de estados permitidos (no es `Resultado`) |
| `filtrar_tareas(tareas, estado=None, responsable_id=None, prioridad=None)` | lista de `Tarea` (no es `Resultado`); `None` = sin filtrar por ese criterio |
