---
agent: 'agent'
description: 'Ejecuta tests y reporta calidad'
tools: [execute, read]
argument-hint: "Comando a ejecutar (Ej: pytest -q --cov, pnpm vitest run --coverage)"
---

Ejecuta tests en el proyecto y reporta resultados.

#file:./_engineering-principles.md

Comando de tests: ${input:test_command:Ej: pytest -q --cov, npm test -- --coverage, pnpm vitest run --coverage}

Cuando termine, analiza el output y reporta:

1. Cuántos tests pasaron, fallaron o tienen errores
2. Si hay tests fallando, muestra el traceback y explica la causa probable
3. Porcentaje de cobertura general (si aplica)
4. Los archivos con cobertura más baja (menos del 80%) y qué líneas no están cubiertas
5. Si hay warnings relevantes, menciónalos

Si algún test falla, corrige la causa raíz, vuelve a ejecutar lo necesario y confirma el resultado.
