#!/usr/bin/env python3
"""
BigAcademy Knowledge Graph Visualization
Text-based visualization of the knowledge graph database
"""

import sys
sys.path.append('/Users/franckbirba/DEV/TEST-CREWAI/bigacademy')

from bigacademy.core.graph_db import GraphDB
from pathlib import Path
import json

def visualize_graph_structure(db: GraphDB, agent_name: str = None):
    """Create text-based visualization of graph structure"""
    print("🕸️  BigAcademy Knowledge Graph Structure")
    print("=" * 60)
    
    # Get overall statistics
    stats = db.get_knowledge_statistics(agent_name)
    
    print(f"📊 Graph Statistics:")
    print(f"   Node Types: {stats.get('node_counts', {})}")
    print(f"   Relationship Types: {stats.get('relationship_counts', {})}")
    
    if agent_name:
        print(f"   Agent Knowledge: {stats.get('agent_knowledge', {})}")
    
    print()
    
    # Get all nodes by type
    agents = db.find_nodes("Agent")
    sources = db.find_nodes("Source")
    chunks = db.find_nodes("KnowledgeChunk")
    technologies = db.find_nodes("Technology")
    skills = db.find_nodes("Skill")
    
    print("🎯 Graph Structure Visualization:")
    print()
    
    # Show agents and their connections
    for agent in agents:
        agent_name = agent.properties.get('name', 'unknown')
        agent_title = agent.properties.get('title', 'Unknown Role')
        
        print(f"🤖 AGENT: {agent_name}")
        print(f"   └── Role: {agent_title}")
        
        # Get agent relationships
        relationships = db.get_relationships(agent.id, direction="outgoing")
        
        # Group relationships by type
        rel_groups = {}
        for rel in relationships:
            rel_type = rel.relationship_type
            if rel_type not in rel_groups:
                rel_groups[rel_type] = []
            rel_groups[rel_type].append(rel)
        
        # Show each relationship type
        for rel_type, rels in rel_groups.items():
            print(f"   │")
            print(f"   ├── {rel_type} ({len(rels)})")
            
            for i, rel in enumerate(rels[:3]):  # Show first 3
                target_node = db.get_node(rel.target_id)
                if target_node:
                    target_name = target_node.properties.get('name', 
                                   target_node.properties.get('url', 
                                   target_node.properties.get('source_path', 'unknown')))
                    
                    connector = "└──" if i == len(rels[:3]) - 1 else "├──"
                    print(f"   │   {connector} {target_node.node_type}: {target_name[:50]}...")
            
            if len(rels) > 3:
                print(f"   │   └── ... and {len(rels) - 3} more")
        
        print()

def visualize_knowledge_flow(db: GraphDB, agent_name: str):
    """Visualize knowledge flow for specific agent"""
    print(f"🌊 Knowledge Flow for Agent: {agent_name}")
    print("=" * 60)
    
    # Find agent
    agents = db.find_nodes("Agent", {"name": agent_name})
    if not agents:
        print(f"❌ Agent '{agent_name}' not found")
        return
    
    agent = agents[0]
    
    # Get extraction sessions
    extract_rels = db.get_relationships(agent.id, "EXTRACTS_FROM", "outgoing")
    
    print(f"📚 Knowledge Sources ({len(extract_rels)}):")
    
    for i, extract_rel in enumerate(extract_rels):
        source_node = db.get_node(extract_rel.target_id)
        if source_node:
            source_url = source_node.properties.get('url', 'unknown')
            total_chunks = source_node.properties.get('total_chunks', 0)
            total_tokens = source_node.properties.get('total_tokens', 0)
            
            print(f"   {i+1}. SOURCE: {source_url}")
            print(f"      └── Extracted: {total_chunks} chunks, {total_tokens:,} tokens")
            
            # Get chunks from this source
            chunk_rels = db.get_relationships(source_node.id, "CONTAINS", "outgoing")
            
            print(f"      └── Top Knowledge Chunks:")
            
            # Get chunk details and sort by relevance
            chunk_details = []
            for chunk_rel in chunk_rels[:10]:  # Top 10
                chunk_node = db.get_node(chunk_rel.target_id)
                if chunk_node:
                    chunk_details.append({
                        'path': chunk_node.properties.get('source_path', 'unknown'),
                        'relevance': chunk_node.properties.get('relevance_score', 0),
                        'tokens': chunk_node.properties.get('size_tokens', 0),
                        'file_type': chunk_node.properties.get('file_type', 'unknown')
                    })
            
            # Sort by relevance
            chunk_details.sort(key=lambda x: x['relevance'], reverse=True)
            
            for j, chunk in enumerate(chunk_details[:5]):
                print(f"          {j+1}. {chunk['path']:<40} (rel: {chunk['relevance']:.3f}, {chunk['tokens']:,} tokens)")
    
    print()

