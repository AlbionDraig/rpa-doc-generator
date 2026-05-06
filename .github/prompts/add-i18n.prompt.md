---
description: "Add new i18n translation keys to the frontend. Ensures all visible strings are added to both en.json and es.json following the project's namespace conventions."
agent: agent
tools: [read, search, edit]
argument-hint: "Describe las strings a añadir y el contexto (Ej: botones de confirmación de pago, página de configuración)"
---

## Contexto

Añade nuevas claves de traducción al sistema i18n del frontend.

**Strings a añadir**: `${input:strings:Describe las strings visibles que necesitan traducción}`
**Sección / feature**: `${input:section:Ej: transactions, auth, settings, common}`

---

## Archivos clave

- `frontend/src/i18n/locales/en.json` — traducciones en inglés
- `frontend/src/i18n/locales/es.json` — traducciones en español
- `frontend/src/i18n/index.ts` — configuración de i18next

## Proceso

### 1. Explorar el namespace existente

Lee `en.json` y `es.json` para entender:
- Qué namespaces/secciones existen (`nav`, `errors`, `common`, etc.).
- La convención de nombres (`camelCase` para las claves).
- Si ya existe una clave similar que pueda reutilizarse.

### 2. Diseñar las claves

Reglas de nomenclatura:
- Usa `camelCase` para los nombres de clave: `confirmDelete`, `saveChanges`.
- Agrupa bajo el namespace de la feature: `{ "transactions": { "confirmDelete": "..." } }`.
- Si la string es reutilizable en múltiples contextos, usa el namespace `common`.
- Usa interpolación para valores dinámicos: `"welcome": "Welcome, {{name}}"`.
- Nunca uses IDs numéricos ni abreviaciones crípticas como `btn1`, `lbl_tx`.

### 3. Añadir en ambos archivos simultáneamente

- Inserta las claves en la sección correspondiente de **`en.json`** (inglés).
- Inserta las mismas claves en la sección correspondiente de **`es.json`** (español).
- Mantén el orden y la indentación consistente con el resto del archivo.
- **Nunca dejes una clave en un idioma sin su contraparte en el otro.**

### 4. Verificar uso en componentes (si aplica)

Si se especificó un componente donde se usarán las claves:
- Reemplaza cualquier string hardcodeada por `t('namespace.key')` usando el hook `useTranslation`.
- Importa `useTranslation` desde `react-i18next` si no está ya importado.

### 5. Output

Presenta:
1. Las claves añadidas en formato JSON (diff o bloque).
2. Ejemplo de uso en un componente React si el contexto lo permite.
3. Si detectas strings hardcodeadas en el componente objetivo que no estén en los archivos de i18n, señálalas como deuda técnica.
