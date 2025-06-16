#!/usr/bin/env python3
"""
Base Knowledge Extractor - Generic extraction interface
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class KnowledgeChunk:
    """Extracted knowledge chunk with metadata"""
    content: str
    source_path: str
    file_type: str
    language: Optional[str]
    size_tokens: int
    relevance_score: float
    metadata: Dict[str, Any]

@dataclass
class ExtractionResult:
    """Result of knowledge extraction"""
    source_id: str
    source_type: str
    total_chunks: int
    total_tokens: int
    chunks: List[KnowledgeChunk]
    extraction_metadata: Dict[str, Any]

class BaseExtractor(ABC):
    """Abstract base class for knowledge extractors"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
    
    @abstractmethod
    def extract(self, source: str, **kwargs) -> ExtractionResult:
        """Extract knowledge from source"""
        pass
    
    @abstractmethod
    def validate_source(self, source: str) -> bool:
        """Validate if source is accessible and valid"""
        pass
    
    def filter_by_patterns(self, file_path: str, 
                          include_patterns: List[str], 
                          exclude_patterns: List[str]) -> bool:
        """Filter files by include/exclude patterns"""
        import fnmatch
        
        # Check exclude patterns first
        for pattern in exclude_patterns:
            if fnmatch.fnmatch(file_path, pattern):
                return False
        
        # If no include patterns, include by default
        if not include_patterns:
            return True
        
        # Check include patterns
        for pattern in include_patterns:
            if fnmatch.fnmatch(file_path, pattern):
                return True
        
        return False
    
    def calculate_relevance_score(self, content: str, 
                                filters: Dict[str, List[str]]) -> float:
        """Calculate relevance score based on content and filters"""
        if not filters:
            return 1.0
        
        content_lower = content.lower()
        total_score = 0.0
        total_weight = len(filters)
        
        for category, keywords in filters.items():
            category_score = 0.0
            for keyword in keywords:
                if keyword.lower() in content_lower:
                    category_score += 1.0
            
            # Normalize by number of keywords in category
            if keywords:
                category_score = min(category_score / len(keywords), 1.0)
            
            total_score += category_score
        
        return total_score / total_weight if total_weight > 0 else 0.0
    
    def detect_language(self, file_path: str) -> Optional[str]:
        """Detect programming language from file extension"""
        extension_map = {
            '.py': 'python',
            '.js': 'javascript', 
            '.ts': 'typescript',
            '.jsx': 'jsx',
            '.tsx': 'tsx',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.go': 'go',
            '.rs': 'rust',
            '.php': 'php',
            '.rb': 'ruby',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.json': 'json',
            '.xml': 'xml',
            '.html': 'html',
            '.css': 'css',
            '.sql': 'sql',
            '.sh': 'bash',
            '.md': 'markdown',
            '.rst': 'rst',
            '.txt': 'text'
        }
        
        suffix = Path(file_path).suffix.lower()
        return extension_map.get(suffix)
    
    def count_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)"""
        # Simple token estimation: ~4 characters per token
        return len(text) // 4