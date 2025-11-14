"""Módulo de transcrição de áudio usando Whisper API da OpenAI."""

import os
import httpx
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
WHISPER_API_URL = "https://api.openai.com/v1/audio/transcriptions"


async def transcribe_audio(audio_file_bytes: bytes, filename: str) -> str:
    """
    Transcreve áudio para texto usando Whisper API da OpenAI.
    
    Args:
        audio_file_bytes: Bytes do arquivo de áudio
        filename: Nome do arquivo (precisa ter extensão correta)
        
    Returns:
        Texto transcrito do áudio
    """
    if not OPENAI_API_KEY:
        return "[❌ Transcrição não configurada. Configure OPENAI_API_KEY]"
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Prepara o arquivo para upload
            files = {
                "file": (filename, audio_file_bytes, "audio/webm")
            }
            
            data = {
                "model": "whisper-1",
                "language": "pt",  # Português
                "response_format": "text"
            }
            
            response = await client.post(
                WHISPER_API_URL,
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}"
                },
                files=files,
                data=data
            )
            
            if response.status_code != 200:
                error_msg = response.json().get("error", {}).get("message", "Erro desconhecido")
                return f"[❌ Erro na transcrição: {error_msg}]"
            
            # Whisper retorna apenas o texto quando response_format=text
            transcription = response.text.strip()
            
            if not transcription:
                return "[🎤 Áudio vazio ou não foi possível transcrever]"
            
            return transcription
            
    except httpx.TimeoutException:
        return "[⏱️ Timeout ao transcrever áudio. Tente novamente.]"
    except Exception as e:
        return f"[❌ Erro ao transcrever: {str(e)}]"


async def transcribe_from_s3(s3_key: str, s3_bucket: str) -> str:
    """
    Baixa áudio do S3 e transcreve.
    
    Args:
        s3_key: Chave do objeto no S3
        s3_bucket: Nome do bucket
        
    Returns:
        Texto transcrito
    """
    try:
        from storage import s3
        
        # Baixa o arquivo do S3
        response = s3.get_object(Bucket=s3_bucket, Key=s3_key)
        audio_bytes = response['Body'].read()
        
        # Extrai o nome do arquivo da chave
        filename = s3_key.split('/')[-1]
        
        # Transcreve
        return await transcribe_audio(audio_bytes, filename)
        
    except Exception as e:
        return f"[❌ Erro ao baixar áudio do S3: {str(e)}]"
