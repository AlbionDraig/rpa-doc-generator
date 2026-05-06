---
agent: 'agent'
description: 'Documenta un endpoint, módulo o contrato API'
tools: [read, search, edit]
argument-hint: "Archivo o módulo a documentar (Ej: app/api/v1/transactions.py)"
---

Documenta el archivo activo o el módulo indicado.

#file:./_engineering-principles.md

Archivo o módulo a documentar: ${input:file:Ej: src/api/users.ts, app/controllers/order.py o "archivo activo"}

Genera documentación en niveles:

1. Código
- Docstring/comentario de módulo.
- Docstring en funciones/clases públicas: propósito, entradas, salida, errores.

2. Contrato API (si aplica)
- Documentar rutas, método, auth, request/response, errores y ejemplos.
- Si usa OpenAPI/Swagger, completar summary/description/responses/tags/examples.

3. Documentación de proyecto
- Actualiza README o docs técnicas con tabla de endpoints/operaciones.
- Incluir decisiones importantes y supuestos.

No cambies la lógica funcional. Si hay documentación desactualizada, corrígela para que refleje el estado real del código.
