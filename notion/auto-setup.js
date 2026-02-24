// Notion Lead Pipeline Auto-Setup
// Führe dies in der Browser Console auf der Notion Datenbank-Seite aus

(async function setupNotionDatabase() {
  const properties = [
    { name: 'Titel', type: 'text' },
    { name: 'Score', type: 'number' },
    { name: 'Tier', type: 'select', options: ['🔥 HOT', '⚡ WARM', '🧊 COLD'] },
    { name: 'Status', type: 'select', options: ['NEW', 'CONTACTED', 'REPLY', 'MEETING', 'WON', 'LOST'] },
    { name: 'Location', type: 'text' },
    { name: 'LinkedIn', type: 'url' },
    { name: 'Outreach', type: 'text' },
    { name: 'Signals', type: 'text' }
  ];

  console.log('🎯 Starte Notion Database Setup...');
  
  for (const prop of properties) {
    console.log(`➕ Füge hinzu: ${prop.name} (${prop.type})`);
    
    // Klicke auf "Add property"
    const addBtn = document.querySelector('[data-testid="property-add-button"]') || 
                   document.querySelector('[role="button"]:has-text("Add property")');
    if (addBtn) addBtn.click();
    
    await new Promise(r => setTimeout(r, 500));
    
    // Property Name eingeben
    const nameInput = document.querySelector('input[placeholder="Property name"]');
    if (nameInput) {
      nameInput.value = prop.name;
      nameInput.dispatchEvent(new Event('input', { bubbles: true }));
    }
    
    await new Promise(r => setTimeout(r, 300));
    
    // Type auswählen
    if (prop.type !== 'text') {
      const typeBtn = document.querySelector(`[role="menuitem"]:has-text("${prop.type}")`);
      if (typeBtn) typeBtn.click();
    }
    
    await new Promise(r => setTimeout(r, 300));
    
    // Select Options hinzufügen
    if (prop.options) {
      for (const opt of prop.options) {
        const optInput = document.querySelector('input[placeholder="Add an option"]');
        if (optInput) {
          optInput.value = opt;
          optInput.dispatchEvent(new Event('input', { bubbles: true }));
          optInput.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' }));
        }
        await new Promise(r => setTimeout(r, 200));
      }
    }
    
    // Speichern
    const saveBtn = document.querySelector('[role="button"]:has-text("Save")') ||
                    document.querySelector('button[type="submit"]');
    if (saveBtn) saveBtn.click();
    
    await new Promise(r => setTimeout(r, 500));
  }
  
  console.log('✅ Setup abgeschlossen!');
})();
