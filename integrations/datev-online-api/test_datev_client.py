"""
Tests für DATEV Online API Integration
========================================

Ausführliche Testsuite mit Mocking für API-Aufrufe.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from datev_client import (
    DATEVClient,
    DATEVDocument,
    DATEVToken,
    Client,
    DocumentType,
    UploadResult,
    DATEVError,
    DATEVAuthError,
    DATEVRateLimitError,
    DATEVValidationError,
    create_datev_client_from_env
)


class TestDATEVToken:
    """Tests für DATEVToken Dataclass."""
    
    def test_token_not_expired(self):
        """Token ist nicht expired wenn expires_at in Zukunft."""
        token = DATEVToken(
            access_token="test",
            refresh_token="refresh",
            expires_at=datetime.now() + timedelta(hours=1)
        )
        assert not token.is_expired
    
    def test_token_expired(self):
        """Token ist expired wenn expires_at in Vergangenheit."""
        token = DATEVToken(
            access_token="test",
            refresh_token="refresh",
            expires_at=datetime.now() - timedelta(minutes=1)
        )
        assert token.is_expired
    
    def test_token_buffer(self):
        """Token gilt 60s vor Ablauf bereits als expired."""
        token = DATEVToken(
            access_token="test",
            refresh_token="refresh",
            expires_at=datetime.now() + timedelta(seconds=30)
        )
        assert token.is_expired


class TestDATEVDocument:
    """Tests für DATEVDocument Dataclass."""
    
    def test_document_from_file(self, tmp_path):
        """Dokument aus Datei erstellen."""
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"PDF content")
        
        doc = DATEVDocument(file_path=str(test_file))
        
        assert doc.filename == "test.pdf"
        assert doc.content_type == "application/pdf"
        assert doc.get_content() == b"PDF content"
    
    def test_document_from_content(self):
        """Dokument aus Bytes erstellen."""
        doc = DATEVDocument(
            file_content=b"content",
            filename="test.txt",
            content_type="text/plain"
        )
        
        assert doc.filename == "test.txt"
        assert doc.get_content() == b"content"
    
    def test_document_no_filename_error(self):
        """Fehler wenn kein Filename angegeben."""
        with pytest.raises(ValueError):
            DATEVDocument(file_content=b"test")


class TestDATEVClientAuth:
    """Tests für OAuth2 Authentifizierung."""
    
    @pytest.fixture
    def client(self):
        return DATEVClient(
            client_id="test-client-id",
            client_secret="test-secret",
            sandbox=True
        )
    
    def test_authorization_url_generation(self, client):
        """Auth-URL enthält alle erforderlichen Parameter."""
        url = client.get_authorization_url("http://localhost:8080/callback")
        
        assert "https://login.datev.de/openidsandbox/authorize" in url
        assert "client_id=test-client-id" in url
        assert "response_type=code" in url
        assert "code_challenge=" in url
        assert "code_challenge_method=S256" in url
        assert "state=" in url
        assert "nonce=" in url
        assert "enableWindowsSso=true" in url
    
    def test_authorization_url_custom_scope(self, client):
        """Custom Scope wird übernommen."""
        url = client.get_authorization_url(
            "http://localhost:8080/callback",
            scope="openid offline_access"
        )
        
        assert "scope=openid+offline_access" in url
    
    @patch('datev_client.requests.Session.post')
    def test_exchange_code_success(self, mock_post, client):
        """Code Exchange erfolgreich."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "test-access-token",
            "refresh_token": "test-refresh-token",
            "expires_in": 900,
            "token_type": "Bearer",
            "scope": "openid accounting:documents"
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        # PKCE vorbereiten
        client.get_authorization_url("http://localhost:8080/callback")
        
        token = client.exchange_code("test-code", "http://localhost:8080/callback")
        
        assert token.access_token == "test-access-token"
        assert token.refresh_token == "test-refresh-token"
        assert token.token_type == "Bearer"
    
    @patch('datev_client.requests.Session.post')
    def test_exchange_code_failure(self, mock_post, client):
        """Code Exchange fehlgeschlagen."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("HTTP Error")
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "invalid_grant"}
        mock_post.return_value = mock_response
        
        client.get_authorization_url("http://localhost:8080/callback")
        
        with pytest.raises(DATEVAuthError):
            client.exchange_code("invalid-code", "http://localhost:8080/callback")


class TestDATEVClientAPI:
    """Tests für API-Operationen."""
    
    @pytest.fixture
    def authenticated_client(self):
        """Client mit gültigem Token."""
        token = DATEVToken(
            access_token="test-token",
            refresh_token="test-refresh",
            expires_at=datetime.now() + timedelta(hours=1)
        )
        return DATEVClient(
            client_id="test-client",
            client_secret="test-secret",
            sandbox=True,
            token=token
        )
    
    @patch('datev_client.requests.Session.request')
    def test_list_clients_success(self, mock_request, authenticated_client):
        """Mandanten erfolgreich listen."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "clients": [
                {
                    "id": "12345-1",
                    "name": "Muster GmbH",
                    "consultant_number": "12345",
                    "client_number": "1"
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        clients = authenticated_client.list_clients()
        
        assert len(clients) == 1
        assert clients[0].client_id == "12345-1"
        assert clients[0].name == "Muster GmbH"
    
    @patch('datev_client.requests.Session.request')
    def test_list_document_types(self, mock_request, authenticated_client):
        """Belegtypen listen."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "document_types": [
                {"id": "RE", "name": "Rechnungseingang"},
                {"id": "RA", "name": "Rechnungsausgang"}
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        types = authenticated_client.list_document_types("12345-1")
        
        assert len(types) == 2
        assert types[0].name == "Rechnungseingang"
    
    @patch('datev_client.requests.Session.request')
    def test_upload_document_success(self, mock_request, authenticated_client, tmp_path):
        """Dokument erfolgreich hochladen."""
        # Testdatei erstellen
        test_file = tmp_path / "rechnung.pdf"
        test_file.write_bytes(b"PDF content")
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "doc-123",
            "files": [{"name": "rechnung.pdf", "size": "100"}],
            "document_type": "Rechnungseingang"
        }
        mock_response.raise_for_status = Mock()
        mock_response.status_code = 201
        mock_request.return_value = mock_response
        
        doc = DATEVDocument(
            file_path=str(test_file),
            document_type="Rechnungseingang"
        )
        
        result = authenticated_client.upload_document("12345-1", doc)
        
        assert result.success
        assert result.document_id == "doc-123"
    
    @patch('datev_client.requests.Session.request')
    def test_rate_limit_error(self, mock_request, authenticated_client):
        """Rate Limit Error wird korrekt behandelt."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}
        mock_response.raise_for_status.side_effect = Exception("429")
        mock_request.return_value = mock_response
        
        with pytest.raises(DATEVRateLimitError) as exc_info:
            authenticated_client.list_clients()
        
        assert exc_info.value.retry_after == 60


class TestExceptions:
    """Tests für Exception-Hierarchie."""
    
    def test_datev_error_base(self):
        """Basis Exception."""
        err = DATEVError("Test error", status_code=500, error_code="E001")
        assert err.status_code == 500
        assert err.error_code == "E001"
    
    def test_auth_error(self):
        """Auth Error."""
        err = DATEVAuthError("Auth failed", status_code=401)
        assert err.status_code == 401
        assert isinstance(err, DATEVError)
    
    def test_rate_limit_error(self):
        """Rate Limit Error."""
        err = DATEVRateLimitError("Too many requests", retry_after=120)
        assert err.status_code == 429
        assert err.retry_after == 120


class TestUtilityFunctions:
    """Tests für Utility-Funktionen."""
    
    @patch.dict('os.environ', {
        'DATEV_CLIENT_ID': 'env-client-id',
        'DATEV_CLIENT_SECRET': 'env-secret'
    })
    def test_create_client_from_env(self):
        """Client aus Umgebungsvariablen erstellen."""
        client = create_datev_client_from_env(sandbox=True)
        
        assert client.client_id == "env-client-id"
        assert client.client_secret == "env-secret"
        assert client.sandbox is True
    
    @patch.dict('os.environ', {}, clear=True)
    def test_create_client_from_env_missing_vars(self):
        """Fehler wenn Umgebungsvariablen fehlen."""
        with pytest.raises(ValueError):
            create_datev_client_from_env()


class TestFilenameSanitization:
    """Tests für Filename-Sanitization."""
    
    @pytest.fixture
    def client(self):
        return DATEVClient(
            client_id="test",
            client_secret="secret",
            sandbox=True
        )
    
    def test_valid_filename(self, client):
        """Gültiger Filename bleibt unverändert."""
        result = client.validate_filename("Rechnung_2025.pdf")
        assert result == "Rechnung_2025.pdf"
    
    def test_invalid_chars_replaced(self, client):
        """Ungültige Zeichen werden durch _ ersetzt."""
        result = client.validate_filename("Rechnung@Home#Test.pdf")
        assert result == "Rechnung_Home_Test.pdf"
    
    def test_umlaute_allowed(self, client):
        """Umlaute sind erlaubt."""
        result = client.validate_filename("Rechnung_Überweisung.pdf")
        assert "Ü" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
