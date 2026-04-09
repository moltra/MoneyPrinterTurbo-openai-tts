import os
import json
import time
import hashlib
from typing import List, Dict, Optional, Tuple
from loguru import logger
from sentence_transformers import SentenceTransformer, util
import numpy as np

from app.models.schema import MaterialInfo, VideoAspect
from app.models.video_constants import SemanticConstants, VideoConstants
from app.services import material
from app.config import config
from app.utils import utils


class ClipRelevanceScorer:
    """Semantic clip relevance scoring using sentence-transformers."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
        self._cache_dir = os.path.join(utils.storage_dir("cache"), "clip_relevance")
        os.makedirs(self._cache_dir, exist_ok=True)
        self._cache_ttl = VideoConstants.CACHE_TTL_DAYS * 24 * 3600

    @property
    def model(self):
        """Lazy load the sentence transformer model."""
        if self._model is None:
            logger.info(f"Loading semantic model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
            logger.success(f"Model loaded: {self.model_name}")
        return self._model

    def _get_cache_key(self, sentence: str, main_keyword: str, provider: str, aspect: str) -> str:
        """Generate cache key from search parameters."""
        key_str = f"{sentence}|{main_keyword}|{provider}|{aspect}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def _load_cache(self, cache_key: str) -> Optional[Dict]:
        """Load cached results if available and not expired."""
        cache_file = os.path.join(self._cache_dir, f"{cache_key}.json")
        if not os.path.exists(cache_file):
            return None

        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cached = json.load(f)
            
            if time.time() - cached.get("timestamp", 0) > self._cache_ttl:
                os.remove(cache_file)
                return None
            
            return cached
        except Exception as e:
            logger.warning(f"Failed to load cache {cache_key}: {str(e)}")
            return None

    def _save_cache(self, cache_key: str, data: Dict):
        """Save results to cache."""
        cache_file = os.path.join(self._cache_dir, f"{cache_key}.json")
        try:
            data["timestamp"] = time.time()
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save cache {cache_key}: {str(e)}")

    def _generate_search_queries(self, main_keyword: str, sentence: str) -> List[str]:
        """Generate multiple search queries combining keyword and sentence."""
        queries = []
        
        # Query 1: Main keyword only (original behavior)
        if main_keyword:
            queries.append(main_keyword.strip())
        
        # Query 2: First N words of sentence (visual concepts)
        words = sentence.split()[:6]  # Extract key visual concepts
        if words:
            queries.append(" ".join(words))
        
        # Query 3: Combined if both exist and different
        if main_keyword and sentence and main_keyword.lower() not in sentence.lower():
            combined = f"{main_keyword} {' '.join(sentence.split()[:4])}"
            queries.append(combined[:60])  # Limit query length
        
        # Deduplicate while preserving order
        seen = set()
        unique_queries = []
        for q in queries:
            q_lower = q.lower().strip()
            if q_lower and q_lower not in seen:
                seen.add(q_lower)
                unique_queries.append(q)
        
        return unique_queries[:SemanticConstants.DEFAULT_QUERIES_PER_SENTENCE]

    def _fetch_candidates(
        self,
        queries: List[str],
        sources: List[str],
        video_aspect: VideoAspect,
        minimum_duration: int,
    ) -> List[MaterialInfo]:
        """Fetch candidates from multiple sources and queries."""
        all_candidates = []
        seen_urls = set()

        for source in sources:
            search_func = material.search_videos_pexels if source == "pexels" else material.search_videos_pixabay
            
            for query in queries:
                try:
                    items = search_func(
                        search_term=query,
                        minimum_duration=minimum_duration,
                        video_aspect=video_aspect,
                    )
                    
                    for item in items[:10]:  # Top 10 per query
                        if item.url and item.url not in seen_urls:
                            seen_urls.add(item.url)
                            all_candidates.append(item)
                            
                except Exception as e:
                    logger.warning(f"Search failed for '{query}' on {source}: {str(e)}")
                    continue

        return all_candidates

    def _extract_clip_text(self, item: MaterialInfo) -> str:
        """Extract searchable text from clip metadata (provider-specific)."""
        # Combine tags and URL-based text
        parts = []
        
        # Tags from API (most important)
        if item.tags:
            parts.append(item.tags.strip())
        
        # Extract text from URL filename
        url_text = item.url.split("/")[-1].replace("-", " ").replace("_", " ")
        if url_text:
            parts.append(url_text)
        
        return " ".join(parts)

    def _score_clip(
        self,
        sentence: str,
        main_keyword: str,
        item: MaterialInfo,
        sentence_embedding: np.ndarray,
    ) -> float:
        """Score a single clip for relevance."""
        # Extract clip metadata text
        clip_text = self._extract_clip_text(item)
        logger.debug(f"[SEMANTIC] Scoring clip: provider={item.provider} tags='{item.tags[:40]}' extracted_text='{clip_text[:60]}...'")
        
        # Semantic similarity (main signal)
        clip_embedding = self.model.encode(clip_text, convert_to_numpy=True)
        semantic_score = float(util.cos_sim(sentence_embedding, clip_embedding)[0][0])
        
        # Keyword match bonus
        keyword_score = 0.0
        if main_keyword:
            main_lower = main_keyword.lower()
            clip_lower = clip_text.lower()
            if main_lower in clip_lower:
                keyword_score = 0.5
            else:
                # Partial word match
                main_words = set(main_lower.split())
                clip_words = set(clip_lower.split())
                overlap = len(main_words & clip_words)
                if overlap > 0:
                    keyword_score = 0.3 * (overlap / len(main_words))
        
        # Duration bonus (prefer clips closer to required duration)
        duration_score = 0.0
        if item.duration:
            # Normalize to 0-1, prefer 5-15 second clips
            if 5 <= item.duration <= 15:
                duration_score = 0.2
            elif item.duration < 5:
                duration_score = 0.1
        
        # Weighted combination
        total_score = (
            0.6 * semantic_score +
            0.3 * keyword_score +
            0.1 * duration_score
        )
        
        return total_score

    def select_relevant_clip(
        self,
        main_keyword: str,
        subtitle_sentence: str,
        required_duration: float,
        video_aspect: VideoAspect = VideoAspect.portrait,
        sources: Optional[List[str]] = None,
    ) -> Dict:
        """
        Select the most relevant clip for a subtitle sentence.
        
        Args:
            main_keyword: Main video topic/keyword
            subtitle_sentence: Exact subtitle text to match
            required_duration: Minimum clip duration in seconds
            video_aspect: Video aspect ratio
            sources: List of sources to search (default: ["pexels", "pixabay"])
        
        Returns:
            Dict with:
                - picked_url: Selected video URL
                - picked_thumbnail: Thumbnail URL
                - picked_provider: Source provider
                - picked_duration: Clip duration
                - relevance_score: Score (0-1)
                - candidates: Top 3 candidates with scores
                - search_queries: Queries used
                - cached: Whether result was cached
        """
        if sources is None:
            sources = ["pexels", "pixabay"]
        
        minimum_duration = int(required_duration)
        aspect_str = str(video_aspect.value)
        
        # Check cache
        cache_key = self._get_cache_key(subtitle_sentence, main_keyword, "|".join(sources), aspect_str)
        cached_result = self._load_cache(cache_key)
        if cached_result:
            logger.info(f"Using cached clip selection for: {subtitle_sentence[:50]}...")
            cached_result["cached"] = True
            return cached_result
        
        # Generate search queries
        queries = self._generate_search_queries(main_keyword, subtitle_sentence)
        logger.info(f"[SEMANTIC] ========================================")
        logger.info(f"[SEMANTIC] Sentence: '{subtitle_sentence[:80]}...'")
        logger.info(f"[SEMANTIC] Main keyword: '{main_keyword}'")
        logger.info(f"[SEMANTIC] Generated {len(queries)} search queries: {queries}")
        
        # Fetch candidates from all sources
        logger.info(f"[SEMANTIC] Fetching candidates from sources: {sources}")
        candidates = self._fetch_candidates(queries, sources, video_aspect, minimum_duration)
        logger.info(f"[SEMANTIC] Fetched {len(candidates)} unique candidates total")
        
        if not candidates:
            return {
                "picked_url": "",
                "picked_thumbnail": "",
                "picked_provider": "",
                "picked_duration": 0,
                "relevance_score": 0.0,
                "candidates": [],
                "search_queries": queries,
                "cached": False,
            }
        
        # Encode sentence once
        sentence_embedding = self.model.encode(subtitle_sentence, convert_to_numpy=True)
        
        # Score all candidates
        scored_candidates = []
        for item in candidates:
            score = self._score_clip(subtitle_sentence, main_keyword, item, sentence_embedding)
            scored_candidates.append({
                "url": item.url,
                "thumbnail": item.thumbnail,
                "provider": item.provider,
                "duration": item.duration,
                "score": score,
            })
        
        # Sort by score descending
        scored_candidates.sort(key=lambda x: x["score"], reverse=True)
        
        # Pick top candidate
        top = scored_candidates[0]
        top_n = min(3, len(scored_candidates))
        logger.info(f"[SEMANTIC] Top {top_n} candidates:")
        for i, cand in enumerate(scored_candidates[:top_n]):
            logger.info(f"[SEMANTIC]   {i+1}. score={cand['score']:.3f} duration={cand['duration']}s provider={cand['provider']}")
            logger.info(f"[SEMANTIC]      url={cand['url'][:80]}...")
        logger.info(f"[SEMANTIC] PICKED: score={top['score']:.3f} url={top['url']}")
        
        result = {
            "picked_url": top["url"],
            "picked_thumbnail": top["thumbnail"],
            "picked_provider": top["provider"],
            "picked_duration": top["duration"],
            "relevance_score": top["score"],
            "candidates": scored_candidates[:top_n],  # Top N for logging
            "search_queries": queries,
            "cached": False,
        }
        
        # Save to cache
        self._save_cache(cache_key, result)
        
        return result


# Global scorer instance
_scorer = None

def get_scorer() -> ClipRelevanceScorer:
    """Get or create global scorer instance."""
    global _scorer
    if _scorer is None:
        _scorer = ClipRelevanceScorer()
    return _scorer


def select_relevant_clip(
    main_keyword: str,
    subtitle_sentence: str,
    required_duration: float,
    video_aspect: VideoAspect = VideoAspect.portrait,
    sources: Optional[List[str]] = None,
) -> Dict:
    """Convenience function to select relevant clip."""
    scorer = get_scorer()
    return scorer.select_relevant_clip(
        main_keyword=main_keyword,
        subtitle_sentence=subtitle_sentence,
        required_duration=required_duration,
        video_aspect=video_aspect,
        sources=sources,
    )
