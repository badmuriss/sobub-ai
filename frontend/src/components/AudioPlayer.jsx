import { useEffect, useRef } from 'react';
import apiService from '../services/api';

export default function AudioPlayer({ triggerData, onPlayComplete }) {
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

  const handleEnded = () => {
    if (onPlayComplete) {
      onPlayComplete();
    }
  };

  return (
    <audio
      ref={audioRef}
      onEnded={handleEnded}
      className="hidden"
    />
  );
}
