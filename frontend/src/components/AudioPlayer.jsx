import { useEffect, useRef, useImperativeHandle, forwardRef } from 'react';
import apiService from '../services/api';

const AudioPlayer = forwardRef(({ triggerData, onPlayComplete, onPlayStart, onPlayEnd }, ref) => {
  const audioRef = useRef(null);

  // Expose stopAudio method to parent components
  useImperativeHandle(ref, () => ({
    stopAudio() {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
        audioRef.current.src = '';
        // Notify that playback stopped
        if (onPlayEnd) {
          onPlayEnd();
        }
      }
    }
  }));

  useEffect(() => {
    if (triggerData && triggerData.meme_id) {
      playAudio(triggerData.meme_id);
    }
  }, [triggerData]);

  const playAudio = async (memeId) => {
    try {
      const audioUrl = apiService.getMemeAudioUrl(memeId);

      if (audioRef.current) {
        audioRef.current.src = audioUrl;
        await audioRef.current.play();
      }
    } catch (error) {
      console.error('Failed to play audio:', error);
      // Reset audio playing state if playback fails
      if (onPlayEnd) {
        onPlayEnd();
      }
    }
  };

  const handlePlay = () => {
    // Notify that audio playback started
    if (onPlayStart) {
      onPlayStart();
    }
  };

  const handleEnded = () => {
    // Notify that audio playback ended
    if (onPlayEnd) {
      onPlayEnd();
    }

    if (onPlayComplete) {
      onPlayComplete();
    }
  };

  const handlePause = () => {
    // Don't do anything on pause - onEnded handles when audio finishes
    // This prevents duplicate onPlayEnd() calls
  };

  const handleError = (e) => {
    console.error('Audio element error:', e);
    // Reset audio playing state on error
    if (onPlayEnd) {
      onPlayEnd();
    }
  };

  return (
    <audio
      ref={audioRef}
      onPlay={handlePlay}
      onEnded={handleEnded}
      onPause={handlePause}
      onError={handleError}
      className="hidden"
    />
  );
});

AudioPlayer.displayName = 'AudioPlayer';

export default AudioPlayer;
