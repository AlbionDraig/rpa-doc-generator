---
description: 'Refactoriza código existente de forma incremental y segura'
agent: 'agent'
tools: [read, search, edit, execute, todo]
argument-hint: "Archivo o módulo a refactorizar + objetivo (Ej: simplify service layer, extract reusable hook)"
---

Refactoriza el código indicado de forma incremental, sin cambiar comportamiento externo observable.

#file:./_engineering-principles.md

Archivo o módulo a refactorizar: ${input:target:Ej: app/services/finance_service.py, src/hooks/useTransactions.ts}
Objetivo del refactor: ${input:goal:Ej: extraer lógica duplicada, separar capas, mejorar legibilidad}
¿Hay tests existentes que lo cubren?: ${input:has_tests:sí | no | parcial}

## Reglas estrictas
- El comportamiento externo observable NO debe cambiar.
- Si no hay tests que cubran el código, créalos ANTES de refactorizar (characterization tests).
- Cambios en pasos pequeños y verificables; no reescrituras totales en un solo paso.
- No agregar features ni corregir bugs en el mismo commit/paso — scope acotado.

## Proceso
1. **Leer** el código actual y sus dependencias para entender el comportamiento real.
2. **Planificar** los pasos con `todo` tool; cada paso debe ser reversible.
3. Si faltan tests: crear tests de caracterización que capturen el comportamiento actual.
4. **Ejecutar** cada paso de refactor y verificar que los tests siguen pasando.
5. **Revisar** que no se hayan filtrado dependencias o acoplamiento nuevo.
6. Reportar qué cambió, qué mejoró (métricas: complejidad, duplicación, tamaño de funciones) y qué tests se ejecutaron.

## Criterios de calidad post-refactor
- Funciones más cortas con responsabilidad única.
- Sin duplicación dentro del mismo módulo.
- Separación de capas respetada (no lógica de negocio en controllers/UI).
- Nombres semánticos orientados al dominio.
