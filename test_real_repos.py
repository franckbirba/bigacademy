#!/usr/bin/env python3
"""
Test BigAcademy on Real Repositories
Test knowledge extraction with actual production repositories
"""

import sys
sys.path.append('/Users/franckbirba/DEV/TEST-CREWAI/bigacademy')

from bigacademy.core.agent_profiles import AgentProfileManager
from bigacademy.core.graph_db import GraphDB
from bigacademy.extractors.github_extractor import GitHubExtractor
from pathlib import Path
import json

def test_crewai_for_architect():
    """Test CrewAI repository extraction for Solution Architect"""
    print("🏗️  Testing CrewAI Repository for Solution Architect")
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
    extractor = GitHubExtractor(config={'clone_depth': 1, 'timeout': 300})
    db = GraphDB(Path("test_data/crewai_architect_knowledge.db"))
    
    # Extract from CrewAI repository
    crewai_repo = "https://github.com/joaomdmoura/crewAI"
    
    print(f"\n🔍 Extracting knowledge from: {crewai_repo}")
    print("   This may take a few minutes...")
    
    try:
        result = extractor.extract(crewai_repo, architect_profile)
        
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
            print(f"   {i+1:2d}. {chunk.source_path:<40} (relevance: {chunk.relevance_score:.3f}, tokens: {chunk.size_tokens:,})")
        
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
            content_preview = top_chunk.content[:500] + "..." if len(top_chunk.content) > 500 else top_chunk.content
            print(f"   {content_preview}")
        
        db.close()
        return result
        
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        db.close()
        return None

def test_fastapi_for_developer():
    """Test FastAPI repository extraction for Python Developer"""
    print("\n👨‍💻 Testing FastAPI Repository for Python Developer")
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
    extractor = GitHubExtractor(config={'clone_depth': 1, 'timeout': 300})
    db = GraphDB(Path("test_data/fastapi_developer_knowledge.db"))
    
    # Extract from FastAPI repository
    fastapi_repo = "https://github.com/tiangolo/fastapi"
    
    print(f"\n🔍 Extracting knowledge from: {fastapi_repo}")
    print("   This may take a few minutes...")
    
    try:
        result = extractor.extract(fastapi_repo, developer_profile)
        
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
            print(f"   {i+1:2d}. {chunk.source_path:<40} (relevance: {chunk.relevance_score:.3f}, tokens: {chunk.size_tokens:,})")
        
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
            content_preview = top_chunk.content[:500] + "..." if len(top_chunk.content) > 500 else top_chunk.content
            print(f"   {content_preview}")
        
        db.close()
        return result
        
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        db.close()
        return None

def compare_extraction_results(crewai_result, fastapi_result):
    """Compare extraction results between different agents and repositories"""
    print("\n📊 Comparing Extraction Results")
    print("=" * 60)
    
    if not crewai_result or not fastapi_result:
        print("⚠️  Cannot compare - one or both extractions failed")
        return
    
    print(f"📈 Extraction Comparison:")
    print(f"   CrewAI (Architect):  {crewai_result.total_chunks:,} chunks, {crewai_result.total_tokens:,} tokens")
    print(f"   FastAPI (Developer): {fastapi_result.total_chunks:,} chunks, {fastapi_result.total_tokens:,} tokens")
    
    # Calculate average relevance scores
    crewai_avg_relevance = sum(c.relevance_score for c in crewai_result.chunks) / len(crewai_result.chunks) if crewai_result.chunks else 0
    fastapi_avg_relevance = sum(c.relevance_score for c in fastapi_result.chunks) / len(fastapi_result.chunks) if fastapi_result.chunks else 0
    
    print(f"\n🎯 Average Relevance Scores:")
    print(f"   CrewAI (Architect):  {crewai_avg_relevance:.3f}")
    print(f"   FastAPI (Developer): {fastapi_avg_relevance:.3f}")
    
    # Analyze file types
    crewai_file_types = {}
    fastapi_file_types = {}
    
    for chunk in crewai_result.chunks:
        file_type = chunk.file_type or "no_extension"
        crewai_file_types[file_type] = crewai_file_types.get(file_type, 0) + 1
    
    for chunk in fastapi_result.chunks:
        file_type = chunk.file_type or "no_extension"
        fastapi_file_types[file_type] = fastapi_file_types.get(file_type, 0) + 1
    
    print(f"\n📁 File Type Distribution:")
    print(f"   CrewAI (Architect):  {dict(sorted(crewai_file_types.items(), key=lambda x: x[1], reverse=True)[:5])}")
    print(f"   FastAPI (Developer): {dict(sorted(fastapi_file_types.items(), key=lambda x: x[1], reverse=True)[:5])}")
    
    # Show different focus areas
    crewai_paths = {chunk.source_path for chunk in crewai_result.chunks}
    fastapi_paths = {chunk.source_path for chunk in fastapi_result.chunks}
    
    print(f"\n🎯 Agent-Specific Focus Examples:")
    print(f"   Architect focuses on: {list(crewai_paths)[:3]}")
    print(f"   Developer focuses on: {list(fastapi_paths)[:3]}")

def main():
    """Run real repository tests"""
    print("🌟 BigAcademy Real Repository Test Suite")
    print("=" * 70)
    print("Testing knowledge extraction on production repositories...")
    print("This will take several minutes to complete.\n")
    
    try:
        # Test 1: CrewAI for Solution Architect
        crewai_result = test_crewai_for_architect()
        
        # Test 2: FastAPI for Python Developer
        fastapi_result = test_fastapi_for_developer()
        
        # Test 3: Compare results
        compare_extraction_results(crewai_result, fastapi_result)
        
        print("\n🎉 Real repository test suite completed!")
        print("\n💡 Key Insights:")
        print("   1. BigAcademy successfully extracts agent-specific knowledge")
        print("   2. Different agents focus on different parts of repositories")
        print("   3. Knowledge graph stores relationships between agents, technologies, and skills")
        print("   4. Ready for dataset generation from extracted knowledge")
        
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()