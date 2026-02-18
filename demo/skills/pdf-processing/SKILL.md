---
name: pdf-processing
description: Extracts text and tables from PDF files, fills forms, and merges documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction.
version: 1.2.0
author: skill-sdk-team
allowed-tools:
  - code_execution
---
# PDF Processing

## Quick start
Extract text with pdfplumber:
```python
import pdfplumber
with pdfplumber.open("file.pdf") as pdf:
    text = pdf.pages[0].extract_text()
```

## Advanced features
**Form filling**: See [FORMS.md](reference/FORMS.md) for complete guide
**Examples**: See [examples.md](examples.md) for common patterns

## Utility scripts
**analyze_form.py**: Extract all form fields from PDF
```bash
python scripts/analyze_form.py input.pdf > fields.json
```
