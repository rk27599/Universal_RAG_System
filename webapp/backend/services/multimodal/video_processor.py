"""
Video Processor - Extract frames and metadata from videos
Supports keyframe extraction, scene detection, and thumbnail generation
"""

import logging
from typing import List, Optional, Dict, Union, Tuple
from pathlib import Path
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)

# Check for OpenCV
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    logger.warning("OpenCV not available. Install with: pip install opencv-python")

# Check for PIL
try:
    from PIL import Image
    import numpy as np
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("PIL not available. Install with: pip install pillow")


@dataclass
class VideoFrame:
    """Single video frame with metadata"""
    frame_number: int
    timestamp: float  # Seconds
    frame_path: Optional[Path] = None
    is_keyframe: bool = False
    scene_id: Optional[int] = None


@dataclass
class VideoMetadata:
    """Video file metadata"""
    duration: float  # Seconds
    fps: float
    width: int
    height: int
    total_frames: int
    codec: str
    bitrate: Optional[int] = None


class VideoProcessor:
    """
    Video Processor for frame extraction and analysis

    Features:
    - Keyframe extraction
    - Uniform frame sampling
    - Scene detection
    - Thumbnail generation
    - Video metadata extraction
    """

    def __init__(self):
        """Initialize video processor"""
        if not OPENCV_AVAILABLE:
            raise RuntimeError(
                "OpenCV not available. "
                "Install with: pip install opencv-python"
            )

        if not PIL_AVAILABLE:
            raise RuntimeError(
                "PIL not available. "
                "Install with: pip install pillow"
            )

        logger.info("Video Processor initialized")

    def get_video_metadata(
        self,
        video_path: Union[str, Path]
    ) -> Optional[VideoMetadata]:
        """
        Extract video metadata

        Args:
            video_path: Path to video file

        Returns:
            VideoMetadata object or None
        """
        try:
            video_path = Path(video_path)
            if not video_path.exists():
                logger.error(f"Video not found: {video_path}")
                return None

            # Open video
            cap = cv2.VideoCapture(str(video_path))

            if not cap.isOpened():
                logger.error(f"Could not open video: {video_path}")
                return None

            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))

            # Calculate duration
            duration = total_frames / fps if fps > 0 else 0

            # Get codec
            codec = self._fourcc_to_codec(fourcc)

            # Try to get bitrate
            bitrate = cap.get(cv2.CAP_PROP_BITRATE)
            bitrate = int(bitrate) if bitrate > 0 else None

            cap.release()

            metadata = VideoMetadata(
                duration=duration,
                fps=fps,
                width=width,
                height=height,
                total_frames=total_frames,
                codec=codec,
                bitrate=bitrate
            )

            return metadata

        except Exception as e:
            logger.error(f"Error extracting video metadata: {e}")
            return None

    def extract_frames_uniform(
        self,
        video_path: Union[str, Path],
        output_dir: Union[str, Path],
        num_frames: int = 10,
        image_format: str = "jpg"
    ) -> List[VideoFrame]:
        """
        Extract frames uniformly distributed across video

        Args:
            video_path: Path to video file
            output_dir: Directory to save frames
            num_frames: Number of frames to extract
            image_format: Output image format (jpg, png)

        Returns:
            List of VideoFrame objects
        """
        try:
            video_path = Path(video_path)
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            # Get video metadata
            metadata = self.get_video_metadata(video_path)
            if not metadata:
                return []

            # Open video
            cap = cv2.VideoCapture(str(video_path))

            # Calculate frame indices to extract
            frame_indices = [
                int(i * metadata.total_frames / num_frames)
                for i in range(num_frames)
            ]

            extracted_frames = []

            for idx, frame_num in enumerate(frame_indices):
                # Seek to frame
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)

                # Read frame
                ret, frame = cap.read()
                if not ret:
                    logger.warning(f"Could not read frame {frame_num}")
                    continue

                # Calculate timestamp
                timestamp = frame_num / metadata.fps

                # Save frame
                output_path = output_dir / f"frame_{idx:04d}.{image_format}"
                cv2.imwrite(str(output_path), frame)

                extracted_frames.append(VideoFrame(
                    frame_number=frame_num,
                    timestamp=timestamp,
                    frame_path=output_path
                ))

            cap.release()

            logger.info(f"✅ Extracted {len(extracted_frames)} frames from {video_path.name}")
            return extracted_frames

        except Exception as e:
            logger.error(f"Error extracting frames: {e}")
            return []

    def extract_keyframes(
        self,
        video_path: Union[str, Path],
        output_dir: Union[str, Path],
        threshold: float = 30.0,
        max_frames: int = 50
    ) -> List[VideoFrame]:
        """
        Extract keyframes based on scene changes

        Args:
            video_path: Path to video file
            output_dir: Directory to save keyframes
            threshold: Scene change threshold (higher = fewer keyframes)
            max_frames: Maximum number of keyframes to extract

        Returns:
            List of VideoFrame objects
        """
        try:
            video_path = Path(video_path)
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            # Get metadata
            metadata = self.get_video_metadata(video_path)
            if not metadata:
                return []

            # Open video
            cap = cv2.VideoCapture(str(video_path))

            prev_frame = None
            keyframes = []
            frame_num = 0
            scene_id = 0

            while frame_num < metadata.total_frames and len(keyframes) < max_frames:
                ret, frame = cap.read()
                if not ret:
                    break

                # Convert to grayscale for comparison
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                # Check for scene change
                is_keyframe = False
                if prev_frame is None:
                    # First frame is always a keyframe
                    is_keyframe = True
                else:
                    # Calculate difference from previous frame
                    diff = cv2.absdiff(prev_frame, gray)
                    mean_diff = diff.mean()

                    if mean_diff > threshold:
                        is_keyframe = True
                        scene_id += 1

                # Save keyframe
                if is_keyframe:
                    timestamp = frame_num / metadata.fps
                    output_path = output_dir / f"keyframe_{len(keyframes):04d}.jpg"
                    cv2.imwrite(str(output_path), frame)

                    keyframes.append(VideoFrame(
                        frame_number=frame_num,
                        timestamp=timestamp,
                        frame_path=output_path,
                        is_keyframe=True,
                        scene_id=scene_id
                    ))

                prev_frame = gray
                frame_num += 1

            cap.release()

            logger.info(f"✅ Extracted {len(keyframes)} keyframes from {video_path.name}")
            return keyframes

        except Exception as e:
            logger.error(f"Error extracting keyframes: {e}")
            return []

    def generate_thumbnail(
        self,
        video_path: Union[str, Path],
        output_path: Union[str, Path],
        timestamp: Optional[float] = None,
        size: Tuple[int, int] = (320, 240)
    ) -> Optional[Path]:
        """
        Generate a thumbnail from video

        Args:
            video_path: Path to video file
            output_path: Output path for thumbnail
            timestamp: Timestamp to extract (None = middle of video)
            size: Thumbnail size (width, height)

        Returns:
            Path to thumbnail or None
        """
        try:
            video_path = Path(video_path)
            output_path = Path(output_path)

            # Get metadata
            metadata = self.get_video_metadata(video_path)
            if not metadata:
                return None

            # Calculate frame number
            if timestamp is None:
                # Use middle frame
                frame_num = metadata.total_frames // 2
            else:
                frame_num = int(timestamp * metadata.fps)

            # Open video and seek to frame
            cap = cv2.VideoCapture(str(video_path))
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)

            # Read frame
            ret, frame = cap.read()
            cap.release()

            if not ret:
                logger.error(f"Could not read frame for thumbnail")
                return None

            # Resize frame
            frame_resized = cv2.resize(frame, size, interpolation=cv2.INTER_AREA)

            # Save thumbnail
            output_path.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(output_path), frame_resized)

            logger.info(f"✅ Generated thumbnail: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error generating thumbnail: {e}")
            return None

    def extract_frame_at_timestamp(
        self,
        video_path: Union[str, Path],
        timestamp: float,
        output_path: Optional[Union[str, Path]] = None
    ) -> Optional[Path]:
        """
        Extract a single frame at specific timestamp

        Args:
            video_path: Path to video file
            timestamp: Timestamp in seconds
            output_path: Output path (optional)

        Returns:
            Path to extracted frame or None
        """
        try:
            video_path = Path(video_path)

            # Generate output path if not provided
            if output_path is None:
                output_path = video_path.parent / f"{video_path.stem}_frame_{timestamp:.2f}s.jpg"
            else:
                output_path = Path(output_path)

            # Get metadata
            metadata = self.get_video_metadata(video_path)
            if not metadata:
                return None

            # Calculate frame number
            frame_num = int(timestamp * metadata.fps)

            # Open video and seek
            cap = cv2.VideoCapture(str(video_path))
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)

            # Read frame
            ret, frame = cap.read()
            cap.release()

            if not ret:
                logger.error(f"Could not read frame at {timestamp}s")
                return None

            # Save frame
            output_path.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(output_path), frame)

            return output_path

        except Exception as e:
            logger.error(f"Error extracting frame at timestamp: {e}")
            return None

    def _fourcc_to_codec(self, fourcc: int) -> str:
        """Convert FourCC code to codec name"""
        try:
            codec_bytes = [
                chr((fourcc >> 8 * i) & 0xFF)
                for i in range(4)
            ]
            return ''.join(codec_bytes)
        except:
            return "unknown"


