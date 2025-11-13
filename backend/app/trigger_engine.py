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

    def select_meme_with_preference(self, matching_memes: List[Dict], match_scores: Dict[str, int]) -> Optional[Dict]:
        """
        Select meme with preference for longer matching tags.

        Strategy:
        1. Calculate score for each meme (max score of its matched tags)
        2. Group memes by score
        3. Select from highest-scoring group randomly

        Args:
            matching_memes: List of memes that match
            match_scores: Dictionary mapping tags to their scores

        Returns:
            Selected meme dict or None
        """
        if not matching_memes:
            return None

        # Calculate score for each meme
        meme_scores = []
        for meme in matching_memes:
            # Find highest scoring tag that matches this meme
            max_score = 0
            for tag in meme.get('tags', []):
                if tag in match_scores:
                    max_score = max(max_score, match_scores[tag])
            meme_scores.append((meme, max_score))

        # Get memes with highest score
        if not meme_scores:
            return self.select_random_meme(matching_memes)

        max_score = max(score for _, score in meme_scores)
        top_memes = [meme for meme, score in meme_scores if score == max_score]

        # Log preference selection
        if len(top_memes) < len(matching_memes):
            logger.info(f"Preference selection: {len(top_memes)}/{len(matching_memes)} memes with score {max_score}")

        # Random selection within top-scoring group
        return random.choice(top_memes)

    def attempt_trigger(self, matching_memes: List[Dict], match_scores: Dict[str, int] = None) -> Optional[Dict]:
        """
        Attempt to trigger a meme based on cooldown and probability.
        Note: Cooldown is NOT started here - call start_cooldown() after audio finishes.

        Args:
            matching_memes: List of memes that match the current context
            match_scores: Optional dictionary of tag scores for preference-based selection

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

        # Select and trigger meme (cooldown will be started when audio ends)
        # Use preference-based selection if scores provided, otherwise random
        if match_scores:
            selected_meme = self.select_meme_with_preference(matching_memes, match_scores)
        else:
            selected_meme = self.select_random_meme(matching_memes)

        if selected_meme:
            logger.info(f"Triggered meme: {selected_meme['filename']} (ID: {selected_meme['id']})")

        return selected_meme

    def start_cooldown(self):
        """Start the cooldown timer (call this when audio finishes playing)."""
        self.last_trigger_time = time.time()
        logger.info(f"Cooldown started ({self.cooldown_seconds}s)")
    
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
