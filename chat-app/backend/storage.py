# storage.py
import os, boto3, mimetypes, time, uuid
from urllib.parse import quote_plus, urlparse

S3_ENDPOINT = os.getenv("S3_ENDPOINT", "http://minio:9000")
S3_REGION = os.getenv("S3_REGION", "us-east-1")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "MINIOADMIN")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "MINIOADMIN")
S3_BUCKET = os.getenv("S3_BUCKET", "chat-uploads")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://localhost:9000")
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "15"))

s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    region_name=S3_REGION,
)

ALLOWED = {
    "image/png","image/jpeg","image/webp","application/pdf",
    "text/plain","application/zip","application/octet-stream",
    "audio/webm","audio/ogg","audio/mpeg","audio/mp4","audio/wav"
}

def new_object_key(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    return f"messages/{time.strftime('%Y/%m/%d')}/{uuid.uuid4().hex}{ext}"

def validate_upload(filename: str, mimetype: str, size_mb: int):
    if size_mb > MAX_UPLOAD_MB:
        raise ValueError("Arquivo excede o limite")
    if mimetype not in ALLOWED:
        # fallback: tente por extensão
        guessed = mimetypes.guess_type(filename)[0]
        if not guessed or guessed not in ALLOWED:
            raise ValueError("Tipo de arquivo não permitido")

def presign_put(key: str, mimetype: str, expires=300):
    url = s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": S3_BUCKET, "Key": key, "ContentType": mimetype},
        ExpiresIn=expires,
    )
    # Substitui o endpoint interno pelo público
    return url.replace(S3_ENDPOINT, PUBLIC_BASE_URL)

def presign_get(key: str, expires=3600):
    url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": S3_BUCKET, "Key": key},
        ExpiresIn=expires,
    )
    # Substitui o endpoint interno pelo público
    return url.replace(S3_ENDPOINT, PUBLIC_BASE_URL)
