"""
Beispiele für DATEV Online API Integration
============================================

Diese Datei enthält praktische Beispiele für die häufigsten Use Cases.

Voraussetzungen:
    export DATEV_CLIENT_ID="your-client-id"
    export DATEV_CLIENT_SECRET="your-client-secret"
"""

import os
from datetime import datetime
from datev_client import (
    DATEVClient, 
    DATEVDocument, 
    DATEVToken,
    UploadResult
)


def example_1_basic_auth():
    """
    Beispiel 1: OAuth2 Authentifizierung
    ====================================
    
    Zeigt den kompletten OAuth2 Flow mit PKCE.
    """
    print("=" * 60)
    print("Beispiel 1: OAuth2 Authentifizierung")
    print("=" * 60)
    
    # Client initialisieren (Sandbox)
    client = DATEVClient(
        client_id=os.environ["DATEV_CLIENT_ID"],
        client_secret=os.environ["DATEV_CLIENT_SECRET"],
        sandbox=True
    )
    
    # Auth-URL generieren
    auth_url = client.get_authorization_url(
        redirect_uri="http://localhost:8080/callback",
        scope="openid accounting:documents accounting:clients:read"
    )
    
    print(f"\n1. Öffne diese URL im Browser:")
    print(f"   {auth_url}")
    
    print(f"\n2. Nach Login wirst du weitergeleitet zu:")
    print(f"   http://localhost:8080/callback?code=AUTH_CODE&state=...")
    
    print(f"\n3. Code aus der URL kopieren und exchange:")
    print(f"   token = client.exchange_code(code, redirect_uri)")
    
    # Hinweis: In echter App würde hier ein Webserver laufen
    print("\n✅ Auth-URL generiert!")
    
    return client


def example_2_list_clients(client: DATEVClient):
    """
    Beispiel 2: Mandanten Listen
    ============================
    
    Alle zugänglichen Mandanten (Clients) abrufen.
    """
    print("\n" + "=" * 60)
    print("Beispiel 2: Mandanten Listen")
    print("=" * 60)
    
    # Voraussetzung: Token muss vorhanden sein
    if not client.token:
        print("❌ Kein Token vorhanden. Bitte zuerst authentifizieren.")
        return
    
    clients = client.list_clients()
    
    print(f"\nGefundene Mandanten: {len(clients)}")
    print("-" * 40)
    
    for c in clients:
        print(f"ID:   {c.client_id}")
        print(f"Name: {c.name}")
        if c.consultant_number and c.client_number:
            print(f"Berater-Nr: {c.consultant_number}")
            print(f"Mandanten-Nr: {c.client_number}")
        print("-" * 40)
    
    return clients


def example_3_list_document_types(client: DATEVClient, client_id: str):
    """
    Beispiel 3: Belegtypen Listen
    =============================
    
    Verfügbare Belegtypen für einen Mandanten anzeigen.
    """
    print("\n" + "=" * 60)
    print("Beispiel 3: Belegtypen Listen")
    print("=" * 60)
    
    doc_types = client.list_document_types(client_id)
    
    print(f"\nVerfügbare Belegtypen: {len(doc_types)}")
    print("-" * 40)
    
    for t in doc_types:
        print(f"ID:   {t.id}")
        print(f"Name: {t.name}")
        if t.description:
            print(f"Desc: {t.description}")
        print("-" * 40)
    
    return doc_types


def example_4_upload_document(client: DATEVClient, client_id: str, file_path: str):
    """
    Beispiel 4: Dokument Hochladen
    ==============================
    
    Eine PDF-Rechnung zu DATEV Unternehmen online hochladen.
    """
    print("\n" + "=" * 60)
    print("Beispiel 4: Dokument Hochladen")
    print("=" * 60)
    
    # Dokument erstellen
    doc = DATEVDocument(
        file_path=file_path,
        document_type="Rechnungseingang",
        note=f"Automatisch hochgeladen am {datetime.now().isoformat()}"
    )
    
    print(f"\nDatei: {doc.filename}")
    print(f"Typ:   {doc.content_type}")
    print(f"Größe: {len(doc.get_content())} bytes")
    
    # Upload
    result = client.upload_document(
        client_id=client_id,
        document=doc,
        idempotent_key=f"upload-{file_path}-{datetime.now().date()}"
    )
    
    if result.success:
        print(f"\n✅ Erfolgreich hochgeladen!")
        print(f"   Document ID: {result.document_id}")
        print(f"   Files: {result.files}")
    else:
        print(f"\n❌ Fehler:")
        print(f"   {result.error}")
        print(f"   Status Code: {result.status_code}")
    
    return result


