---
agent: 'ask'
description: 'Revisa el código del archivo o PR actual'
tools: [read, search]
argument-hint: "Archivo o área a revisar (Ej: app/services/auth_service.py, o 'cambios del PR')"
---

Haz una revisión técnica del archivo activo o de los cambios recientes.

#file:./_engineering-principles.md

Evalúa con foco en:

1. Correctitud funcional
- Bugs lógicos, regresiones, casos borde y supuestos incorrectos.

2. Arquitectura y diseño
- Violaciones a DRY, SRP o separación de capas (UI/app/dominio/infra).
- Acoplamiento innecesario a framework o infraestructura.

3. Seguridad
- Validación insuficiente de inputs, inyección, secretos expuestos, auth/autz incompleta.

4. Rendimiento
- N+1, consultas/IO redundantes, cálculos costosos, falta de paginación o caché donde aplica.

5. Mantenibilidad
- Nombres poco claros, funciones largas, duplicación, tipos débiles, código muerto.

6. Pruebas
- Cobertura faltante para rutas críticas y manejo de errores.

Formato de salida:
- Lista de hallazgos ordenada por severidad: crítico, importante, sugerencia.
- Cada hallazgo debe incluir archivo, línea aproximada, impacto y recomendación concreta.
- Si no hay hallazgos, dilo explícitamente y menciona riesgos residuales o gaps de testing.
