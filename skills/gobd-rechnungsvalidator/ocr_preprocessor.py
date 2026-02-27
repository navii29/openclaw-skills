#!/usr/bin/env python3
"""
GoBD OCR Preprocessor v2.0
Erweiterte Bildvorverarbeitung für optimale Tesseract-Erkennung
"""

from typing import Tuple, Optional, List, Dict
from pathlib import Path
from dataclasses import dataclass
import logging

# PIL/Pillow für Bildverarbeitung
try:
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# pdf2image für PDF-Konvertierung
try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

# pytesseract
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False


@dataclass
class OCRConfig:
    """Konfiguration für OCR-Preprocessing"""
    dpi: int = 300
    contrast_factor: float = 1.5
    sharpness_factor: float = 2.0
    brightness_factor: float = 1.0
    binarize: bool = True
    denoise: bool = True
    deskew: bool = True
    languages: List[str] = None
    psm_mode: int = 6  # Page Segmentation Mode
    oem_mode: int = 3  # OCR Engine Mode
    
    def __post_init__(self):
        if self.languages is None:
            self.languages = ['deu']  # Standard: Deutsch


@dataclass
class OCRResult:
    """Ergebnis der OCR-Erkennung"""
    text: str
    confidence: float
    language: str
    page_num: int
    preprocessing_applied: List[str]
    raw_image_size: Tuple[int, int]
    processed_image_size: Tuple[int, int]


