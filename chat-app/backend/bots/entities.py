"""Extração de Entidades - Identificação automática de informações estruturadas.

Extrai CPF, telefone, CEP, email, datas, valores monetários e outras
entidades do texto do usuário.
"""

import re
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass


@dataclass
class Entity:
    """Representa uma entidade extraída."""
    type: str
    value: str
    normalized: Optional[str] = None
    valid: bool = True
    metadata: dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


# Padrões regex para extração
PATTERNS = {
    "cpf": r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b",
    "cnpj": r"\b\d{2}\.?\d{3}\.?\d{3}/?0001-?\d{2}\b",
    "phone": r"\(?\d{2}\)?\s*9?\d{4}-?\d{4}",
    "cep": r"\b\d{5}-?\d{3}\b",
    "email": r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b",
    "url": r"https?://[^\s]+",
    "date": r"\b\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b",
    "time": r"\b\d{1,2}:\d{2}(?:\s*(?:am|pm|AM|PM))?\b",
    "money": r"R\$\s*\d+(?:[.,]\d{3})*(?:[.,]\d{2})?",
}


def validate_cpf(cpf: str) -> bool:
    """
    Valida CPF usando algoritmo de dígitos verificadores.
    
    Args:
        cpf: CPF no formato 111.222.333-44 ou 11122233344
        
    Returns:
        True se CPF é válido
    """
    # Remove pontuação
    cpf = re.sub(r'\D', '', cpf)
    
    # CPF deve ter 11 dígitos
    if len(cpf) != 11:
        return False
    
    # CPF não pode ser sequência (111.111.111-11)
    if cpf == cpf[0] * 11:
        return False
    
    # Valida primeiro dígito verificador
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    digito1 = (soma * 10 % 11) % 10
    if int(cpf[9]) != digito1:
        return False
    
    # Valida segundo dígito verificador
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    digito2 = (soma * 10 % 11) % 10
    if int(cpf[10]) != digito2:
        return False
    
    return True


def normalize_cpf(cpf: str) -> str:
    """Normaliza CPF para formato 111.222.333-44"""
    digits = re.sub(r'\D', '', cpf)
    return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"


def normalize_phone(phone: str) -> str:
    """Normaliza telefone para formato (11) 91234-5678"""
    digits = re.sub(r'\D', '', phone)
    if len(digits) == 11:
        return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
    elif len(digits) == 10:
        return f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"
    return phone


def normalize_cep(cep: str) -> str:
    """Normaliza CEP para formato 12345-678"""
    digits = re.sub(r'\D', '', cep)
    return f"{digits[:5]}-{digits[5:]}"


