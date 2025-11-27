#!/usr/bin/env python3
"""
Script de teste para comparar NLU com Pattern Matching vs GPT.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Adiciona o diretório backend ao path
sys.path.insert(0, '/app')

load_dotenv()

from bots.nlu import detect_intent

# Mensagens de teste variadas
TEST_MESSAGES = [
    # Claras e diretas
    ("Quero agendar uma reunião", "customer"),
    ("Preciso comprar notebooks", "customer"),
    ("Meu sistema travou", "customer"),
    
    # Com sinônimos
    ("Gostaria de marcar um horário", "customer"),
    ("Quero adquirir produtos", "customer"),
    ("O aplicativo parou de funcionar", "customer"),
    
    # Ambíguas
    ("Preciso resolver um problema urgente", "customer"),
    ("Vocês vendem?", "customer"),
    ("Como funciona?", "customer"),
    
    # Contextuais
    ("Aquilo que conversamos ontem, deu errado", "customer"),
    ("Ainda tá disponível?", "customer"),
]

async def compare_methods():
    """Compara pattern matching vs GPT"""
    
    print("\n" + "="*80)
    print("🔬 COMPARAÇÃO: PATTERN MATCHING vs GPT")
    print("="*80 + "\n")
    
    has_api_key = bool(os.getenv("OPENAI_API_KEY"))
    
    if not has_api_key:
        print("⚠️  OPENAI_API_KEY não configurada - testando apenas pattern matching\n")
    
    for text, speaker in TEST_MESSAGES:
        print(f"\n📨 Mensagem: \"{text}\"")
        print("-" * 80)
        
        # Pattern matching
        intent_pattern = await detect_intent(text, speaker, use_gpt=False)
        print(f"🔍 Pattern Matching:")
        print(f"   Intent: {intent_pattern.name}")
        print(f"   Confidence: {intent_pattern.confidence}")
        print(f"   Agent: {intent_pattern.suggested_agent}")
        print(f"   Keywords: {intent_pattern.keywords_matched[:3]}")
        
        # GPT (se disponível)
        if has_api_key:
            intent_gpt = await detect_intent(text, speaker, use_gpt=True)
            print(f"\n🤖 GPT:")
            print(f"   Intent: {intent_gpt.name}")
            print(f"   Confidence: {intent_gpt.confidence}")
            print(f"   Agent: {intent_gpt.suggested_agent}")
            print(f"   Reasoning: {intent_gpt.keywords_matched[0] if intent_gpt.keywords_matched else 'N/A'}")
            
            # Comparação
            if intent_pattern.name != intent_gpt.name:
                print(f"\n⚠️  DIVERGÊNCIA: Pattern={intent_pattern.name} vs GPT={intent_gpt.name}")
                if intent_gpt.confidence > intent_pattern.confidence:
                    print(f"   → GPT parece mais confiante (+{intent_gpt.confidence - intent_pattern.confidence:.2f})")
            elif intent_gpt.confidence > intent_pattern.confidence + 0.2:
                print(f"\n✅ CONCORDAM mas GPT mais confiante (+{intent_gpt.confidence - intent_pattern.confidence:.2f})")
        
        print()
    
    print("\n" + "="*80)
    print("✅ Teste concluído!")
    print("="*80 + "\n")

if __name__ == "__main__":
    asyncio.run(compare_methods())