def visualize_technology_skills_network(db: GraphDB, agent_name: str):
    """Visualize technology and skills network"""
    print(f"🔧 Technology & Skills Network for: {agent_name}")
    print("=" * 60)
    
    # Find agent
    agents = db.find_nodes("Agent", {"name": agent_name})
    if not agents:
        print(f"❌ Agent '{agent_name}' not found")
        return
    
    agent = agents[0]
    
    # Get technologies
    tech_rels = db.get_relationships(agent.id, "REQUIRES", "outgoing")
    skill_rels = db.get_relationships(agent.id, "SPECIALIZES_IN", "outgoing")
    
    print(f"🔧 Technologies ({len(tech_rels)}):")
    for tech_rel in tech_rels:
        tech_node = db.get_node(tech_rel.target_id)
        if tech_node:
            tech_name = tech_node.properties.get('name', 'unknown')
            
            # Find chunks that implement this technology
            impl_rels = db.get_relationships(tech_node.id, "IMPLEMENTS", "incoming")
            
            print(f"   └── {tech_name}")
            print(f"       └── Implemented in {len(impl_rels)} knowledge chunks")
            
            # Show sample implementations
            for i, impl_rel in enumerate(impl_rels[:3]):
                chunk_node = db.get_node(impl_rel.source_id)
                if chunk_node:
                    chunk_path = chunk_node.properties.get('source_path', 'unknown')
                    print(f"           {i+1}. {chunk_path}")
    
    print()
    print(f"🎯 Skills & Expertise ({len(skill_rels)}):")
    for skill_rel in skill_rels:
        skill_node = db.get_node(skill_rel.target_id)
        if skill_node:
            skill_name = skill_node.properties.get('name', 'unknown')
            keywords = skill_node.properties.get('keywords', [])
            
            # Find chunks that demonstrate this skill
            demo_rels = db.get_relationships(skill_node.id, "DEMONSTRATES", "incoming")
            
            print(f"   └── {skill_name}")
            print(f"       ├── Keywords: {', '.join(keywords[:5])}")
            print(f"       └── Demonstrated in {len(demo_rels)} knowledge chunks")
            
            # Calculate average demonstration score
            if demo_rels:
                avg_score = sum(rel.weight for rel in demo_rels) / len(demo_rels)
                print(f"           └── Average relevance: {avg_score:.3f}")

