# CRM STAGES v1 - Lead Pipeline Definitions

**System:** Notion Database "LinkedIn Lead Pipeline"  
**Last Updated:** 2026-02-19  

---

## Stage Definitions

### 1. NEW 🆕
**Entry Criteria:** Lead gefunden, noch nicht kontaktiert  
**Exit Criteria:** Erster Touchpoint (Email/LinkedIn/Call)  
**Actions:**
- Scoring durchführen
- Outreach-Text vorbereiten
- In Queue eintragen

**Time in Stage:** Max 24h

---

### 2. CONTACTED 📤
**Entry Criteria:** Erste Nachricht gesendet  
**Exit Criteria:** Response erhalten ODER 3 Follow-ups ohne Response  
**Actions:**
- Warte auf Response (24-48h)
- Follow-up #1 nach 3 Tagen
- Follow-up #2 nach 7 Tagen  
- Break-up nach 14 Tagen

**Time in Stage:** Max 14 Tage

---

### 3. RESPONDED 💬
**Entry Criteria:** Lead hat geantwortet (nicht Absage)  
**Exit Criteria:** Termin gebucht ODER weitere Info gesendet  
**Actions:**
- Antwort analysieren
- Passende Antwort senden
- Calendly-Link teilen
- Fragen beantworten

**Time in Stage:** Max 7 Tage

---

### 4. MEETING BOOKED 📅
**Entry Criteria:** Termin über Calendly gebucht  
**Exit Criteria:** Meeting stattgefunden  
**Actions:**
- Vorbereitung: ICP Research, Pain Points
- Discovery Call durchführen (15-30 Min)
- Notes in CRM
- Next Steps definieren

**Time in Stage:** Max 3 Tage (bis Meeting)

---

### 5. PROPOSAL SENT 📋
**Entry Criteria:** Nach Meeting, Interesse bestätigt  
**Exit Criteria:** Proposal accepted/declined  
**Actions:**
- Angebot erstellen (Starter/Growth/Enterprise)
- ROI-Berechnung
- Scope definieren
- Senden + Follow-up

**Time in Stage:** Max 7 Tage

---

### 6. WON ✅
**Entry Criteria:** Vertrag unterschrieben + Payment  
**Exit Criteria:** - (Final Stage)  
**Actions:**
- Onboarding starten
- Delivery Blueprint laden
- Kickoff Call
- Projekt in Notion anlegen

---

### 7. LOST ❌
**Entry Criteria:** Absage zu jeder Stage  
**Exit Criteria:** - (Final Stage)  
**Actions:**
- Grund dokumentieren
- In "Nurture" verschieben (falls später)
- Learnings notieren

---

## 🔄 Stage Transitions

```
NEW → CONTACTED → RESPONDED → MEETING BOOKED → PROPOSAL SENT → WON
                    ↓
                  LOST (jederzeit möglich)
```

## 📊 Conversion Targets

| Stage | Target Conversion | Realistic |
|-------|-------------------|-----------|
| NEW → CONTACTED | 100% | 100% |
| CONTACTED → RESPONDED | 20% | 15% |
| RESPONDED → MEETING | 50% | 40% |
| MEETING → PROPOSAL | 70% | 60% |
| PROPOSAL → WON | 40% | 30% |

**Gesamt:** NEW → WON = 2.8% (Target), 1.08% (Realistic)

## 🎯 Current Pipeline

| Lead | Stage | Score | Next Action |
|------|-------|-------|-------------|
| Sadik Alipour | CONTACTED | - | Wait 3 days |
| Sebastián Ramírez | CONTACTED | 95 | Wait 3 days |
| Gunnar Morling | CONTACTED | 85 | Wait 3 days |

---

**Next Review:** Daily 9am
