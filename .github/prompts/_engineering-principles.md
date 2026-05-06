# Principios de Ingeniería Reutilizables

Aplica estas reglas en cualquier proyecto, independientemente del stack.

## Objetivo
- Resolver el requerimiento completo con cambios mínimos, coherentes y mantenibles.
- Priorizar legibilidad, testabilidad y seguridad por encima de atajos.

## DRY y simplicidad
- Evita duplicar lógica: extrae utilidades, helpers o servicios compartidos.
- Si hay repetición de reglas de negocio, centralízalas en una capa de dominio/aplicación.
- Evita abstracciones prematuras: abstrae solo cuando la duplicación o variabilidad lo justifique.

## Clean Architecture (orientativa)
- Separa capas con responsabilidades claras:
  - Presentación/Entrada (UI, controllers, handlers)
  - Aplicación (casos de uso, orquestación)
  - Dominio (reglas de negocio puras)
  - Infraestructura (DB, APIs externas, filesystem, colas)
- La lógica de dominio no debe depender de frameworks ni de detalles de infraestructura.
- Inyecta dependencias por interfaces/contratos cuando sea viable.

## SOLID y diseño
- SRP: cada módulo debe tener una razón clara de cambio.
- OCP: extensible sin romper comportamiento existente.
- LSP/ISP/DIP: usar contratos pequeños y dependencias explícitas.
- Mantén funciones y clases pequeñas con nombres orientados al negocio.

## Errores y observabilidad
- Falla temprano con mensajes claros y accionables.
- No ocultes errores relevantes ni los conviertas en estados ambiguos.
- Registra contexto útil sin exponer secretos o datos sensibles.

## Seguridad
- Validar y sanitizar toda entrada externa.
- Evitar secretos hardcodeados y usar variables de entorno/gestor de secretos.
- Aplicar principio de mínimo privilegio en acceso a datos y servicios.

## Calidad y pruebas
- Acompaña cambios no triviales con pruebas (unitarias/integración/e2e según impacto).
- Mantén alta cohesión de tests: un comportamiento por test, nombre descriptivo.
- Evita tests frágiles acoplados a detalles internos.

## Convenciones y consistencia
- Respeta estilo, estructura y patrones ya existentes en el repositorio.
- Si no existe convención, adopta una simple y consistente.
- Evita cambios cosméticos no relacionados al objetivo.

## Idioma en docstrings y comentarios
- Docstrings de funciones, clases y módulos: **inglés** (compatibilidad con herramientas de generación de documentación: Sphinx, TypeDoc, JSDoc, etc.).
- Comentarios inline sobre lógica de negocio o decisiones de diseño: **español o inglés**, consistente con el idioma predominante en el archivo.
- Nunca mezclar idiomas dentro del mismo docstring o bloque de comentarios.

## Entrega
- Explica brevemente qué cambió, por qué y riesgos residuales.
- Si no puedes verificar algo (tests/build), indícalo explícitamente.
