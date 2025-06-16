#!/usr/bin/env python3
"""
BigAcademy Knowledge Graph Database
SQLite-based graph storage with NetworkX for analysis
"""

import sqlite3
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
import networkx as nx

from .agent_profiles import AgentProfile
from ..extractors.base_extractor import KnowledgeChunk, ExtractionResult

@dataclass
class GraphNode:
    """Generic graph node"""
    id: str
    node_type: str
    properties: Dict[str, Any]
    created_at: str
    updated_at: str

@dataclass
class GraphEdge:
    """Generic graph edge/relationship"""
    id: str
    source_id: str
    target_id: str
    relationship_type: str
    properties: Dict[str, Any]
    weight: float
    created_at: str

class GraphDB:
    """Knowledge graph database with SQLite backend and NetworkX analysis"""
    
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or Path("data/knowledge_base.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize SQLite database with graph schema"""
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Enable column access by name
        
        # Create tables
        self._create_tables()
        
        # Create indexes for performance
        self._create_indexes()
        
        print(f"✅ Graph database initialized: {self.db_path}")
    
    def _create_tables(self):
        """Create database tables for graph storage"""
        
        # Nodes table - stores all entities
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS nodes (
                id TEXT PRIMARY KEY,
                node_type TEXT NOT NULL,
                properties TEXT NOT NULL,  -- JSON
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        
        # Edges table - stores all relationships
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS edges (
                id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                relationship_type TEXT NOT NULL,
                properties TEXT NOT NULL,  -- JSON
                weight REAL DEFAULT 1.0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (source_id) REFERENCES nodes (id),
                FOREIGN KEY (target_id) REFERENCES nodes (id)
            )
        ''')
        
        # Agent sessions - track extraction sessions
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS agent_sessions (
                id TEXT PRIMARY KEY,
                agent_name TEXT NOT NULL,
                source_id TEXT NOT NULL,
                source_type TEXT NOT NULL,
                total_chunks INTEGER,
                total_tokens INTEGER,
                extraction_metadata TEXT,  -- JSON
                created_at TEXT NOT NULL
            )
        ''')
        
        self.conn.commit()
    
    def _create_indexes(self):
        """Create database indexes for performance"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(node_type)",
            "CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id)",
            "CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id)",
            "CREATE INDEX IF NOT EXISTS idx_edges_type ON edges(relationship_type)",
            "CREATE INDEX IF NOT EXISTS idx_sessions_agent ON agent_sessions(agent_name)"
        ]
        
        for index in indexes:
            self.conn.execute(index)
        
        self.conn.commit()
    
    def add_node(self, node_type: str, properties: Dict[str, Any], 
                 node_id: Optional[str] = None) -> str:
        """Add a node to the graph"""
        node_id = node_id or str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        self.conn.execute('''
            INSERT OR REPLACE INTO nodes (id, node_type, properties, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (node_id, node_type, json.dumps(properties), now, now))
        
        self.conn.commit()
        return node_id
    
    def add_edge(self, source_id: str, target_id: str, relationship_type: str,
                 properties: Optional[Dict[str, Any]] = None, weight: float = 1.0) -> str:
        """Add an edge/relationship to the graph"""
        edge_id = str(uuid.uuid4())
        properties = properties or {}
        now = datetime.now().isoformat()
        
        self.conn.execute('''
            INSERT INTO edges (id, source_id, target_id, relationship_type, properties, weight, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (edge_id, source_id, target_id, relationship_type, json.dumps(properties), weight, now))
        
        self.conn.commit()
        return edge_id
    
    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """Get a node by ID"""
        cursor = self.conn.execute('SELECT * FROM nodes WHERE id = ?', (node_id,))
        row = cursor.fetchone()
        
        if row:
            return GraphNode(
                id=row['id'],
                node_type=row['node_type'],
                properties=json.loads(row['properties']),
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
        return None
    
    def find_nodes(self, node_type: Optional[str] = None, 
                   properties_filter: Optional[Dict[str, Any]] = None) -> List[GraphNode]:
        """Find nodes by type and/or properties"""
        query = "SELECT * FROM nodes"
        params = []
        conditions = []
        
        if node_type:
            conditions.append("node_type = ?")
            params.append(node_type)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        cursor = self.conn.execute(query, params)
        nodes = []
        
        for row in cursor.fetchall():
            node = GraphNode(
                id=row['id'],
                node_type=row['node_type'],
                properties=json.loads(row['properties']),
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
            
            # Apply properties filter if specified
            if properties_filter:
                match = all(
                    node.properties.get(key) == value 
                    for key, value in properties_filter.items()
                )
                if match:
                    nodes.append(node)
            else:
                nodes.append(node)
        
        return nodes
    
    def get_relationships(self, node_id: str, 
                         relationship_type: Optional[str] = None,
                         direction: str = "both") -> List[GraphEdge]:
        """Get relationships for a node"""
        conditions = []
        params = []
        
        if direction in ["outgoing", "both"]:
            conditions.append("source_id = ?")
            params.append(node_id)
        
        if direction in ["incoming", "both"] and direction != "outgoing":
            if conditions:
                conditions = [f"({' OR '.join(conditions)} OR target_id = ?)"]
                params.append(node_id)
            else:
                conditions.append("target_id = ?")
                params.append(node_id)
        
        if relationship_type:
            conditions.append("relationship_type = ?")
            params.append(relationship_type)
        
        query = "SELECT * FROM edges"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        cursor = self.conn.execute(query, params)
        edges = []
        
        for row in cursor.fetchall():
            edges.append(GraphEdge(
                id=row['id'],
                source_id=row['source_id'],
                target_id=row['target_id'],
                relationship_type=row['relationship_type'],
                properties=json.loads(row['properties']),
                weight=row['weight'],
                created_at=row['created_at']
            ))
        
        return edges
    
    def store_extraction_result(self, result: ExtractionResult, 
                               agent_profile: AgentProfile) -> str:
        """Store extraction result in knowledge graph"""
        print(f"📊 Storing extraction result for {agent_profile.name}")
        
        # Create agent session
        session_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        self.conn.execute('''
            INSERT INTO agent_sessions 
            (id, agent_name, source_id, source_type, total_chunks, total_tokens, extraction_metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id, agent_profile.name, result.source_id, result.source_type,
            result.total_chunks, result.total_tokens, 
            json.dumps(result.extraction_metadata), now
        ))
        
        # Create agent node if not exists
        agent_id = self._ensure_agent_node(agent_profile)
        
        # Create source node
        source_id = self.add_node("Source", {
            "url": result.source_id,
            "source_type": result.source_type,
            "total_chunks": result.total_chunks,
            "total_tokens": result.total_tokens,
            "metadata": result.extraction_metadata
        })
        
        # Create agent -> source relationship
        self.add_edge(agent_id, source_id, "EXTRACTS_FROM", {
            "session_id": session_id,
            "extraction_date": now
        })
        
        # Process knowledge chunks
        technology_nodes = {}
        skill_nodes = {}
        
        for chunk in result.chunks:
            # Create knowledge chunk node
            chunk_id = self.add_node("KnowledgeChunk", {
                "content": chunk.content,
                "source_path": chunk.source_path,
                "file_type": chunk.file_type,
                "language": chunk.language,
                "size_tokens": chunk.size_tokens,
                "relevance_score": chunk.relevance_score,
                "metadata": chunk.metadata
            })
            
            # Create source -> chunk relationship
            self.add_edge(source_id, chunk_id, "CONTAINS", weight=chunk.relevance_score)
            
            # Create agent -> chunk relationship
            self.add_edge(agent_id, chunk_id, "LEARNS_FROM", {
                "relevance_score": chunk.relevance_score,
                "session_id": session_id
            }, weight=chunk.relevance_score)
            
            # Extract and link technologies
            for tech in agent_profile.technologies:
                if tech.lower() in chunk.content.lower():
                    if tech not in technology_nodes:
                        tech_id = self.add_node("Technology", {
                            "name": tech,
                            "agent_context": agent_profile.name
                        })
                        technology_nodes[tech] = tech_id
                        
                        # Create agent -> technology relationship
                        self.add_edge(agent_id, tech_id, "REQUIRES")
                    
                    # Create chunk -> technology relationship
                    self.add_edge(chunk_id, technology_nodes[tech], "IMPLEMENTS")
            
            # Extract and link skills based on knowledge filters
            for skill_category, keywords in agent_profile.knowledge_filters.items():
                skill_score = sum(
                    1 for keyword in keywords 
                    if keyword.lower() in chunk.content.lower()
                ) / len(keywords) if keywords else 0
                
                if skill_score > 0.1:  # Minimum relevance threshold
                    if skill_category not in skill_nodes:
                        skill_id = self.add_node("Skill", {
                            "name": skill_category,
                            "keywords": keywords,
                            "agent_context": agent_profile.name
                        })
                        skill_nodes[skill_category] = skill_id
                        
                        # Create agent -> skill relationship
                        self.add_edge(agent_id, skill_id, "SPECIALIZES_IN")
                    
                    # Create chunk -> skill relationship
                    self.add_edge(chunk_id, skill_nodes[skill_category], "DEMONSTRATES", 
                                weight=skill_score)
        
        self.conn.commit()
        print(f"✅ Stored {len(result.chunks)} knowledge chunks in graph")
        return session_id
    
    def _ensure_agent_node(self, agent_profile: AgentProfile) -> str:
        """Ensure agent node exists in graph"""
        # Check if agent node exists
        existing_agents = self.find_nodes("Agent", {"name": agent_profile.name})
        
        if existing_agents:
            return existing_agents[0].id
        
        # Create new agent node
        return self.add_node("Agent", {
            "name": agent_profile.name,
            "title": agent_profile.role.title,
            "description": agent_profile.role.description,
            "identity_prompt": agent_profile.role.identity_prompt,
            "communication_style": agent_profile.role.communication_style,
            "technologies": agent_profile.technologies,
            "focus_areas": agent_profile.focus_areas,
            "domain_expertise": agent_profile.role.domain_expertise
        })
    
    def get_agent_knowledge_graph(self, agent_name: str) -> nx.Graph:
        """Get NetworkX graph for an agent's knowledge"""
        G = nx.Graph()
        
        # Get agent node
        agents = self.find_nodes("Agent", {"name": agent_name})
        if not agents:
            return G
        
        agent_id = agents[0].id
        
        # Add agent node
        G.add_node(agent_id, **agents[0].properties, node_type="Agent")
        
        # Get all relationships from agent
        relationships = self.get_relationships(agent_id, direction="outgoing")
        
        for edge in relationships:
            target_node = self.get_node(edge.target_id)
            if target_node:
                G.add_node(edge.target_id, **target_node.properties, 
                          node_type=target_node.node_type)
                G.add_edge(agent_id, edge.target_id, 
                          relationship_type=edge.relationship_type,
                          weight=edge.weight, **edge.properties)
        
        return G
    
    def get_knowledge_statistics(self, agent_name: Optional[str] = None) -> Dict[str, Any]:
        """Get knowledge graph statistics"""
        stats = {}
        
        # Node counts by type
        cursor = self.conn.execute('SELECT node_type, COUNT(*) as count FROM nodes GROUP BY node_type')
        stats['node_counts'] = dict(cursor.fetchall())
        
        # Edge counts by type
        cursor = self.conn.execute('SELECT relationship_type, COUNT(*) as count FROM edges GROUP BY relationship_type')
        stats['relationship_counts'] = dict(cursor.fetchall())
        
        # Agent-specific stats
        if agent_name:
            cursor = self.conn.execute('''
                SELECT COUNT(*) as sessions FROM agent_sessions WHERE agent_name = ?
            ''', (agent_name,))
            stats['agent_sessions'] = cursor.fetchone()[0]
            
            cursor = self.conn.execute('''
                SELECT SUM(total_chunks) as chunks, SUM(total_tokens) as tokens 
                FROM agent_sessions WHERE agent_name = ?
            ''', (agent_name,))
            row = cursor.fetchone()
            stats['agent_knowledge'] = {
                'total_chunks': row[0] or 0,
                'total_tokens': row[1] or 0
            }
        
        return stats
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None