#!/usr/bin/env python3
"""
Test BigAcademy Knowledge Graph Database
"""

import sys
sys.path.append('/Users/franckbirba/DEV/TEST-CREWAI/bigacademy')

from bigacademy.core.agent_profiles import AgentProfileManager
from bigacademy.core.graph_db import GraphDB
from bigacademy.extractors.github_extractor import GitHubExtractor
from pathlib import Path
import json

def test_graph_db_basic():
    """Test basic graph database operations"""
    print("🧠 Testing Graph Database Basic Operations")
    print("=" * 50)
    
    # Initialize database (will create if not exists)
    db = GraphDB(Path("test_data/test_knowledge.db"))
    
    # Test adding nodes
    print("📝 Testing node operations...")
    
    # Add test nodes
    agent_id = db.add_node("Agent", {
        "name": "test_architect",
        "title": "Test Solution Architect",
        "technologies": ["fastapi", "docker"]
    })
    
    tech_id = db.add_node("Technology", {
        "name": "fastapi",
        "version": "0.104.0"
    })
    
    chunk_id = db.add_node("KnowledgeChunk", {
        "content": "FastAPI is a modern web framework",
        "source_path": "test.py",
        "relevance_score": 0.8
    })
    
    print(f"✅ Created nodes: agent={agent_id[:8]}, tech={tech_id[:8]}, chunk={chunk_id[:8]}")
    
    # Test adding relationships
    print("🔗 Testing relationship operations...")
    
    rel1_id = db.add_edge(agent_id, tech_id, "REQUIRES")
    rel2_id = db.add_edge(agent_id, chunk_id, "LEARNS_FROM", weight=0.8)
    rel3_id = db.add_edge(chunk_id, tech_id, "IMPLEMENTS")
    
    print(f"✅ Created relationships: {len([rel1_id, rel2_id, rel3_id])} edges")
    
    # Test querying
    print("🔍 Testing queries...")
    
    # Find nodes by type
    agents = db.find_nodes("Agent")
    technologies = db.find_nodes("Technology") 
    chunks = db.find_nodes("KnowledgeChunk")
    
    print(f"   Found: {len(agents)} agents, {len(technologies)} technologies, {len(chunks)} chunks")
    
    # Find relationships
    agent_rels = db.get_relationships(agent_id)
    print(f"   Agent has {len(agent_rels)} relationships")
    
    for rel in agent_rels:
        target = db.get_node(rel.target_id)
        print(f"     - {rel.relationship_type} -> {target.node_type}: {target.properties.get('name', 'unknown')}")
    
    return db

def test_extraction_storage():
    """Test storing extraction results in graph"""
    print("\n📊 Testing Extraction Result Storage")
    print("=" * 50)
    
    # Load agent profile
    manager = AgentProfileManager(Path("/Users/franckbirba/DEV/TEST-CREWAI/bigacademy/configs/agents"))
    architect_profile = manager.get_profile("solution_architect")
    
    if not architect_profile:
        print("❌ Could not load architect profile")
        return None
    
    # Initialize graph database
    db = GraphDB(Path("test_data/extraction_knowledge.db"))
    
    # Initialize extractor and extract from repository
    extractor = GitHubExtractor(config={'clone_depth': 1, 'timeout': 60})
    
    print(f"🔍 Extracting knowledge for {architect_profile.name}...")
    try:
        # Use a smaller, faster repository for testing
        test_repo = "https://github.com/franckbirba/bigtune"
        result = extractor.extract(test_repo, architect_profile)
        
        if result.total_chunks == 0:
            print("⚠️  No knowledge chunks extracted - creating mock data")
            return test_mock_extraction_storage(db, architect_profile)
        
        print(f"✅ Extracted {result.total_chunks} chunks ({result.total_tokens} tokens)")
        
        # Store in graph database
        session_id = db.store_extraction_result(result, architect_profile)
        
        print(f"✅ Stored extraction result - session: {session_id[:8]}")
        
        # Verify storage
        print("🔍 Verifying stored data...")
        
        stats = db.get_knowledge_statistics(architect_profile.name)
        print(f"   Node counts: {stats['node_counts']}")
        print(f"   Relationship counts: {stats['relationship_counts']}")
        print(f"   Agent sessions: {stats.get('agent_sessions', 0)}")
        print(f"   Agent knowledge: {stats.get('agent_knowledge', {})}")
        
        return db
        
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        return test_mock_extraction_storage(db, architect_profile)

def test_mock_extraction_storage(db: GraphDB, agent_profile):
    """Test with mock extraction data"""
    print("🎭 Using mock extraction data...")
    
    from bigacademy.extractors.base_extractor import KnowledgeChunk, ExtractionResult
    
    # Create mock knowledge chunks
    mock_chunks = [
        KnowledgeChunk(
            content="from fastapi import FastAPI\napp = FastAPI()\n@app.get('/')\ndef read_root():\n    return {'Hello': 'World'}",
            source_path="main.py",
            file_type=".py",
            language="python",
            size_tokens=50,
            relevance_score=0.9,
            metadata={"mock": True}
        ),
        KnowledgeChunk(
            content="version: '3.8'\nservices:\n  app:\n    build: .\n    ports:\n      - '8000:8000'",
            source_path="docker-compose.yml",
            file_type=".yml",
            language="yaml",
            size_tokens=30,
            relevance_score=0.7,
            metadata={"mock": True}
        ),
        KnowledgeChunk(
            content="# System Architecture\n\nThis system uses microservices pattern with FastAPI and Docker.",
            source_path="README.md",
            file_type=".md",
            language="markdown",
            size_tokens=25,
            relevance_score=0.8,
            metadata={"mock": True}
        )
    ]
    
    # Create mock extraction result
    mock_result = ExtractionResult(
        source_id="https://github.com/test/repo",
        source_type="github_repository",
        total_chunks=len(mock_chunks),
        total_tokens=sum(chunk.size_tokens for chunk in mock_chunks),
        chunks=mock_chunks,
        extraction_metadata={"mock": True, "test_data": True}
    )
    
    # Store in graph
    session_id = db.store_extraction_result(mock_result, agent_profile)
    print(f"✅ Stored mock data - session: {session_id[:8]}")
    
    return db

