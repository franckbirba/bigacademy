#!/usr/bin/env python3
"""
Test BigAcademy GitHub Extractor with Agent Profiles
"""

import sys
sys.path.append('/Users/franckbirba/DEV/TEST-CREWAI/bigacademy')

from bigacademy.core.agent_profiles import AgentProfileManager
from bigacademy.extractors.github_extractor import GitHubExtractor
from pathlib import Path
import json

def test_agent_profiles():
    """Test loading agent profiles from config"""
    print("🎓 Testing Agent Profile Loading")
    print("=" * 50)
    
    # Initialize profile manager
    profiles_dir = Path("/Users/franckbirba/DEV/TEST-CREWAI/bigacademy/configs/agents")
    manager = AgentProfileManager(profiles_dir)
    
    # Load all profiles
    profiles = manager.load_all_profiles()
    
    print(f"📋 Loaded {len(profiles)} agent profiles:")
    for name, profile in profiles.items():
        print(f"\n🤖 Agent: {profile.name}")
        print(f"   Role: {profile.role.title}")
        print(f"   Technologies: {', '.join(profile.technologies[:5])}...")
        print(f"   Focus Areas: {', '.join(profile.focus_areas[:3])}...")
        print(f"   File Patterns: {len(profile.file_patterns)} patterns")
        print(f"   Knowledge Filters: {len(profile.knowledge_filters)} categories")
        
        # Show identity prompt
        print(f"   Identity: {profile.role.identity_prompt[:100]}...")
    
    return profiles

def test_github_extractor_basic():
    """Test basic GitHub extractor functionality"""
    print("\n🔧 Testing GitHub Extractor Basic Functions")
    print("=" * 50)
    
    extractor = GitHubExtractor()
    
    # Test URL validation
    test_urls = [
        "https://github.com/joaomdmoura/crewAI",
        "https://github.com/tiangolo/fastapi", 
        "invalid-url",
        "https://gitlab.com/some/repo"
    ]
    
    print("🔍 Testing URL validation:")
    for url in test_urls:
        valid = extractor.validate_source(url)
        status = "✅" if valid else "❌"
        print(f"   {status} {url}")
    
    return extractor

def test_repo_info_extraction():
    """Test repository info extraction (lightweight)"""
    print("\n📊 Testing Repository Info Extraction")
    print("=" * 50)
    
    extractor = GitHubExtractor(config={'clone_depth': 1, 'timeout': 60})
    
    # Test with a smaller repository first
    test_repo = "https://github.com/psf/requests"  # Well-known, smaller repo
    
    print(f"🔍 Extracting info from: {test_repo}")
    try:
        repo_info = extractor.extract_repository_info(test_repo)
        
        if "error" in repo_info:
            print(f"❌ Error: {repo_info['error']}")
            return None
        
        print(f"✅ Repository analyzed successfully!")
        print(f"   Total files: {repo_info.get('total_files', 'unknown')}")
        print(f"   Languages: {', '.join(repo_info.get('languages', []))}")
        print(f"   File types: {dict(list(repo_info.get('file_counts', {}).items())[:5])}")
        
        return repo_info
        
    except Exception as e:
        print(f"❌ Repository info extraction failed: {e}")
        return None

def test_agent_specific_extraction():
    """Test agent-specific knowledge extraction"""
    print("\n🧠 Testing Agent-Specific Knowledge Extraction")
    print("=" * 50)
    
    # Load agent profiles
    manager = AgentProfileManager(Path("/Users/franckbirba/DEV/TEST-CREWAI/bigacademy/configs/agents"))
    architect_profile = manager.get_profile("solution_architect")
    developer_profile = manager.get_profile("python_developer")
    
    if not architect_profile or not developer_profile:
        print("❌ Could not load agent profiles")
        return
    
    # Initialize extractor
    extractor = GitHubExtractor(config={'clone_depth': 1, 'timeout': 120})
    
    # Test with BigTune repository (local, faster)
    test_repo = "https://github.com/franckbirba/bigtune"
    
    print(f"🔍 Testing with repository: {test_repo}")
    
    # Test architect extraction
    print(f"\n🏗️  Extracting for Solution Architect...")
    try:
        architect_result = extractor.extract(test_repo, architect_profile)
        
        print(f"✅ Architect extraction completed!")
        print(f"   Total chunks: {architect_result.total_chunks}")
        print(f"   Total tokens: {architect_result.total_tokens}")
        print(f"   Average relevance: {sum(c.relevance_score for c in architect_result.chunks) / len(architect_result.chunks) if architect_result.chunks else 0:.2f}")
        
        # Show top relevant chunks
        print(f"   Top relevant files:")
        for chunk in architect_result.chunks[:5]:
            print(f"     - {chunk.source_path} (relevance: {chunk.relevance_score:.2f})")
            
    except Exception as e:
        print(f"❌ Architect extraction failed: {e}")
        architect_result = None
    
    # Test developer extraction  
    print(f"\n👨‍💻 Extracting for Python Developer...")
    try:
        developer_result = extractor.extract(test_repo, developer_profile)
        
        print(f"✅ Developer extraction completed!")
        print(f"   Total chunks: {developer_result.total_chunks}")
        print(f"   Total tokens: {developer_result.total_tokens}")
        print(f"   Average relevance: {sum(c.relevance_score for c in developer_result.chunks) / len(developer_result.chunks) if developer_result.chunks else 0:.2f}")
        
        # Show top relevant chunks
        print(f"   Top relevant files:")
        for chunk in developer_result.chunks[:5]:
            print(f"     - {chunk.source_path} (relevance: {chunk.relevance_score:.2f})")
            
    except Exception as e:
        print(f"❌ Developer extraction failed: {e}")
        developer_result = None
    
    # Compare results
    if architect_result and developer_result:
        print(f"\n📊 Comparison:")
        print(f"   Architect chunks: {architect_result.total_chunks}")
        print(f"   Developer chunks: {developer_result.total_chunks}")
        
        # Find different focuses
        arch_files = {c.source_path for c in architect_result.chunks}
        dev_files = {c.source_path for c in developer_result.chunks}
        
        arch_only = arch_files - dev_files
        dev_only = dev_files - arch_files
        
        print(f"   Architect-only files: {len(arch_only)}")
        if arch_only:
            for file in list(arch_only)[:3]:
                print(f"     - {file}")
        
        print(f"   Developer-only files: {len(dev_only)}")
        if dev_only:
            for file in list(dev_only)[:3]:
                print(f"     - {file}")

def main():
    """Run all tests"""
    print("🎓 BigAcademy GitHub Extractor Test Suite")
    print("=" * 60)
    
    try:
        # Test 1: Agent profiles
        profiles = test_agent_profiles()
        if not profiles:
            print("❌ Agent profile test failed")
            return
        
        # Test 2: Basic extractor
        extractor = test_github_extractor_basic()
        if not extractor:
            print("❌ Basic extractor test failed")
            return
        
        # Test 3: Repository info (lightweight)
        repo_info = test_repo_info_extraction()
        # Continue even if this fails
        
        # Test 4: Agent-specific extraction (main test)
        test_agent_specific_extraction()
        
        print("\n🎉 Test suite completed!")
        print("\n💡 Next steps:")
        print("   1. GitHub extractor is working with agent profiles")
        print("   2. Ready to build knowledge graph storage")
        print("   3. Ready to build dataset generation")
        
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()