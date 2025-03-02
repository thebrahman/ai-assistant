import logging
import tempfile
import os
import numpy as np
import sounddevice as sd
import soundfile as sf
import threading
import pygame
from gtts import gTTS
from groq import Groq

logger = logging.getLogger(__name__)

class AudioManager:
    """Handles audio recording, speech-to-text, and text-to-speech functionality."""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        
        # Fix: Use named parameter 'default' for dictionaries
        speech_config = config_manager.get("speech", default={})
        stt_config = config_manager.get("speech", "stt", default={})
        tts_config = config_manager.get("speech", "tts", default={})
        
        # STT configuration
        self.stt_engine = stt_config.get("engine", "groq")
        self.stt_api_key = stt_config.get("api_key", "")
        self.stt_model = stt_config.get("model", "whisper-large-v3-turbo")
        
        # TTS configuration
        self.tts_engine = tts_config.get("engine", "gtts")
        self.tts_rate = tts_config.get("rate", 190)
        self.tts_volume = tts_config.get("volume", 1.0)
        self.tts_voice = tts_config.get("voice", None)
        
        # Audio recording configuration
        self.channels = 1
        self.sample_rate = 16000
        self.recording = False
        self.frames = []
        self.stream = None
        
        # Initialize pygame mixer for audio playback
        pygame.mixer.init()
        logger.info(f"Audio Manager initialized with TTS engine: {self.tts_engine}")
    
    def start_recording(self):
        """Start recording audio from the microphone."""
        if self.recording:
            return
        
        self.frames = []
        self.recording = True
        
        def callback(indata, frames, time, status):
            if status:
                logger.warning(f"Audio callback status: {status}")
            if self.recording:
                self.frames.append(indata.copy())
        
        try:
            self.stream = sd.InputStream(
                callback=callback,
                channels=self.channels,
                samplerate=self.sample_rate
            )
            self.stream.start()
            logger.info("Audio recording started")
        except Exception as e:
            logger.error(f"Error starting audio recording: {e}")
            self.recording = False
    
    def stop_recording(self):
        """
        Stop recording audio and return the recorded data.
        
        Returns:
            numpy.ndarray: Recorded audio data
        """
        if not self.recording:
            return None
        
        self.recording = False
        
        try:
            self.stream.stop()
            self.stream.close()
            
            if not self.frames:
                logger.warning("No audio data recorded")
                return None
            
            # Combine all recorded frames
            audio_data = np.concatenate(self.frames, axis=0)
            logger.info(f"Audio recording stopped. Duration: {len(audio_data) / self.sample_rate:.2f} seconds")
            
            return audio_data
        except Exception as e:
            logger.error(f"Error stopping audio recording: {e}")
            return None
    
    def transcribe_audio(self, audio_data):
        """
        Convert audio data to text using the configured STT engine.
        
        Args:
            audio_data (numpy.ndarray): Audio data to transcribe
            
        Returns:
            str: Transcribed text
        """
        if audio_data is None or (isinstance(audio_data, np.ndarray) and audio_data.size == 0):
            logger.warning("No audio data to transcribe")
            return ""
        
        if self.stt_engine == "groq":
            return self._transcribe_with_groq(audio_data)
        else:
            logger.error(f"Unsupported STT engine: {self.stt_engine}")
            return ""
    
    def _transcribe_with_groq(self, audio_data):
        """
        Transcribe audio data using the Groq API.
        
        Args:
            audio_data (numpy.ndarray): Audio data to transcribe
            
        Returns:
            str: Transcribed text
        """
        try:
            # Check if API key is available
            if not self.stt_api_key:
                logger.error("Groq API key not configured")
                return "Error: Groq API key not configured. Please add your API key to the config file."
            
            # Save audio to a temporary file for processing
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                tmp_path = tmp_file.name
            
            sf.write(tmp_path, audio_data, self.sample_rate)
            
            # Initialize Groq client
            client = Groq(api_key=self.stt_api_key)
            
            # Use the audio transcriptions API
            with open(tmp_path, "rb") as audio_file:
                transcription = client.audio.transcriptions.create(
                    file=(tmp_path, audio_file.read()),
                    model=self.stt_model,
                )
            
            # Clean up temporary file
            os.unlink(tmp_path)
            
            # Get transcribed text
            transcribed_text = transcription.text.strip()
            logger.info(f"Audio transcribed: \"{transcribed_text}\"")
            return transcribed_text
            
        except Exception as e:
            logger.error(f"Error transcribing audio with Groq: {e}")
            return f"Error: {str(e)}"
    
    def speak_text(self, text):
        """
        Convert text to speech using the configured TTS engine.
        
        Args:
            text (str): Text to speak
        """
        if not text:
            logger.warning("No text to speak")
            return
        
        # Select TTS engine based on configuration
        if self.tts_engine.lower() == "gtts":
            threading.Thread(target=self._speak_with_gtts, args=(text,)).start()
        else:
            logger.warning(f"Unsupported TTS engine: {self.tts_engine}. Using gTTS as fallback.")
            threading.Thread(target=self._speak_with_gtts, args=(text,)).start()
    
    def _speak_with_gtts(self, text):
        """
        Speak text using Google Text-to-Speech.
        
        Args:
            text (str): Text to speak
        """
        try:
            # Create a temporary file for the audio
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
                temp_filename = fp.name
            
            # Generate speech
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(temp_filename)
            
            # Play the audio
            pygame.mixer.music.load(temp_filename)
            pygame.mixer.music.play()
            
            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            
            # Clean up
            os.unlink(temp_filename)
            
            logger.info("Text spoken successfully with gTTS")
        except Exception as e:
            logger.error(f"Error speaking text with gTTS: {e}")