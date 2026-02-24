const { chromium } = require('playwright');

const NOTION_PAGE_URL = 'https://www.notion.so/30cbf9ffaf15809685d6fc4f2e64864d';

const PROPERTIES = [
  { name: 'Titel', type: 'text' },
  { name: 'Score', type: 'number' },
  { name: 'Tier', type: 'select', options: ['🔥 HOT', '⚡ WARM', '🧊 COLD'] },
  { name: 'Status', type: 'select', options: ['NEW', 'CONTACTED', 'REPLY', 'MEETING', 'WON', 'LOST'] },
  { name: 'Location', type: 'text' },
  { name: 'LinkedIn', type: 'url' },
  { name: 'Outreach', type: 'text' },
  { name: 'Signals', type: 'text' }
];

async function setupNotionDatabase() {
  console.log('🎯 Starte Notion Database Setup mit Playwright...');
  
  const browser = await chromium.launch({ 
    headless: false,
    executablePath: '/Applications/Google Chrome Beta.app/Contents/MacOS/Google Chrome Beta'
  });
  
  const context = await browser.newContext();
  const page = await context.newPage();
  
  // Lade die Notion-Seite
  console.log('📄 Öffne Notion-Seite...');
  await page.goto(NOTION_PAGE_URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForTimeout(5000);
  
  // Warte auf die Datenbank
  await page.waitForTimeout(3000);
  
  // Füge Properties hinzu
  for (const prop of PROPERTIES) {
    console.log(`➕ Füge hinzu: ${prop.name} (${prop.type})`);
    
    // Finde und klicke "Add property" Button
    const addButton = await page.locator('button:has-text("Add property"), [data-testid="property-add-button"]').first();
    if (await addButton.isVisible().catch(() => false)) {
      await addButton.click();
    } else {
      // Alternative: Klicke auf das + Icon in der Header-Zeile
      const plusButtons = await page.locator('button').filter({ hasText: /^$/ }).all();
      for (const btn of plusButtons) {
        const aria = await btn.getAttribute('aria-label');
        if (aria?.includes('property') || aria?.includes('Add')) {
          await btn.click();
          break;
        }
      }
    }
    
    await page.waitForTimeout(500);
    
    // Property Name eingeben
    const nameInput = await page.locator('input[placeholder*="Property"], input[placeholder*="property"]').first();
    if (await nameInput.isVisible().catch(() => false)) {
      await nameInput.fill(prop.name);
    }
    
    await page.waitForTimeout(300);
    
    // Property Type auswählen
    if (prop.type !== 'text') {
      const typeMenu = await page.locator('[role="menuitem"]').filter({ hasText: new RegExp(`^${prop.type}$`, 'i') }).first();
      if (await typeMenu.isVisible().catch(() => false)) {
        await typeMenu.click();
      }
    }
    
    await page.waitForTimeout(300);
    
    // Select Options hinzufügen
    if (prop.options) {
      for (const opt of prop.options) {
        const optInput = await page.locator('input[placeholder*="option"], input[placeholder*="Option"]').first();
        if (await optInput.isVisible().catch(() => false)) {
          await optInput.fill(opt);
          await optInput.press('Enter');
          await page.waitForTimeout(200);
        }
      }
    }
    
    await page.waitForTimeout(300);
    
    // Speichern
    const saveButton = await page.locator('button[type="submit"], button:has-text("Save")').first();
    if (await saveButton.isVisible().catch(() => false)) {
      await saveButton.click();
    } else {
      await page.keyboard.press('Enter');
    }
    
    await page.waitForTimeout(800);
  }
  
  console.log('✅ Properties hinzugefügt!');
  
  // Erstelle Board View
  console.log('📋 Erstelle Board View...');
  const addViewBtn = await page.locator('button:has-text("Add view"), [data-testid="view-add-button"]').first();
  if (await addViewBtn.isVisible().catch(() => false)) {
    await addViewBtn.click();
    await page.waitForTimeout(500);
    
    const boardOption = await page.locator('[role="menuitem"]:has-text("Board"), button:has-text("Board")').first();
    if (await boardOption.isVisible().catch(() => false)) {
      await boardOption.click();
      await page.waitForTimeout(1000);
      
      // Konfiguriere Board: Group by Tier
      const settingsBtn = await page.locator('button[aria-label="View settings"], button:has-text("Settings")').first();
      if (await settingsBtn.isVisible().catch(() => false)) {
        await settingsBtn.click();
        await page.waitForTimeout(500);
        
        // Suche Group by Option
        const groupBySelect = await page.locator('text=Group by').locator('..').locator('select, [role="combobox"]').first();
        if (await groupBySelect.isVisible().catch(() => false)) {
          await groupBySelect.selectOption('Tier');
        }
      }
    }
  }
  
  console.log('✅ Board View erstellt!');
  console.log('\n🎉 Setup abgeschlossen!');
  console.log('Die Datenbank ist jetzt bereit für den CSV-Import.');
  
  // Browser bleibt offen für manuelle Nacharbeit
  // await browser.close();
}

setupNotionDatabase().catch(err => {
  console.error('❌ Fehler:', err.message);
  process.exit(1);
});
