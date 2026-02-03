import asyncio
import os
from core.service import VisionService
from adapters.vision.gemini_adapter import GeminiAdapter

# Vou tentar usar a chave de API que o OpenClaw está usando no momento
GEMINI_API_KEY = os.environ.get("GOOGLE_API_KEY", "SUA_API_KEY_AQUI")

async def test_logic():
    print("--- Iniciando Teste de Lógica (Arquitetura Hexagonal) ---")
    
    # 1. Mock de imagem (um pequeno quadrado preto em bytes)
    # Na vida real, isso viria do TelegramAdapter
    fake_image_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n2\xb4\x00\x00\x00\x00IEND\xaeB`\x82'

    try:
        # 2. Setup do Hexágono
        model = GeminiAdapter(api_key=GEMINI_API_KEY)
        service = VisionService(vision_model=model)
        
        print("Enviando imagem simulada para o Gemini...")
        description = await service.process_image_request(fake_image_bytes)
        
        print("\nResultado da Audiodescrição:")
        print(description)
        print("\n--- Teste Concluído com Sucesso ---")
        
    except Exception as e:
        print(f"\nErro durante o teste: {e}")

if __name__ == "__main__":
    asyncio.run(test_logic())
