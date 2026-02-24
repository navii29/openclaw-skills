#!/usr/bin/env python3
"""
Inbox AI Skill - Demo Script
Zeigt automatisierte E-Mail-Verarbeitung für Unternehmen
"""

import os
import sys

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def demo_categorization():
    """Demo: E-Mail Kategorisierung"""
    print_section("1. Automatische E-Mail Kategorisierung")
    
    emails = [
        ("Buchungsanfrage für Juni", "Ich möchte einen Termin buchen..."),
        ("RE: Support Ticket #1234", "Mein Problem ist dringend!"),
        ("Angebot angefordert", "Bitte senden Sie mir ein Angebot"),
        ("Gewinnspiel!!!", "Sie haben 1 Million gewonnen!!!"),
    ]
    
    print("📧 Beispiel-E-Mails werden kategorisiert:\n")
    
    for subject, body in emails:
        # Simulierte Kategorisierung
        if "dringend" in body.lower() or "!!!" in subject:
            category = "🔴 DRINGEND"
        elif "buchung" in subject.lower() or "termin" in body.lower():
            category = "📅 Buchung"
        elif "angebot" in subject.lower():
            category = "💼 Anfrage"
        elif "gewinnspiel" in subject.lower() or "!!!" in subject:
            category = "🗑️ Spam"
        else:
            category = "📨 Allgemein"
        
        print(f"   {category:<15} | {subject[:40]}")
    
    print("\n💡 Automatische Kategorien:")
    print("   • Buchung / Termin-Anfragen")
    print("   • Support-Anfragen (mit Eskalation)")
    print("   • Angebots-Anfragen")
    print("   • Spam (automatisch archivieren)")

def demo_prioritization():
    """Demo: Intelligente Priorisierung"""
    print_section("2. Intelligente Priorisierung")
    
    print("📊 Prioritäts-Scores (0.0 - 1.0):\n")
    
    examples = [
        ("bestandskunde@firma.de", "Vertragsverlängerung", 0.95),
        ("neukunde@startup.de", "Erstanfrage", 0.80),
        ("newsletter@shop.de", "Wochenangebote", 0.20),
        ("support@tool.de", "Störungsmeldung", 0.90),
    ]
    
    for sender, subject, score in examples:
        bar = "█" * int(score * 10) + "░" * (10 - int(score * 10))
        print(f"   [{bar}] {score:.2f} | {subject[:30]}")
    
    print("\n💡 Priorisierungs-Faktoren:")
    print("   • Absender-Domain (Bestandskunden = höher)")
    print("   • Keywords (dringend, problem, störung)")
    print("   • Zeitliche Dringlichkeit")

def demo_auto_reply():
    """Demo: Automatische Antworten"""
    print_section("3. Automatische Antworten")
    
    print("🤖 AI-generierte Antworten:\n")
    
    print("   EINGANG:")
    print("   ─────────────────────────────────────")
    print("   Von: neukunde@beispiel.de")
    print("   Betreff: Angebot für Webdesign gesucht")
    print("")
    print("   > Guten Tag,")
    print("   > wir benötigen ein neues Webdesign für")
    print("   > unsere Unternehmenswebsite.")
    print("")
    
    print("   AUTO-ANTWORT:")
    print("   ─────────────────────────────────────")
    print("   Guten Tag,")
    print("")
    print("   vielen Dank für Ihre Anfrage! Ich habe Ihr")
    print("   Anliegen erhalten und werde mich innerhalb")
    print("   von 24 Stunden bei Ihnen melden.")
    print("")
    print("   Für dringende Anliegen erreichen Sie mich")
    print("   auch telefonisch unter +49 123 456789.")
    print("")
    print("   Mit freundlichen Grüßen")
    print("   Ihr Navii Automation Team")
    print("")
    print("   ⚡ Gesendet in < 5 Minuten (24/7)")

def demo_escalation():
    """Demo: Eskalation für komplexe Fälle"""
    print_section("4. Smarte Eskalation")
    
    print("🚨 Fälle, die an Menschen eskaliert werden:\n")
    
    escalations = [
        ("Beschwerde über Mitarbeiter", "Negativer Sentiment-Score: 0.85"),
        ("Vertragskündigung", "Kritisches Geschäftsereignis"),
        ("Rechtsstreitigkeit", "Rechtliche Keywords erkannt"),
        ("Spezielle Rabattforderung", "Nicht im Standard-Template"),
    ]
    
    for case, reason in escalations:
        print(f"   ⚠️  {case}")
        print(f"      → {reason}")
        print(f"      → Telegram-Benachrichtigung gesendet")
        print()
    
    print("💡 Eskalation-Threshold: 0.7 (konfigurierbar)")

def demo_summary():
    """Demo: TL;DR Zusammenfassungen"""
    print_section("5. E-Mail Zusammenfassungen")
    
    print("📨 Langer E-Mail-Thread:\n")
    print("   [14 Nachrichten, 3.200 Wörter]")
    print("   - Erstanfrage (15.02.)")
    print("   - Klärung Details (16.02.)")
    print("   - Angebotsänderung (18.02.)")
    print("   - Nachfassung (20.02.)")
    print("   - ...")
    
    print("\n   🤖 AI-ZUSAMMENFASSUNG:")
    print("   ─────────────────────────────────────")
    print("   • Kunde möchte Projekttermin vorziehen")
    print("   • Ursprünglich: 01.04. → Gewünscht: 15.03.")
    print("   • Zusätzliche Features angefragt")
    print("   • Kunde wartet auf Kostenschätzung")
    print("   ⚡ Lesedauer gespart: ~12 Minuten")

def demo_stats():
    """Demo: Statistiken"""
    print_section("6. Performance-Statistiken")
    
    print("📊 Letzte 30 Tage:\n")
    print("   ┌─────────────────────────────────────┐")
    print("   │  E-Mails verarbeitet:      1,247    │")
    print("   │  Automatisch beantwortet:  892 (71%)│")
    print("   │  Durchschn. Antwortzeit:   3.2 min  │")
    print("   │  Eskaliert:                45 (4%)  │")
    print("   │  Spam erkannt:             78 (6%)  │")
    print("   └─────────────────────────────────────┘")
    
    print("\n⏱️  Zeitersparnis: ~25 Stunden/Monat")

def main():
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   📧 INBOX AI v2.0 - DEMO                                 ║
    ║                                                           ║
    ║   KI-gestützte E-Mail Automatisierung für Unternehmen     ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    demo_categorization()
    demo_prioritization()
    demo_auto_reply()
    demo_escalation()
    demo_summary()
    demo_stats()
    
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   ✅ DEMO ABGESCHLOSSEN                                   ║
    ║                                                           ║
    ║   Preis: 199 EUR / Monat (inkl. 1000 E-Mails)            ║
    ║   Zusätzliche E-Mails: 0.10 EUR / 100 E-Mails            ║
    ║                                                           ║
    ║   Unterstützte Provider: IONOS, Gmail, Custom IMAP       ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)

if __name__ == '__main__':
    main()
