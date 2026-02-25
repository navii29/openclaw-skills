# Skill: LinkedIn Post Scheduler

## Use Case
Deutsche B2B-Unternehmen (Beratung, Agenturen, SaaS) müssen LinkedIn-Posts zu optimalen Zeiten veröffentlichen. Dieser Skill plant und postet automatisch.

## Problem
- LinkedIn-Posts müssen manuell veröffentlicht werden
- Optimale Posting-Zeiten werden verpasst (8-9 Uhr, 12-13 Uhr, 17-18 Uhr)
- Keine Consistency im Content
- Zeitverschwendung durch manuelles Posting

## Lösung
LinkedIn API Scheduler:
1. Posts aus CSV/JSON laden
2. Optimalen Zeitpunkt berechnen
3. Automatisch veröffentlichen (LinkedIn API)
4. Queue-Management

## Inputs
- LinkedIn Access Token
- Posts (CSV mit Text, Zeit, Bild-URL)
- Zeitzone (Europe/Berlin default)

## Outputs
- Veröffentlichte Posts
- Scheduling-Report
- Queue-Status

## API Keys Required
- LinkedIn API Access Token

## Setup Time
10 Minuten

## Use Cases
- Wochenplanung von Content
- Evergreen-Content Recycling
- Event-Posts timen
- Employee Advocacy Automation

## Tags
linkedin, social-media, scheduler, marketing, automation, b2b, content
