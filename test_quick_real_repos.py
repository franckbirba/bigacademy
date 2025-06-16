#!/usr/bin/env python3
"""
Quick Test BigAcademy on Real Repositories
Test knowledge extraction with smaller production repositories
"""

import sys
sys.path.append('/Users/franckbirba/DEV/TEST-CREWAI/bigacademy')

from bigacademy.core.agent_profiles import AgentProfileManager
from bigacademy.core.graph_db import GraphDB
from bigacademy.extractors.github_extractor import GitHubExtractor
from pathlib import Path
import json

def test_smaller_repo_for_architect():
    """Test smaller repository extraction for Solution Architect"""
    print("🏗️  Testing Smaller Repository for Solution Architect")
    print("=" * 60)
    
    # Load Solution Architect profile
    manager = AgentProfileManager(Path("/Users/franckbirba/DEV/TEST-CREWAI/bigacademy/configs/agents"))
    architect_profile = manager.get_profile("solution_architect")
    
    if not architect_profile:
        print("❌ Could not load Solution Architect profile")
        return None
    
    print(f"🤖 Agent: {architect_profile.name}")
    print(f"   Technologies: {', '.join(architect_profile.technologies[:8])}")
    print(f"   Focus Areas: {', '.join(architect_profile.focus_areas[:5])}")
    
    # Initialize extractor and database
    extractor = GitHubExtractor(config={'clone_depth': 1, 'timeout': 180})
    db = GraphDB(Path("test_data/fastapi_minimal_architect.db"))
    
    # Test with FastAPI-users (smaller, focused repo)
    test_repo = "https://github.com/fastapi-users/fastapi-users"
    
    print(f"\n🔍 Extracting knowledge from: {test_repo}")
    print("   This should take 1-2 minutes...")
    
    try:
        result = extractor.extract(test_repo, architect_profile)
        
        print(f"\n✅ Extraction completed!")
        print(f"   Total chunks: {result.total_chunks}")
        print(f"   Total tokens: {result.total_tokens:,}")
        
        if result.total_chunks == 0:
            print("⚠️  No relevant chunks found for this agent")
            return None
        
        # Store in graph database
        session_id = db.store_extraction_result(result, architect_profile)
        print(f"   Session ID: {session_id[:8]}")
        
        # Show top relevant files
        print(f"\n📊 Top 10 Most Relevant Files:")
        for i, chunk in enumerate(result.chunks[:10]):
            print(f"   {i+1:2d}. {chunk.source_path:<50} (relevance: {chunk.relevance_score:.3f}, tokens: {chunk.size_tokens:,})")
        
        # Show knowledge statistics
        stats = db.get_knowledge_statistics(architect_profile.name)
        print(f"\n📈 Knowledge Graph Statistics:")
        print(f"   Node counts: {stats['node_counts']}")
        print(f"   Relationship counts: {stats['relationship_counts']}")
        print(f"   Total knowledge: {stats.get('agent_knowledge', {})}")
        
        # Show sample content from top chunk
        if result.chunks:
            top_chunk = result.chunks[0]
            print(f"\n📝 Sample from top file ({top_chunk.source_path}):")
            content_preview = top_chunk.content[:300] + "..." if len(top_chunk.content) > 300 else top_chunk.content
            print(f"   {content_preview}")
        
        # Analyze technologies found
        found_technologies = []
        for chunk in result.chunks[:5]:  # Check top 5 chunks
            for tech in architect_profile.technologies:
                if tech.lower() in chunk.content.lower():
                    found_technologies.append(tech)
        
        print(f"\n🔧 Technologies found in content: {list(set(found_technologies))}")
        
        db.close()
        return result
        
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        db.close()
        return None

