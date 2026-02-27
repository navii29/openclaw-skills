#!/bin/bash
# GitHub Repository Setup und Push
# Alle Skills kategorisch in 10 Repos organisieren

set -e

WORKSPACE="/Users/fridolin/.openclaw/workspace"
GITHUB_USER="navii29"
REPOS_DIR="$WORKSPACE/github-repos"

echo "🚀 GitHub Repository Setup"
echo "=========================="

# Funktion: Repo vorbereiten
prepare_repo() {
    local repo_name=$1
    shift
    local skills=($@)
    
    echo ""
    echo "📦 Vorbereite: $repo_name"
    
    # Repo-Verzeichnis erstellen
    mkdir -p "$REPOS_DIR/$repo_name"
    cd "$REPOS_DIR/$repo_name"
    
    # Git init
    git init --quiet
    
    # Skills kopieren
    for skill in "${skills[@]}"; do
        if [ -d "$WORKSPACE/skills/$skill" ]; then
            echo "  📂 Kopiere $skill"
            cp -r "$WORKSPACE/skills/$skill" .
        else
            echo "  ⚠️  Nicht gefunden: $skill"
        fi
    done
    
    # README erstellen
    cat > README.md << EOF
# $repo_name

OpenClaw Skills for $repo_name

## Skills included
$(for s in "${skills[@]}"; do echo "- $s"; done)

## Installation
\`\`\`bash
pip install -r requirements.txt
\`\`\`

## License
Private - Navii Automation Agency
EOF
    
    # Commit
    git add -A
    git commit -m "Initial commit: $(date +%Y-%m-%d)

Skills:
$(for s in "${skills[@]}"; do echo "- $s"; done)

Total: ${#skills[@]} skills" --quiet
    
    echo "  ✅ Fertig: $repo_name (${#skills[@]} skills)"
}

# 1. German Accounting Suite (Höchste Priorität)
prepare_repo "german-accounting-suite" \
    "gobd-rechnungsvalidator" \
    "zugferd-generator" \
    "datev-csv-export" \
    "sepa_xml_generator" \
    "german-accounting-suite"

# 2. Inbox AI Core
prepare_repo "inbox-ai-core" \
    "inbox-ai" \
    "sevdesk" \
    "gmail-auto-responder" \
    "aa"

# 3. Lead Pipeline Suite
prepare_repo "lead-pipeline-suite" \
    "calendly-notion-crm" \
    "website-lead-alerts" \
    "email-slack-tickets" \
    "lead-pipeline-suite"

# 4. Competitive Intelligence
prepare_repo "competitive-intelligence" \
    "ebay-kleinanzeigen-scraper" \
    "google-reviews-monitor" \
    "amazon-seller-alerts"

# 5. E-Commerce Automation
prepare_repo "e-commerce-automation" \
    "shopify-telegram-alerts" \
    "woocommerce-alerts" \
    "stripe-payment-alerts" \
    "tiktok-shop-integration"

# 6. Social Media Suite
prepare_repo "social-media-suite" \
    "meta-business-automation" \
    "linkedin-scheduler"

# 7. Executive Productivity
prepare_repo "executive-productivity" \
    "notion-ical-sync" \
    "executive-kalender"

# 8. Voice Automation
prepare_repo "voice-automation" \
    "voice-workflow"

# 9. Crypto DeFi Suite
prepare_repo "crypto-defi-suite" \
    "a2a-market" \
    "aave-liquidation-monitor"

# 10. Social Platform Agents
prepare_repo "social-platform-agents" \
    "37soul" \
    "24konbini"

echo ""
echo "=========================="
echo "✅ Alle Repos vorbereitet!"
echo "=========================="
echo ""
echo "Verzeichnis: $REPOS_DIR"
echo ""
echo "Nächster Schritt: Push zu GitHub"
echo ""
echo "Für jedes Repo ausführen:"
echo ""
echo "cd $REPOS_DIR/german-accounting-suite"
echo "git remote add origin https://github.com/$GITHUB_USER/german-accounting-suite.git"
echo "git push -u origin main"
echo ""
echo "ODER mit GitHub CLI:"
echo "gh repo create german-accounting-suite --private --source=. --push"
echo ""
echo "Alle Repos auf einmal:"
cd "$REPOS_DIR"
for dir in */; do
    repo=$(basename "$dir")
    echo "cd $REPOS_DIR/$repo && git remote add origin https://github.com/$GITHUB_USER/$repo.git && git push -u origin main"
done
