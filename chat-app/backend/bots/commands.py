from datetime import datetime, timezone
from typing import Callable

def cmd_help(args: list[str]) -> str:
    """Retorna lista de comandos disponíveis."""
    return (
        "🤖 Comandos disponíveis:\n\n"
        "/help - Mostra esta mensagem de ajuda\n"
        "/echo <texto> - Repete o texto fornecido\n"
        "/time - Mostra a hora atual em UTC\n"
        "/ai <pergunta> - Pergunta algo para o ChatGPT\n"
        "/limpar - Limpa o histórico de conversa com o bot\n\n"
        "💡 Dica: Abra o painel do bot (ou use /ai) para perguntas. Evite usar @bot em mensagens.\n"
        "🧠 O bot mantém contexto das últimas 10 mensagens da conversa"
    )

def cmd_echo(args: list[str]) -> str:
    """Repete o texto fornecido."""
    return " ".join(args) if args else "Nada para repetir!"

def cmd_time(args: list[str]) -> str:
    """Retorna a hora atual em UTC."""
    return f"⏰ Agora (UTC): {datetime.now(timezone.utc).isoformat(timespec='seconds')}"


def cmd_ai(args: list[str]) -> str:
    """
    Comando assíncrono placeholder para ChatGPT.
    A lógica real está em main.py pois precisa ser async.
    """
    if not args:
        return "💭 Use: /ai <sua pergunta>\nExemplo: /ai O que é Python?"
    return "🤔 Processando..."  # Será substituído pela resposta real


def cmd_limpar(args: list[str]) -> str:
    """
    Comando para limpar histórico de conversa.
    A lógica real está em main.py pois precisa do user_id.
    """
    return "🧹 Limpando..."  # Será substituído pela mensagem real


COMMANDS: dict[str, Callable[[list[str]], str]] = {
    "help": cmd_help,
    "echo": cmd_echo,
    "time": cmd_time,
    "ai": cmd_ai,
    "limpar": cmd_limpar,
    "clear": cmd_limpar,  # Alias em inglês
}