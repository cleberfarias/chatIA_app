"""
Testes para módulo de storage (storage.py)
Cobertura: validate_upload, new_object_key, presign_put, presign_get
"""
import pytest
from unittest.mock import patch, MagicMock
import storage
import os
from datetime import datetime


class TestValidateUpload:
    """Testes para validate_upload"""
    
    def test_valid_image_png(self):
        """Testa upload de PNG válido"""
        storage.validate_upload("photo.png", "image/png", 5)
        # Não deve lançar exceção
    
    def test_valid_image_jpeg(self):
        """Testa upload de JPEG válido"""
        storage.validate_upload("photo.jpg", "image/jpeg", 10)
    
    def test_valid_pdf(self):
        """Testa upload de PDF válido"""
        storage.validate_upload("document.pdf", "application/pdf", 8)
    
    def test_valid_audio_webm(self):
        """Testa upload de áudio WebM válido"""
        storage.validate_upload("audio.webm", "audio/webm", 3)
    
    def test_valid_audio_mp3(self):
        """Testa upload de MP3 válido"""
        storage.validate_upload("music.mp3", "audio/mpeg", 7)
    
    def test_exceeds_size_limit(self):
        """Testa arquivo que excede limite de tamanho"""
        with pytest.raises(ValueError) as exc_info:
            storage.validate_upload("huge.png", "image/png", 20)  # > 15MB
        
        assert "excede o limite" in str(exc_info.value)
    
    def test_exactly_at_size_limit(self):
        """Testa arquivo exatamente no limite"""
        storage.validate_upload("max.png", "image/png", 15)  # Exatamente 15MB
    
    def test_invalid_mimetype(self):
        """Testa tipo de arquivo não permitido"""
        with pytest.raises(ValueError) as exc_info:
            storage.validate_upload("virus.exe", "application/x-executable", 1)
        
        assert "não permitido" in str(exc_info.value)
    
    def test_octet_stream_with_allowed_extension(self):
        """Testa octet-stream com extensão permitida (.zip)"""
        storage.validate_upload("archive.zip", "application/octet-stream", 5)
    
    def test_octet_stream_with_txt_extension(self):
        """Testa octet-stream com .txt"""
        storage.validate_upload("file.txt", "application/octet-stream", 1)
    
    def test_octet_stream_with_disallowed_extension(self):
        """Testa octet-stream com extensão não permitida"""
        with pytest.raises(ValueError):
            storage.validate_upload("malware.exe", "application/octet-stream", 1)
    
    def test_guess_mimetype_from_extension(self):
        """Testa fallback para adivinhar mimetype por extensão"""
        # Tenta enviar PNG com mimetype errado, mas extensão correta
        storage.validate_upload("image.png", "application/octet-stream", 5)
    
    def test_empty_filename(self):
        """Testa filename vazio"""
        with pytest.raises(ValueError):
            storage.validate_upload("", "image/png", 5)
    
    def test_zero_size(self):
        """Testa arquivo de tamanho zero"""
        storage.validate_upload("empty.txt", "text/plain", 0)
    
    def test_negative_size(self):
        """Testa tamanho negativo (edge case)"""
        storage.validate_upload("file.png", "image/png", -1)  # Não bloqueia negativo
    
    def test_webp_image(self):
        """Testa imagem WebP"""
        storage.validate_upload("modern.webp", "image/webp", 3)
    
    def test_audio_ogg(self):
        """Testa áudio OGG"""
        storage.validate_upload("voice.ogg", "audio/ogg", 2)
    
    def test_audio_wav(self):
        """Testa áudio WAV"""
        storage.validate_upload("recording.wav", "audio/wav", 4)


class TestNewObjectKey:
    """Testes para new_object_key"""
    
    def test_generates_key_with_correct_structure(self):
        """Testa estrutura da chave gerada"""
        key = storage.new_object_key("test.png")
        
        # Formato esperado: messages/YYYY/MM/DD/uuid.ext
        assert key.startswith("messages/")
        assert key.endswith(".png")
        assert key.count("/") == 4  # messages/YYYY/MM/DD/filename
    
    def test_preserves_file_extension(self):
        """Testa se extensão do arquivo é preservada"""
        extensions = [".png", ".jpg", ".pdf", ".txt", ".webm"]
        
        for ext in extensions:
            key = storage.new_object_key(f"file{ext}")
            assert key.endswith(ext)
    
    def test_generates_unique_keys(self):
        """Testa se chaves geradas são únicas"""
        keys = [storage.new_object_key("test.png") for _ in range(10)]
        
        # Todas as chaves devem ser diferentes
        assert len(set(keys)) == 10
    
    def test_includes_current_date(self):
        """Testa se chave inclui data atual"""
        key = storage.new_object_key("file.pdf")
        
        now = datetime.now()
        year = now.strftime("%Y")
        month = now.strftime("%m")
        day = now.strftime("%d")
        
        assert f"/{year}/" in key
        assert f"/{month}/" in key
        assert f"/{day}/" in key
    
    def test_handles_uppercase_extension(self):
        """Testa extensão em maiúsculas (deve converter para minúsculas)"""
        key = storage.new_object_key("FILE.PNG")
        
        assert key.endswith(".png")  # Deve ser minúscula
    
    def test_handles_no_extension(self):
        """Testa arquivo sem extensão"""
        key = storage.new_object_key("noextension")
        
        assert key.startswith("messages/")
        # Não deve ter extensão
        assert not key.endswith(".")
    
    def test_handles_multiple_dots(self):
        """Testa arquivo com múltiplos pontos"""
        key = storage.new_object_key("my.file.name.pdf")
        
        assert key.endswith(".pdf")
    
    def test_uuid_format(self):
        """Testa se UUID está em formato hexadecimal"""
        key = storage.new_object_key("test.txt")
        
        # Extrai a parte do UUID (entre última / e extensão)
        filename = key.split("/")[-1]
        uuid_part = filename.rsplit(".", 1)[0]
        
        # UUID hex tem 32 caracteres
        assert len(uuid_part) == 32
        # Deve ser hexadecimal
        assert all(c in "0123456789abcdef" for c in uuid_part)


