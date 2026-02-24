#!/usr/bin/env node
/**
 * LinkedIn Lead Intelligence Agent
 * 
 * Chrome-basierte Lead-Recherche für die Agentur.
 * Extrahiert Profil-Daten, bewertet Lead-Qualität, 
 * generiert personalisierte Outreach-Vorschläge.
 */

const fs = require('fs');
const path = require('path');

// Konfiguration
const CONFIG = {
  outputDir: './leads',
  minLeadScore: 60,  // Mindestscore für "hot leads"
  searchUrls: [
    // Beispiel-Such-URLs (anpassbar)
    'https://www.linkedin.com/search/results/people/?keywords=CEO%20SaaS%20Germany',
    'https://www.linkedin.com/search/results/people/?keywords=Founder%20Startup%20Berlin'
  ]
};

// Lead-Scoring Kriterien
const SCORING = {
  titleKeywords: {
    'CEO': 25, 'Founder': 25, 'Co-Founder': 25, 'Geschäftsführer': 25,
    'CTO': 20, 'COO': 20, 'Head of': 15, 'Director': 15,
    'Manager': 10, 'VP': 20
  },
  companyKeywords: {
    'SaaS': 15, 'Software': 10, 'Tech': 10, 'AI': 20, 'Automation': 20,
    'Startup': 10, 'Scale-up': 15, 'Digital': 10
  },
  sizeIndicators: {
    '10-50': 20, '50-200': 25, '200-500': 20, '500-1000': 10
  }
};

/**
 * Extrahiert Profildaten aus einer LinkedIn-Seite
 */
async function extractProfileData(browserAPI, targetId) {
  // JavaScript, das auf der LinkedIn-Seite ausgeführt wird
  const extractionScript = `
    (() => {
      const data = {
        name: '',
        headline: '',
        currentTitle: '',
        company: '',
        location: '',
        about: '',
        experience: [],
        url: window.location.href,
        extractedAt: new Date().toISOString()
      };
      
      // Name
      const nameEl = document.querySelector('h1');
      if (nameEl) data.name = nameEl.innerText.trim();
      
      // Headline (Untertitel)
      const headlineEl = document.querySelector('.text-body-medium');
      if (headlineEl) data.headline = headlineEl.innerText.trim();
      
      // Aktuelle Position
      const expSection = document.querySelector('#experience');
      if (expSection) {
        const firstExp = expSection.closest('section').querySelector('li');
        if (firstExp) {
          const titleEl = firstExp.querySelector('span[aria-hidden="true"]');
          if (titleEl) data.currentTitle = titleEl.innerText.trim();
          
          const companyEl = firstExp.querySelector('.hoverable-link-text');
          if (companyEl) data.company = companyEl.innerText.trim();
        }
      }
      
      // Location
      const locationEl = document.querySelector('.t-16.t-black--light');
      if (locationEl) data.location = locationEl.innerText.trim();
      
      // About
      const aboutSection = document.querySelector('#about');
      if (aboutSection) {
        const aboutText = aboutSection.closest('section').querySelector('.inline-show-more-text');
        if (aboutText) data.about = aboutText.innerText.trim();
      }
      
      return data;
    })()
  `;
  
  return extractionScript;
}

/**
 * Berechnet Lead-Score basierend auf Profildaten
 */
function calculateLeadScore(profile) {
  let score = 0;
  const signals = [];
  
  const text = `${profile.headline} ${profile.currentTitle} ${profile.company} ${profile.about}`.toLowerCase();
  
  // Title-Scoring
  for (const [keyword, points] of Object.entries(SCORING.titleKeywords)) {
    if (text.includes(keyword.toLowerCase())) {
      score += points;
      signals.push(`Title: ${keyword} (+${points})`);
    }
  }
  
  // Company-Scoring
  for (const [keyword, points] of Object.entries(SCORING.companyKeywords)) {
    if (text.includes(keyword.toLowerCase())) {
      score += points;
      signals.push(`Industry: ${keyword} (+${points})`);
    }
  }
  
  // Entscheider-Status Bonus
  if (text.includes('founder') || text.includes('ceo') || text.includes('geschäftsführer')) {
    score += 10;
    signals.push('Decision maker (+10)');
  }
  
  // AI/Automation Interesse
  if (text.includes('ai') || text.includes('automation') || text.includes('efficiency')) {
    score += 15;
    signals.push('AI/Automation interest (+15)');
  }
  
  return {
    score: Math.min(score, 100),
    signals,
    tier: score >= 80 ? 'HOT' : score >= 60 ? 'WARM' : 'COLD'
  };
}

