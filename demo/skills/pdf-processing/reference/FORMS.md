# Form Filling Guide

## Supported field types
- `text` – Plain text fields
- `checkbox` – Boolean checkboxes
- `sig` – Signature fields

## Workflow
1. Run `scripts/analyze_form.py` to extract fields.
2. Fill values into the JSON structure.
3. Apply with `scripts/fill_form.py`.
