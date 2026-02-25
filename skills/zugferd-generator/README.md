# ZUGFeRD E-Rechnung Generator

## Schnellstart

```bash
# Installation
cd skills/zugferd-generator

# Beispielrechnung generieren
python3 zugferd_generator.py --input examples/invoice_example.json --output rechnung.zip

# Als XRechnung (reines XML)
python3 zugferd_generator.py --input examples/invoice_example.json --output rechnung.xml --format xrechnung

# Tests ausführen
python3 -m pytest tests/test_zugferd.py -v
```

## Python API

```python
from zugferd_generator import ZUGFeRDGenerator, Invoice, InvoiceItem, Party

# Rechnung erstellen
invoice = Invoice(
    invoice_number="RE-001",
    invoice_date="2025-02-25",
    seller=Party(...),
    buyer=Party(...),
    items=[
        InvoiceItem(description="Produkt", quantity=1, price=100.00, vat_rate=19)
    ]
)

# Generieren
generator = ZUGFeRDGenerator()
zugferd_bytes = generator.generate_zugferd(invoice)
```

## JSON Format

Siehe `examples/invoice_example.json`
