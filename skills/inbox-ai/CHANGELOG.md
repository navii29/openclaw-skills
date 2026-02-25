# Inbox AI Changelog

## v2.2.0 (2026-02-25) - OPTIMIZATION STREAM

### 🚀 Performance Improvements
- **SMTP Connection Pooling**: Wiederverwendung von SMTP-Verbindungen statt jedes Mal neu verbinden
  - Pool-Größe: max 3 Verbindungen
  - Automatische Verbindungsvalidierung vor Wiederverwendung
  - ~70% schneller bei Massen-Auto-Replies

### 🛡️ Robustness Improvements  
- **Persistent Job Queue**: SQLite-basierte Warteschlange für Crash-Recovery
  - Kein Verlust von Emails bei Abstürzen
  - Idempotenz-Prüfung (keine doppelte Verarbeitung)
  - Retry-Logik mit max 3 Versuchen
  - Queue-Statistiken für Monitoring

### ✨ New Features
- **Professional HTML Auto-Replies**: Schön formatierte HTML-E-Mails statt nur Plain-Text
  - Responsive Design für Mobile
  - Branding mit konfigurierbaren Farben
  - Kategorie-spezifische Templates (booking, inquiry, support, general)
  - Automatische Plain-Text + HTML Multipart-E-Mails

### 🔧 Technical Changes
- Added `PersistentJobQueue` class mit SQLite-Backend
- Added `generate_html_reply()` Methode für HTML-Templates
- SMTP-Verbindungen werden jetzt gepoolt in `_smtp_pool`
- Idempotenz-Tracking via `processed_emails` Tabelle
- Neue Queue-Metriken in Logs

## v2.1.0 (2026-02-24) - Self-Healing System

### ✨ New Features
- **Zero-Config Onboarding**: Auto-detect email provider from address
- **Circuit Breaker**: Automatic failover on email provider issues
- **Exponential Backoff**: Intelligent retry with jitter
- **Health Monitoring**: Real-time system health score
- **Learning Engine**: Adapts from user feedback

## v2.0.0 (2026-02-24)

### ✨ Improvements
- **Structured Logging**: Proper logging with rotation and levels
- **Retry Logic**: Automatic retry with exponential backoff for IMAP/SMTP
- **Rate Limiting**: Prevents email blacklisting (configurable per hour)
- **Config Validation**: Validates all settings on startup
- **Graceful Shutdown**: Handles SIGINT/SIGTERM properly
- **Better Error Handling**: Detailed error messages and recovery

### 🔧 Technical Changes
- Refactored to class-based architecture
- Added `EmailConfig` dataclass for type-safe configuration
- Added `ProcessingResult` dataclass for structured output

## v1.0.0 (2026-02-19)

### Initial Release
- Basic email processing
- Auto-reply functionality
- Simple categorization
