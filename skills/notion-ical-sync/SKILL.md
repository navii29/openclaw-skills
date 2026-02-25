# Skill: Notion zu iCal Sync

## Use Case
Deutsche Teams nutzen Notion für Projekt-Management. Dieser Skill exportiert Notion-Datenbanken (mit Datum-Feldern) zu iCal/ICS für Kalender-Integration.

## Problem
- Notion-Termine nicht im Google/Apple Kalender sichtbar
- Manuelle Übertragung fehleranfällig
- Keine Erinnerungen für Notion-Daten
- Team-Synchronisation schwierig

## Lösung
Notion → iCal Konverter:
1. Notion-Datenbank abfragen
2. Datum-Felder extrahieren
3. iCal/ICS Datei generieren
4. Automatischer Export (für Calendar-Subscribe)

## Inputs
- Notion Integration Token
- Datenbank ID
- Datum-Feld Mapping

## Outputs
- ICS-Datei (iCal Format)
- Kalender-Abonnement URL
- Sync-Report

## API Keys Required
- Notion Integration Token

## Setup Time
10 Minuten

## Use Cases
- Projekt-Deadlines im Kalender
- Content-Kalender Export
- Event-Planung Synchronisation
- Team-Urlaubsübersicht

## Tags
notion, ical, calendar, sync, export, projects, automation
