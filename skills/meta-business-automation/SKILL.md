# Skill: Meta Business Suite Automation

## Description
Automatisiere Instagram und Facebook Posts via Meta Graph API. Plane Content, poste Bilder/Videos/Reels und verwalte mehrere Accounts – alles aus Python.

## Capabilities
- `meta.post_photo` - Poste Bild auf Instagram/Facebook
- `meta.post_video` - Poste Video/Reel
- `meta.post_carousel` - Poste Carousel (Mehrfach-Bild)
- `meta.schedule` - Plane Posts für später
- `meta.analytics` - Rufe Post-Insights ab

## Problem
- Manuelles Posten zeitaufwändig
- Keine einfache API für Automation
- Schwierig Content zu planen

## Lösung
Python-basierte Meta Graph API Integration mit Scheduling.

## API Keys Required
- Meta App Access Token
- Instagram Business Account ID
- Facebook Page ID
- (Optional) Meta App Secret

## Setup Time
10-15 Minuten

## Use Cases
- Social Media Automation
- Content Planning
- Multi-Account Management
- E-Commerce Product Posts

## Tags
meta, facebook, instagram, api, automation, social-media, scheduling

## Configuration

```bash
export META_ACCESS_TOKEN="your_token"
export INSTAGRAM_BUSINESS_ID="your_ig_id"
export FACEBOOK_PAGE_ID="your_page_id"
```

## Usage

```bash
# Post photo to Instagram
python meta_automation.py --platform instagram --image photo.jpg --caption "Hello!"

# Schedule post
python meta_automation.py --platform facebook --image photo.jpg --caption "Hello!" --schedule "2025-03-01 09:00"

# Post carousel
python meta_automation.py --platform instagram --carousel img1.jpg img2.jpg img3.jpg --caption "Collection"
```
