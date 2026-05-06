---
agent: 'agent'
description: 'Crea una pantalla/página frontend completa'
tools: [read, search, edit]
argument-hint: "Nombre y ruta (Ej: TransactionsPage en /transactions)"
---

Crea una página/pantalla completa siguiendo la arquitectura del frontend.

#file:./_engineering-principles.md

Framework (si se conoce): ${input:framework:react | vue | svelte | angular | auto}
Nombre de la página: ${input:name:Ej: TransactionsPage, BudgetPage, UsersPage}
Ruta en el router: ${input:route:Ej: /transactions, /budget}
Qué muestra: ${input:description:Ej: Lista de transacciones con filtros por fecha y categoría}
Endpoints que consume: ${input:endpoints:Ej: GET /api/transactions, GET /api/categories}

Genera los siguientes archivos:

1. Página principal con layout y composición de UI.
2. Hook/composable para fetching/orquestación de datos.
3. Tipos/contratos específicos de la pantalla.
4. Registro de ruta en router principal.

Convenciones:
- Mostrar estados loading/error/empty de forma explícita.
- Separar lógica de negocio y acceso a datos de la capa visual.
- Mantener componentes pequeños y reutilizables.
- Aplicar accesibilidad y consistencia de diseño.
