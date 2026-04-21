"""
Voice Matcher Service
Automatically selects the best voice profile based on video subject/keywords
"""
from typing import Dict, Optional
from loguru import logger


class VoiceMatcher:
    """Maps video subjects to optimal voice profiles"""
    
    # Voice profile definitions for AllTalk v2
    VOICE_PROFILES = {
        "authoritative_male": {
            "name": "Graham",  # Deep, trustworthy
            "speed": 0.9,
            "stability": 0.85,
            "best_for": ["history", "finance", "science", "documentary", "true crime", "politics"]
        },
        "friendly_female": {
            "name": "Pippa",  # Warm, approachable
            "speed": 1.0,
            "stability": 0.80,
            "best_for": ["tutorial", "how-to", "lifestyle", "cooking", "diy", "education", "tech review"]
        },
        "expressive_narrator": {
            "name": "Expressive_Narrator",  # Emotional range
            "speed": 1.0,
            "stability": 0.75,
            "best_for": ["story", "motivation", "fiction", "drama", "reddit", "entertainment"]
        },
        "professional_female": {
            "name": "Saanvi",  # Clear, articulate
            "speed": 1.05,
            "stability": 0.82,
            "best_for": ["business", "news", "technology", "product review", "analysis"]
        },
        "casual_male": {
            "name": "Casual_Male",  # Relatable, conversational
            "speed": 1.1,
            "stability": 0.78,
            "best_for": ["gaming", "vlog", "comedy", "commentary", "reaction"]
        }
    }
    
    @classmethod
    def match_voice_to_subject(cls, subject: str, keywords: Optional[str] = None) -> Dict:
        """
        Match the best voice profile based on subject and keywords
        
        Args:
            subject: Video subject/topic
            keywords: Additional keywords for matching
            
        Returns:
            Dict with voice profile settings
        """
        text_to_analyze = f"{subject} {keywords or ''}".lower()
        
        # Score each voice profile
        scores = {}
        for profile_id, profile in cls.VOICE_PROFILES.items():
            score = 0
            for keyword in profile["best_for"]:
                if keyword in text_to_analyze:
                    score += 1
            scores[profile_id] = score
        
        # Get best match
        best_profile_id = max(scores, key=scores.get)
        best_score = scores[best_profile_id]
        
        # Default to authoritative if no match
        if best_score == 0:
            logger.warning(f"No voice match for '{subject}', using default authoritative voice")
            best_profile_id = "authoritative_male"
        
        profile = cls.VOICE_PROFILES[best_profile_id]
        logger.info(f"Matched '{subject}' to voice profile '{best_profile_id}' (score: {best_score})")
        
        return {
            "profile_id": best_profile_id,
            "voice_name": profile["name"],
            "speed": profile["speed"],
            "stability": profile["stability"]
        }
    
    @classmethod
    def get_voice_profile(cls, profile_id: str) -> Optional[Dict]:
        """Get specific voice profile by ID"""
        return cls.VOICE_PROFILES.get(profile_id)
    
    @classmethod
    def list_profiles(cls) -> Dict:
        """List all available voice profiles"""
        return cls.VOICE_PROFILES