# Singleton instance
_video_processor_instance = None


def get_video_processor() -> VideoProcessor:
    """Get singleton video processor instance"""
    global _video_processor_instance
    if _video_processor_instance is None:
        _video_processor_instance = VideoProcessor()
    return _video_processor_instance


# Example usage
if __name__ == "__main__":
    # Test video processor
    processor = VideoProcessor()

    # Test with sample video
    test_video = "test_video.mp4"
    if Path(test_video).exists():
        # Get metadata
        metadata = processor.get_video_metadata(test_video)
        if metadata:
            print(f"\n🎬 Video Metadata:")
            print(f"  Duration: {metadata.duration:.2f}s")
            print(f"  FPS: {metadata.fps}")
            print(f"  Resolution: {metadata.width}x{metadata.height}")
            print(f"  Total frames: {metadata.total_frames}")
            print(f"  Codec: {metadata.codec}")

        # Extract frames
        output_dir = Path("video_frames")
        frames = processor.extract_frames_uniform(
            test_video,
            output_dir,
            num_frames=10
        )
        print(f"\n📸 Extracted {len(frames)} frames to {output_dir}")

        # Generate thumbnail
        thumb_path = Path("thumbnail.jpg")
        processor.generate_thumbnail(test_video, thumb_path)
        print(f"\n🖼️  Generated thumbnail: {thumb_path}")
    else:
        print(f"Test video not found: {test_video}")
