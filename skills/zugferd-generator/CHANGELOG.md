# ZUGFeRD E-Rechnung Generator - Changelog

## v1.0.0 (2025-02-25)

### Features
- ✅ ZUGFeRD 2.1 Generator (EN 16931 kompatibel)
- ✅ Factur-X Unterstützung (französischer Standard)
- ✅ XRechnung Generator (reines XML für Behörden)
- ✅ XML-Validierung vor Generierung
- ✅ Mehrere Steuersätze (19%, 7%, 0%)
- ✅ Leitweg-ID Unterstützung
- ✅ CLI Interface
- ✅ JSON Import/Export
- ✅ Umfassende Test-Suite (11 Tests)

### Technische Details
- Reine Python-Implementierung (keine externen Abhängigkeiten für XML)
- ZIP-basiertes ZUGFeRD-Format (XML + Metadaten)
- UNECE Einheitencodes (C62, MON, HUR, etc.)
- DSGVO-konform (keine Cloud-APIs)

### Bekannte Limitationen
- Keine PDF/A-3 Integration (nur ZIP mit XML)
- Keine digitale Signatur
- Kein OCR für bestehende PDFs

### Roadmap
- [ ] PDF/A-3 Erzeugung mit eingebettetem XML
- [ ] ZUGFeRD 2.2 Support
- [ ] Digitale Signatur (XAdES)
- [ ] Massenverarbeitung (Batch)
- [ ] REST API
