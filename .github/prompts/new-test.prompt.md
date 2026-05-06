---
agent: 'agent'
description: 'Genera tests unitarios y de integración para un service o endpoint'
tools: [read, search, edit, execute]
argument-hint: "Archivo a testear (Ej: app/services/finance_service.py)"
---

Genera tests para el siguiente archivo del proyecto.

#file:./_engineering-principles.md

Archivo a testear: ${input:file:Ej: app/services/finance_service.py}
Tipo de tests: ${input:type:unitarios | integración | e2e | ambos}
Casos a cubrir: ${input:cases:Ej: caso feliz, usuario no encontrado, monto negativo — o "todos los casos"}
Stack/lenguaje (si se conoce): ${input:stack:python-pytest | js-vitest | js-jest | java-junit | go-test | auto}

Genera o actualiza archivo(s) de test respetando la estructura del repo:

1. Fixtures necesarios en el archivo o en `conftest.py` si son reutilizables
2. Mocks para dependencias externas (DB, servicios externos, APIs)
3. Un test por caso de uso — nombres descriptivos: `test_should_{behavior}_when_{condition}`
4. Assertions específicas — no solo `assert response.status_code == 200`

Para tests de integración de API:
- Inicializar app/servidor de test según framework.
- Usar dobles de prueba para servicios externos.
- Validar códigos de estado, contrato y efectos en persistencia.

Para tests unitarios:
- Aislar dependencias externas.
- Testear comportamiento observable, no detalles internos.
- Cubrir casos de error y borde.

Al final ejecuta los tests nuevos con el runner detectado del proyecto y reporta resultado.
