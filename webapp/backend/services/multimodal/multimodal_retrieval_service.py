"""
Multimodal Retrieval Service - Cross-modal search orchestration
Handles retrieval across text, images, audio, and video
"""

import logging
from typing import List, Optional, Dict, Union
from pathlib import Path
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """Type of query input"""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"


class MultimodalRetrievalService:
    """
    Multimodal Retrieval Service for cross-modal search

    Features:
    - Text → Image search (find images matching text)
    - Image → Text search (find documents matching image)
    - Cross-modal similarity scoring
    - Unified ranking across modalities
    - Multimodal fusion strategies
    """

    def __init__(
        self,
        clip_service=None,
        embedding_service=None,
        document_service=None
    ):
        """
        Initialize multimodal retrieval service

        Args:
            clip_service: CLIPEmbeddingService instance
            embedding_service: BGEEmbeddingService instance (for text)
            document_service: DocumentProcessingService instance
        """
        self.clip_service = clip_service
        self.embedding_service = embedding_service
        self.document_service = document_service

        logger.info("Multimodal Retrieval Service initialized")

    def search_multimodal(
        self,
        query: Union[str, Path],
        query_type: QueryType,
        top_k: int = 10,
        modality_filter: Optional[List[str]] = None,
        fusion_weights: Optional[Dict[str, float]] = None
    ) -> List[Dict]:
        """
        Search across multiple modalities

        Args:
            query: Query text or path to image/audio/video file
            query_type: Type of query (TEXT, IMAGE, AUDIO, VIDEO)
            top_k: Number of results to return
            modality_filter: Filter results by modality (e.g., ['image', 'text'])
            fusion_weights: Weights for different modalities (e.g., {'text': 0.7, 'image': 0.3})

        Returns:
            List of results with modality information
        """
        try:
            if query_type == QueryType.TEXT:
                return self._search_with_text_query(query, top_k, modality_filter, fusion_weights)
            elif query_type == QueryType.IMAGE:
                return self._search_with_image_query(query, top_k, modality_filter)
            elif query_type == QueryType.AUDIO:
                return self._search_with_audio_query(query, top_k)
            elif query_type == QueryType.VIDEO:
                return self._search_with_video_query(query, top_k)
            else:
                logger.error(f"Unsupported query type: {query_type}")
                return []

        except Exception as e:
            logger.error(f"Error in multimodal search: {e}")
            return []

    def _search_with_text_query(
        self,
        query_text: str,
        top_k: int,
        modality_filter: Optional[List[str]],
        fusion_weights: Optional[Dict[str, float]]
    ) -> List[Dict]:
        """Search using text query across all modalities"""
        results = []

        # Set default weights
        if fusion_weights is None:
            fusion_weights = {'text': 0.7, 'image': 0.3}

        # 1. Text-to-Text search (traditional RAG)
        if modality_filter is None or 'text' in modality_filter:
            text_results = self._search_text_content(query_text, top_k)
            for result in text_results:
                result['modality'] = 'text'
                result['fusion_score'] = result.get('similarity', 0.0) * fusion_weights.get('text', 0.7)
            results.extend(text_results)

        # 2. Text-to-Image search (CLIP)
        if (modality_filter is None or 'image' in modality_filter) and self.clip_service:
            image_results = self._search_images_with_text(query_text, top_k)
            for result in image_results:
                result['modality'] = 'image'
                result['fusion_score'] = result.get('similarity', 0.0) * fusion_weights.get('image', 0.3)
            results.extend(image_results)

        # 3. Sort by fusion score
        results.sort(key=lambda x: x.get('fusion_score', 0.0), reverse=True)

        return results[:top_k]

    def _search_with_image_query(
        self,
        image_path: Path,
        top_k: int,
        modality_filter: Optional[List[str]]
    ) -> List[Dict]:
        """Search using image query"""
        results = []

        if not self.clip_service:
            logger.error("CLIP service not available for image queries")
            return []

        # Encode query image
        query_embedding = self.clip_service.encode_image(image_path)
        if query_embedding is None:
            return []

        # 1. Image-to-Image search (find similar images)
        if modality_filter is None or 'image' in modality_filter:
            similar_images = self._search_similar_images(query_embedding, top_k)
            for result in similar_images:
                result['modality'] = 'image'
            results.extend(similar_images)

        # 2. Image-to-Text search (find related documents)
        if modality_filter is None or 'text' in modality_filter:
            related_docs = self._search_documents_with_image_embedding(query_embedding, top_k)
            for result in related_docs:
                result['modality'] = 'text'
            results.extend(related_docs)

        # Sort by similarity
        results.sort(key=lambda x: x.get('similarity', 0.0), reverse=True)

        return results[:top_k]

    def _search_with_audio_query(
        self,
        audio_path: Path,
        top_k: int
    ) -> List[Dict]:
        """Search using audio query (via transcription)"""
        try:
            from .audio_processor import get_audio_processor

            # Transcribe audio
            audio_processor = get_audio_processor()
            transcript = audio_processor.transcribe(audio_path)

            if not transcript or not transcript.text:
                logger.error("Could not transcribe audio")
                return []

            # Search using transcript text
            logger.info(f"Searching with transcript: {transcript.text[:100]}...")
            return self._search_with_text_query(transcript.text, top_k, None, None)

        except Exception as e:
            logger.error(f"Error in audio query search: {e}")
            return []

    def _search_with_video_query(
        self,
        video_path: Path,
        top_k: int
    ) -> List[Dict]:
        """Search using video query (via frame extraction)"""
        try:
            from .video_processor import get_video_processor
            import tempfile

            # Extract a representative frame
            video_processor = get_video_processor()

            with tempfile.TemporaryDirectory() as temp_dir:
                # Extract middle frame
                thumbnail_path = Path(temp_dir) / "query_frame.jpg"
                frame_path = video_processor.generate_thumbnail(video_path, thumbnail_path)

                if frame_path is None:
                    logger.error("Could not extract frame from video")
                    return []

                # Search using extracted frame
                return self._search_with_image_query(frame_path, top_k, None)

        except Exception as e:
            logger.error(f"Error in video query search: {e}")
            return []

    def _search_text_content(self, query_text: str, top_k: int) -> List[Dict]:
        """Search text content using BGE embeddings"""
        if not self.document_service:
            logger.warning("Document service not available")
            return []

        try:
            # Use existing document search
            results = self.document_service.search_documents(
                query_text,
                top_k=top_k,
                min_similarity=0.5
            )
            return results

        except Exception as e:
            logger.error(f"Error searching text content: {e}")
            return []

    def _search_images_with_text(self, query_text: str, top_k: int) -> List[Dict]:
        """Search images using CLIP text embedding"""
        if not self.clip_service:
            return []

        try:
            # Encode text query
            text_embedding = self.clip_service.encode_text(query_text)
            if text_embedding is None:
                return []

            # Search for images with matching CLIP embeddings
            # This requires querying media_metadata table
            # Implementation depends on database setup
            return self._search_media_by_clip_embedding(text_embedding, 'image', top_k)

        except Exception as e:
            logger.error(f"Error searching images with text: {e}")
            return []

    def _search_similar_images(self, query_embedding: List[float], top_k: int) -> List[Dict]:
        """Find similar images using CLIP embeddings"""
        try:
            return self._search_media_by_clip_embedding(query_embedding, 'image', top_k)
        except Exception as e:
            logger.error(f"Error searching similar images: {e}")
            return []

    def _search_documents_with_image_embedding(
        self,
        image_embedding: List[float],
        top_k: int
    ) -> List[Dict]:
        """Find documents related to image (via captions or context)"""
        try:
            # This would search for documents that mention concepts in the image
            # Implementation depends on how captions are indexed
            return []
        except Exception as e:
            logger.error(f"Error searching documents with image: {e}")
            return []

    def _search_media_by_clip_embedding(
        self,
        query_embedding: List[float],
        modality: str,
        top_k: int
    ) -> List[Dict]:
        """
        Search media by CLIP embedding

        Args:
            query_embedding: Query CLIP embedding
            modality: Media modality to search ('image', 'video', etc.)
            top_k: Number of results

        Returns:
            List of matching media results
        """
        try:
            if not self.document_service or not self.document_service.db:
                return []

            from models.media import MediaMetadata
            from sqlalchemy import func

            db = self.document_service.db

            # Search using pgvector cosine distance
            results = db.query(MediaMetadata).filter(
                MediaMetadata.modality == modality,
                MediaMetadata.clip_embedding.isnot(None)
            ).order_by(
                MediaMetadata.clip_embedding.cosine_distance(query_embedding)
            ).limit(top_k * 2).all()  # Get more candidates

            # Convert to result format
            formatted_results = []
            for media in results:
                # Calculate similarity score
                similarity = 1.0 - float(
                    db.query(
                        MediaMetadata.clip_embedding.cosine_distance(query_embedding)
                    ).filter(MediaMetadata.id == media.id).scalar()
                )

                formatted_results.append({
                    'media_id': media.id,
                    'chunk_id': media.chunk_id,
                    'modality': media.modality.value,
                    'media_path': media.media_path,
                    'caption': media.caption,
                    'similarity': similarity,
                    'metadata': media.get_metadata_dict()
                })

            return formatted_results[:top_k]

        except Exception as e:
            logger.error(f"Error searching media by CLIP embedding: {e}")
            return []

    def hybrid_search(
        self,
        text_query: str,
        image_query: Optional[Path] = None,
        top_k: int = 10,
        text_weight: float = 0.7,
        image_weight: float = 0.3
    ) -> List[Dict]:
        """
        Hybrid search combining text and image queries

        Args:
            text_query: Text query string
            image_query: Optional path to query image
            top_k: Number of results
            text_weight: Weight for text results (0-1)
            image_weight: Weight for image results (0-1)

        Returns:
            Combined and ranked results
        """
        all_results = []

        # Text query results
        if text_query:
            text_results = self._search_with_text_query(
                text_query,
                top_k * 2,
                None,
                {'text': text_weight, 'image': image_weight}
            )
            all_results.extend(text_results)

        # Image query results
        if image_query:
            image_results = self._search_with_image_query(
                image_query,
                top_k * 2,
                None
            )
            for result in image_results:
                result['fusion_score'] = result.get('similarity', 0.0) * image_weight
            all_results.extend(image_results)

        # Deduplicate and rank
        seen_ids = set()
        unique_results = []

        for result in sorted(all_results, key=lambda x: x.get('fusion_score', 0.0), reverse=True):
            result_id = (result.get('chunk_id'), result.get('media_id'))
            if result_id not in seen_ids:
                seen_ids.add(result_id)
                unique_results.append(result)

        return unique_results[:top_k]


# Example usage
if __name__ == "__main__":
    print("Multimodal Retrieval Service Example")
    print("\nFeatures:")
    print("  - Text → Image search")
    print("  - Image → Text search")
    print("  - Audio → Text search (via transcription)")
    print("  - Video → Image search (via frame extraction)")
    print("  - Hybrid multimodal search")