class ImagePreprocessor:
    """Bildvorverarbeitung für optimale OCR-Ergebnisse"""
    
    # Optimaler DPI für OCR (Tesseract empfiehlt mindestens 300)
    OPTIMAL_DPI = 300
    
    # Kontrast-Korrektur-Parameter
    AUTO_CONTRAST_CUTOFF = 1  # Prozent
    
    def __init__(self, config: Optional[OCRConfig] = None):
        self.config = config or OCRConfig()
        self.logger = logging.getLogger(__name__)
        
        if not PIL_AVAILABLE:
            raise ImportError("PIL/Pillow ist erforderlich. Installieren mit: pip install Pillow")
    
    def preprocess(self, image: Image.Image) -> Tuple[Image.Image, List[str]]:
        """
        Wendet alle konfigurierten Preprocessing-Schritte an
        
        Returns:
            Tuple von (verarbeitetes Bild, Liste der angewendeten Schritte)
        """
        applied_steps = []
        original_size = image.size
        
        # 1. Konvertiere zu RGB (falls nötig)
        if image.mode not in ('RGB', 'L'):
            image = image.convert('RGB')
            applied_steps.append('convert_rgb')
        
        # 2. Skalierung auf optimale DPI
        image = self._resize_to_dpi(image, self.config.dpi)
        if image.size != original_size:
            applied_steps.append(f'resize_to_{self.config.dpi}dpi')
        
        # 3. Deskewing (Schräglage korrigieren)
        if self.config.deskew:
            image = self._deskew(image)
            applied_steps.append('deskew')
        
        # 4. Helligkeitsanpassung
        if self.config.brightness_factor != 1.0:
            image = self._adjust_brightness(image, self.config.brightness_factor)
            applied_steps.append('brightness')
        
        # 5. Kontrastverstärkung
        if self.config.contrast_factor != 1.0:
            image = self._adjust_contrast(image, self.config.contrast_factor)
            applied_steps.append('contrast')
        
        # 6. Schärfung
        if self.config.sharpness_factor != 1.0:
            image = self._sharpen(image, self.config.sharpness_factor)
            applied_steps.append('sharpen')
        
        # 7. Rauschunterdrückung
        if self.config.denoise:
            image = self._denoise(image)
            applied_steps.append('denoise')
        
        # 8. Binarisierung (Schwarz/Weiß)
        if self.config.binarize:
            image = self._binarize(image)
            applied_steps.append('binarize')
        
        return image, applied_steps
    
    def _resize_to_dpi(self, image: Image.Image, target_dpi: int) -> Image.Image:
        """Skaliert Bild auf Ziel-DPI (angenommen 72 DPI als Basis)"""
        current_dpi = 72  # Standard-Annahme
        scale_factor = target_dpi / current_dpi
        
        if scale_factor <= 1.0:
            return image
        
        new_width = int(image.width * scale_factor)
        new_height = int(image.height * scale_factor)
        
        # Verwende LANCZOS für beste Qualität
        return image.resize((new_width, new_height), Image.LANCZOS)
    
    def _deskew(self, image: Image.Image) -> Image.Image:
        """Korrigiert Schräglage des Dokuments"""
        # Konvertiere zu Graustufen für die Analyse
        gray = image.convert('L')
        
        # Erkenne Orientierung mit Tesseract (falls verfügbar)
        if TESSERACT_AVAILABLE:
            try:
                osd = pytesseract.image_to_osd(gray, output_type=pytesseract.Output.DICT)
                rotation = osd.get('rotate', 0)
                
                if rotation != 0:
                    # Rotiere entgegengesetzt
                    return image.rotate(-rotation, expand=True, fillcolor='white')
            except Exception:
                pass  # Fallback zu einfacher Methode
        
        # Einfache Schräglagenerkennung über Kantendetektion
        edges = gray.filter(ImageFilter.FIND_EDGES)
        
        # Für nicht-Binar-Bilder: Projektiere auf x-Achse
        # und finde den optimalen Rotationswinkel
        # (Vereinfachte Implementierung)
        
        return image
    
    def _adjust_brightness(self, image: Image.Image, factor: float) -> Image.Image:
        """Passt die Helligkeit an"""
        enhancer = ImageEnhance.Brightness(image)
        return enhancer.enhance(factor)
    
    def _adjust_contrast(self, image: Image.Image, factor: float) -> Image.Image:
        """Verstärkt den Kontrast"""
        # Auto-Kontrast für bessere Ergebnisse
        if factor == 0:
            # Automatischer Kontrast
            return ImageOps.autocontrast(image, cutoff=self.AUTO_CONTRAST_CUTOFF)
        
        enhancer = ImageEnhance.Contrast(image)
        return enhancer.enhance(factor)
    
    def _sharpen(self, image: Image.Image, factor: float) -> Image.Image:
        """Schärft das Bild für bessere Texterkennung"""
        enhancer = ImageEnhance.Sharpness(image)
        sharpened = enhancer.enhance(factor)
        
        # Zusätzliche Unsharp Mask für Kanten
        if factor > 1.5:
            sharpened = sharpened.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
        
        return sharpened
    
    def _denoise(self, image: Image.Image) -> Image.Image:
        """Rauschunterdrückung mit Bewahrung von Kanten"""
        # Median-Filter für Rauschunterdrückung
        if image.mode == 'RGB':
            # Für Farbbilder: separat auf jeden Kanal anwenden
            r, g, b = image.split()
            r = r.filter(ImageFilter.MedianFilter(size=3))
            g = g.filter(ImageFilter.MedianFilter(size=3))
            b = b.filter(ImageFilter.MedianFilter(size=3))
            return Image.merge('RGB', (r, g, b))
        else:
            return image.filter(ImageFilter.MedianFilter(size=3))
    
    def _binarize(self, image: Image.Image) -> Image.Image:
        """Wandelt in Schwarz/Weiß um (Otsu-Thresholding)"""
        # Konvertiere zu Graustufen
        gray = image.convert('L')
        
        # Adaptive Binarisierung (vergleichbar mit Otsu)
        threshold = self._calculate_otsu_threshold(gray)
        
        return gray.point(lambda x: 0 if x < threshold else 255, '1')
    
    def _calculate_otsu_threshold(self, image: Image.Image) -> int:
        """Berechnet den optimalen Schwellenwert nach Otsu"""
        histogram = image.histogram()
        total_pixels = sum(histogram)
        
        sum_total = 0
        for i, count in enumerate(histogram):
            sum_total += i * count
        
        sum_background = 0
        weight_background = 0
        max_variance = 0
        threshold = 0
        
        for i, count in enumerate(histogram):
            weight_background += count
            if weight_background == 0:
                continue
            
            weight_foreground = total_pixels - weight_background
            if weight_foreground == 0:
                break
            
            sum_background += i * count
            mean_background = sum_background / weight_background
            mean_foreground = (sum_total - sum_background) / weight_foreground
            
            # Zwischenklassen-Varianz
            variance = weight_background * weight_foreground * (mean_background - mean_forefront) ** 2
            
            if variance > max_variance:
                max_variance = variance
                threshold = i
        
        return threshold


