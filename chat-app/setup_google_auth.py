#!/usr/bin/env python3
"""
Script para configurar autenticação do Google Calendar.
Execute FORA do Docker para gerar o token.json
"""

import os
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

SCOPES = ['https://www.googleapis.com/auth/calendar']

def setup_google_calendar():
    """Configura autenticação OAuth2 com Google Calendar."""
    
    credentials_path = Path("backend/credentials.json")
    token_path = Path("backend/token.json")
    
    if not credentials_path.exists():
        print("❌ Erro: Arquivo credentials.json não encontrado em backend/")
        print("\n📝 Passos para obter credentials.json:")
        print("1. Acesse: https://console.cloud.google.com/")
        print("2. Crie um projeto ou selecione existente")
        print("3. Ative Google Calendar API")
        print("4. Vá em 'Credenciais' > 'Criar Credenciais' > 'ID do cliente OAuth'")
        print("5. Tipo: Aplicativo de área de trabalho")
        print("6. Baixe o JSON e salve como backend/credentials.json")
        return False
    
    print("🔐 Iniciando autenticação OAuth2...")
    print("📱 Seu navegador será aberto para autorização")
    
    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            str(credentials_path), 
            SCOPES
        )
        
        # Abre navegador para autorização
        credentials = flow.run_local_server(port=0)
        
        # Salva token
        with open(token_path, 'w') as token_file:
            token_file.write(credentials.to_json())
        
        print(f"\n✅ Token gerado com sucesso!")
        print(f"📁 Salvo em: {token_path}")
        print(f"\n🐳 Agora reinicie o Docker:")
        print(f"   cd {os.getcwd()}")
        print(f"   docker compose restart api")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erro na autenticação: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🗓️  Configuração Google Calendar - Chat App")
    print("=" * 60)
    print()
    
    success = setup_google_calendar()
    
    if not success:
        exit(1)
