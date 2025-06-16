#!/usr/bin/env python3
"""
GitHub Repository Knowledge Extractor
Wraps gpt-repository-loader with agent-specific intelligence
"""

import tempfile
import subprocess
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
import gpt_repository_loader

from .base_extractor import BaseExtractor, KnowledgeChunk, ExtractionResult
from ..core.agent_profiles import AgentProfile

class GitHubExtractor(BaseExtractor):
    """Extract knowledge from GitHub repositories with agent-specific filtering"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.clone_depth = config.get('clone_depth', 1) if config else 1
        self.timeout = config.get('timeout', 300) if config else 300
    
    def validate_source(self, source: str) -> bool:
        """Validate GitHub repository URL"""
        github_patterns = [
            'github.com/',
            'https://github.com/',
            'git@github.com:'
        ]
        return any(pattern in source for pattern in github_patterns)
    
    def extract(self, source: str, agent_profile: Optional[AgentProfile] = None, **kwargs) -> ExtractionResult:
        """Extract knowledge from GitHub repository"""
        
        if not self.validate_source(source):
            raise ValueError(f"Invalid GitHub source: {source}")
        
        # Create temporary directory for cloning
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir) / "repository"
            
            try:
                # Clone repository
                print(f"📥 Cloning repository: {source}")
                self._clone_repository(source, repo_path)
                
                # Extract with gpt-repository-loader
                print(f"📝 Extracting repository content...")
                raw_content = self._extract_with_gpt_loader(repo_path, agent_profile)
                
                # Parse and filter content for agent
                print(f"🔍 Analyzing content for agent relevance...")
                chunks = self._parse_content_to_chunks(raw_content, source, agent_profile)
                
                # Calculate extraction metadata
                total_tokens = sum(chunk.size_tokens for chunk in chunks)
                
                return ExtractionResult(
                    source_id=source,
                    source_type="github_repository",
                    total_chunks=len(chunks),
                    total_tokens=total_tokens,
                    chunks=chunks,
                    extraction_metadata={
                        "repository_url": source,
                        "clone_depth": self.clone_depth,
                        "agent_profile": agent_profile.name if agent_profile else None,
                        "extraction_method": "gpt_repository_loader"
                    }
                )
                
            except Exception as e:
                print(f"❌ Extraction failed: {e}")
                return ExtractionResult(
                    source_id=source,
                    source_type="github_repository", 
                    total_chunks=0,
                    total_tokens=0,
                    chunks=[],
                    extraction_metadata={"error": str(e)}
                )
    
    def _clone_repository(self, repo_url: str, target_path: Path):
        """Clone GitHub repository"""
        cmd = [
            "git", "clone",
            repo_url,
            str(target_path),
            "--depth", str(self.clone_depth)
        ]
        
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=self.timeout
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Git clone failed: {result.stderr}")
    
    def _extract_with_gpt_loader(self, repo_path: Path, agent_profile: Optional[AgentProfile]) -> str:
        """Extract repository content using gpt-repository-loader"""
        
        # Configure ignore patterns based on agent profile
        ignore_list = gpt_repository_loader.get_ignore_list(
            str(repo_path),
            ignore_tests=True,  # Can be configured per agent
            additional_ignores=agent_profile.exclude_patterns if agent_profile else None
        )
        
        # Extract repository content
        result = gpt_repository_loader.git_repo_to_text(
            str(repo_path),
            ignore_list=ignore_list,
            list_files=True
        )
        
        # Handle tuple result (content, file_list)
        if isinstance(result, tuple):
            content = result[0]
        else:
            content = result
        
        return content
    
    def _parse_content_to_chunks(self, raw_content: str, source: str, 
                                agent_profile: Optional[AgentProfile]) -> List[KnowledgeChunk]:
        """Parse raw content into knowledge chunks with agent-specific filtering"""
        chunks = []
        
        # Split content by file separators (gpt-repository-loader format)
        file_sections = raw_content.split('----\n')
        
        for section in file_sections[1:]:  # Skip first empty section
            if not section.strip() or section.startswith('--END--'):
                continue
            
            lines = section.split('\n')
            if len(lines) < 2:
                continue
            
            file_path = lines[0].strip()
            file_content = '\n'.join(lines[1:])
            
            # Skip if file doesn't match agent's patterns
            if agent_profile and not self._matches_agent_patterns(file_path, agent_profile):
                continue
            
            # Calculate relevance score
            relevance_score = 1.0
            if agent_profile:
                relevance_score = self.calculate_relevance_score(
                    file_content, 
                    agent_profile.knowledge_filters
                )
            
            # Skip low relevance content
            if relevance_score < 0.1:
                continue
            
            # Create knowledge chunk
            chunk = KnowledgeChunk(
                content=file_content,
                source_path=file_path,
                file_type=Path(file_path).suffix,
                language=self.detect_language(file_path),
                size_tokens=self.count_tokens(file_content),
                relevance_score=relevance_score,
                metadata={
                    "source_repository": source,
                    "file_size": len(file_content),
                    "extraction_method": "gpt_repository_loader"
                }
            )
            
            chunks.append(chunk)
        
        # Sort by relevance score (highest first)
        chunks.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return chunks
    
    def _matches_agent_patterns(self, file_path: str, agent_profile: AgentProfile) -> bool:
        """Check if file matches agent's file patterns"""
        return self.filter_by_patterns(
            file_path,
            agent_profile.file_patterns,
            agent_profile.exclude_patterns
        )
    
    def extract_repository_info(self, source: str) -> Dict[str, Any]:
        """Extract basic repository information without full content"""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir) / "repository"
            
            try:
                self._clone_repository(source, repo_path)
                
                # Get repository structure
                structure_output = []
                gpt_repository_loader.print_directory_structure(
                    str(repo_path), 
                    max_depth=3
                )
                
                # Get file counts by type
                file_counts = {}
                for file_path in repo_path.rglob("*"):
                    if file_path.is_file():
                        suffix = file_path.suffix.lower()
                        file_counts[suffix] = file_counts.get(suffix, 0) + 1
                
                return {
                    "repository_url": source,
                    "file_counts": file_counts,
                    "total_files": sum(file_counts.values()),
                    "languages": list(set(
                        self.detect_language(f".{ext}") 
                        for ext in file_counts.keys() 
                        if self.detect_language(f".{ext}")
                    ))
                }
                
            except Exception as e:
                return {"error": str(e)}