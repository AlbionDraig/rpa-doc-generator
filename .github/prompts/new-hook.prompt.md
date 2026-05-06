---
agent: 'agent'
description: 'Crea una abstracción de datos para frontend (hook/composable)'
tools: [read, search, edit]
argument-hint: "Nombre y endpoint (Ej: useTransactions — GET /api/transactions)"
---

Crea un hook/composable para acceso a datos en frontend.

#file:./_engineering-principles.md

Framework (si se conoce): ${input:framework:react | vue | svelte | auto}
Nombre: ${input:name:Ej: useTransactions, useCreateBudget, useUsers}
Tipo de operación: ${input:type:query | mutation | ambos}
Endpoint: ${input:endpoint:Ej: GET /api/transactions?period=month}
Parámetros que recibe: ${input:params:Ej: period: string, category?: string | ninguno}

Genera archivo en la carpeta de hooks/composables del proyecto con:

1. Tipos/contratos de params y response.
2. Integración con librería de datos que use el proyecto (React Query, SWR, Apollo, etc.).
3. Keys/identificadores de caché deterministas.
4. Política de caché/reintentos coherente al dato.
5. Mapeo de errores a mensajes de dominio legibles.
6. Invalidación/refetch en mutaciones cuando corresponda.

Convenciones:
- Reusar cliente HTTP y capa de transporte existente.
- No hacer requests directos dentro de componentes visuales.
- Exportar tipos reutilizables.
- Evitar duplicación de lógica entre hooks similares.
