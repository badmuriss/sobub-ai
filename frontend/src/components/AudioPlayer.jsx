import { useEffect, useRef, useImperativeHandle, forwardRef } from 'react';
import apiService from '../services/api';

const AudioPlayer = forwardRef(({ triggerData, onPlayComplete, onPlayStart, onPlayEnd, onAutoplayBlocked }, ref) => {
  const audioRef = useRef(null);

  // Expose methods to parent components
  useImperativeHandle(ref, () => ({
    stopAudio() {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
        audioRef.current.src = '';
        if (onPlayEnd) {
          onPlayEnd();
        }
      }
    },

    async retryPlay() {
      if (audioRef.current && audioRef.current.src) {
        try {
          await audioRef.current.play();
          return true;
        } catch (error) {
          return false;
        }
      }
      return false;
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

        const playPromise = audioRef.current.play();

        if (playPromise !== undefined) {
          try {
            await playPromise;
          } catch (playError) {
            if (onAutoplayBlocked) {
              onAutoplayBlocked();
            } else {
              if (onPlayEnd) {
                onPlayEnd();
              }
            }
          }
        }
      }
    } catch (error) {
      console.error('Failed to play audio:', error);
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
    if (onPlayEnd) {
      onPlayEnd();
    }

    if (onPlayComplete) {
      onPlayComplete();
    }
  };


  const handleError = (e) => {
    console.error('Audio element error:', e);
    if (onPlayEnd) {
      onPlayEnd();
    }
  };

  return (
    <audio
      ref={audioRef}
      onPlay={handlePlay}
      onEnded={handleEnded}
      onError={handleError}
      className="hidden"
    />
  );
});

AudioPlayer.displayName = 'AudioPlayer';

export default AudioPlayer;