def test_python_project_for_developer():
    """Test Python project for Developer"""
    print("\n👨‍💻 Testing Python Project for Developer")
    print("=" * 60)
    
    # Load Python Developer profile
    manager = AgentProfileManager(Path("/Users/franckbirba/DEV/TEST-CREWAI/bigacademy/configs/agents"))
    developer_profile = manager.get_profile("python_developer")
    
    if not developer_profile:
        print("❌ Could not load Python Developer profile")
        return None
    
    print(f"🤖 Agent: {developer_profile.name}")
    print(f"   Technologies: {', '.join(developer_profile.technologies[:8])}")
    print(f"   Focus Areas: {', '.join(developer_profile.focus_areas[:5])}")
    
    # Initialize extractor and database
    extractor = GitHubExtractor(config={'clone_depth': 1, 'timeout': 180})
    db = GraphDB(Path("test_data/pydantic_developer.db"))
    
    # Test with Pydantic core (smaller but relevant)
    test_repo = "https://github.com/pydantic/pydantic-core"
    
    print(f"\n🔍 Extracting knowledge from: {test_repo}")
    print("   This should take 1-2 minutes...")
    
    try:
        result = extractor.extract(test_repo, developer_profile)
        
        print(f"\n✅ Extraction completed!")
        print(f"   Total chunks: {result.total_chunks}")
        print(f"   Total tokens: {result.total_tokens:,}")
        
        if result.total_chunks == 0:
            print("⚠️  No relevant chunks found for this agent")
            return None
        
        # Store in graph database
        session_id = db.store_extraction_result(result, developer_profile)
        print(f"   Session ID: {session_id[:8]}")
        
        # Show top relevant files
        print(f"\n📊 Top 10 Most Relevant Files:")
        for i, chunk in enumerate(result.chunks[:10]):
            print(f"   {i+1:2d}. {chunk.source_path:<50} (relevance: {chunk.relevance_score:.3f}, tokens: {chunk.size_tokens:,})")
        
        # Show knowledge statistics
        stats = db.get_knowledge_statistics(developer_profile.name)
        print(f"\n📈 Knowledge Graph Statistics:")
        print(f"   Node counts: {stats['node_counts']}")
        print(f"   Relationship counts: {stats['relationship_counts']}")
        print(f"   Total knowledge: {stats.get('agent_knowledge', {})}")
        
        # Show sample content from top chunk
        if result.chunks:
            top_chunk = result.chunks[0]
            print(f"\n📝 Sample from top file ({top_chunk.source_path}):")
            content_preview = top_chunk.content[:300] + "..." if len(top_chunk.content) > 300 else top_chunk.content
            print(f"   {content_preview}")
        
        # Analyze file types found
        file_types = {}
        for chunk in result.chunks:
            file_type = chunk.file_type or "no_extension"
            file_types[file_type] = file_types.get(file_type, 0) + 1
        
        print(f"\n📁 File types extracted: {dict(sorted(file_types.items(), key=lambda x: x[1], reverse=True))}")
        
        db.close()
        return result
        
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        db.close()
        return None

def main():
    """Run quick real repository tests"""
    print("⚡ BigAcademy Quick Real Repository Test")
    print("=" * 60)
    print("Testing with smaller, focused repositories for faster results...\n")
    
    try:
        # Test 1: FastAPI-users for Solution Architect
        architect_result = test_smaller_repo_for_architect()
        
        # Test 2: Pydantic-core for Python Developer  
        developer_result = test_python_project_for_developer()
        
        print("\n🎉 Quick test completed!")
        print("\n💡 Key Findings:")
        
        if architect_result:
            print(f"   ✅ Architect extracted {architect_result.total_chunks} chunks from FastAPI-users")
            avg_relevance = sum(c.relevance_score for c in architect_result.chunks) / len(architect_result.chunks)
            print(f"      Average relevance: {avg_relevance:.3f}")
        
        if developer_result:
            print(f"   ✅ Developer extracted {developer_result.total_chunks} chunks from Pydantic-core")
            avg_relevance = sum(c.relevance_score for c in developer_result.chunks) / len(developer_result.chunks)
            print(f"      Average relevance: {avg_relevance:.3f}")
        
        print("\n🚀 BigAcademy is successfully extracting agent-specific knowledge!")
        print("   Ready to scale to larger repositories and build datasets.")
        
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()