def example_5_batch_upload(client: DATEVClient, client_id: str, file_paths: list):
    """
    Beispiel 5: Batch Upload
    ========================
    
    Mehrere Dokumente nacheinander hochladen.
    """
    print("\n" + "=" * 60)
    print("Beispiel 5: Batch Upload")
    print("=" * 60)
    
    results = []
    
    for i, file_path in enumerate(file_paths, 1):
        print(f"\n[{i}/{len(file_paths)}] {file_path}...")
        
        try:
            doc = DATEVDocument(
                file_path=file_path,
                document_type="Rechnungseingang"
            )
            
            result = client.upload_document(
                client_id=client_id,
                document=doc
            )
            
            results.append(result)
            
            if result.success:
                print(f"   ✅ {result.document_id}")
            else:
                print(f"   ❌ {result.error}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            results.append(UploadResult(success=False, error=str(e)))
    
    # Statistik
    successful = sum(1 for r in results if r.success)
    print(f"\n{'='*60}")
    print(f"Ergebnis: {successful}/{len(file_paths)} erfolgreich")
    
    return results


def example_6_error_handling(client: DATEVClient):
    """
    Beispiel 6: Fehlerbehandlung
    ============================
    
    Zeigt verschiedene Fehlerszenarien und deren Behandlung.
    """
    print("\n" + "=" * 60)
    print("Beispiel 6: Fehlerbehandlung")
    print("=" * 60)
    
    from datev_client import (
        DATEVAuthError,
        DATEVRateLimitError,
        DATEVValidationError
    )
    
    try:
        # Ungültiger Mandant
        result = client.upload_document(
            client_id="invalid-client-id",
            document=DATEVDocument(
                file_content=b"test",
                filename="test.pdf"
            )
        )
        
        if not result.success:
            print(f"❌ Upload fehlgeschlagen (erwartet):")
            print(f"   {result.error}")
            
    except DATEVAuthError as e:
        print(f"🔐 Auth-Fehler: {e}")
        print(f"   Status: {e.status_code}")
        
    except DATEVRateLimitError as e:
        print(f"⏳ Rate Limit: {e}")
        print(f"   Retry after: {e.retry_after}s")
        
    except DATEVValidationError as e:
        print(f"📝 Validierungs-Fehler: {e}")
        print(f"   Details: {e.details}")
        
    except Exception as e:
        print(f"💥 Unerwarteter Fehler: {e}")


def example_7_token_refresh(client: DATEVClient):
    """
    Beispiel 7: Token Refresh
    =========================
    
    Manuelle Token-Aktualisierung (wird normalerweise automatisch gemacht).
    """
    print("\n" + "=" * 60)
    print("Beispiel 7: Token Refresh")
    print("=" * 60)
    
    if not client.token:
        print("❌ Kein Token vorhanden")
        return
    
    print(f"\nAktuelles Token:")
    print(f"   Expired: {client.token.is_expired}")
    print(f"   Expires: {client.token.expires_at}")
    
    # Token aktualisieren
    new_token = client.refresh_token()
    
    print(f"\nNeues Token:")
    print(f"   Expires: {new_token.expires_at}")
    print(f"   Scope: {new_token.scope}")
    
    return new_token


def example_8_user_info(client: DATEVClient):
    """
    Beispiel 8: User Info
    =====================
    
    Informationen über den authentifizierten Benutzer abrufen.
    """
    print("\n" + "=" * 60)
    print("Beispiel 8: User Info")
    print("=" * 60)
    
    try:
        user_info = client.get_user_info()
        
        print(f"\nBenutzer-Informationen:")
        for key, value in user_info.items():
            print(f"   {key}: {value}")
            
    except Exception as e:
        print(f"❌ Fehler: {e}")


def main():
    """
    Hauptfunktion - führt alle Beispiele aus.
    
    Hinweis: Einige Beispiele erfordern ein gültiges Token!
    """
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║     DATEV Online API - Python Integration Beispiele      ║
    ║                                                          ║
    ║  Voraussetzungen:                                        ║
    ║  - DATEV_CLIENT_ID und DATEV_CLIENT_SECRET gesetzt      ║
    ║  - Gültiges OAuth2 Token (für Beispiele 2-8)            ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    # Prüfe Umgebungsvariablen
    if not os.environ.get("DATEV_CLIENT_ID"):
        print("❌ DATEV_CLIENT_ID nicht gesetzt!")
        print("   export DATEV_CLIENT_ID='your-client-id'")
        return
    
    if not os.environ.get("DATEV_CLIENT_SECRET"):
        print("❌ DATEV_CLIENT_SECRET nicht gesetzt!")
        print("   export DATEV_CLIENT_SECRET='your-client-secret'")
        return
    
    # Beispiel 1: Auth (funktioniert immer)
    client = example_1_basic_auth()
    
    # Für weitere Beispiele Token aus Umgebung laden
    # (Muss vorher durch OAuth2 Flow erstellt werden)
    if os.environ.get("DATEV_ACCESS_TOKEN"):
        from datev_client import create_datev_client_from_env
        client = create_datev_client_from_env(sandbox=True)
        
        # Beispiel 2: Mandanten listen
        clients = example_2_list_clients(client)
        
        if clients:
            client_id = clients[0].client_id
            
            # Beispiel 3: Belegtypen
            example_3_list_document_types(client, client_id)
            
            # Beispiel 6: Fehlerbehandlung
            example_6_error_handling(client)
            
            # Beispiel 7: Token Refresh
            example_7_token_refresh(client)
            
            # Beispiel 8: User Info
            example_8_user_info(client)
            
            # Beispiel 4 & 5 erfordern existierende Dateien
            # example_4_upload_document(client, client_id, "/path/to/file.pdf")
    else:
        print("\n" + "=" * 60)
        print("Hinweis: Weitere Beispiele erfordern ein gültiges Token.")
        print("Setze DATEV_ACCESS_TOKEN und DATEV_REFRESH_TOKEN")
        print("=" * 60)


if __name__ == "__main__":
    main()
