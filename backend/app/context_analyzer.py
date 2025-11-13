import re
from typing import List, Set, Dict, Tuple
import logging
from unidecode import unidecode
from nltk.stem import PorterStemmer

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
        self.stemmer = PorterStemmer()

    def normalize_text(self, text: str, apply_stemming: bool = False) -> str:
        """
        Normalize text by removing accents, converting to lowercase, and optionally stemming.

        Args:
            text: Input text to normalize
            apply_stemming: Whether to apply word stemming (default: False)

        Returns:
            Normalized text string
        """
        if not text:
            return ""

        # Remove accents/diacritics (café → cafe, niño → nino)
        text = unidecode(text)

        # Convert to lowercase
        text = text.lower()

        # Remove punctuation but keep spaces and alphanumeric
        text = re.sub(r'[^a-z0-9\s]', ' ', text)

        # Apply stemming if requested
        if apply_stemming:
            words = text.split()
            stemmed_words = [self.stemmer.stem(word) for word in words if word]
            text = ' '.join(stemmed_words)

        # Clean up extra whitespace
        text = ' '.join(text.split())

        return text

    def extract_keywords(self, text: str, apply_stemming: bool = True) -> Set[str]:
        """
        Extract meaningful keywords from text with normalization.

        Args:
            text: Input text to analyze
            apply_stemming: Whether to apply word stemming (default: True)

        Returns:
            Set of normalized keywords
        """
        # Normalize text (accents, lowercase, punctuation, optional stemming)
        normalized = self.normalize_text(text, apply_stemming=apply_stemming)

        # Split into words
        words = normalized.split()

        # Filter out stop words and short words
        keywords = {
            word for word in words
            if word not in self.stop_words and len(word) > 2
        }

        return keywords

    def score_matches(self, text: str, matched_tags: List[str]) -> Dict[str, int]:
        """
        Score matched tags by word count (more words = more specific).

        Args:
            text: Original transcribed text
            matched_tags: List of tags that matched

        Returns:
            Dictionary mapping tag to its score (word count)
        """
        scores = {}
        text_lower = text.lower()

        for tag in matched_tags:
            tag_lower = tag.lower()
            # Count words in the tag (split by whitespace)
            word_count = len(tag_lower.split())

            # Score is the word count of the tag if it appears in text
            if tag_lower in text_lower:
                scores[tag] = word_count
            else:
                # Fallback: tag matched via keyword but not exact phrase
                scores[tag] = max(1, word_count // 2)  # Half score, minimum 1

        return scores

    def match_tags(self, text: str, available_tags: List[str], use_stemming: bool = True) -> Tuple[List[str], Dict[str, int]]:
        """
        Match text against available tags with full normalization (accents + optional stemming).

        Args:
            text: Transcribed text to analyze
            available_tags: List of all available tags from memes
            use_stemming: Whether to apply word stemming (default: True)

        Returns:
            Tuple of (matched_tags, match_scores)
        """
        if not text or not available_tags:
            return [], {}

        # Normalize transcription text with optional stemming
        normalized_text = self.normalize_text(text, apply_stemming=use_stemming)

        # Extract keywords from normalized text
        keywords = self.extract_keywords(text, apply_stemming=use_stemming)

        # Normalize all tags with optional stemming and create mapping
        normalized_tags = {
            self.normalize_text(tag, apply_stemming=use_stemming): tag
            for tag in available_tags
        }

        matched_tags = []

        # Match tags as complete phrases in the normalized text
        # This ensures multi-word tags match only when the whole phrase appears
        for normalized_tag, original_tag in normalized_tags.items():
            # Check if the entire normalized tag phrase appears in normalized text
            # Use word boundaries to ensure complete phrase matching
            tag_words = normalized_tag.split()
            text_words = normalized_text.split()

            # Single-word tags: match if word appears in text
            if len(tag_words) == 1:
                if normalized_tag in text_words:
                    matched_tags.append(original_tag)
            # Multi-word tags: match only if complete phrase appears
            else:
                # Check if the tag phrase appears as a substring in the text
                if normalized_tag in normalized_text:
                    matched_tags.append(original_tag)

        # Score the matched tags (using original text for word count)
        match_scores = self.score_matches(text, matched_tags)

        if matched_tags:
            logger.info(f"Matched tags with scores: {match_scores} from text: '{text}' (normalized: '{normalized_text}', stemming: {use_stemming})")
        else:
            logger.debug(f"No matches found for text: '{text}' (normalized: '{normalized_text}', stemming: {use_stemming})")

        return matched_tags, match_scores
    
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