def parse_date(date_str: str) -> Optional[datetime]:
    """
    Parseia data em diversos formatos.
    
    Suporta: 25/11/2025, 25-11-2025, 25/11/25
    """
    date_str = date_str.strip()
    
    formats = [
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d/%m/%y",
        "%d-%m-%y",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    return None


def parse_time(time_str: str) -> Optional[str]:
    """
    Parseia hora para formato 24h (HH:MM).
    
    Suporta: 14:30, 2:30pm, 02:30 PM
    """
    time_str = time_str.strip().lower()
    
    # Remove espaços entre hora e am/pm
    time_str = re.sub(r'\s+(am|pm)', r'\1', time_str)
    
    # Padrão para 14:30 ou 2:30pm
    match = re.match(r'(\d{1,2}):(\d{2})\s*(am|pm)?', time_str)
    if not match:
        return None
    
    hour, minute, period = match.groups()
    hour = int(hour)
    minute = int(minute)
    
    # Converte PM para 24h
    if period == 'pm' and hour != 12:
        hour += 12
    elif period == 'am' and hour == 12:
        hour = 0
    
    return f"{hour:02d}:{minute:02d}"


def parse_money(money_str: str) -> Optional[float]:
    """
    Parseia valor monetário para float.
    
    Suporta: R$ 1.500,00 ou R$ 1500.00
    """
    # Remove R$ e espaços
    money_str = re.sub(r'R\$\s*', '', money_str)
    
    # Detecta se usa vírgula ou ponto como decimal
    if ',' in money_str:
        # Formato BR: 1.500,00
        money_str = money_str.replace('.', '').replace(',', '.')
    
    try:
        return float(money_str)
    except ValueError:
        return None


def extract_quantity(text: str) -> Optional[int]:
    """
    Extrai quantidade de produtos do texto.
    
    Ex: "quero 5 notebooks" → 5
    """
    patterns = [
        r'\b(\d+)\s+(?:unidades?|produtos?|itens?|pcs?)',
        r'\bquero\s+(\d+)',
        r'\bpreciso\s+de\s+(\d+)',
        r'\b(\d+)x\b',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            return int(match.group(1))
    
    return None


def extract_product_name(text: str) -> Optional[str]:
    """
    Tenta extrair nome do produto do texto.
    
    Ex: "quero comprar notebooks Dell" → "notebooks Dell"
    """
    # Lista de produtos comuns (expandir conforme necessário)
    products = [
        "notebook", "laptop", "computador", "pc", "desktop",
        "celular", "smartphone", "iphone", "samsung",
        "tablet", "ipad",
        "mouse", "teclado", "monitor", "webcam",
    ]
    
    text_lower = text.lower()
    
    for product in products:
        if product in text_lower:
            # Tenta pegar palavras ao redor do produto (marca, modelo)
            pattern = rf'\b\w*{product}\w*(?:\s+\w+){{0,2}}\b'
            match = re.search(pattern, text_lower)
            if match:
                return match.group(0).strip()
    
    return None


def extract_entities(text: str, context: dict = None) -> dict[str, Entity]:
    """
    Extrai todas as entidades do texto.
    
    Args:
        text: Texto para extrair entidades
        context: Contexto da conversa (entidades já extraídas antes)
        
    Returns:
        Dict com entidades encontradas {tipo: Entity}
    """
    if context is None:
        context = {}
    
    entities = {}
    
    # CPF
    if "cpf" not in context:
        match = re.search(PATTERNS["cpf"], text)
        if match:
            cpf = match.group(0)
            is_valid = validate_cpf(cpf)
            entities["cpf"] = Entity(
                type="cpf",
                value=cpf,
                normalized=normalize_cpf(cpf) if is_valid else None,
                valid=is_valid,
                metadata={"masked": cpf[:3] + ".***.***-" + cpf[-2:]}
            )
    
    # Telefone
    if "phone" not in context:
        match = re.search(PATTERNS["phone"], text)
        if match:
            phone = match.group(0)
            entities["phone"] = Entity(
                type="phone",
                value=phone,
                normalized=normalize_phone(phone),
                metadata={"ddd": phone[:2] if len(phone) >= 2 else None}
            )
    
    # CEP
    if "cep" not in context:
        match = re.search(PATTERNS["cep"], text)
        if match:
            cep = match.group(0)
            entities["cep"] = Entity(
                type="cep",
                value=cep,
                normalized=normalize_cep(cep),
                metadata={"needs_address_lookup": True}
            )
    
    # Email
    if "email" not in context:
        match = re.search(PATTERNS["email"], text)
        if match:
            email = match.group(0)
            domain = email.split('@')[1]
            entities["email"] = Entity(
                type="email",
                value=email,
                normalized=email.lower(),
                metadata={"domain": domain}
            )
    
    # Data
    match = re.search(PATTERNS["date"], text)
    if match:
        date_str = match.group(0)
        parsed = parse_date(date_str)
        if parsed:
            entities["date"] = Entity(
                type="date",
                value=date_str,
                normalized=parsed.strftime("%Y-%m-%d"),
                metadata={
                    "is_past": parsed < datetime.now(),
                    "day_of_week": parsed.strftime("%A"),
                }
            )
    
    # Hora
    match = re.search(PATTERNS["time"], text)
    if match:
        time_str = match.group(0)
        normalized = parse_time(time_str)
        if normalized:
            entities["time"] = Entity(
                type="time",
                value=time_str,
                normalized=normalized,
            )
    
    # Dinheiro
    match = re.search(PATTERNS["money"], text)
    if match:
        money_str = match.group(0)
        amount = parse_money(money_str)
        if amount:
            entities["money"] = Entity(
                type="money",
                value=money_str,
                normalized=f"R$ {amount:.2f}",
                metadata={"amount": amount}
            )
    
    # Quantidade de produto
    quantity = extract_quantity(text)
    if quantity:
        entities["quantity"] = Entity(
            type="quantity",
            value=str(quantity),
            normalized=str(quantity),
            metadata={"numeric": quantity}
        )
    
    # Nome do produto
    product = extract_product_name(text)
    if product:
        entities["product"] = Entity(
            type="product",
            value=product,
            normalized=product.title(),
        )
    
    return entities


# Exemplo de uso
if __name__ == "__main__":
    test_texts = [
        "Meu CPF é 123.456.789-10 e telefone (11) 98765-4321",
        "Quero comprar 3 notebooks Dell por R$ 5.000,00",
        "Preciso agendar para 25/12/2025 às 14:30",
        "Envie para CEP 01310-100 no email joao@empresa.com.br",
    ]
    
    for text in test_texts:
        print(f"\n📝 Texto: '{text}'")
        entities = extract_entities(text)
        for entity_type, entity in entities.items():
            print(f"  🔍 {entity_type}: {entity.value}")
            if entity.normalized:
                print(f"     → Normalizado: {entity.normalized}")
            if entity.metadata:
                print(f"     → Metadata: {entity.metadata}")
            if not entity.valid:
                print(f"     ⚠️  Inválido!")
