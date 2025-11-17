"""
Multimodal RAG System - Example Usage
Demonstrates text, image, audio, and video processing capabilities
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "webapp" / "backend"))

import asyncio
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


async def example_1_clip_embeddings():
    """Example 1: CLIP text and image embeddings"""
    logger.info("\n" + "="*60)
    logger.info("Example 1: CLIP Text-Image Embeddings")
    logger.info("="*60)

    from services.multimodal.embedding_service_clip import CLIPEmbeddingService
    from services.multimodal.multimodal_embedding_base import ModalityType

    # Initialize CLIP service
    clip = CLIPEmbeddingService(model_name="ViT-L-14")
    clip.load_model()

    # 1. Encode text
    text = "A diagram showing a neural network architecture"
    text_embedding = clip.encode_text(text)
    logger.info(f"✅ Text encoded: '{text}'")
    logger.info(f"   Embedding shape: {len(text_embedding)} dimensions")

    # 2. Encode image (if available)
    test_image = Path("test_image.jpg")
    if test_image.exists():
        image_embedding = clip.encode_image(test_image)
        logger.info(f"✅ Image encoded: {test_image}")
        logger.info(f"   Embedding shape: {len(image_embedding)} dimensions")

        # 3. Compute similarity
        similarity = clip.compute_similarity(text_embedding, image_embedding)
        logger.info(f"📊 Text-Image Similarity: {similarity:.3f}")
    else:
        logger.info(f"⚠️  Test image not found: {test_image}")

    # 4. Batch processing
    texts = [
        "A flowchart diagram",
        "A cat sitting on a couch",
        "A technical schematic"
    ]
    embeddings = clip.encode_batch(texts, ModalityType.TEXT, batch_size=3)
    logger.info(f"✅ Batch encoded {len(embeddings)} texts")

    clip.unload_model()


async def example_2_ocr():
    """Example 2: OCR text extraction"""
    logger.info("\n" + "="*60)
    logger.info("Example 2: OCR Text Extraction")
    logger.info("="*60)

    from services.multimodal.ocr_service import OCRService

    # Initialize OCR service
    ocr = OCRService(use_easyocr=False, languages=['en'])

    # Test with an image containing text
    test_image = Path("test_document.jpg")
    if test_image.exists():
        # Extract text
        result = ocr.extract_text(test_image)

        if result:
            logger.info(f"✅ OCR completed")
            logger.info(f"📄 Extracted Text:\n{result.text[:200]}...")
            logger.info(f"📊 Confidence: {result.confidence:.2%}")
            logger.info(f"🌐 Language: {result.language}")
            logger.info(f"📦 Bounding boxes: {len(result.bounding_boxes)}")
        else:
            logger.error("❌ OCR failed")
    else:
        logger.info(f"⚠️  Test image not found: {test_image}")
        logger.info("   Create a test image with text to try OCR")


async def example_3_image_captioning():
    """Example 3: Image captioning"""
    logger.info("\n" + "="*60)
    logger.info("Example 3: Image Captioning")
    logger.info("="*60)

    from services.multimodal.image_captioning_service import ImageCaptioningService

    try:
        # Initialize captioning service
        captioner = ImageCaptioningService(model_name="Salesforce/blip2-opt-2.7b")
        captioner.load_model()

        test_image = Path("test_image.jpg")
        if test_image.exists():
            # 1. Basic caption
            caption = captioner.generate_caption(test_image)
            logger.info(f"📷 Basic Caption: {caption}")

            # 2. Detailed descriptions
            descriptions = captioner.generate_detailed_description(test_image)
            if descriptions:
                logger.info(f"\n📝 Detailed Descriptions:")
                for desc_type, desc in descriptions.items():
                    logger.info(f"  {desc_type}: {desc}")

            # 3. Check if chart/diagram
            is_chart = captioner.is_chart_or_diagram(test_image)
            logger.info(f"\n📊 Is chart/diagram: {is_chart}")

        else:
            logger.info(f"⚠️  Test image not found: {test_image}")

        captioner.unload_model()

    except Exception as e:
        logger.error(f"❌ Image captioning example failed: {e}")
        logger.info("   This requires BLIP-2 model (~5GB download)")


async def example_4_audio_transcription():
    """Example 4: Audio transcription"""
    logger.info("\n" + "="*60)
    logger.info("Example 4: Audio Transcription")
    logger.info("="*60)

    from services.multimodal.audio_processor import AudioProcessor

    try:
        # Initialize audio processor
        audio_proc = AudioProcessor(
            model_size="base",
            use_faster_whisper=True,
            device="cuda"
        )
        audio_proc.load_model()

        test_audio = Path("test_audio.mp3")
        if test_audio.exists():
            # Get audio duration
            duration = audio_proc.get_audio_duration(test_audio)
            logger.info(f"🎵 Audio file: {test_audio}")
            logger.info(f"⏱️  Duration: {duration:.1f}s")

            # Transcribe
            transcript = audio_proc.transcribe(test_audio, language=None)

            if transcript:
                logger.info(f"\n✅ Transcription completed")
                logger.info(f"🌐 Language: {transcript.language}")
                logger.info(f"📄 Transcript:\n{transcript.text}")
                logger.info(f"\n📊 Segments: {len(transcript.segments)}")

                # Show first 3 segments
                for i, segment in enumerate(transcript.segments[:3], 1):
                    logger.info(
                        f"  [{segment.start_time:.1f}s - {segment.end_time:.1f}s] "
                        f"{segment.text}"
                    )
            else:
                logger.error("❌ Transcription failed")
        else:
            logger.info(f"⚠️  Test audio not found: {test_audio}")
            logger.info("   Create a test audio file to try transcription")

        audio_proc.unload_model()

    except Exception as e:
        logger.error(f"❌ Audio transcription example failed: {e}")
        logger.info("   This requires Whisper model (~140MB download)")


async def example_5_video_processing():
    """Example 5: Video frame extraction"""
    logger.info("\n" + "="*60)
    logger.info("Example 5: Video Processing")
    logger.info("="*60)

    from services.multimodal.video_processor import VideoProcessor

    try:
        video_proc = VideoProcessor()

        test_video = Path("test_video.mp4")
        if test_video.exists():
            # Get metadata
            metadata = video_proc.get_video_metadata(test_video)
            if metadata:
                logger.info(f"🎬 Video: {test_video}")
                logger.info(f"⏱️  Duration: {metadata.duration:.1f}s")
                logger.info(f"📺 Resolution: {metadata.width}x{metadata.height}")
                logger.info(f"🎞️  FPS: {metadata.fps:.1f}")
                logger.info(f"💾 Total frames: {metadata.total_frames}")
                logger.info(f"🔧 Codec: {metadata.codec}")

                # Generate thumbnail
                output_dir = Path("temp_video_output")
                output_dir.mkdir(exist_ok=True)

                thumbnail_path = output_dir / "thumbnail.jpg"
                video_proc.generate_thumbnail(test_video, thumbnail_path)
                logger.info(f"✅ Thumbnail saved: {thumbnail_path}")

                # Extract frames
                frames = video_proc.extract_frames_uniform(
                    test_video,
                    output_dir,
                    num_frames=5
                )
                logger.info(f"✅ Extracted {len(frames)} frames")

                for frame in frames:
                    logger.info(
                        f"  Frame {frame.frame_number} @ {frame.timestamp:.1f}s: "
                        f"{frame.frame_path}"
                    )
        else:
            logger.info(f"⚠️  Test video not found: {test_video}")
            logger.info("   Create a test video file to try video processing")

    except Exception as e:
        logger.error(f"❌ Video processing example failed: {e}")
        logger.info("   This requires OpenCV (pip install opencv-python)")


async def example_6_multimodal_retrieval():
    """Example 6: Cross-modal retrieval"""
    logger.info("\n" + "="*60)
    logger.info("Example 6: Multimodal Retrieval")
    logger.info("="*60)

    from services.multimodal.multimodal_retrieval_service import (
        MultimodalRetrievalService,
        QueryType
    )
    from services.multimodal.embedding_service_clip import CLIPEmbeddingService

    # Initialize services
    clip = CLIPEmbeddingService()
    retrieval = MultimodalRetrievalService(clip_service=clip)

    # Example: Text-to-Image search
    text_query = "flowchart showing system architecture"
    logger.info(f"🔍 Query: '{text_query}'")

    # This would search your database for matching images
    logger.info(f"   → Searching for images matching text query...")
    logger.info(f"   → In production, this queries media_metadata table")
    logger.info(f"   → Returns images with similar CLIP embeddings")

    # Example: Image-to-Text search
    test_image = Path("query_image.jpg")
    if test_image.exists():
        logger.info(f"\n🖼️  Query Image: {test_image}")
        logger.info(f"   → Searching for documents related to this image...")
        logger.info(f"   → Finds text chunks discussing similar concepts")

    logger.info(f"\n💡 Multimodal Retrieval Features:")
    logger.info(f"   - Text → Image: Find images matching description")
    logger.info(f"   - Image → Text: Find documents about image content")
    logger.info(f"   - Audio → Text: Search via transcription")
    logger.info(f"   - Video → Image: Search via extracted frames")
    logger.info(f"   - Hybrid: Combine multiple query modalities")


async def main():
    """Run all examples"""
    logger.info("\n" + "="*60)
    logger.info("🎨 MULTIMODAL RAG SYSTEM - EXAMPLES")
    logger.info("="*60)

    logger.info("\nThis demo showcases:")
    logger.info("  ✅ CLIP embeddings (text + image)")
    logger.info("  ✅ OCR text extraction")
    logger.info("  ✅ Image captioning (BLIP-2)")
    logger.info("  ✅ Audio transcription (Whisper)")
    logger.info("  ✅ Video frame extraction")
    logger.info("  ✅ Cross-modal retrieval")

    # Run examples
    try:
        await example_1_clip_embeddings()
    except Exception as e:
        logger.error(f"Example 1 failed: {e}")

    try:
        await example_2_ocr()
    except Exception as e:
        logger.error(f"Example 2 failed: {e}")

    try:
        await example_3_image_captioning()
    except Exception as e:
        logger.error(f"Example 3 failed: {e}")

    try:
        await example_4_audio_transcription()
    except Exception as e:
        logger.error(f"Example 4 failed: {e}")

    try:
        await example_5_video_processing()
    except Exception as e:
        logger.error(f"Example 5 failed: {e}")

    try:
        await example_6_multimodal_retrieval()
    except Exception as e:
        logger.error(f"Example 6 failed: {e}")

    logger.info("\n" + "="*60)
    logger.info("✅ Examples completed!")
    logger.info("="*60)

    logger.info("\n📚 Next Steps:")
    logger.info("  1. Upload documents via web UI")
    logger.info("  2. System will auto-extract images, audio, video")
    logger.info("  3. Try cross-modal search queries")
    logger.info("  4. See webapp/docs/MULTIMODAL_GUIDE.md for details")


if __name__ == "__main__":
    asyncio.run(main())
