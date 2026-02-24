# Email Template Sender

Quick email templates with placeholders for common business communications.

## Quick Start

```bash
# List templates
python3 email_templates.py list

# Show template
python3 email_templates.py show --template followup

# Send email
python3 email_templates.py send --template followup --to "client@example.com" --vars '{"name":"Max","topic":"Automation"}'

# Interactive mode
python3 email_templates.py interactive
```

## Templates

| Template | Use Case | Placeholders |
|----------|----------|--------------|
| `followup` | Follow-up email | `name`, `topic` |
| `angebot` | Quote/offer | `name`, `service`, `angebot_details`, `laufzeit`, `preis` |
| `danke` | Thank you | `name`, `zusammenfassung` |
| `termin` | Appointment | `name`, `termin_datum`, `termin_zeit`, `thema`, `call_link` |
| `cold` | Cold outreach | `name`, `company`, `trigger`, `benefit` |

## Example

```bash
# Follow-up email
python3 email_templates.py send \
  --template followup \
  --to "kunde@firma.de" \
  --vars '{"name":"Herr Schmidt","topic":"das Angebot"}'
```

Result:
```
Subject: Nachfass: das Angebot

Hallo Herr Schmidt,

ich wollte noch einmal nachfragen, ob Sie bereits Zeit hatten, 
sich das Angebot anzuschauen.

...
```

## Custom Templates

Edit `templates.json` to add your own:
```json
{
  "mytemplate": {
    "name": "My Template",
    "subject": "Re: {{topic}}",
    "body": "Hello {{name}},\n\n..."
  }
}
```

## Features

- 🚀 Gmail SMTP integration
- 📊 Send history tracking
- 📝 Placeholder substitution
- 💾 Template persistence

## History

All sends logged in `send_history.json`:
```json
{
  "sends": [
    {
      "to": "client@example.com",
      "subject": "Nachfass:...",
      "template": "followup",
      "sent_at": "2026-02-24T18:32:00"
    }
  ]
}
```