class TestPresignFunctions:
    """Testes para presign_put e presign_get"""
    
    @patch('storage.s3')
    def test_presign_put_generates_url(self, mock_s3):
        """Testa geração de URL presigned para PUT"""
        mock_s3.generate_presigned_url.return_value = "http://minio:9000/bucket/key?signature=abc"
        
        url = storage.presign_put("test/file.png", "image/png")
        
        assert url is not None
        assert isinstance(url, str)
        
        # Verifica se chamou generate_presigned_url corretamente
        mock_s3.generate_presigned_url.assert_called_once_with(
            "put_object",
            Params={
                "Bucket": storage.S3_BUCKET,
                "Key": "test/file.png",
                "ContentType": "image/png"
            },
            ExpiresIn=300
        )
    
    @patch('storage.s3')
    def test_presign_put_replaces_internal_endpoint(self, mock_s3):
        """Testa substituição de endpoint interno pelo público"""
        mock_s3.generate_presigned_url.return_value = "http://minio:9000/bucket/key?sig=123"
        
        url = storage.presign_put("key", "image/jpeg")
        
        # Deve substituir minio:9000 por localhost:9000
        assert "minio:9000" not in url
        assert "localhost:9000" in url
    
    @patch('storage.s3')
    def test_presign_put_custom_expiration(self, mock_s3):
        """Testa presign_put com expiração customizada"""
        mock_s3.generate_presigned_url.return_value = "http://url"
        
        storage.presign_put("key", "image/png", expires=600)
        
        # Verifica se passou ExpiresIn correto
        call_args = mock_s3.generate_presigned_url.call_args
        assert call_args[1]["ExpiresIn"] == 600
    
    @patch('storage.s3')
    def test_presign_get_generates_url(self, mock_s3):
        """Testa geração de URL presigned para GET"""
        mock_s3.generate_presigned_url.return_value = "http://minio:9000/bucket/key?signature=xyz"
        
        url = storage.presign_get("downloads/file.pdf")
        
        assert url is not None
        assert isinstance(url, str)
        
        mock_s3.generate_presigned_url.assert_called_once_with(
            "get_object",
            Params={
                "Bucket": storage.S3_BUCKET,
                "Key": "downloads/file.pdf"
            },
            ExpiresIn=3600
        )
    
    @patch('storage.s3')
    def test_presign_get_replaces_internal_endpoint(self, mock_s3):
        """Testa substituição de endpoint no presign_get"""
        mock_s3.generate_presigned_url.return_value = "http://minio:9000/path?sig=abc"
        
        url = storage.presign_get("key")
        
        assert "minio:9000" not in url
        assert "localhost:9000" in url
    
    @patch('storage.s3')
    def test_presign_get_custom_expiration(self, mock_s3):
        """Testa presign_get com expiração customizada"""
        mock_s3.generate_presigned_url.return_value = "http://url"
        
        storage.presign_get("key", expires=7200)
        
        call_args = mock_s3.generate_presigned_url.call_args
        assert call_args[1]["ExpiresIn"] == 7200
    
    @patch('storage.s3')
    def test_presign_put_with_special_characters(self, mock_s3):
        """Testa presign com caracteres especiais na chave"""
        mock_s3.generate_presigned_url.return_value = "http://minio:9000/key"
        
        key_with_spaces = "folder/my file with spaces.pdf"
        storage.presign_put(key_with_spaces, "application/pdf")
        
        # Verifica se chamou com a chave correta
        call_args = mock_s3.generate_presigned_url.call_args
        assert call_args[1]["Params"]["Key"] == key_with_spaces
    
    @patch('storage.s3')
    def test_presign_default_expirations(self, mock_s3):
        """Testa expirações padrão"""
        mock_s3.generate_presigned_url.return_value = "http://url"
        
        # PUT deve ter 300s (5 min) por padrão
        storage.presign_put("key", "image/png")
        assert mock_s3.generate_presigned_url.call_args[1]["ExpiresIn"] == 300
        
        # GET deve ter 3600s (1 hora) por padrão
        storage.presign_get("key")
        assert mock_s3.generate_presigned_url.call_args[1]["ExpiresIn"] == 3600


class TestStorageConfiguration:
    """Testes para configuração do storage"""
    
    def test_s3_bucket_configured(self):
        """Testa se bucket S3 está configurado"""
        assert storage.S3_BUCKET is not None
        assert len(storage.S3_BUCKET) > 0
    
    def test_max_upload_size_configured(self):
        """Testa se tamanho máximo está configurado"""
        assert storage.MAX_UPLOAD_MB > 0
        assert isinstance(storage.MAX_UPLOAD_MB, int)
    
    def test_allowed_mimetypes_not_empty(self):
        """Testa se lista de tipos permitidos não está vazia"""
        assert len(storage.ALLOWED) > 0
        assert "image/png" in storage.ALLOWED
        assert "image/jpeg" in storage.ALLOWED
    
    def test_allowed_extensions_mapping(self):
        """Testa mapeamento de extensões permitidas"""
        assert ".zip" in storage.ALLOWED_BY_EXTENSION
        assert ".txt" in storage.ALLOWED_BY_EXTENSION
