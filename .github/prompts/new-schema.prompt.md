---
agent: 'agent'
description: 'Crea schemas/DTOs para un recurso'
tools: [read, search, edit]
argument-hint: "Nombre del recurso y campos principales (Ej: Transaction — amount, category, date)"
---

Crea los schemas/DTOs/contratos para el recurso indicado.

#file:./_engineering-principles.md

Nombre del recurso: ${input:resource:Ej: Transaction, User, Budget}
Campos del modelo: ${input:fields:Ej: amount: float, category: str, date: datetime, description: str opcional}
Tecnología de schema (si se conoce): ${input:schema_tech:pydantic | zod | joi | marshmallow | class-validator | auto}
¿Tiene modelo en persistencia?: ${input:has_db_model:sí | no}

Genera contratos con esta estructura (adaptada al stack):

1. `{Resource}Base` — campos comunes compartidos
2. `{Resource}Create` — entrada para creación
3. `{Resource}Update` — entrada parcial para actualización
4. `{Resource}Response` — salida pública de API/capa de aplicación
5. `{Resource}ListResponse` — lista paginada o agregada (si aplica)

Convenciones:
- Tipos estrictos y validaciones de dominio.
- Campos opcionales solo donde negocio lo permita.
- No exponer campos internos/sensibles en responses.
- Incluir ejemplos/documentación del contrato cuando el stack lo soporte.
