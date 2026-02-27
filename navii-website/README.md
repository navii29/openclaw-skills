# Navii Automation Website

## Lokale Vorschau
```bash
cd website
python3 -m http.server 8000
# Oder: npx serve .
```

## Deploy-Optionen

### Option A: Vercel (Empfohlen)
1. GitHub Account erstellen (falls nicht vorhanden)
2. Repo erstellen, diese Dateien pushen
3. Auf vercel.com mit GitHub verbinden
4. Domain navii-automation.com verbinden

### Option B: Netlify Drop (Schnellste)
1. Netlify.com → "Add new site" → "Deploy manually"
2. `website`-Ordner als ZIP hochladen
3. Domain in Settings → Domain management hinzufügen

### Option C: GitHub Pages (Kostenlos)
1. Repo auf GitHub erstellen
2. Settings → Pages → Deploy from branch
3. Custom domain eintragen

## DNS-Einstellungen (für navii-automation.com)

Bei deinem Domain-Registrar (z.B. GoDaddy, Namecheap, Cloudflare):

**Option 1: A-Records (Vercel)**
```
Type: A
Name: @
Value: 76.76.21.21
```

**Option 2: CNAME (Netlify/GitHub)**
```
Type: CNAME
Name: www
Value: [deine-netlify-url].netlify.app
```

## Email-Einrichtung
Für hello@navii-automation.com:
- Zoho Mail (kostenlos)
- Google Workspace ($6/Monat)
- Oder einfach Forwarding einrichten an deine private Mail

## Nach dem Deploy
- [ ] SSL aktivieren (sollte automatisch gehen)
- [ ] Favicon hinzufügen
- [ ] Analytics (Plausible oder Google)
- [ ] Kontaktformular statt nur mailto: (z.B. Formspree)