class MultilingualOCR:
    """Mehrsprachige OCR mit automatischer Spracherkennung"""
    
    # Verfügbare Tesseract-Sprachen
    AVAILABLE_LANGUAGES = {
        'deu': 'Deutsch',
        'eng': 'Englisch',
        'fra': 'Französisch',
        'ita': 'Italienisch',
        'spa': 'Spanisch',
        'nld': 'Niederländisch',
        'pol': 'Polnisch',
        'rus': 'Russisch',
        'tur': 'Türkisch',
        'por': 'Portugiesisch',
        'ces': 'Tschechisch',
        'hun': 'Ungarisch',
        'ron': 'Rumänisch',
        'swe': 'Schwedisch',
        'dan': 'Dänisch',
        'nor': 'Norwegisch',
        'fin': 'Finnisch',
    }
    
    # Sprachen für typische Rechnungsszenarien
    BUSINESS_LANGUAGES = ['deu', 'eng', 'fra']
    
    def __init__(self, config: Optional[OCRConfig] = None):
        self.config = config or OCRConfig()
        self.preprocessor = ImagePreprocessor(self.config)
        
        if not TESSERACT_AVAILABLE:
            raise ImportError("pytesseract ist erforderlich. Installieren mit: pip install pytesseract")
        
        if not PDF2IMAGE_AVAILABLE:
            raise ImportError("pdf2image ist erforderlich. Installieren mit: pip install pdf2image")
    
    def extract_from_pdf(self, pdf_path: str, page_numbers: Optional[List[int]] = None) -> List[OCRResult]:
        """
        Extrahiert Text aus PDF mit optimiertem Preprocessing
        
        Args:
            pdf_path: Pfad zur PDF-Datei
            page_numbers: Optionale Liste der zu verarbeitenden Seiten
            
        Returns:
            Liste von OCRResult pro Seite
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF nicht gefunden: {pdf_path}")
        
        # Konvertiere PDF zu Bildern
        self.logger.info(f"Konvertiere PDF: {pdf_path}")
        images = convert_from_path(
            pdf_path, 
            dpi=self.config.dpi,
            first_page=page_numbers[0] if page_numbers else None,
            last_page=page_numbers[-1] if page_numbers else None
        )
        
        results = []
        for page_num, image in enumerate(images, 1):
            if page_numbers and page_num not in page_numbers:
                continue
            
            result = self.extract_from_image(image, page_num)
            results.append(result)
        
        return results
    
    def extract_from_image(self, image: Image.Image, page_num: int = 1) -> OCRResult:
        """
        Extrahiert Text aus einem Bild mit Preprocessing
        
        Args:
            image: PIL Image Objekt
            page_num: Seitennummer für Logging
            
        Returns:
            OCRResult mit Text und Metadaten
        """
        raw_size = image.size
        
        # Preprocessing
        processed_image, preprocessing_steps = self.preprocessor.preprocess(image)
        processed_size = processed_image.size
        
        # Spracherkennung (falls mehrere Sprachen konfiguriert)
        detected_language = self.config.languages[0]
        if len(self.config.languages) > 1:
            detected_language = self._detect_language(processed_image)
        
        # OCR mit optimierten Parametern
        lang_string = '+'.join(self.config.languages)
        custom_config = f'--psm {self.config.psm_mode} --oem {self.config.oem_mode}'
        
        try:
            text = pytesseract.image_to_string(
                processed_image,
                lang=lang_string,
                config=custom_config
            )
            
            # Konfidenz berechnen
            confidence = self._calculate_confidence(processed_image, lang_string, custom_config)
            
        except Exception as e:
            self.logger.error(f"OCR-Fehler auf Seite {page_num}: {e}")
            text = ""
            confidence = 0.0
        
        return OCRResult(
            text=text,
            confidence=confidence,
            language=detected_language,
            page_num=page_num,
            preprocessing_applied=preprocessing_steps,
            raw_image_size=raw_size,
            processed_image_size=processed_size
        )
    
    def _detect_language(self, image: Image.Image) -> str:
        """
        Erkennt die Sprache des Dokuments
        Testet mit allen konfigurierten Sprachen und gibt die beste zurück
        """
        best_lang = self.config.languages[0]
        best_confidence = 0
        
        # Konvertiere zu RGB für Spracherkennung
        if image.mode != 'RGB':
            test_image = image.convert('RGB')
        else:
            test_image = image
        
        for lang in self.config.languages:
            try:
                data = pytesseract.image_to_data(
                    test_image,
                    lang=lang,
                    output_type=pytesseract.Output.DICT
                )
                
                # Berechne durchschnittliche Konfidenz
                confidences = [int(c) for c in data.get('conf', []) if int(c) > 0]
                avg_conf = sum(confidences) / len(confidences) if confidences else 0
                
                if avg_conf > best_confidence:
                    best_confidence = avg_conf
                    best_lang = lang
                    
            except Exception:
                continue
        
        return best_lang
    
    def _calculate_confidence(self, image: Image.Image, lang: str, config: str) -> float:
        """Berechnet die durchschnittliche OCR-Konfidenz"""
        try:
            data = pytesseract.image_to_data(
                image,
                lang=lang,
                config=config,
                output_type=pytesseract.Output.DICT
            )
            
            confidences = [int(c) for c in data.get('conf', []) if int(c) > 0]
            
            if confidences:
                return sum(confidences) / len(confidences) / 100.0
            return 0.0
            
        except Exception:
            return 0.0
    
    def get_available_languages(self) -> Dict[str, str]:
        """Gibt alle verfügbaren Tesseract-Sprachen zurück"""
        try:
            # Prüfe installierte Sprachen
            installed = pytesseract.get_languages()
            return {code: name for code, name in self.AVAILABLE_LANGUAGES.items() 
                    if code in installed}
        except Exception:
            return self.AVAILABLE_LANGUAGES


class OCRPresets:
    """Vordefinierte OCR-Konfigurationen für verschiedene Szenarien"""
    
    @staticmethod
    def scanned_document() -> OCRConfig:
        """Optimal für gescannte Dokumente"""
        return OCRConfig(
            dpi=300,
            contrast_factor=1.5,
            sharpness_factor=2.0,
            brightness_factor=1.1,
            binarize=True,
            denoise=True,
            deskew=True,
            languages=['deu', 'eng'],
            psm_mode=6  # Annahme: einheitlicher Textblock
        )
    
    @staticmethod
    def low_quality_scan() -> OCRConfig:
        """Für schlechte Scan-Qualität"""
        return OCRConfig(
            dpi=400,
            contrast_factor=2.0,
            sharpness_factor=2.5,
            brightness_factor=1.2,
            binarize=True,
            denoise=True,
            deskew=True,
            languages=['deu', 'eng'],
            psm_mode=4  # Annahme: einzelne Spalte
        )
    
    @staticmethod
    def invoice_multilingual() -> OCRConfig:
        """Für mehrsprachige Rechnungen"""
        return OCRConfig(
            dpi=300,
            contrast_factor=1.3,
            sharpness_factor=1.5,
            brightness_factor=1.0,
            binarize=False,  # Farbe kann hilfreich sein
            denoise=True,
            deskew=True,
            languages=['deu', 'eng', 'fra', 'ita', 'spa'],
            psm_mode=6
        )
    
    @staticmethod
    def fast_processing() -> OCRConfig:
        """Schnelle Verarbeitung (geringere Qualität)"""
        return OCRConfig(
            dpi=150,
            contrast_factor=1.0,
            sharpness_factor=1.0,
            brightness_factor=1.0,
            binarize=False,
            denoise=False,
            deskew=False,
            languages=['deu'],
            psm_mode=3  # Vollautomatisch
        )
    
    @staticmethod
    def maximum_quality() -> OCRConfig:
        """Maximale Qualität (langsamer)"""
        return OCRConfig(
            dpi=400,
            contrast_factor=0,  # Auto-Kontrast
            sharpness_factor=3.0,
            brightness_factor=1.0,
            binarize=True,
            denoise=True,
            deskew=True,
            languages=['deu', 'eng', 'fra', 'ita', 'spa', 'nld'],
            psm_mode=4
        )


# Convenience-Funktion für einfachen Zugriff
def extract_text_from_pdf(
    pdf_path: str,
    dpi: int = 300,
    languages: List[str] = None,
    preset: str = None
) -> str:
    """
    Einfache Funktion zum Extrahieren von Text aus PDF
    
    Args:
        pdf_path: Pfad zur PDF-Datei
        dpi: Auflösung für die Konvertierung
        languages: Liste der Sprachen (z.B. ['deu', 'eng'])
        preset: Voreinstellung ('scanned', 'low_quality', 'invoice', 'fast', 'max_quality')
    
    Returns:
        Extrahierter Text
    """
    # Wähle Preset
    if preset == 'scanned':
        config = OCRPresets.scanned_document()
    elif preset == 'low_quality':
        config = OCRPresets.low_quality_scan()
    elif preset == 'invoice':
        config = OCRPresets.invoice_multilingual()
    elif preset == 'fast':
        config = OCRPresets.fast_processing()
    elif preset == 'max_quality':
        config = OCRPresets.maximum_quality()
    else:
        config = OCRConfig(dpi=dpi, languages=languages or ['deu'])
    
    ocr = MultilingualOCR(config)
    results = ocr.extract_from_pdf(pdf_path)
    
    # Kombiniere alle Seiten
    return '\n\n--- Seitenumbruch ---\n\n'.join(r.text for r in results)


if __name__ == '__main__':
    # Demo/Test
    import argparse
    
    parser = argparse.ArgumentParser(description='GoBD OCR Preprocessor')
    parser.add_argument('pdf', help='PDF-Datei')
    parser.add_argument('--dpi', type=int, default=300)
    parser.add_argument('--lang', nargs='+', default=['deu'])
    parser.add_argument('--preset', choices=['scanned', 'low_quality', 'invoice', 'fast', 'max_quality'])
    parser.add_argument('--output', '-o', help='Ausgabedatei')
    
    args = parser.parse_args()
    
    print(f"🔍 OCR mit Preprocessing: {args.pdf}")
    
    text = extract_text_from_pdf(
        args.pdf,
        dpi=args.dpi,
        languages=args.lang,
        preset=args.preset
    )
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"✅ Text gespeichert: {args.output}")
    else:
        print("\n" + "="*50)
        print(text)
        print("="*50)
