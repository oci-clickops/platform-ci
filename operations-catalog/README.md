# Operations Catalog

Catálogo de operaciones para APEX UI.

## Uso

APEX lee estos JSON para:

1. Descubrir operaciones disponibles
2. Generar formularios dinámicos
3. Saber qué workflow triggear

## Schema

```json
{
  "name": "Nombre",
  "description": "Descripción",
  "workflow": "workflow-name.yaml",
  "auto_approve": true,
  "parameters": {
    "param": {
      "label": "Label",
      "type": "choice|boolean|number",
      "options": ["a", "b"],
      "required": true
    }
  }
}
```
