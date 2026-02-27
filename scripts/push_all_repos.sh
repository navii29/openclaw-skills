#!/bin/bash
# Push alle Repositories zu GitHub

REPOS_DIR="/Users/fridolin/.openclaw/workspace/github-repos"
GITHUB_USER="navii29"

echo "🚀 Pushing alle Repositories zu GitHub..."
echo ""

cd "$REPOS_DIR"

for dir in */; do
    repo=$(basename "$dir")
    echo "📤 Pushing: $repo"
    
    cd "$REPOS_DIR/$repo"
    
    # Remote hinzufügen (falls nicht vorhanden)
    git remote remove origin 2>/dev/null || true
    git remote add origin "https://github.com/$GITHUB_USER/$repo.git" 2>/dev/null || true
    
    # Push
    if git push -u origin main 2>&1; then
        echo "  ✅ $repo gepusht"
    else
        echo "  ❌ $repo fehlgeschlagen (kein Zugriff/Repo existiert nicht)"
    fi
    
    echo ""
done

echo "=========================="
echo "Fertig!"
