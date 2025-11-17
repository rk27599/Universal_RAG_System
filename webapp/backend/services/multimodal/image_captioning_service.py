"""
Image Captioning Service - Generate descriptions for images
Uses BLIP-2, LLaVA, or similar vision-language models
"""

import logging
from typing import List, Optional, Union, Dict
from pathlib import Path
from datetime import datetime
import torch

logger = logging.getLogger(__name__)

# Check for transformers and PIL
try:
    from transformers import Blip2Processor, Blip2ForConditionalGeneration
    from PIL import Image
    BLIP2_AVAILABLE = True
except ImportError:
    BLIP2_AVAILABLE = False
    logger.warning("BLIP-2 not available. Install with: pip install transformers pillow")


class ImageCaptioningService:
    """
    Image Captioning Service for generating natural language descriptions

    Features:
    - BLIP-2 for high-quality captions
    - Detailed scene descriptions
    - Object detection integration
    - Batch processing support
    - GPU acceleration
    """

    def __init__(
        self,
        model_name: str = "Salesforce/blip2-opt-2.7b",
        use_fp16: bool = True
    ):
        """
        Initialize image captioning service

        Args:
            model_name: Model identifier for BLIP-2 or compatible model
                       Options:
                       - "Salesforce/blip2-opt-2.7b" (balanced)
                       - "Salesforce/blip2-opt-6.7b" (better quality, slower)
                       - "Salesforce/blip2-flan-t5-xl" (excellent quality)
            use_fp16: Use half precision for faster inference
        """
        if not BLIP2_AVAILABLE:
            raise RuntimeError(
                "BLIP-2 not available. "
                "Install with: pip install transformers pillow torch"
            )

        self.model_name = model_name
        self.use_fp16 = use_fp16
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.processor = None
        self.last_access_time: Optional[datetime] = None

        logger.info(f"Initializing Image Captioning Service")
        logger.info(f"Model: {model_name}")
        logger.info(f"Device: {self.device}")
        logger.info(f"FP16: {use_fp16}")

    def load_model(self):
        """Load the BLIP-2 model"""
        if self.model is None:
            try:
                logger.info(f"Loading BLIP-2 model: {self.model_name}")

                # Load processor
                self.processor = Blip2Processor.from_pretrained(self.model_name)

                # Load model
                self.model = Blip2ForConditionalGeneration.from_pretrained(
                    self.model_name,
                    device_map="auto" if self.device == "cuda" else None,
                    torch_dtype=torch.float16 if self.use_fp16 and self.device == "cuda" else torch.float32
                )

                if self.device == "cpu":
                    self.model = self.model.to(self.device)

                self.model.eval()
                self.last_access_time = datetime.now()

                logger.info(f"✅ BLIP-2 model loaded successfully")

            except Exception as e:
                logger.error(f"❌ Failed to load BLIP-2 model: {e}")
                raise RuntimeError(f"Failed to load BLIP-2 model: {e}")

    def unload_model(self):
        """Unload the model to free memory"""
        if self.model is not None:
            logger.info(f"🔄 Unloading BLIP-2 model to free memory...")

            del self.model
            del self.processor
            self.model = None
            self.processor = None

            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            import gc
            gc.collect()

            self.last_access_time = None
            logger.info(f"✅ BLIP-2 model unloaded successfully")

    def generate_caption(
        self,
        image_path: Union[str, Path],
        prompt: Optional[str] = None,
        max_length: int = 50
    ) -> Optional[str]:
        """
        Generate a caption for an image

        Args:
            image_path: Path to image file
            prompt: Optional prompt to guide caption generation
                   e.g., "A photo of", "This image shows"
            max_length: Maximum caption length in tokens

        Returns:
            Generated caption or None on failure
        """
        try:
            # Ensure model is loaded
            if self.model is None:
                self.load_model()

            self.last_access_time = datetime.now()

            # Load image
            image_path = Path(image_path)
            if not image_path.exists():
                logger.error(f"Image not found: {image_path}")
                return None

            image = Image.open(image_path).convert("RGB")

            # Process image
            if prompt:
                inputs = self.processor(image, text=prompt, return_tensors="pt").to(self.device)
            else:
                inputs = self.processor(image, return_tensors="pt").to(self.device)

            # Generate caption
            with torch.no_grad():
                generated_ids = self.model.generate(
                    **inputs,
                    max_length=max_length,
                    num_beams=5,  # Beam search for better quality
                    early_stopping=True
                )

            # Decode caption
            caption = self.processor.decode(generated_ids[0], skip_special_tokens=True)

            return caption.strip()

        except Exception as e:
            logger.error(f"Error generating caption for {image_path}: {e}")
            return None

    def generate_detailed_description(
        self,
        image_path: Union[str, Path]
    ) -> Optional[Dict[str, str]]:
        """
        Generate multiple descriptions with different prompts

        Args:
            image_path: Path to image file

        Returns:
            Dict with different types of descriptions
        """
        try:
            descriptions = {}

            # Basic caption
            descriptions['caption'] = self.generate_caption(image_path)

            # Detailed description
            descriptions['detailed'] = self.generate_caption(
                image_path,
                prompt="Describe this image in detail:",
                max_length=100
            )

            # Objects
            descriptions['objects'] = self.generate_caption(
                image_path,
                prompt="What objects are in this image?",
                max_length=50
            )

            # Scene
            descriptions['scene'] = self.generate_caption(
                image_path,
                prompt="What is the scene or setting of this image?",
                max_length=50
            )

            return descriptions

        except Exception as e:
            logger.error(f"Error generating detailed description: {e}")
            return None

    def generate_captions_batch(
        self,
        image_paths: List[Union[str, Path]],
        batch_size: int = 4,
        max_length: int = 50
    ) -> List[Optional[str]]:
        """
        Generate captions for multiple images

        Args:
            image_paths: List of image paths
            batch_size: Batch size for processing
            max_length: Maximum caption length

        Returns:
            List of captions (one per image)
        """
        captions = []

        try:
            # Ensure model is loaded
            if self.model is None:
                self.load_model()

            self.last_access_time = datetime.now()

            # Process in batches
            for i in range(0, len(image_paths), batch_size):
                batch_paths = image_paths[i:i + batch_size]
                batch_images = []

                # Load images
                for img_path in batch_paths:
                    try:
                        img_path = Path(img_path)
                        if img_path.exists():
                            image = Image.open(img_path).convert("RGB")
                            batch_images.append(image)
                        else:
                            logger.warning(f"Image not found: {img_path}")
                            captions.append(None)
                    except Exception as e:
                        logger.error(f"Error loading image {img_path}: {e}")
                        captions.append(None)

                if batch_images:
                    # Process batch
                    inputs = self.processor(batch_images, return_tensors="pt").to(self.device)

                    # Generate captions
                    with torch.no_grad():
                        generated_ids = self.model.generate(
                            **inputs,
                            max_length=max_length,
                            num_beams=5,
                            early_stopping=True
                        )

                    # Decode captions
                    batch_captions = [
                        self.processor.decode(ids, skip_special_tokens=True).strip()
                        for ids in generated_ids
                    ]

                    captions.extend(batch_captions)

                logger.info(f"Processed {min(i + batch_size, len(image_paths))}/{len(image_paths)} images")

            return captions

        except Exception as e:
            logger.error(f"Error in batch caption generation: {e}")
            return [None] * len(image_paths)

    def is_chart_or_diagram(
        self,
        image_path: Union[str, Path]
    ) -> bool:
        """
        Detect if image is a chart, diagram, or graph

        Args:
            image_path: Path to image

        Returns:
            True if image appears to be a chart/diagram
        """
        try:
            caption = self.generate_caption(
                image_path,
                prompt="What type of image is this?",
                max_length=30
            )

            if not caption:
                return False

            # Check for chart/diagram keywords
            chart_keywords = [
                'chart', 'graph', 'diagram', 'plot', 'figure',
                'table', 'visualization', 'bar chart', 'line graph',
                'pie chart', 'scatter plot', 'histogram'
            ]

            caption_lower = caption.lower()
            return any(keyword in caption_lower for keyword in chart_keywords)

        except Exception as e:
            logger.error(f"Error detecting chart/diagram: {e}")
            return False

    def is_loaded(self) -> bool:
        """Check if model is currently loaded"""
        return self.model is not None

    def get_model_info(self) -> Dict[str, any]:
        """Get information about the captioning model"""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "use_fp16": self.use_fp16,
            "is_loaded": self.is_loaded()
        }


# Singleton instance
_captioning_service_instance = None


def get_captioning_service(
    model_name: str = "Salesforce/blip2-opt-2.7b"
) -> ImageCaptioningService:
    """Get singleton image captioning service instance"""
    global _captioning_service_instance
    if _captioning_service_instance is None:
        _captioning_service_instance = ImageCaptioningService(model_name=model_name)
    return _captioning_service_instance


# Example usage
if __name__ == "__main__":
    # Test image captioning service
    captioner = ImageCaptioningService()

    # Test with sample image
    test_image = "test_image.jpg"
    if Path(test_image).exists():
        # Basic caption
        caption = captioner.generate_caption(test_image)
        print(f"\n📷 Caption: {caption}")

        # Detailed descriptions
        descriptions = captioner.generate_detailed_description(test_image)
        if descriptions:
            print(f"\n📝 Detailed Descriptions:")
            for desc_type, desc in descriptions.items():
                print(f"  {desc_type}: {desc}")

        # Check if chart/diagram
        is_chart = captioner.is_chart_or_diagram(test_image)
        print(f"\n📊 Is chart/diagram: {is_chart}")
    else:
        print(f"Test image not found: {test_image}")
