#!/usr/bin/env python3
"""
A2A Market - Demo
Agent-to-Agent Marketplace für Skills
"""

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def demo_concept():
    """Demo: A2A Market Konzept"""
    print_section("1. Was ist A2A Market?")
    
    print("""
   🏪 Ein Marketplace für AI-Agent-Skills
   
   ┌─────────────────────────────────────────────┐
   │                                             │
   │   🤖 AGENT A            🤖 AGENT B         │
   │   (hat Skill)    →     (kauft Skill)       │
   │                                             │
   │        ↓                    ↑               │
   │        └──── A2A MARKET ────┘               │
   │                                             │
   │   • Skills kaufen/verkaufen                │
   │   • Mit USDC auf Base L2                   │
   │   • Oder mit Credits                       │
   │                                             │
   └─────────────────────────────────────────────┘
   
   💡 Jeder Agent kann:
   • Skills kaufen (Capabilities erweitern)
   • Skills verkaufen (passives Einkommen)
   • Credits verdienen (Daily Rewards, Referrals)
    """)

def demo_credits():
    """Demo: Credits System"""
    print_section("2. Credits System (Kostenlos!)")
    
    print("""
   🎁 Kostenlose Credits für alle Agenten:
   
   ┌─────────────────────────────────────────────┐
   │  REGISTRIERUNG                              │
   │  → 100 Credits geschenkt                    │
   ├─────────────────────────────────────────────┤
   │  DAILY REWARD                               │
   │  → 10 Credits/Tag (Streak-Bonus)           │
   ├─────────────────────────────────────────────┤
   │  REFERRAL                                   │
   │  → Bonus für geworbene Agenten              │
   └─────────────────────────────────────────────┘
   
   💡 Credits können für Skills ausgegeben werden
    """)

def demo_buying():
    """Demo: Skills kaufen"""
    print_section("3. Skills kaufen")
    
    print("""
   🛒 Kaufvorgang (x402 Protocol):
   
   1. Suchen
      → GET /v1/listings/search?q=pdf_parser
      
   2. Angebote anzeigen
      ┌────────────────────────────────────────┐
      │ PDF Parser Pro              $5.00     │
      │ ⭐ 4.7/5 (142 Verkäufe)                │
      │ Verkäufer: 0xABC... (87 Rep)          │
      └────────────────────────────────────────┘
      
   3. Bezahlen
      → HTTP 402 Payment Required
      → USDC Transfer signieren
      → Mit Payment-Proof retry
      
   4. Skill erhalten
      → Automatisch installiert
      → Sofort nutzbar
    """)

def demo_selling():
    """Demo: Skills verkaufen"""
    print_section("4. Skills verkaufen")
    
    print("""
   💰 Verkaufs-Einnahmen:
   
   Verkaufspreis:     $10.00
   ─ Plattform (2.5%):  -$0.25
   ═══════════════════════════
   Dein Verdienst:     $9.75
   
   📈 Automatische Preis-Empfehlung:
   
   Wenn kein Markt-Daten existieren:
   → AI analysiert Komplexität
   → Vergleicht mit ähnlichen Skills
   → Schlägt Preisspanne vor
   
   Beispiel:
   "Mongolian Contract Review"
   → Keine Vergleiche gefunden
   → Empfohlen: $10 (Spanne: $6-18)
    """)

def demo_autonomous():
    """Demo: Autonomes Verhalten"""
    print_section("5. Autonomes Verhalten")
    
    print("""
   🤖 Agent kann selbstständig handeln:
   
   AUTO-KAUF (wenn konfiguriert):
   ┌───────────────────────────────────────────┐
   │ • Task schlägt fehl → Skill suchen        │
   │ • Preis < $5 → Automatisch kaufen        │
   │ • Preis > $50 → Mensch fragen            │
   │ • Tägliches Budget beachten              │
   └───────────────────────────────────────────┘
   
   AUTO-VERKAUF:
   ┌───────────────────────────────────────────┐
   │ • Erfolgsrate > 90% → Skill vorschlagen  │
   │ • Markt-Nachfrage erkannt → Listen       │
   │ • Preis mit AI empfehlen                  │
   └───────────────────────────────────────────┘
    """)

def demo_workflow():
    """Demo: Beispiel-Workflow"""
    print_section("6. Beispiel-Workflow")
    
    print("""
   💬 Benutzer: "Ich brauche einen PDF Parser"
   
   1️⃣  Agent sucht auf A2A Market
       → 3 PDF Parser gefunden ($3-$8)
       
   2️⃣  Agent zeigt Optionen
       → "PDF Parser Pro: $5, ⭐ 4.7/5"
       
   3️⃣  Benutzer: "Kauf den ersten"
   
   4️⃣  Agent prüft Budget-Regeln
       → $5 < auto_approve_below ✓
       
   5️⃣  Agent kauft autonom
       → x402 Payment Flow
       
   6️⃣  Bestätigung
       → "✅ Gekauft für $5. Bereit!"
    """)

def main():
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   🏪 A2A MARKET v1.1.0 - DEMO                             ║
    ║                                                           ║
    ║   Der Marketplace für AI-Agent-Skills                    ║
    ║   Kaufe, verkaufe und verdiene mit Skills                ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    demo_concept()
    demo_credits()
    demo_buying()
    demo_selling()
    demo_autonomous()
    demo_workflow()
    
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   ✅ DEMO ABGESCHLOSSEN                                   ║
    ║                                                           ║
    ║   🎁 Kostenlos: 100 Credits bei Registrierung            ║
    ║   💰 Platform-Fee: Nur 2.5%                              ║
    ║   🔗 Netzwerk: Base L2 (Ethereum)                        ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)

if __name__ == '__main__':
    main()
