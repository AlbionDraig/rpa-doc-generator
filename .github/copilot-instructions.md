# Instrucciones Generales de Ingeniería

Estas reglas deben servir para cualquier proyecto y stack.

## Objetivo
- Entregar soluciones completas, mantenibles y seguras.
- Priorizar claridad, consistencia y bajo acoplamiento.

## Principios obligatorios
- DRY: evitar lógica duplicada; extraer piezas reutilizables.
- Clean Architecture: separar entrada/presentación, aplicación, dominio e infraestructura.
- SOLID: responsabilidades claras, dependencias explícitas e inversión de dependencias cuando aplique.
- KISS y YAGNI: resolver con la mínima complejidad necesaria.

## Reglas de implementación
- Respetar convenciones y estructura existente del repositorio.
- No mezclar lógica de negocio con controladores, vistas o detalles de framework.
- Preferir contratos/tipos explícitos en bordes del sistema (DTOs, interfaces, schemas).
- Mantener funciones cortas, nombres semánticos y módulos cohesivos.
- Evitar cambios no relacionados con la tarea.

## Calidad y pruebas
- Todo cambio no trivial debe venir con pruebas adecuadas al impacto.
- Mantener cobertura en rutas críticas y casos de error.
- Corregir causa raíz, no solo síntomas.
- Verificar lint, type-check y tests relevantes antes de cerrar.

## Seguridad y resiliencia
- Validar entradas y manejar errores de forma explícita.
- Nunca exponer secretos, tokens ni datos sensibles en código, logs o respuestas.
- Aplicar mínimo privilegio para acceso a DB, APIs y recursos.
- Incluir mensajes de error útiles para diagnóstico sin filtrar detalles internos.

## Rendimiento y operabilidad
- Evitar N+1, trabajo redundante y operaciones bloqueantes en rutas críticas.
- Diseñar para observabilidad: logs estructurados, contexto mínimo útil y trazabilidad.
- Medir y optimizar solo donde exista impacto real.

## Frontend (si aplica)
- Reutilizar sistema de diseño/tokens existentes del proyecto.
- Mantener separación entre UI, estado y acceso a datos.
- Implementar estados de carga, error y vacío en vistas de datos.
- Garantizar accesibilidad básica (semántica, foco, labels y contraste).

## Backend/API (si aplica)
- Definir contratos de entrada/salida claros.
- Mantener capa de aplicación/dominio independiente del framework.
- Versionar y documentar endpoints cuando sea requerido.

## Entrega esperada
- Describir qué se cambió y por qué.
- Indicar validaciones ejecutadas y resultado.
- Declarar riesgos residuales o tareas pendientes si existen.
