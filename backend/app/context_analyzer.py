import re
from typing import List, Set
import logging

logger = logging.getLogger(__name__)


class ContextAnalyzer:
    """Analyzes transcribed text to match against meme tags."""
    
    def __init__(self):
        self.stop_words = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'will', 'with', 'the', 'this', 'but', 'they', 'have',
            'had', 'what', 'when', 'where', 'who', 'which', 'why', 'how'
        }
    
    def extract_keywords(self, text: str) -> Set[str]:
        """
        Extract meaningful keywords from text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Set of keywords
        """
        # Convert to lowercase
        text = text.lower()
        
        # Remove punctuation and split into words
        words = re.findall(r'\b\w+\b', text)
        
        # Filter out stop words and short words
        keywords = {
            word for word in words 
            if word not in self.stop_words and len(word) > 2
        }
        
        return keywords
    
    def match_tags(self, text: str, available_tags: List[str]) -> List[str]:
        """
        Match text against available tags.
        
        Args:
            text: Transcribed text to analyze
            available_tags: List of all available tags from memes
            
        Returns:
            List of matched tags
        """
        if not text or not available_tags:
            return []
        
        # Extract keywords from text
        keywords = self.extract_keywords(text)
        
        # Normalize tags for comparison
        normalized_tags = {tag.lower(): tag for tag in available_tags}
        
        matched_tags = []
        
        # Direct keyword matching
        for keyword in keywords:
            if keyword in normalized_tags:
                matched_tags.append(normalized_tags[keyword])
        
        # Partial matching (tag contains keyword or keyword contains tag)
        for keyword in keywords:
            for normalized_tag, original_tag in normalized_tags.items():
                if original_tag not in matched_tags:
                    # Check if keyword is in tag or tag is in keyword
                    if normalized_tag in keyword or keyword in normalized_tag:
                        matched_tags.append(original_tag)
        
        # Check for multi-word tags
        text_lower = text.lower()
        for normalized_tag, original_tag in normalized_tags.items():
            if original_tag not in matched_tags:
                # Check if the entire tag phrase appears in the text
                if normalized_tag in text_lower:
                    matched_tags.append(original_tag)
        
        if matched_tags:
            logger.info(f"Matched tags: {matched_tags} from text: '{text}'")
        
        return matched_tags
    
    def get_unique_tags_from_memes(self, memes: List[dict]) -> List[str]:
        """
        Extract all unique tags from meme list.
        
        Args:
            memes: List of meme dictionaries with 'tags' field
            
        Returns:
            List of unique tags
        """
        all_tags = set()
        for meme in memes:
            if 'tags' in meme:
                all_tags.update(meme['tags'])
        
        return list(all_tags)


# Global instance
context_analyzer = ContextAnalyzer()
