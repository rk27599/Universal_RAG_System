"""
CLIP Embedding Service - Text and Image in Shared Embedding Space
Uses OpenCLIP for high-quality multimodal embeddings
"""

import logging
from typing import List, Optional, Union
from pathlib import Path
from datetime import datetime
import numpy as np
import torch

from .multimodal_embedding_base import MultimodalEmbeddingBase, ModalityType

logger = logging.getLogger(__name__)

# Check for required dependencies
try:
    import open_clip
    from PIL import Image
    CLIP_AVAILABLE = True
except ImportError:
    CLIP_AVAILABLE = False
    logger.warning("OpenCLIP not available. Install with: pip install open_clip_torch pillow")


class CLIPEmbeddingService(MultimodalEmbeddingBase):
    """
    CLIP Embedding Service for text and image embeddings

    Features:
    - 768-dimensional embeddings (ViT-L/14 model)
    - Shared embedding space for text and images
    - Cross-modal retrieval (search images with text, vice versa)
    - Efficient batch processing
    - GPU acceleration support

    Models:
    - Default: ViT-L-14 (768-dim, trained on LAION-2B)
    - Alternative: ViT-B-32 (512-dim, faster)
    """

    def __init__(
        self,
        model_name: str = "ViT-L-14",
        pretrained: str = "laion2b_s32b_b82k",
        use_fp16: bool = True
    ):
        """
        Initialize CLIP embedding service

        Args:
            model_name: CLIP model architecture (ViT-L-14, ViT-B-32)
            pretrained: Pretrained weights identifier
            use_fp16: Use half precision for faster inference
        """
        if not CLIP_AVAILABLE:
            raise RuntimeError(
                "OpenCLIP library not installed. "
                "Install with: pip install open_clip_torch pillow"
            )

        # Get embedding dimension for the model
        embedding_dim = self._get_embedding_dim(model_name)

        super().__init__(model_name=model_name, embedding_dim=embedding_dim)

        self.pretrained = pretrained
        self.use_fp16 = use_fp16
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.preprocess = None
        self.tokenizer = None
        self.last_access_time: Optional[datetime] = None

        logger.info(f"Initializing CLIP Embedding Service")
        logger.info(f"Model: {model_name} ({pretrained})")
        logger.info(f"Device: {self.device}")
        logger.info(f"FP16: {use_fp16}")
        logger.info(f"Embedding dimension: {embedding_dim}")

    def _get_embedding_dim(self, model_name: str) -> int:
        """Get embedding dimension for model architecture"""
        dim_mapping = {
            "ViT-L-14": 768,
            "ViT-L-14-336": 768,
            "ViT-B-32": 512,
            "ViT-B-16": 512,
            "ViT-H-14": 1024,
        }
        return dim_mapping.get(model_name, 768)

    @property
    def supported_modalities(self) -> List[ModalityType]:
        """CLIP supports text and images"""
        return [ModalityType.TEXT, ModalityType.IMAGE]

    def load_model(self):
        """Load the CLIP model"""
        if self.model is None:
            try:
                logger.info(f"Loading CLIP model: {self.model_name}")

                # Load model and preprocessing
                self.model, _, self.preprocess = open_clip.create_model_and_transforms(
                    self.model_name,
                    pretrained=self.pretrained,
                    device=self.device
                )

                # Load tokenizer
                self.tokenizer = open_clip.get_tokenizer(self.model_name)

                # Set to evaluation mode
                self.model.eval()

                # Convert to FP16 if requested and on GPU
                if self.use_fp16 and self.device == "cuda":
                    self.model = self.model.half()

                self.last_access_time = datetime.now()

                logger.info(f"✅ CLIP model loaded successfully")
                logger.info(f"📊 Embedding dimension: {self.embedding_dim}")
                logger.info(f"💾 Device: {self.device}")

            except Exception as e:
                logger.error(f"❌ Failed to load CLIP model: {e}")
                raise RuntimeError(f"Failed to load CLIP model: {e}")

    def unload_model(self):
        """Unload the CLIP model to free memory"""
        if self.model is not None:
            logger.info(f"🔄 Unloading CLIP model to free memory...")

            del self.model
            del self.preprocess
            del self.tokenizer

            self.model = None
            self.preprocess = None
            self.tokenizer = None

            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            import gc
            gc.collect()

            self.last_access_time = None
            logger.info(f"✅ CLIP model unloaded successfully")

    def encode_text(self, text: str) -> Optional[List[float]]:
        """
        Encode text into CLIP embedding

        Args:
            text: Input text

        Returns:
            768-dim embedding vector or None on failure
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for CLIP encoding")
            return None

        try:
            # Ensure model is loaded
            if self.model is None:
                self.load_model()

            self.last_access_time = datetime.now()

            # Tokenize text
            text_tokens = self.tokenizer([text]).to(self.device)

            # Encode
            with torch.no_grad():
                text_features = self.model.encode_text(text_tokens)
                # Normalize embeddings
                text_features = text_features / text_features.norm(dim=-1, keepdim=True)

            # Convert to list
            embedding = text_features.cpu().numpy()[0].tolist()

            return embedding

        except Exception as e:
            logger.error(f"Error encoding text with CLIP: {e}")
            return None

    def encode_image(self, image_path: Union[str, Path]) -> Optional[List[float]]:
        """
        Encode image into CLIP embedding

        Args:
            image_path: Path to image file

        Returns:
            768-dim embedding vector or None on failure
        """
        try:
            # Ensure model is loaded
            if self.model is None:
                self.load_model()

            self.last_access_time = datetime.now()

            # Load and preprocess image
            image_path = Path(image_path)
            if not image_path.exists():
                logger.error(f"Image not found: {image_path}")
                return None

            image = Image.open(image_path).convert("RGB")
            image_tensor = self.preprocess(image).unsqueeze(0).to(self.device)

            # Encode
            with torch.no_grad():
                image_features = self.model.encode_image(image_tensor)
                # Normalize embeddings
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)

            # Convert to list
            embedding = image_features.cpu().numpy()[0].tolist()

            return embedding

        except Exception as e:
            logger.error(f"Error encoding image with CLIP: {e}")
            return None

    def encode_batch(
        self,
        inputs: List[Union[str, Path]],
        modality: ModalityType,
        batch_size: int = 32
    ) -> List[Optional[List[float]]]:
        """
        Encode multiple inputs of the same modality

        Args:
            inputs: List of texts or image paths
            modality: Type of modality (TEXT or IMAGE)
            batch_size: Batch size for processing

        Returns:
            List of embedding vectors
        """
        if not inputs:
            return []

        try:
            # Ensure model is loaded
            if self.model is None:
                self.load_model()

            self.last_access_time = datetime.now()

            embeddings = []

            if modality == ModalityType.TEXT:
                # Batch text encoding
                for i in range(0, len(inputs), batch_size):
                    batch = inputs[i:i + batch_size]

                    # Tokenize batch
                    text_tokens = self.tokenizer(batch).to(self.device)

                    # Encode
                    with torch.no_grad():
                        text_features = self.model.encode_text(text_tokens)
                        text_features = text_features / text_features.norm(dim=-1, keepdim=True)

                    # Convert to list
                    batch_embeddings = text_features.cpu().numpy().tolist()
                    embeddings.extend(batch_embeddings)

                    logger.info(f"Encoded {min(i + batch_size, len(inputs))}/{len(inputs)} texts")

            elif modality == ModalityType.IMAGE:
                # Batch image encoding
                for i in range(0, len(inputs), batch_size):
                    batch = inputs[i:i + batch_size]
                    batch_images = []

                    # Load and preprocess images
                    for img_path in batch:
                        try:
                            img_path = Path(img_path)
                            if img_path.exists():
                                image = Image.open(img_path).convert("RGB")
                                batch_images.append(self.preprocess(image))
                            else:
                                logger.warning(f"Image not found: {img_path}")
                                embeddings.append(None)
                        except Exception as e:
                            logger.error(f"Error loading image {img_path}: {e}")
                            embeddings.append(None)

                    if batch_images:
                        # Stack images into batch
                        image_batch = torch.stack(batch_images).to(self.device)

                        # Encode
                        with torch.no_grad():
                            image_features = self.model.encode_image(image_batch)
                            image_features = image_features / image_features.norm(dim=-1, keepdim=True)

                        # Convert to list
                        batch_embeddings = image_features.cpu().numpy().tolist()
                        embeddings.extend(batch_embeddings)

                    logger.info(f"Encoded {min(i + batch_size, len(inputs))}/{len(inputs)} images")

            else:
                logger.error(f"Unsupported modality for CLIP: {modality}")
                return [None] * len(inputs)

            return embeddings

        except Exception as e:
            logger.error(f"Error in batch encoding: {e}")
            return [None] * len(inputs)

    def compute_text_image_similarity(
        self,
        text: str,
        image_path: Union[str, Path]
    ) -> Optional[float]:
        """
        Compute similarity between text and image

        Args:
            text: Text query
            image_path: Path to image

        Returns:
            Similarity score (0-1) or None on failure
        """
        text_emb = self.encode_text(text)
        image_emb = self.encode_image(image_path)

        if text_emb is None or image_emb is None:
            return None

        return self.compute_similarity(text_emb, image_emb)

    def search_images_with_text(
        self,
        text_query: str,
        image_embeddings: List[List[float]],
        top_k: int = 5
    ) -> List[tuple]:
        """
        Search images using text query

        Args:
            text_query: Text search query
            image_embeddings: List of image embeddings to search
            top_k: Number of top results to return

        Returns:
            List of (index, similarity_score) tuples
        """
        text_emb = self.encode_text(text_query)
        if text_emb is None:
            return []

        # Compute similarities
        similarities = []
        for idx, img_emb in enumerate(image_embeddings):
            if img_emb is not None:
                sim = self.compute_similarity(text_emb, img_emb)
                similarities.append((idx, sim))

        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)

        return similarities[:top_k]
