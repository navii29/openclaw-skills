# Quick Invoice Generator

Generate invoices from command line. Markdown export with automatic numbering and calculations.

## Quick Start

```bash
# Create invoice
python3 invoice_generator.py create \
  --client "Musterfirma GmbH" \
  -i "Beratung" 10 150 \
  -i "Implementation" 5 200

# List invoices
python3 invoice_generator.py list

# Financial report
python3 invoice_generator.py report

# Mark as paid
python3 invoice_generator.py paid --number RE-2026-0001
```

## Features

- 🧾 Automatic invoice numbering (RE-YYYY-NNNN)
- 💰 Automatic tax calculation
- 📄 Markdown export
- 📊 Financial reporting
- ✅ Payment tracking

## Invoice Items

Add items with `-i` flag:
```bash
-i "Description" quantity unit_price
```

Multiple items:
```bash
-i "Consulting" 10 150 \
-i "Development" 20 120 \
-i "Meeting" 2 0
```

## Output Format

Generated markdown includes:
- Invoice header with number and dates
- Client information
- Itemized table
- Subtotal, tax, and total
- Payment instructions
- Notes

## Status Values

| Status | Emoji | Meaning |
|--------|-------|---------|
| draft | 📝 | Created, not sent |
| sent | 📤 | Sent to client |
| paid | ✅ | Payment received |
| overdue | ⚠️ | Past due date |

## Report Output

```
💰 FINANZ ÜBERSICHT

📊 Rechnungen gesamt: 10
💵 Bezahlt: 15,000.00 €
⏳ Ausstehend: 3,500.00 €
📝 Entwürfe: 1,200.00 €

📈 Umsatz: 15,000.00 €
```

## Storage

- `invoices.json` - Invoice registry
- `RE-YYYY-NNNN.md` - Individual invoices

## Future Enhancements

- [ ] PDF generation
- [ ] Email integration
- [ ] Recurring invoices
- [ ] Multi-currency support
- [ ] Client database
