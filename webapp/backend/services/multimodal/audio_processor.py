"""
Audio Processor - Transcribe audio using Whisper
Supports multiple audio formats and languages
"""

import logging
from typing import List, Optional, Dict, Union
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
import json

logger = logging.getLogger(__name__)

# Check for Whisper
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logger.warning("Whisper not available. Install with: pip install openai-whisper")

# Check for faster-whisper (optional, much faster)
try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False
    logger.info("faster-whisper not available. Install with: pip install faster-whisper")


@dataclass
class TranscriptSegment:
    """Single transcript segment with timing"""
    text: str
    start_time: float
    end_time: float
    confidence: float = 1.0
    language: str = "en"
    speaker_id: Optional[str] = None


@dataclass
class AudioTranscript:
    """Complete audio transcript"""
    text: str
    language: str
    segments: List[TranscriptSegment]
    duration: float
    method: str  # whisper, faster-whisper
    model_size: str  # tiny, base, small, medium, large


class AudioProcessor:
    """
    Audio Processor for transcription using Whisper

    Features:
    - OpenAI Whisper (accurate, slower)
    - faster-whisper (10x faster, same quality)
    - Multi-language support (100+ languages)
    - Time-aligned segments
    - Speaker diarization ready
    - GPU acceleration
    """

    def __init__(
        self,
        model_size: str = "base",
        use_faster_whisper: bool = True,
        device: str = "cuda",
        compute_type: str = "float16"
    ):
        """
        Initialize audio processor

        Args:
            model_size: Whisper model size
                       - tiny: fastest, lowest quality
                       - base: balanced (recommended)
                       - small: good quality
                       - medium: better quality
                       - large: best quality, slowest
            use_faster_whisper: Use faster-whisper if available
            device: Device for inference (cuda, cpu)
            compute_type: Compute type for faster-whisper (float16, int8)
        """
        self.model_size = model_size
        self.use_faster_whisper = use_faster_whisper and FASTER_WHISPER_AVAILABLE
        self.device = device
        self.compute_type = compute_type
        self.model = None
        self.last_access_time: Optional[datetime] = None

        if self.use_faster_whisper:
            if not FASTER_WHISPER_AVAILABLE:
                logger.warning("faster-whisper not available, using standard Whisper")
                self.use_faster_whisper = False
            else:
                logger.info(f"Using faster-whisper")
        else:
            if not WHISPER_AVAILABLE:
                raise RuntimeError(
                    "Neither Whisper nor faster-whisper available. "
                    "Install: pip install openai-whisper faster-whisper"
                )
            logger.info(f"Using standard Whisper")

        logger.info(f"Model size: {model_size}")
        logger.info(f"Device: {device}")

    def load_model(self):
        """Load Whisper model"""
        if self.model is None:
            try:
                logger.info(f"Loading Whisper model: {self.model_size}")

                if self.use_faster_whisper:
                    # Load faster-whisper model
                    self.model = WhisperModel(
                        self.model_size,
                        device=self.device,
                        compute_type=self.compute_type
                    )
                else:
                    # Load standard Whisper model
                    self.model = whisper.load_model(
                        self.model_size,
                        device=self.device
                    )

                self.last_access_time = datetime.now()
                logger.info(f"✅ Whisper model loaded successfully")

            except Exception as e:
                logger.error(f"❌ Failed to load Whisper model: {e}")
                raise RuntimeError(f"Failed to load Whisper model: {e}")

    def unload_model(self):
        """Unload model to free memory"""
        if self.model is not None:
            logger.info(f"🔄 Unloading Whisper model...")

            del self.model
            self.model = None

            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            import gc
            gc.collect()

            self.last_access_time = None
            logger.info(f"✅ Whisper model unloaded")

    def transcribe(
        self,
        audio_path: Union[str, Path],
        language: Optional[str] = None,
        task: str = "transcribe"
    ) -> Optional[AudioTranscript]:
        """
        Transcribe audio file

        Args:
            audio_path: Path to audio file (mp3, wav, m4a, etc.)
            language: Language code (e.g., 'en', 'es', 'zh')
                     If None, auto-detect language
            task: Task type ('transcribe' or 'translate' to English)

        Returns:
            AudioTranscript object with full transcript and segments
        """
        try:
            # Ensure model is loaded
            if self.model is None:
                self.load_model()

            self.last_access_time = datetime.now()

            audio_path = Path(audio_path)
            if not audio_path.exists():
                logger.error(f"Audio file not found: {audio_path}")
                return None

            logger.info(f"Transcribing: {audio_path.name}")

            if self.use_faster_whisper:
                return self._transcribe_faster_whisper(audio_path, language, task)
            else:
                return self._transcribe_standard_whisper(audio_path, language, task)

        except Exception as e:
            logger.error(f"Error transcribing {audio_path}: {e}")
            return None

    def _transcribe_standard_whisper(
        self,
        audio_path: Path,
        language: Optional[str],
        task: str
    ) -> AudioTranscript:
        """Transcribe using standard Whisper"""
        # Transcribe
        result = self.model.transcribe(
            str(audio_path),
            language=language,
            task=task,
            verbose=False
        )

        # Parse segments
        segments = []
        for seg in result['segments']:
            segments.append(TranscriptSegment(
                text=seg['text'].strip(),
                start_time=seg['start'],
                end_time=seg['end'],
                confidence=seg.get('confidence', 1.0),
                language=result['language']
            ))

        # Create transcript
        transcript = AudioTranscript(
            text=result['text'].strip(),
            language=result['language'],
            segments=segments,
            duration=segments[-1].end_time if segments else 0.0,
            method="whisper",
            model_size=self.model_size
        )

        return transcript

    def _transcribe_faster_whisper(
        self,
        audio_path: Path,
        language: Optional[str],
        task: str
    ) -> AudioTranscript:
        """Transcribe using faster-whisper"""
        # Transcribe
        segments_generator, info = self.model.transcribe(
            str(audio_path),
            language=language,
            task=task,
            beam_size=5,
            vad_filter=True,  # Voice activity detection
            vad_parameters=dict(min_silence_duration_ms=500)
        )

        # Collect segments
        segments = []
        full_text = []

        for seg in segments_generator:
            segments.append(TranscriptSegment(
                text=seg.text.strip(),
                start_time=seg.start,
                end_time=seg.end,
                confidence=seg.avg_logprob,  # Log probability as confidence
                language=info.language
            ))
            full_text.append(seg.text.strip())

        # Create transcript
        transcript = AudioTranscript(
            text=" ".join(full_text),
            language=info.language,
            segments=segments,
            duration=segments[-1].end_time if segments else 0.0,
            method="faster-whisper",
            model_size=self.model_size
        )

        return transcript

    def get_audio_duration(self, audio_path: Union[str, Path]) -> Optional[float]:
        """
        Get duration of audio file in seconds

        Args:
            audio_path: Path to audio file

        Returns:
            Duration in seconds or None
        """
        try:
            import subprocess
            import json

            audio_path = Path(audio_path)
            if not audio_path.exists():
                return None

            # Use ffprobe to get duration
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                str(audio_path)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            data = json.loads(result.stdout)

            duration = float(data['format']['duration'])
            return duration

        except Exception as e:
            logger.warning(f"Could not get audio duration: {e}")
            return None

    def extract_audio_from_video(
        self,
        video_path: Union[str, Path],
        output_audio_path: Optional[Union[str, Path]] = None
    ) -> Optional[Path]:
        """
        Extract audio from video file

        Args:
            video_path: Path to video file
            output_audio_path: Output path for audio (optional)

        Returns:
            Path to extracted audio file or None
        """
        try:
            import subprocess

            video_path = Path(video_path)
            if not video_path.exists():
                logger.error(f"Video file not found: {video_path}")
                return None

            # Generate output path if not provided
            if output_audio_path is None:
                output_audio_path = video_path.parent / f"{video_path.stem}_audio.mp3"
            else:
                output_audio_path = Path(output_audio_path)

            logger.info(f"Extracting audio from: {video_path.name}")

            # Extract audio using ffmpeg
            cmd = [
                'ffmpeg',
                '-i', str(video_path),
                '-vn',  # No video
                '-acodec', 'libmp3lame',  # MP3 codec
                '-ab', '192k',  # Bitrate
                '-ar', '44100',  # Sample rate
                '-y',  # Overwrite output
                str(output_audio_path)
            ]

            subprocess.run(cmd, check=True, capture_output=True)

            logger.info(f"✅ Audio extracted to: {output_audio_path}")
            return output_audio_path

        except Exception as e:
            logger.error(f"Error extracting audio: {e}")
            return None

    def transcribe_batch(
        self,
        audio_paths: List[Union[str, Path]],
        language: Optional[str] = None
    ) -> List[Optional[AudioTranscript]]:
        """
        Transcribe multiple audio files

        Args:
            audio_paths: List of audio file paths
            language: Language code (optional)

        Returns:
            List of AudioTranscript objects
        """
        transcripts = []

        for i, audio_path in enumerate(audio_paths):
            logger.info(f"Processing {i+1}/{len(audio_paths)}: {audio_path}")
            transcript = self.transcribe(audio_path, language)
            transcripts.append(transcript)

        return transcripts

    def is_loaded(self) -> bool:
        """Check if model is loaded"""
        return self.model is not None

    def get_model_info(self) -> Dict[str, any]:
        """Get model information"""
        return {
            "model_size": self.model_size,
            "method": "faster-whisper" if self.use_faster_whisper else "whisper",
            "device": self.device,
            "is_loaded": self.is_loaded()
        }


# Singleton instance
_audio_processor_instance = None


def get_audio_processor(model_size: str = "base") -> AudioProcessor:
    """Get singleton audio processor instance"""
    global _audio_processor_instance
    if _audio_processor_instance is None:
        _audio_processor_instance = AudioProcessor(model_size=model_size)
    return _audio_processor_instance


# Example usage
if __name__ == "__main__":
    # Test audio processor
    processor = AudioProcessor(model_size="base", use_faster_whisper=True)

    # Test with sample audio
    test_audio = "test_audio.mp3"
    if Path(test_audio).exists():
        transcript = processor.transcribe(test_audio)

        if transcript:
            print(f"\n🎤 Transcript:")
            print(transcript.text)
            print(f"\n🌐 Language: {transcript.language}")
            print(f"⏱️  Duration: {transcript.duration:.2f}s")
            print(f"📊 Segments: {len(transcript.segments)}")
            print(f"🔧 Method: {transcript.method}")

            # Print segments
            print(f"\n📜 Segments:")
            for i, seg in enumerate(transcript.segments[:5], 1):
                print(f"  [{seg.start_time:.1f}s - {seg.end_time:.1f}s] {seg.text}")
    else:
        print(f"Test audio not found: {test_audio}")