/**
 * Generiert personalisierte Outreach-Message
 */
function generateOutreach(profile, scoreData) {
  const templates = {
    HOT: [
      `Hi {{name}}, als {{title}} bei {{company}} interessieren Sie sich sicher für operative Effizienz. Wir helfen Tech-Führungskräften, 10+ Stunden/Woche durch AI-Automation zu sparen. Interesse an einem 15-minütigen Austausch?`,
      `{{name}}, gesehen dass Sie bei {{company}} {{title}} sind. Wir haben gerade eine Automation für ein {{industry}}-Unternehmen gebaut, die 40% Zeitersparnis bringt. Passt das zu Ihren aktuellen Prioritäten?`
    ],
    WARM: [
      `Hallo {{name}}, Ihr Background bei {{company}} ist interessant. Wir spezialisieren uns auf AI-Automation für {{industry}}. Gibt es Prozesse, die Sie gerade optimieren möchten?`,
      `Hi {{name}}, als {{title}} bei {{company}} – wie skalieren Sie aktuell Ihre operativen Prozesse? Wir helfen Teams, repetitive Arbeit zu automatisieren.`
    ],
    COLD: [
      `Hallo {{name}}, ich folge {{company}} schon länger. Spannende Entwicklung im {{industry}}-Bereich. Wir helfen Unternehmen dieser Größe bei der Prozess-Automation.`,
      `Hi {{name}}, gesehen dass Sie bei {{company}} arbeiten. Wir bauen AI-Automation für Teams, die schneller wachsen wollen.`
    ]
  };
  
  const tierTemplates = templates[scoreData.tier];
  const template = tierTemplates[Math.floor(Math.random() * tierTemplates.length)];
  
  // Simple Template-Engine
  const industry = extractIndustry(profile);
  return template
    .replace('{{name}}', profile.name.split(' ')[0])
    .replace('{{title}}', profile.currentTitle || profile.headline?.split(' at ')[0] || 'Leader')
    .replace('{{company}}', profile.company || 'Ihrem Unternehmen')
    .replace('{{industry}}', industry);
}

function extractIndustry(profile) {
  const text = `${profile.headline} ${profile.about}`.toLowerCase();
  if (text.includes('saas')) return 'SaaS';
  if (text.includes('e-commerce') || text.includes('ecommerce')) return 'E-Commerce';
  if (text.includes('fintech')) return 'Fintech';
  if (text.includes('health')) return 'HealthTech';
  if (text.includes('ai') || text.includes('artificial intelligence')) return 'AI';
  return 'Tech';
}

/**
 * Speichert Lead in strukturiertem Format
 */
function saveLead(lead) {
  if (!fs.existsSync(CONFIG.outputDir)) {
    fs.mkdirSync(CONFIG.outputDir, { recursive: true });
  }
  
  const filename = `${lead.tier}-${lead.name.replace(/\s+/g, '_')}-${Date.now()}.json`;
  const filepath = path.join(CONFIG.outputDir, filename);
  
  fs.writeFileSync(filepath, JSON.stringify(lead, null, 2));
  console.log(`✅ Lead gespeichert: ${filepath}`);
  return filepath;
}

/**
 * Generiert tägliche Lead-Report
 */
function generateDailyReport() {
  if (!fs.existsSync(CONFIG.outputDir)) return null;
  
  const files = fs.readdirSync(CONFIG.outputDir).filter(f => f.endsWith('.json'));
  const leads = files.map(f => JSON.parse(fs.readFileSync(path.join(CONFIG.outputDir, f))));
  
  const report = {
    date: new Date().toISOString().split('T')[0],
    total: leads.length,
    hot: leads.filter(l => l.tier === 'HOT').length,
    warm: leads.filter(l => l.tier === 'WARM').length,
    cold: leads.filter(l => l.tier === 'COLD').length,
    leads: leads.sort((a, b) => b.score - a.score).slice(0, 10)
  };
  
  const reportPath = path.join(CONFIG.outputDir, `report-${report.date}.json`);
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
  
  return report;
}

// Export für externe Nutzung
module.exports = {
  extractProfileData,
  calculateLeadScore,
  generateOutreach,
  saveLead,
  generateDailyReport,
  CONFIG
};

// CLI-Modus
if (require.main === module) {
  console.log('🎯 LinkedIn Lead Intelligence Agent');
  console.log('=====================================\n');
  console.log('Bereit für Chrome-Integration. Nutze via:');
  console.log('  - Browser-Snapshot → Profil-Extraktion');
  console.log('  - Scoring → Outreach-Generierung');
  console.log('  - Export → CRM/Notion\n');
}
