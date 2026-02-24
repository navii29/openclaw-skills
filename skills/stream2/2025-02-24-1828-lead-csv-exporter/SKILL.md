# Lead CSV Exporter

Exports leads detected by `lead_detector.py` to CSV format for Excel/Google Sheets analysis.

## Quick Start

```bash
# Export all leads to CSV
python3 ~/.openclaw/workspace/skills/stream2/2025-02-24-1828-lead-csv-exporter/csv_exporter.py

# Files created in exports/:
# - leads_export_YYYYMMDD_HHMM.csv
# - weekly_report_YYYY_WW.txt
```

## Features

- 📁 Exports leads to CSV format
- 📊 Generates weekly statistics
- 🔥 Tracks hot vs warm leads
- 📈 Calculates average lead score

## CSV Format

| Column | Description |
|--------|-------------|
| date | Lead detection timestamp |
| sender | Email sender |
| subject | Email subject |
| score | Lead quality (1-10) |
| status | new / contacted / qualified |
| notes | Manual notes |

## Integration

Works with Skill 1 (Email Lead Detector). Reads from:
`~/.openclaw/workspace/skills/stream2/2025-02-24-1827-email-lead-detector/lead_state.json`

## Workflow

1. Run `lead_detector.py` to find leads
2. Run `csv_exporter.py` to export them
3. Import CSV into Excel/Sheets
4. Analyze and track conversions

## Future Enhancements

- [ ] Google Sheets direct integration
- [ ] Notion database sync
- [ ] Airtable integration
- [ ] Automated weekly email reports
