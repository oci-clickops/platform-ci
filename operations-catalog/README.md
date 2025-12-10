# Operations Catalog

Operations catalog for APEX UI.

## Usage

APEX reads these JSON files to:

1. Discover available operations
2. Generate dynamic forms
3. Determine which workflow to trigger

## Schema

```json
{
  "name": "Name",
  "description": "Description",
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
