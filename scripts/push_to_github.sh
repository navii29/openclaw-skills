#!/bin/bash
# GitHub Push Skript für alle Skills
# Führt Skills in die bestehenden 6 Repositories zusammen

set -e

WORKSPACE="/Users/fridolin/.openclaw/workspace"
GITHUB_USER="navii29"

# Repository-URLs (anpassen wenn nötig)
declare -A REPOS=(
    ["dokument-processing"]="https://github.com/$GITHUB_USER/dokument-processing.git"
    ["lead-qualification"]="https://github.com/$GITHUB_USER/lead-qualification.git"
    ["competitive-intelligence"]="https://github.com/$GITHUB_USER/competitive-intelligence.git"
    ["voice-workflow"]="https://github.com/$GITHUB_USER/voice-workflow.git"
    ["executive-kalender"]="https://github.com/$GITHUB_USER/executive-kalender.git"
    ["inbox-ai-template"]="https://github.com/$GITHUB_USER/inbox-ai-template.git"
)

# Skill-Mapping
declare -A SKILL_MAPPING=(
    # German Accounting Suite → dokument-processing
    ["skills/gobd-rechnungsvalidator"]="dokument-processing/skills/gobd-rechnungsvalidator"
    ["skills/zugferd-generator"]="dokument-processing/skills/zugferd-generator"
    ["skills/datev-csv-export"]="dokument-processing/skills/datev-csv-export"
    ["skills/sepa_xml_generator"]="dokument-processing/skills/sepa-xml-generator"
    
    # Lead Pipeline → lead-qualification
    ["skills/calendly-notion-crm"]="lead-qualification/skills/calendly-notion-crm"
    ["skills/website-lead-alerts"]="lead-qualification/skills/website-lead-alerts"
    ["skills/email-slack-tickets"]="lead-qualification/skills/email-slack-tickets"
    
    # Competitive Intelligence → competitive-intelligence
    ["skills/ebay-kleinanzeigen-scraper"]="competitive-intelligence/skills/ebay-kleinanzeigen-scraper"
    ["skills/google-reviews-monitor"]="competitive-intelligence/skills/google-reviews-monitor"
    ["skills/amazon-seller-alerts"]="competitive-intelligence/skills/amazon-seller-alerts"
    
    # Executive Productivity → executive-kalender
    ["skills/notion-ical-sync"]="executive-kalender/skills/notion-ical-sync"
    ["skills/linkedin-scheduler"]="executive-kalender/skills/linkedin-scheduler"
    ["skills/meta-business-automation"]="executive-kalender/skills/meta-business-automation"
    
    # Inbox AI Core → inbox-ai-template
    ["skills/inbox-ai"]="inbox-ai-template/skills/inbox-ai"
    ["skills/sevdesk"]="inbox-ai-template/skills/sevdesk"
    ["skills/gmail-auto-responder"]="inbox-ai-template/skills/gmail-auto-responder"
)

echo "🚀 OpenClaw Skills GitHub Push"
echo "=============================="
echo ""

# Temporäres Verzeichnis für Clones
TEMP_DIR=$(mktemp -d)
echo "📁 Temporäres Verzeichnis: $TEMP_DIR"

# Funktion: Skill zu Repo kopieren
copy_skill_to_repo() {
    local skill_path=$1
    local repo_name=$2
    local target_path=$3
    
    echo "  📦 Kopiere $(basename $skill_path) → $repo_name"
    
    # Repo klonen (falls noch nicht geschehen)
    if [ ! -d "$TEMP_DIR/$repo_name" ]; then
        echo "    📥 Klone $repo_name..."
        git clone "${REPOS[$repo_name]}" "$TEMP_DIR/$repo_name" 2>/dev/null || {
            echo "    ⚠️  Konnte $repo_name nicht klonen - erstelle neu..."
            mkdir -p "$TEMP_DIR/$repo_name"
            cd "$TEMP_DIR/$repo_name"
            git init
            git remote add origin "${REPOS[$repo_name]}"
        }
    fi
    
    # Skill kopieren
    mkdir -p "$TEMP_DIR/$target_path"
    cp -r "$WORKSPACE/$skill_path/"* "$TEMP_DIR/$target_path/" 2>/dev/null || true
}

# Alle Skills kopieren
echo ""
echo "📋 Kopiere Skills zu Repositories..."
echo ""

for skill in "${!SKILL_MAPPING[@]}"; do
    target="${SKILL_MAPPING[$skill]}"
    repo=$(echo $target | cut -d'/' -f1)
    copy_skill_to_repo "$skill" "$repo" "$target"
done

# Commits erstellen
echo ""
echo "📝 Erstelle Commits..."
echo ""

for repo in "${!REPOS[@]}"; do
    if [ -d "$TEMP_DIR/$repo" ]; then
        echo "  💾 Committe $repo..."
        cd "$TEMP_DIR/$repo"
        
        # Git Konfiguration
        git config user.email "navii@navii-automation.de" 2>/dev/null || true
        git config user.name "Navii Automation" 2>/dev/null || true
        
        # Alle Dateien adden
        git add -A
        
        # Commit (nur wenn Änderungen vorhanden)
        if ! git diff --cached --quiet; then
            git commit -m "feat: Add OpenClaw skills - $(date +%Y-%m-%d)

New skills added:
$(git status --short | grep '^A' | wc -l | xargs echo) new files
$(git status --short | grep '^M' | wc -l | xargs echo) modified files

Skills include:
- SKILL.md documentation
- Python implementation
- Unit tests" || true
            
            echo "    ✅ Commit erstellt"
        else
            echo "    ⏭️  Keine Änderungen"
        fi
    fi
done

# Push (manuell - erfordert Auth)
echo ""
echo "📤 Push zu GitHub..."
echo ""

for repo in "${!REPOS[@]}"; do
    if [ -d "$TEMP_DIR/$repo/.git" ]; then
        echo "  🚀 Push $repo..."
        cd "$TEMP_DIR/$repo"
        
        # Push (wird fehlschlagen ohne Auth - ist OK für jetzt)
        git push origin main 2>/dev/null && echo "    ✅ Gepusht" || echo "    ⚠️  Push fehlgeschlagen (Auth erforderlich)"
    fi
done

# Zusammenfassung
echo ""
echo "=============================="
echo "✅ Vorbereitung abgeschlossen!"
echo "=============================="
echo ""
echo "📂 Temporäre Repos in: $TEMP_DIR"
echo ""
echo "Manueller Push (falls automatisch fehlgeschlagen):"
for repo in "${!REPOS[@]}"; do
    echo "  cd $TEMP_DIR/$repo && git push origin main"
done
echo ""
echo "Oder mit GitHub Token:"
echo "  git remote set-url origin https://TOKEN@github.com/$GITHUB_USER/REPO.git"
echo "  git push origin main"
