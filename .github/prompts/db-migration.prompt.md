---
agent: 'agent'
description: 'Genera y ejecuta una migración de base de datos'
tools: [read, edit, execute, search]
argument-hint: "Describe el cambio de esquema (Ej: agregar columna currency a transactions)"
---

Genera y aplica una migración de base de datos de forma segura.

#file:./_engineering-principles.md

Descripción del cambio: ${input:change:Ej: agregar columna currency a tabla transactions}
Herramienta de migración (si se conoce): ${input:migration_tool:alembic | prisma | knex | typeorm | django | liquibase | flyway | auto}

Flujo:
1. Detecta la herramienta del proyecto si está en auto.
2. Actualiza modelos/schemas antes de generar la migración.
3. Genera migración con mensaje claro y trazable.
4. Revisa manualmente:
- `up`/`down` o `upgrade`/`downgrade` correctos.
- Cambios destructivos protegidos o explícitos.
- Índices/constraints esperados.
- Backfill o defaults cuando haga falta.
5. Ejecuta la migración en entorno local/test.
6. Verifica estado final y consistencia de esquema.

Reglas:
- No aplicar migraciones con rollback incompleto.
- Si hay riesgo de pérdida de datos, documenta plan de mitigación.
- Si el proyecto requiere seed/backfill, créalo en el mismo cambio.
