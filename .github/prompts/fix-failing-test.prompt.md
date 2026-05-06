---
agent: 'agent'
description: 'Analiza un test fallando y propone el fix'
tools: [read, search, edit, execute]
argument-hint: "Nombre del test o comando que falla (Ej: pytest tests/unit/test_auth.py)"
---

Analiza un test fallando y corrige la causa raíz.

#file:./_engineering-principles.md

Comando de tests (si se conoce): ${input:test_command:Ej: pytest -q, npm test, pnpm vitest, go test ./...}

Con el output del error:
1. Determina si falla por test incorrecto o por bug de producción.
2. Explica causa raíz con evidencia del traceback y código.
3. Aplica fix en el lugar correcto, evitando sobreajuste al test.
4. Ejecuta test afectado.
5. Ejecuta suite relevante para descartar regresiones.

Si el comportamiento cambió intencionalmente, actualiza el test solo cuando el nuevo comportamiento sea correcto y esté documentado.
