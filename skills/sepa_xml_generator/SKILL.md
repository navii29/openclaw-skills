# SEPA-XML Generator

Generates valid SEPA XML files for German banks according to ISO 20022 standards.

## Supported Formats

| Format | Type | Use Case |
|--------|------|----------|
| `pain.001.001.09` | Credit Transfer (Überweisung) | Sending money to suppliers |
| `pain.008.001.08` | Direct Debit (Lastschrift) | Collecting money from customers |

## Quick Start

```python
from sepa_generator import SepaCreditTransfer, SepaDirectDebit

# Credit Transfer
sct = SepaCreditTransfer(
    msg_id="MSG-001",
    initiator_name="Meine Firma GmbH",
    creation_date_time="2024-02-25T10:00:00"
)

sct.add_payment_info(
    payment_info_id="PAY-001",
    debtor_name="Meine Firma GmbH",
    debtor_iban="DE89370400440532013000",
    debtor_bic="COBADEFFXXX"
)

sct.add_transaction(
    end_to_end_id="E2E-001",
    amount=1500.00,
    creditor_name="Lieferant AG",
    creditor_iban="DE75512108001245126199",
    creditor_bic="INGDDEFFXXX",
    remittance_info="Rechnung 2024-001"
)

xml_string = sct.to_xml()
```

## CLI Usage

```bash
# Generate from JSON
python sepa_generator.py --input payments.json --output sepa.xml --type credit-transfer

# Validate existing XML
python sepa_generator.py --validate existing.xml
```

## API Reference

### SepaCreditTransfer

```python
SepaCreditTransfer(
    msg_id: str,              # Unique message identifier
    initiator_name: str,      # Initiating party name
    creation_date_time: str   # ISO 8601 datetime
)

Methods:
- add_payment_info(**kwargs) -> None
- add_transaction(**kwargs) -> None
- to_xml() -> str
- to_file(path: str) -> None
- validate() -> bool
```

### SepaDirectDebit

```python
SepaDirectDebit(
    msg_id: str,
    initiator_name: str,
    creation_date_time: str,
    sequence_type: str  # 'FRST', 'RCUR', 'FNAL', 'OOFF'
)

Methods:
- add_payment_info(**kwargs) -> None
- add_transaction(**kwargs) -> None
- to_xml() -> str
- to_file(path: str) -> None
- validate() -> bool
```

## Validation Rules

- IBAN: Valid German IBAN format (22 chars, starts with DE)
- BIC: 8 or 11 characters
- Amount: Maximum 999999999.99 EUR
- Remittance: Maximum 140 characters
- References: Maximum 35 characters

## References

- [EBA SEPA Guidelines](https://www.europeanpaymentscouncil.eu/)
- [ISO 20022 pain.001 Message](https://www.iso20022.org/)
- [German Banking Industry Committee](https://www.die-deutsche-kreditwirtschaft.de/)
