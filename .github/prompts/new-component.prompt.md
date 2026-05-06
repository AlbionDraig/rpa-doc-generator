---
agent: 'agent'
description: 'Crea un componente frontend reutilizable'
tools: [read, search, edit]
argument-hint: "Nombre y propósito del componente (Ej: TransactionCard — muestra monto, categoría y fecha)"
---

Crea un componente frontend siguiendo convenciones del proyecto.

#file:./_engineering-principles.md

Framework (si se conoce): ${input:framework:react | vue | svelte | angular | auto}
Nombre del componente: ${input:name:Ej: TransactionCard, UserRow, ProductBadge}
Qué hace: ${input:description:Ej: Muestra resumen con estado, metadata y acciones}
Props/inputs: ${input:props:Ej: amount: number, status: string, createdAt: string}
¿Tiene estado interno?: ${input:has_state:sí | no}
¿Consume datos remotos?: ${input:calls_api:sí | no}

Genera o actualiza componente en la ruta estándar del proyecto con:

1. Tipos/props explícitos.
2. Estructura visual desacoplada de la lógica de datos.
3. Integración con capa de datos existente del proyecto (hook/store/service).
4. Estados loading/error/empty si aplica.
5. Exportaciones consistentes con el codebase.

Convenciones:
- Reutilizar design system/tokens del proyecto; no introducir estilos arbitrarios.
- Accesibilidad básica: semántica, labels, focus y navegación por teclado.
- Evitar lógica de negocio en capa visual.
- Si se repite UI, extraer subcomponentes reutilizables.
