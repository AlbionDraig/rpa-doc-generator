---
agent: 'agent'
description: 'Crea un endpoint backend completo con arquitectura limpia'
tools: [read, search, edit, execute]
argument-hint: "Recurso y método (Ej: GET /api/transactions — lista paginada del usuario autenticado)"
---

Crea un endpoint backend completo respetando la arquitectura del proyecto.

#file:./_engineering-principles.md

Nombre del recurso: ${input:resource:Ej: transaction, account, budget}
Framework backend (si se conoce): ${input:backend:fastapi | express | nestjs | django | flask | spring | rails | auto}
Método HTTP: ${input:method:GET | POST | PUT | PATCH | DELETE}
Descripción de qué hace: ${input:description:Ej: Retorna todas las transacciones del usuario autenticado}
¿Requiere autenticación?: ${input:auth:sí | no}

Genera o actualiza (según convención del repo):

1. Capa de entrada (controller/router/handler).
2. Contratos de entrada/salida (DTO/schema/request/response).
3. Caso de uso/service de aplicación.
4. Integración con repositorio/infra sin filtrar detalles al cliente.
5. Registro del endpoint en módulo de rutas principal.

Convenciones del proyecto:
- Validación de entrada y salida tipada.
- Manejo explícito de errores de dominio e infraestructura.
- No retornar entidades de persistencia directamente.
- Mantener lógica de negocio fuera del controller/router.
- Añadir pruebas mínimas del endpoint (caso feliz y error principal).