def create_ascii_graph(db: GraphDB, agent_name: str):
    """Create ASCII art representation of the graph"""
    print(f"🎨 ASCII Graph Representation for: {agent_name}")
    print("=" * 80)
    
    # Find agent
    agents = db.find_nodes("Agent", {"name": agent_name})
    if not agents:
        print(f"❌ Agent '{agent_name}' not found")
        return
    
    agent = agents[0]
    
    # Get relationships
    extract_rels = db.get_relationships(agent.id, "EXTRACTS_FROM", "outgoing")
    tech_rels = db.get_relationships(agent.id, "REQUIRES", "outgoing")
    skill_rels = db.get_relationships(agent.id, "SPECIALIZES_IN", "outgoing")
    learn_rels = db.get_relationships(agent.id, "LEARNS_FROM", "outgoing")
    
    agent_name_display = agent.properties.get('name', 'Agent')
    
    print("                    BIGACADEMY KNOWLEDGE GRAPH")
    print()
    print("    ┌─────────────────────────────────────────────────────────────────┐")
    print("    │                          SOURCES                                │")
    print("    └─────────────────────┬───────────────────────────────────────────┘")
    print("                          │ EXTRACTS_FROM")
    print("                          ▼")
    print(f"        ┌─────────────────────────────────────────────────────┐")
    print(f"        │                   AGENT                             │")
    print(f"        │              {agent_name_display:<20}              │")
    print(f"        │         ({agent.properties.get('title', 'Unknown Role'):<25})         │")
    print(f"        └─────────────────┬───────────────────┬───────────────┘")
    print("                          │                   │")
    print("                 REQUIRES │                   │ SPECIALIZES_IN")
    print("                          ▼                   ▼")
    print("        ┌─────────────────┐                   ┌─────────────────┐")
    print(f"        │  TECHNOLOGIES   │                   │     SKILLS      │")
    print(f"        │   ({len(tech_rels)} items)       │                   │   ({len(skill_rels)} items)       │")
    print("        └─────────────────┘                   └─────────────────┘")
    print("                  │                                   │")
    print("         IMPLEMENTS │                                   │ DEMONSTRATES")
    print("                  ▼                                   ▼")
    print("        ┌─────────────────────────────────────────────────────┐")
    print("        │                KNOWLEDGE CHUNKS                    │")
    print(f"        │                  ({len(learn_rels)} chunks)                      │")
    print("        │            (Extracted & Filtered Content)          │")
    print("        └─────────────────────────────────────────────────────┘")
    print()
    
    # Show detailed breakdown
    print("📊 Detailed Breakdown:")
    print(f"   🤖 Agent: {agent_name_display}")
    print(f"   📚 Sources: {len(extract_rels)} repositories")
    print(f"   🔧 Technologies: {len(tech_rels)} items")
    print(f"   🎯 Skills: {len(skill_rels)} areas")
    print(f"   📝 Knowledge Chunks: {len(learn_rels)} pieces")
    
    # Show technologies
    if tech_rels:
        print(f"\n   🔧 Technologies:")
        for tech_rel in tech_rels:
            tech_node = db.get_node(tech_rel.target_id)
            if tech_node:
                tech_name = tech_node.properties.get('name', 'unknown')
                print(f"      • {tech_name}")
    
    # Show skills
    if skill_rels:
        print(f"\n   🎯 Skills:")
        for skill_rel in skill_rels:
            skill_node = db.get_node(skill_rel.target_id)
            if skill_node:
                skill_name = skill_node.properties.get('name', 'unknown')
                print(f"      • {skill_name}")

def main():
    """Visualize knowledge graphs from test databases"""
    print("🕸️  BigAcademy Knowledge Graph Visualization Suite")
    print("=" * 70)
    
    # Test databases from our previous runs
    test_dbs = [
        ("test_data/fastapi_minimal_architect.db", "solution_architect"),
        ("test_data/pydantic_developer.db", "python_developer")
    ]
    
    for db_path, agent_name in test_dbs:
        db_file = Path(db_path)
        if not db_file.exists():
            print(f"⚠️  Database not found: {db_path}")
            continue
            
        print(f"\n{'='*70}")
        print(f"Database: {db_path}")
        print(f"Agent: {agent_name}")
        print(f"{'='*70}")
        
        try:
            db = GraphDB(db_file)
            
            # 1. Overall structure
            visualize_graph_structure(db, agent_name)
            
            # 2. Knowledge flow
            visualize_knowledge_flow(db, agent_name)
            
            # 3. Technology & skills network  
            visualize_technology_skills_network(db, agent_name)
            
            # 4. ASCII representation
            create_ascii_graph(db, agent_name)
            
            db.close()
            
        except Exception as e:
            print(f"❌ Error visualizing {db_path}: {e}")
    
    print(f"\n🎉 Graph visualization complete!")

if __name__ == "__main__":
    main()