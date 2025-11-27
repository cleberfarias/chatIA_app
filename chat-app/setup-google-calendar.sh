#!/bin/bash
# Script para autenticar Google Calendar pela primeira vez

echo "🔐 Autenticação Google Calendar"
echo "================================"
echo ""
echo "Este script irá:"
echo "1. Abrir seu navegador"
echo "2. Solicitar login na sua conta Google"
echo "3. Solicitar permissão para acessar o calendário"
echo "4. Gerar um token que será salvo em backend/token.json"
echo ""
echo "Pressione ENTER para continuar..."
read

# Executa dentro do container Docker
docker compose exec api python3 -c "
from integrations.google_calendar import GoogleCalendarService
import sys

try:
    service = GoogleCalendarService()
    print('\\n🔄 Iniciando autenticação OAuth2...')
    print('📱 Um navegador será aberto. Faça login e autorize o aplicativo.')
    
    if service.authenticate():
        print('\\n✅ Autenticação bem-sucedida!')
        print('📄 Token salvo em backend/token.json')
    else:
        print('\\n❌ Falha na autenticação')
        sys.exit(1)
except Exception as e:
    print(f'\\n❌ Erro: {e}')
    sys.exit(1)
"

if [ -f "token.json" ]; then
    echo ""
    echo "✅ Autenticação concluída com sucesso!"
    echo "📄 Token salvo em: backend/token.json"
    echo ""
    echo "Agora você pode:"
    echo "  - Usar o agente SDR para agendar reuniões"
    echo "  - Verificar disponibilidade via API"
    echo "  - Criar eventos no Google Calendar"
    echo ""
else
    echo ""
    echo "⚠️  Token não foi criado. Verifique se:"
    echo "  - O arquivo credentials.json está em backend/"
    echo "  - Você autorizou o aplicativo no navegador"
    echo "  - Não houve erros durante a execução"
    echo ""
fi
