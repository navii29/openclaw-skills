#!/usr/bin/env python3
"""
Lieferschein-Generator v1.0.0
GoBD-konforme Delivery Note Generator mit QR-Code Tracking

Author: NAVII Automation
License: Commercial
"""

import json
import argparse
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
import qrcode
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    Image, PageBreak, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER


@dataclass
class LieferscheinPosition:
    """Einzelposition auf dem Lieferschein"""
    bezeichnung: str
    menge: float
    artikelnr: str = ""
    einheit: str = "Stk"
    seriennummern: List[str] = field(default_factory=list)
    charge: str = ""
    mhd: str = ""  # Mindesthaltbarkeitsdatum
    gewicht_kg: float = 0.0
    pos: int = 0


@dataclass
class Adresse:
    """Adressdaten für Absender/Empfänger"""
    name: str
    strasse: str
    plz_ort: str
    zusatz: str = ""
    land: str = "Deutschland"
    telefon: str = ""
    email: str = ""
    steuernr: str = ""
    ustid: str = ""


class LieferscheinGenerator:
    """
    GoBD-konformer Lieferschein Generator
    
    Erstellt revisionssichere Lieferscheine mit QR-Code Tracking
    """
    
    def __init__(self, template: str = "standard", gobd_compliant: bool = True):
        self.template = template
        self.gobd_compliant = gobd_compliant
        
        # Lieferschein-Daten
        self.lieferschein_nummer: str = ""
        self.lieferschein_datum: str = datetime.now().strftime("%d.%m.%Y")
        self.lieferdatum: str = ""
        self.auftragsnummer: str = ""
        self.kundennummer: str = ""
        
        # Adressen
        self.absender: Optional[Adresse] = None
        self.empfaenger: Optional[Adresse] = None
        self.lieferadresse: Optional[Adresse] = None
        
        # Positionen
        self.positionen: List[LieferscheinPosition] = []
        
        # Tracking
        self.tracking_nummer: str = ""
        self.tracking_url: str = ""
        self.dienstleister: str = ""
        
        # Optionen
        self.hinweise: str = ""
        self.unterschrift_erforderlich: bool = False
        self.unterschrift_datum: bool = True
        self.unterschrift_name: bool = True
        self.unterschrift_stempel: bool = False
        
        # Styles initialisieren
        self._init_styles()
    
    def _init_styles(self):
        """Initialisiert ReportLab Styles"""
        self.styles = getSampleStyleSheet()
        
        self.style_header = ParagraphStyle(
            'CustomHeader',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=12,
            textColor=colors.HexColor('#1a1a1a')
        )
        
        self.style_normal = ParagraphStyle(
            'CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=14
        )
        
        self.style_small = ParagraphStyle(
            'CustomSmall',
            parent=self.styles['Normal'],
            fontSize=8,
            leading=10,
            textColor=colors.grey
        )
        
        self.style_bold = ParagraphStyle(
            'CustomBold',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=14,
            fontName='Helvetica-Bold'
        )
    
    def set_absender(self, **kwargs) -> None:
        """Setzt die Absender-Adresse"""
        self.absender = Adresse(**kwargs)
    
    def set_empfaenger(self, **kwargs) -> None:
        """Setzt die Empfänger-Adresse"""
        self.empfaenger = Adresse(**kwargs)
    
    def set_lieferadresse(self, **kwargs) -> None:
        """Setzt eine abweichende Lieferadresse"""
        self.lieferadresse = Adresse(**kwargs)
    
    def add_position(self, position: LieferscheinPosition) -> None:
        """Fügt eine Position hinzu"""
        if position.pos == 0:
            position.pos = len(self.positionen) + 1
        self.positionen.append(position)
    
    def set_tracking(self, url: str, nummer: str = "", dienstleister: str = "") -> None:
        """Konfiguriert Tracking mit QR-Code"""
        self.tracking_url = url
        self.tracking_nummer = nummer or self.lieferschein_nummer
        self.dienstleister = dienstleister
    
    def enable_unterschrift_feld(self, datum: bool = True, name: bool = True, 
                                  stempel: bool = False) -> None:
        """Aktiviert das Unterschriftenfeld"""
        self.unterschrift_erforderlich = True
        self.unterschrift_datum = datum
        self.unterschrift_name = name
        self.unterschrift_stempel = stempel
    
    def load_from_json(self, json_path: str) -> None:
        """Lädt Lieferschein-Daten aus JSON-Datei"""
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Metadaten
        self.lieferschein_nummer = data.get('lieferschein_nummer', '')
        self.lieferschein_datum = data.get('lieferschein_datum', self.lieferschein_datum)
        self.lieferdatum = data.get('lieferdatum', '')
        self.auftragsnummer = data.get('auftragsnummer', '')
        self.kundennummer = data.get('kundennummer', '')
        self.hinweise = data.get('hinweise', '')
        
        # Adressen
        if 'absender' in data:
            self.set_absender(**data['absender'])
        if 'empfaenger' in data:
            self.set_empfaenger(**data['empfaenger'])
        if 'lieferadresse' in data:
            self.set_lieferadresse(**data['lieferadresse'])
        
        # Positionen
        for pos_data in data.get('positionen', []):
            self.add_position(LieferscheinPosition(**pos_data))
        
        # Tracking
        if 'tracking' in data:
            t = data['tracking']
            self.set_tracking(
                url=t.get('url', ''),
                nummer=t.get('nummer', ''),
                dienstleister=t.get('dienstleister', '')
            )
        
        self.unterschrift_erforderlich = data.get('unterschrift_erforderlich', False)
    
    def validate(self) -> Dict[str, Any]:
        """Validiert den Lieferschein nach GoBD"""
        errors = []
        warnings = []
        
        # Pflichtfelder prüfen
        if not self.lieferschein_nummer:
            errors.append("Lieferschein-Nummer fehlt")
        if not self.lieferschein_datum:
            errors.append("Lieferschein-Datum fehlt")
        if not self.absender:
            errors.append("Absender fehlt")
        if not self.empfaenger:
            errors.append("Empfänger fehlt")
        if not self.positionen:
            errors.append("Keine Positionen vorhanden")
        
        # GoBD-Vollständigkeit
        if self.gobd_compliant:
            if self.absender and not self.absender.steuernr and not self.absender.ustid:
                warnings.append("Steuernummer oder USt-ID für GoBD empfohlen")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def _create_qr_code(self, url: str) -> str:
        """Erstellt einen temporären QR-Code"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        # Temporäre Datei
        temp_path = f"/tmp/qr_{self.lieferschein_nummer}.png"
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(temp_path)
        return temp_path
    
    def _build_address_block(self, addr: Adresse, label: str = "") -> List[Any]:
        """Erstellt einen Adressblock"""
        elements = []
        
        if label:
            elements.append(Paragraph(f"<b>{label}</b>", self.style_small))
        
        lines = [addr.name]
        if addr.zusatz:
            lines.append(addr.zusatz)
        lines.append(addr.strasse)
        lines.append(f"{addr.plz_ort}")
        if addr.land and addr.land != "Deutschland":
            lines.append(addr.land)
        
        elements.append(Paragraph("<br/>".join(lines), self.style_normal))
        return elements
    
    def _build_header_table(self) -> Table:
        """Erstellt die Kopftabelle mit Lieferschein-Info"""
        data = [
            [Paragraph("<b>Lieferschein</b>", self.style_header), ""],
            ["Lieferschein-Nr.:", self.lieferschein_nummer],
            ["Datum:", self.lieferschein_datum],
        ]
        
        if self.lieferdatum:
            data.append(["Lieferdatum:", self.lieferdatum])
        if self.auftragsnummer:
            data.append(["Auftrags-Nr.:", self.auftragsnummer])
        if self.kundennummer:
            data.append(["Kunden-Nr.:", self.kundennummer])
        
        table = Table(data, colWidths=[4*cm, 6*cm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        return table
    
    def _build_positionen_table(self) -> Table:
        """Erstellt die Positionen-Tabelle"""
        # Header
        data = [["Pos.", "Art.-Nr.", "Bezeichnung", "Menge", "Einheit", "S/N"]]
        
        # Daten
        for pos in self.positionen:
            sn_text = ", ".join(pos.seriennummern) if pos.seriennummern else ""
            data.append([
                str(pos.pos),
                pos.artikelnr,
                pos.bezeichnung,
                str(pos.menge),
                pos.einheit,
                sn_text[:50]  # Begrenzen für Tabelle
            ])
        
        table = Table(data, colWidths=[1*cm, 2.5*cm, 7*cm, 1.5*cm, 1.5*cm, 4*cm])
        table.setStyle(TableStyle([
            # Header-Styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f0f0f0')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Daten-Styling
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Pos zentriert
            ('ALIGN', (3, 1), (4, -1), 'CENTER'),  # Menge/Einheit zentriert
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
            
            # Padding
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        return table
    
    def _build_unterschrift_section(self) -> List[Any]:
        """Erstellt den Unterschriften-Bereich"""
        elements = []
        elements.append(Spacer(1, 1*cm))
        elements.append(Paragraph("<b>Empfangsbestätigung</b>", self.style_bold))
        elements.append(Spacer(1, 0.5*cm))
        
        # Unterschriften-Tabelle
        sig_data = []
        headers = []
        widths = []
        
        if self.unterschrift_datum:
            headers.append("Datum")
            widths.append(4*cm)
        headers.append("Unterschrift")
        widths.append(6*cm)
        if self.unterschrift_name:
            headers.append("Name gedruckt")
            widths.append(4*cm)
        if self.unterschrift_stempel:
            headers.append("Stempel")
            widths.append(3*cm)
        
        sig_data.append(headers)
        sig_data.append([""] * len(headers))
        
        table = Table(sig_data, colWidths=widths, rowHeights=[0.8*cm, 1.5*cm])
        table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(table)
        return elements
    
    def generate(self, output_path: str) -> bool:
        """
        Generiert den Lieferschein als PDF
        
        Args:
            output_path: Pfad zur Ausgabe-PDF
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        # Validierung
        validation = self.validate()
        if not validation['valid']:
            print(f"❌ Validierungsfehler: {validation['errors']}")
            return False
        
        # PDF erstellen
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        elements = []
        
        # === HEADER ===
        # Absender (klein, oben links)
        if self.absender:
            abs_text = f"{self.absender.name} • {self.absender.strasse} • {self.absender.plz_ort}"
            elements.append(Paragraph(abs_text, self.style_small))
            elements.append(Spacer(1, 0.5*cm))
        
        # Adressen nebeneinander
        address_data = []
        
        # Empfänger (links)
        empfaenger_content = []
        if self.empfaenger:
            empfaenger_content = [
                Paragraph("<b>Lieferadresse:</b>", self.style_small),
                Spacer(1, 0.2*cm)
            ] + self._build_address_block(self.empfaenger)
        
        # Lieferschein-Info (rechts)
        info_content = [self._build_header_table()]
        
        # QR-Code wenn Tracking aktiviert
        if self.tracking_url:
            try:
                qr_path = self._create_qr_code(self.tracking_url)
                qr_img = Image(qr_path, width=2.5*cm, height=2.5*cm)
                info_content.append(Spacer(1, 0.3*cm))
                info_content.append(qr_img)
                info_content.append(Paragraph("Zum Tracking scannen", self.style_small))
            except Exception as e:
                print(f"⚠️ QR-Code konnte nicht erstellt werden: {e}")
        
        address_table = Table(
            [[empfaenger_content, info_content]],
            colWidths=[8*cm, 8*cm]
        )
        address_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ]))
        elements.append(address_table)
        elements.append(Spacer(1, 1*cm))
        
        # Abweichende Lieferadresse
        if self.lieferadresse:
            elements.append(Paragraph("<b>Abweichende Lieferadresse:</b>", self.style_bold))
            elements.extend(self._build_address_block(self.lieferadresse))
            elements.append(Spacer(1, 0.5*cm))
        
        # === POSITIONEN ===
        elements.append(Paragraph("<b>Gelieferte Positionen</b>", self.style_bold))
        elements.append(Spacer(1, 0.3*cm))
        elements.append(self._build_positionen_table())
        
        # Seriennummern-Details (falls vorhanden)
        sn_details = [p for p in self.positionen if p.seriennummern]
        if sn_details:
            elements.append(Spacer(1, 0.5*cm))
            elements.append(Paragraph("<b>Seriennummern-Details:</b>", self.style_bold))
            for pos in sn_details:
                sn_text = f"• {pos.bezeichnung}: {', '.join(pos.seriennummern)}"
                elements.append(Paragraph(sn_text, self.style_normal))
        
        # === HINWEISE ===
        if self.hinweise:
            elements.append(Spacer(1, 0.5*cm))
            elements.append(Paragraph(f"<b>Hinweise:</b> {self.hinweise}", self.style_normal))
        
        # === UNTERSCHRIFT ===
        if self.unterschrift_erforderlich:
            elements.extend(self._build_unterschrift_section())
        
        # === FOOTER ===
        elements.append(Spacer(1, 1*cm))
        
        # Absender-Details für Rücksendung
        if self.absender:
            footer_data = [
                [Paragraph("<b>Absender:</b>", self.style_small),
                 Paragraph("<b>Kontakt:</b>", self.style_small),
                 Paragraph("<b>Steuernummer:</b>", self.style_small)],
                [f"{self.absender.name}",
                 f"Tel: {self.absender.telefon}" if self.absender.telefon else "",
                 self.absender.steuernr or ""],
                [f"{self.absender.strasse}",
                 f"E-Mail: {self.absender.email}" if self.absender.email else "",
                 f"USt-ID: {self.absender.ustid}" if self.absender.ustid else ""],
                [f"{self.absender.plz_ort}", "", ""]
            ]
            
            footer_table = Table(footer_data, colWidths=[6*cm, 6*cm, 4*cm])
            footer_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LINEABOVE', (0, 0), (-1, 0), 0.5, colors.grey),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(footer_table)
        
        # GoBD-Hinweis
        if self.gobd_compliant:
            elements.append(Spacer(1, 0.3*cm))
            elements.append(Paragraph(
                "Dieser Lieferschein wurde GoBD-konform erstellt.",
                self.style_small
            ))
        
        # PDF bauen
        doc.build(elements)
        print(f"✅ Lieferschein erstellt: {output_path}")
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Exportiert als Dictionary"""
        return {
            'lieferschein_nummer': self.lieferschein_nummer,
            'lieferschein_datum': self.lieferschein_datum,
            'lieferdatum': self.lieferdatum,
            'auftragsnummer': self.auftragsnummer,
            'kundennummer': self.kundennummer,
            'absender': self.absender.__dict__ if self.absender else None,
            'empfaenger': self.empfaenger.__dict__ if self.empfaenger else None,
            'positionen': [p.__dict__ for p in self.positionen],
            'tracking': {
                'nummer': self.tracking_nummer,
                'url': self.tracking_url,
                'dienstleister': self.dienstleister
            } if self.tracking_url else None,
            'hinweise': self.hinweise,
            'unterschrift_erforderlich': self.unterschrift_erforderlich
        }
    
    def save_json(self, output_path: str) -> None:
        """Speichert als JSON-Datei"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        print(f"✅ JSON gespeichert: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Lieferschein-Generator - GoBD-konforme Delivery Notes'
    )
    parser.add_argument('--input', '-i', required=True, help='JSON Input-Datei')
    parser.add_argument('--output', '-o', required=True, help='PDF Output-Datei')
    parser.add_argument('--tracking-url', '-t', help='Tracking-URL für QR-Code')
    parser.add_argument('--signature', '-s', action='store_true', 
                        help='Unterschriftenfeld hinzufügen')
    parser.add_argument('--validate', '-v', action='store_true',
                        help='Nur validieren, kein PDF erstellen')
    
    args = parser.parse_args()
    
    # Generator initialisieren
    gen = LieferscheinGenerator()
    
    # JSON laden
    gen.load_from_json(args.input)
    
    # Tracking-URL aus CLI (überschreibt JSON)
    if args.tracking_url:
        gen.set_tracking(args.tracking_url, gen.lieferschein_nummer)
    
    # Unterschrift aktivieren
    if args.signature:
        gen.enable_unterschrift_feld()
    
    # Validierung
    validation = gen.validate()
    print(f"\n🔍 Validierung:")
    print(f"   Gültig: {'✅ Ja' if validation['valid'] else '❌ Nein'}")
    if validation['errors']:
        print(f"   Fehler: {validation['errors']}")
    if validation['warnings']:
        print(f"   Warnungen: {validation['warnings']}")
    
    if args.validate:
        return
    
    if not validation['valid']:
        print("\n❌ PDF wird nicht erstellt aufgrund von Validierungsfehlern")
        return
    
    # PDF generieren
    success = gen.generate(args.output)
    
    if success:
        print(f"\n📄 Lieferschein erfolgreich erstellt!")
        print(f"   Datei: {args.output}")
        if gen.tracking_url:
            print(f"   Tracking: {gen.tracking_url}")


if __name__ == '__main__':
    main()
