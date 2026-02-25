# Skill: Calendly zu Notion CRM Sync

## Use Case
Berater, Coaches und Agenturen nutzen Calendly für Terminbuchung. Dieser Skill synchronisiert automatisch alle Termine in ein Notion-CRM mit Follow-up-Tracking.

## Problem
- Calendly-Termine liegen isoliert
- Keine zentrale Kundenübersicht
- Follow-ups werden vergessen
- Manueller Export notwendig

## Lösung
Automatischer Sync:
1. Calendly Events abrufen (API)
2. In Notion-Datenbank speichern
3. Follow-up-Status tracken
4. Status-Updates bei Terminänderungen

## Inputs
- Calendly API Key
- Notion Integration Token
- Notion Database ID

## Outputs
- Notion CRM Einträge:
  ```
  Name | Email | Datum | Status | Follow-up | Notizen
  ```
- Follow-up Reminders
- Termin-Statistiken

## API Keys Required
- Calendly API (Personal Access Token)
- Notion Integration Token

## Setup Time
10 Minuten

## Use Cases
- Kunden-Termin-Tracking
- Follow-up Automatisierung
- Umsatz-Tracking pro Termin
- Team-Termin-Übersicht

## Tags
calendly, notion, crm, appointments, sync, calendar, leads
