import random
import time
import logging
from typing import Optional, Dict, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class TriggerEngine:
    """Manages triggering logic with cooldown and probability."""
    
    def __init__(self):
        self.last_trigger_time: Optional[float] = None
        self.cooldown_seconds: int = 300  # Default 5 minutes
        self.trigger_probability: float = 30.0  # Default 30%
    
    def set_cooldown(self, seconds: int):
        """Set the cooldown period in seconds."""
        self.cooldown_seconds = seconds
        logger.info(f"Cooldown set to {seconds} seconds")
    
    def set_probability(self, probability: float):
        """Set the trigger probability (0-100)."""
        self.trigger_probability = max(0.0, min(100.0, probability))
        logger.info(f"Trigger probability set to {self.trigger_probability}%")
    
    def is_cooldown_active(self) -> bool:
        """Check if cooldown is currently active."""
        if self.last_trigger_time is None:
            return False
        
        elapsed = time.time() - self.last_trigger_time
        return elapsed < self.cooldown_seconds
    
    def get_cooldown_remaining(self) -> int:
        """Get remaining cooldown time in seconds."""
        if not self.is_cooldown_active():
            return 0
        
        elapsed = time.time() - self.last_trigger_time
        remaining = self.cooldown_seconds - elapsed
        return max(0, int(remaining))
    
    def should_trigger(self) -> bool:
        """
        Determine if a trigger should occur based on probability.
        Does not check cooldown - call is_cooldown_active() first.
        
        Returns:
            True if random check passes
        """
        roll = random.uniform(0, 100)
        should_fire = roll < self.trigger_probability
        
        logger.debug(f"Probability check: {roll:.2f} < {self.trigger_probability} = {should_fire}")
        return should_fire
    
    def select_random_meme(self, matching_memes: List[Dict]) -> Optional[Dict]:
        """
        Select a random meme from the matching list.
        
        Args:
            matching_memes: List of memes that match the context
            
        Returns:
            Selected meme dict or None
        """
        if not matching_memes:
            return None
        
        return random.choice(matching_memes)
    
    def attempt_trigger(self, matching_memes: List[Dict]) -> Optional[Dict]:
        """
        Attempt to trigger a meme based on cooldown and probability.
        
        Args:
            matching_memes: List of memes that match the current context
            
        Returns:
            Selected meme if triggered, None otherwise
        """
        # Check if we have any matching memes
        if not matching_memes:
            logger.debug("No matching memes")
            return None
        
        # Check cooldown
        if self.is_cooldown_active():
            remaining = self.get_cooldown_remaining()
            logger.debug(f"Cooldown active: {remaining}s remaining")
            return None
        
        # Check probability
        if not self.should_trigger():
            logger.debug("Probability check failed")
            return None
        
        # Select and trigger meme
        selected_meme = self.select_random_meme(matching_memes)
        if selected_meme:
            self.last_trigger_time = time.time()
            logger.info(f"Triggered meme: {selected_meme['filename']} (ID: {selected_meme['id']})")
        
        return selected_meme
    
    def reset_cooldown(self):
        """Manually reset the cooldown (for testing or manual control)."""
        self.last_trigger_time = None
        logger.info("Cooldown reset")
    
    def get_status(self) -> Dict:
        """Get current trigger engine status."""
        return {
            "cooldown_seconds": self.cooldown_seconds,
            "trigger_probability": self.trigger_probability,
            "cooldown_active": self.is_cooldown_active(),
            "cooldown_remaining": self.get_cooldown_remaining(),
            "last_trigger_time": datetime.fromtimestamp(self.last_trigger_time).isoformat() if self.last_trigger_time else None
        }


# Global instance
trigger_engine = TriggerEngine()