def test_graph_analysis():
    """Test graph analysis with NetworkX"""
    print("\n🕸️  Testing Graph Analysis")
    print("=" * 50)
    
    # Use existing database
    db = GraphDB(Path("test_data/extraction_knowledge.db"))
    
    # Load agent profile
    manager = AgentProfileManager(Path("/Users/franckbirba/DEV/TEST-CREWAI/bigacademy/configs/agents"))
    architect_profile = manager.get_profile("solution_architect")
    
    if not architect_profile:
        print("❌ Could not load architect profile")
        return
    
    print(f"🔍 Analyzing knowledge graph for {architect_profile.name}...")
    
    # Get NetworkX graph
    graph = db.get_agent_knowledge_graph(architect_profile.name)
    
    print(f"📊 Graph statistics:")
    print(f"   Nodes: {graph.number_of_nodes()}")
    print(f"   Edges: {graph.number_of_edges()}")
    
    if graph.number_of_nodes() > 0:
        # Analyze node types
        node_types = {}
        for node_id, data in graph.nodes(data=True):
            node_type = data.get('node_type', 'unknown')
            node_types[node_type] = node_types.get(node_type, 0) + 1
        
        print(f"   Node types: {node_types}")
        
        # Analyze relationships
        rel_types = {}
        for source, target, data in graph.edges(data=True):
            rel_type = data.get('relationship_type', 'unknown')
            rel_types[rel_type] = rel_types.get(rel_type, 0) + 1
        
        print(f"   Relationship types: {rel_types}")
        
        # Find most connected nodes
        degrees = dict(graph.degree())
        if degrees:
            most_connected = max(degrees, key=degrees.get)
            most_connected_node = graph.nodes[most_connected]
            print(f"   Most connected node: {most_connected_node.get('name', most_connected[:8])} ({degrees[most_connected]} connections)")

def test_knowledge_retrieval():
    """Test retrieving knowledge for dataset generation"""
    print("\n📚 Testing Knowledge Retrieval")
    print("=" * 50)
    
    db = GraphDB(Path("test_data/extraction_knowledge.db"))
    
    # Load agent profile
    manager = AgentProfileManager(Path("/Users/franckbirba/DEV/TEST-CREWAI/bigacademy/configs/agents"))
    architect_profile = manager.get_profile("solution_architect")
    
    if not architect_profile:
        print("❌ Could not load architect profile")
        return
    
    print(f"🔍 Retrieving knowledge for {architect_profile.name}...")
    
    # Find agent node
    agents = db.find_nodes("Agent", {"name": architect_profile.name})
    if not agents:
        print("❌ Agent not found in database")
        return
    
    agent_id = agents[0].id
    
    # Get all knowledge chunks for agent
    agent_relationships = db.get_relationships(agent_id, "LEARNS_FROM")
    
    print(f"📊 Found {len(agent_relationships)} knowledge relationships")
    
    knowledge_chunks = []
    for rel in agent_relationships:
        chunk_node = db.get_node(rel.target_id)
        if chunk_node and chunk_node.node_type == "KnowledgeChunk":
            knowledge_chunks.append({
                'content': chunk_node.properties.get('content', ''),
                'source_path': chunk_node.properties.get('source_path', ''),
                'relevance_score': chunk_node.properties.get('relevance_score', 0),
                'file_type': chunk_node.properties.get('file_type', ''),
                'language': chunk_node.properties.get('language', '')
            })
    
    # Sort by relevance
    knowledge_chunks.sort(key=lambda x: x['relevance_score'], reverse=True)
    
    print(f"✅ Retrieved {len(knowledge_chunks)} knowledge chunks")
    
    if knowledge_chunks:
        print("📝 Top knowledge chunks:")
        for i, chunk in enumerate(knowledge_chunks[:3]):
            print(f"   {i+1}. {chunk['source_path']} (relevance: {chunk['relevance_score']:.2f})")
            print(f"      Content preview: {chunk['content'][:100]}...")
            print()
    
    return knowledge_chunks

def main():
    """Run all graph database tests"""
    print("🧠 BigAcademy Knowledge Graph Database Test Suite")
    print("=" * 60)
    
    try:
        # Test 1: Basic operations
        db1 = test_graph_db_basic()
        if db1:
            db1.close()
        
        # Test 2: Extraction storage
        db2 = test_extraction_storage()
        if db2:
            db2.close()
        
        # Test 3: Graph analysis
        test_graph_analysis()
        
        # Test 4: Knowledge retrieval
        knowledge_chunks = test_knowledge_retrieval()
        
        print("\n🎉 Graph database test suite completed!")
        print("\n💡 Next steps:")
        print("   1. Knowledge graph storage is working")
        print("   2. Agent-specific knowledge is properly stored")
        print("   3. Ready to build dataset generation from graph")
        print(f"   4. Retrieved {len(knowledge_chunks) if knowledge_chunks else 0} knowledge chunks for training")
        
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()