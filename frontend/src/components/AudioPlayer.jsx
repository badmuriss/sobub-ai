import { useEffect, useRef } from 'react';
import apiService from '../services/api';

export default function AudioPlayer({ triggerData, onPlayComplete, onPlayStart, onPlayEnd }) {
  const audioRef = useRef(null);

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
    // If audio is paused/stopped, also notify
    if (audioRef.current && audioRef.current.ended && onPlayEnd) {
      onPlayEnd();
    }
  };

  return (
    <audio
      ref={audioRef}
      onPlay={handlePlay}
      onEnded={handleEnded}
      onPause={handlePause}
      className="hidden"
    />
  );
}
