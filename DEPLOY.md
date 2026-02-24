# Deployment Guide: GitHub + Vercel

## Schritt 1: GitHub Repository erstellen

```bash
# 1. Auf github.com/new ein Repo erstellen:
#    Name: navii-automation
#    Public oder Private (egal)
#    NICHT "Initialize with README" (wir haben schon commits)

# 2. Remote hinzufügen und pushen:
git remote add origin https://github.com/DEIN_USERNAME/navii-automation.git
git branch -M main
git push -u origin main
```

## Schritt 2: Vercel verbinden

1. **https://vercel.com/new** öffnen
2. Mit GitHub anmelden
3. Repository "navii-automation" importieren
4. Framework Preset: **Other** (statische HTML)
5. Root Directory: `./website` (oder `/` wenn Website im Root)
6. Deploy klicken

**Settings in Vercel:**
- Build Command: `echo "No build needed"`
- Output Directory: `.`

## Schritt 3: Domain verbinden

In Vercel Dashboard:
1. Project → Settings → Domains
2. `navii-automation.com` hinzufügen
3. DNS-Records von Vercel anzeigen lassen (meist A-Record oder CNAME)

**DNS bei deinem Registrar:**
```
Type: A
Name: @
Value: 76.76.21.21

Type: CNAME
Name: www
Value: cname.vercel-dns.com
```

## Schritt 4: SSL (automatisch)

Vercel macht HTTPS automatisch. Kann 5-10 Minuten dauern nach DNS-Änderung.

## Schritt 5: Email einrichten (optional)

Für hello@navii-automation.com:
- Zoho Mail: https://www.zoho.com/mail/ (kostenlos bis 5 User)
- Oder: Im Vercel Dashboard → Email forwarding einrichten

## Updates deployen

Nach Änderungen:
```bash
git add .
git commit -m "Update website"
git push
```

Vercel deployed automatisch bei jedem Push!

---

**Aktueller Status:**
- ✅ Website gebaut (~/workspace/website/)
- ✅ Git initialisiert + committed
- ⏳ GitHub Repo (wartet auf dich)
- ⏳ Vercel Deploy (wartet auf dich)
- ⏳ Domain-Connect (wartet auf dich)

Soll ich einen Schritt für dich übernehmen (z.B. wenn du GitHub-Token gibst)?
