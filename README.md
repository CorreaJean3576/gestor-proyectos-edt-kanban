# Gestor de proyectos con EDT y Kanban

Aplicación web local para crear un proyecto, descomponerlo en entregables y tareas (EDT/WBS),
asignar responsables y seguir el trabajo en un tablero Kanban.
Programación Funcional · Grupo 04 · Tamara, Mike y Jean Pierre.

## Tecnologías
ReactPy (interfaz) · FastAPI (integra y sirve la app, **sin API REST propia**) · SQLite · Functional Core / Imperative Shell.

## Instalación y ejecución
```bash
git clone https://github.com/CorreaJean3576/gestor-proyectos-edt-kanban.git
cd gestor-proyectos-edt-kanban
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m app.main
```
Abrir <http://127.0.0.1:8000>. La base `gestor.db` se crea sola en la primera ejecución.

Pruebas: `pytest`

## Estructura
```
app/
  domain/      Tipos inmutables y errores (contrato compartido)
  core/        Functional Core: reglas y transformaciones puras (Tamara y Mike)
  adapters/    sqlite.py: persistencia SQLite (Imperative Shell)
  ui/          componentes.py (ReactPy) y mensajes.py (errores -> texto para el usuario)
  servicio.py  Casos de uso de la shell: leer -> core -> guardar
  decoradores.py  Decorador de registro/medición de duración
  main.py      Ensamble e inicio (FastAPI + ReactPy)
tests/
  unit/        Pruebas del núcleo funcional (Tamara y Mike)
  integration/ Adaptador SQLite, decorador y flujo shell+core
```

## Arquitectura
Flujo de cada acción: **evento ReactPy → la shell lee de SQLite → función pura del core → la shell guarda
en una transacción → se actualiza la interfaz**. El core devuelve `Ok`/`Err`; la shell traduce los errores
a mensajes. El core no importa ReactPy, FastAPI ni `sqlite3`. El contrato entre ambos está en `CONTRATOS_CORE.md`.

## Evidencias por tema

### Jean Pierre
| Concepto | Archivo y función |
|---|---|
| Integración ReactPy/FastAPI | `app/main.py::crear_app`, `app/ui/componentes.py::crear_componente` |
| Adaptador SQLite y transacciones | `app/adapters/sqlite.py` (`conectar`, `transaccion`, `guardar_*`, `listar_*`) |
| Efectos fuera del core | `app/adapters/sqlite.py`, `app/servicio.py` |
| Decorador | `app/decoradores.py::medir_duracion` (aplicado en `app/adapters/sqlite.py`) |
| Errores hacia la UI | `app/ui/mensajes.py::mensaje_para_usuario` (`match/case`) |
| Filtros y estados vacíos en la UI | `app/ui/componentes.py::Kanban` (usa `filtrar_tareas` del core) |
| Pruebas | `tests/integration/test_sqlite.py`, `test_decoradores.py`, `test_servicio.py` |

### Tamara
_(archivo/función de EDT, validaciones, inmutabilidad, ausencia de valor, pruebas del núcleo)_

### Mike
| Concepto | Archivo y función |
|---|---|
| Reglas de transición | `app/core/kanban.py::TRANSICIONES`, `siguientes_estados`, `cambiar_estado` (devuelve `Ok`/`Err(ErrorTransicion)`) |
| Pattern matching | `app/core/kanban.py::aplicar_comando` (`match/case` sobre `CambiarEstado` y `CambiarPrioridad`) |
| Funciones de orden superior | `app/core/kanban.py::combinar` (recibe criterios y devuelve otro criterio), `filtrar_tareas` |
| Lambdas | `ordenar_tareas` (clave de orden) y `por_*`; se usa función con nombre cuando hay reglas (`cambiar_estado`, `aplicar_comando`) |
| Closures | `app/core/kanban.py::por_estado`, `por_responsable`, `por_prioridad` (capturan un criterio inmutable) |
| Ausencia de valor | `app/core/kanban.py::buscar_tarea` (devuelve `None` si no existe) y `filtrar_tareas` (`None` = sin filtro) |
| Inmutabilidad | `cambiar_estado` y `aplicar_comando` usan `dataclasses.replace`: la tarea original no cambia |
| Consultas del avance | `ordenar_tareas`, `pendientes_por_integrante` |
| Pruebas | `tests/unit/test_kanban.py` |
