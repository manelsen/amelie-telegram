from ports.interfaces import VisionModelPort

class VisionService:
    def __init__(self, vision_model: VisionModelPort):
        self.vision_model = vision_model

    async def process_image_request(self, image_bytes: bytes) -> str:
        # Aqui você pode adicionar lógica de negócio, 
        # como filtros, logs ou pré-processamento.
        description = await self.vision_model.describe_image(image_bytes)
        return f"[Audio Descrição]: {description}"
