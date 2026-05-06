---
agent: 'agent'
description: 'Crea un service/caso de uso con inyección de dependencias'
tools: [read, search, edit]
argument-hint: "Nombre y responsabilidad (Ej: FinanceService — calcular métricas del usuario)"
---

Crea un service/caso de uso siguiendo Clean Architecture.

#file:./_engineering-principles.md

Nombre del service: ${input:name:Ej: FinanceService, AuthService}
Responsabilidad principal: ${input:responsibility:Ej: Calcular métricas financieras del usuario}
¿Depende de la base de datos?: ${input:uses_db:sí | no}
¿Depende de otro service?: ${input:dependencies:Ej: CurrencyService, ninguno}

Genera módulo de servicio (ruta según convención del proyecto) con:

1. Clase del service con `__init__` que recibe dependencias por parámetro
2. Métodos por caso de uso con contratos explícitos
3. Excepciones de dominio propias si aplica
4. Adaptador/factory de inyección de dependencias si el framework lo requiere
5. Tipado completo sin tipos ambiguos

Convenciones:
- Lógica de negocio en servicio, no en controller/UI.
- Dependencias invertidas mediante interfaces cuando sea viable.
- Diseñar para test unitario aislado.
- Mantener side effects encapsulados en infraestructura.
