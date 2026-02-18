# Examples

## Example 1: Extract text from a single page
```python
import pdfplumber
with pdfplumber.open("report.pdf") as pdf:
    print(pdf.pages[0].extract_text())
```

## Example 2: Merge two PDFs
```python
from PyPDF2 import PdfMerger
merger = PdfMerger()
merger.append("doc1.pdf")
merger.append("doc2.pdf")
merger.write("merged.pdf")
```
