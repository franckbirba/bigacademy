#!/usr/bin/env python3
"""
BigAcademy Dataset Generator
Generate training datasets from knowledge graph using Distilabel
"""

import json
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional, Iterator
from dataclasses import dataclass, asdict
from datetime import datetime
import random

from ..core.agent_profiles import AgentProfile
from ..core.graph_db import GraphDB
from ..extractors.base_extractor import KnowledgeChunk
from .prompt_templates import PromptTemplateManager

@dataclass
class DatasetSample:
    """Single training sample for agent dataset"""
    id: str
    agent_name: str
    template_type: str
    prompt: str
    expected_response: str
    metadata: Dict[str, Any]
    created_at: str

@dataclass
class DatasetBatch:
    """Batch of dataset samples"""
    agent_name: str
    template_type: str
    samples: List[DatasetSample]
    total_samples: int
    generation_config: Dict[str, Any]
    created_at: str

class DatasetGenerator:
    """Generate training datasets from knowledge graph using prompt templates"""
    
    def __init__(self, 
                 graph_db: GraphDB,
                 template_manager: PromptTemplateManager,
                 output_dir: Path = None):
        self.graph_db = graph_db
        self.template_manager = template_manager
        self.output_dir = output_dir or Path("datasets")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generation statistics
        self.generation_stats = {
            'total_samples': 0,
            'samples_by_agent': {},
            'samples_by_template': {},
            'failed_generations': 0
        }
    
    def generate_agent_dataset(self,
                             agent_profile: AgentProfile,
                             template_types: Optional[List[str]] = None,
                             max_samples_per_template: int = 50,
                             min_relevance_score: float = 0.2,
                             randomize_order: bool = True) -> List[DatasetBatch]:
        """Generate complete dataset for an agent using multiple template types"""
        
        print(f"🎯 Generating dataset for agent: {agent_profile.name}")
        print(f"   Role: {agent_profile.role.title}")
        
        # Get suitable templates for this agent
        if template_types is None:
            template_types = self.template_manager.get_suitable_templates(agent_profile, "code")
        
        print(f"   Templates: {template_types}")
        
        # Get agent's knowledge chunks from graph
        knowledge_chunks = self._get_agent_knowledge_chunks(
            agent_profile, min_relevance_score
        )
        
        if not knowledge_chunks:
            print(f"❌ No knowledge chunks found for {agent_profile.name}")
            return []
        
        print(f"   Knowledge chunks: {len(knowledge_chunks)} (relevance >= {min_relevance_score})")
        
        dataset_batches = []
        
        for template_type in template_types:
            print(f"\n📝 Generating samples with template: {template_type}")
            
            batch = self._generate_template_batch(
                agent_profile=agent_profile,
                template_type=template_type,
                knowledge_chunks=knowledge_chunks,
                max_samples=max_samples_per_template,
                randomize_order=randomize_order
            )
            
            if batch and batch.samples:
                dataset_batches.append(batch)
                print(f"   ✅ Generated {len(batch.samples)} samples")
            else:
                print(f"   ⚠️  No samples generated")
        
        # Update statistics
        total_samples = sum(len(batch.samples) for batch in dataset_batches)
        self.generation_stats['total_samples'] += total_samples
        self.generation_stats['samples_by_agent'][agent_profile.name] = total_samples
        
        print(f"\n✅ Dataset generation complete: {total_samples} total samples")
        return dataset_batches
    
    def _get_agent_knowledge_chunks(self, 
                                   agent_profile: AgentProfile, 
                                   min_relevance_score: float) -> List[Dict[str, Any]]:
        """Get knowledge chunks for an agent from the graph database"""
        
        # Find agent in graph
        agents = self.graph_db.find_nodes("Agent", {"name": agent_profile.name})
        if not agents:
            return []
        
        agent_node = agents[0]
        
        # Get all knowledge relationships
        learn_relationships = self.graph_db.get_relationships(
            agent_node.id, "LEARNS_FROM", "outgoing"
        )
        
        knowledge_chunks = []
        
        for rel in learn_relationships:
            chunk_node = self.graph_db.get_node(rel.target_id)
            if not chunk_node:
                continue
            
            # Check relevance score
            relevance = chunk_node.properties.get('relevance_score', 0)
            if relevance < min_relevance_score:
                continue
            
            # Create knowledge chunk data
            chunk_data = {
                'chunk': KnowledgeChunk(
                    content=chunk_node.properties.get('content', ''),
                    source_path=chunk_node.properties.get('source_path', ''),
                    file_type=chunk_node.properties.get('file_type', ''),
                    language=chunk_node.properties.get('language', 'text'),
                    size_tokens=chunk_node.properties.get('size_tokens', 0),
                    relevance_score=relevance,
                    metadata=chunk_node.properties.get('metadata', {})
                ),
                'source_info': self._get_source_info_for_chunk(rel.target_id)
            }
            
            knowledge_chunks.append(chunk_data)
        
        # Sort by relevance score (highest first)
        knowledge_chunks.sort(key=lambda x: x['chunk'].relevance_score, reverse=True)
        
        return knowledge_chunks
    
    def _get_source_info_for_chunk(self, chunk_id: str) -> Dict[str, Any]:
        """Get source information for a knowledge chunk"""
        
        # Find source that contains this chunk
        contains_rels = self.graph_db.get_relationships(chunk_id, "CONTAINS", "incoming")
        
        for rel in contains_rels:
            source_node = self.graph_db.get_node(rel.source_id)
            if source_node and source_node.node_type == "Source":
                return {
                    'url': source_node.properties.get('url', 'unknown'),
                    'type': source_node.properties.get('source_type', 'unknown'),
                    'total_chunks': source_node.properties.get('total_chunks', 0),
                    'total_tokens': source_node.properties.get('total_tokens', 0)
                }
        
        return {'url': 'unknown', 'type': 'unknown'}
    
    def _generate_template_batch(self,
                               agent_profile: AgentProfile,
                               template_type: str,
                               knowledge_chunks: List[Dict[str, Any]],
                               max_samples: int,
                               randomize_order: bool) -> Optional[DatasetBatch]:
        """Generate a batch of samples using a specific template"""
        
        if randomize_order:
            knowledge_chunks = knowledge_chunks.copy()
            random.shuffle(knowledge_chunks)
        
        samples = []
        generation_config = {
            'template_type': template_type,
            'max_samples': max_samples,
            'agent_name': agent_profile.name,
            'min_relevance_score': min([chunk['chunk'].relevance_score for chunk in knowledge_chunks]) if knowledge_chunks else 0,
            'max_relevance_score': max([chunk['chunk'].relevance_score for chunk in knowledge_chunks]) if knowledge_chunks else 0
        }
        
        # Generate samples up to max_samples
        for i, chunk_data in enumerate(knowledge_chunks[:max_samples]):
            try:
                sample = self._generate_single_sample(
                    agent_profile=agent_profile,
                    template_type=template_type,
                    chunk_data=chunk_data,
                    sample_index=i
                )
                
                if sample:
                    samples.append(sample)
                    
                    # Progress indicator
                    if (i + 1) % 10 == 0:
                        print(f"      Generated {i + 1}/{min(max_samples, len(knowledge_chunks))} samples")
                
            except Exception as e:
                print(f"      ❌ Error generating sample {i+1}: {e}")
                self.generation_stats['failed_generations'] += 1
                continue
        
        if not samples:
            return None
        
        return DatasetBatch(
            agent_name=agent_profile.name,
            template_type=template_type,
            samples=samples,
            total_samples=len(samples),
            generation_config=generation_config,
            created_at=datetime.now().isoformat()
        )
    
    def _generate_single_sample(self,
                              agent_profile: AgentProfile,
                              template_type: str,
                              chunk_data: Dict[str, Any],
                              sample_index: int) -> Optional[DatasetSample]:
        """Generate a single training sample"""
        
        chunk = chunk_data['chunk']
        source_info = chunk_data['source_info']
        
        # Generate prompt using template
        prompt = self.template_manager.generate_prompt(
            template_type=template_type,
            agent_profile=agent_profile,
            knowledge_chunk=chunk,
            source_info=source_info,
            question_type="professional",
            sample_index=sample_index
        )
        
        # For now, we'll create a placeholder response
        # In a real implementation, this would call an LLM to generate the response
        expected_response = self._generate_placeholder_response(
            template_type, agent_profile, chunk
        )
        
        # Create sample metadata
        metadata = {
            'source_path': chunk.source_path,
            'source_url': source_info['url'],
            'relevance_score': chunk.relevance_score,
            'chunk_tokens': chunk.size_tokens,
            'file_type': chunk.file_type,
            'language': chunk.language,
            'template_type': template_type,
            'agent_role': agent_profile.role.title,
            'agent_technologies': agent_profile.technologies,
            'agent_focus_areas': agent_profile.focus_areas,
            'generation_timestamp': datetime.now().isoformat()
        }
        
        return DatasetSample(
            id=str(uuid.uuid4()),
            agent_name=agent_profile.name,
            template_type=template_type,
            prompt=prompt,
            expected_response=expected_response,
            metadata=metadata,
            created_at=datetime.now().isoformat()
        )
    
    def _generate_placeholder_response(self,
                                     template_type: str,
                                     agent_profile: AgentProfile,
                                     chunk: KnowledgeChunk) -> str:
        """Generate placeholder response for testing (replace with LLM call)"""
        
        responses = {
            'question_answer': f"""**Question:** How would you implement this functionality as an Expert {agent_profile.role.title}?

**Answer:** As an Expert {agent_profile.role.title}, I would approach this implementation by focusing on {', '.join(agent_profile.focus_areas[:2])}. The solution should leverage {', '.join(agent_profile.technologies[:3])} technologies to ensure scalability and maintainability.

[This is a placeholder response - in production, this would be generated by an LLM using the full prompt]""",
            
            'code_review': f"""**Code Review Summary:**

**Overall Assessment:** This code demonstrates solid understanding of {chunk.language} fundamentals.

**Strengths:**
- Clean structure and readable implementation
- Appropriate use of {chunk.language} patterns

**Areas for Improvement:**
- Consider adding error handling
- Add comprehensive documentation
- Implement proper testing coverage

**Recommended Changes:**
[Specific code improvements would be provided here]

**Additional Recommendations:**
Based on my expertise in {', '.join(agent_profile.focus_areas[:2])}, I recommend implementing proper logging and monitoring.

Review conducted by: Expert {agent_profile.role.title}""",
            
            'implementation_task': f"""**Implementation Task:**

**Scenario:** [Realistic scenario based on the knowledge context]

**Requirements:**
- Implement using {', '.join(agent_profile.technologies[:2])}
- Follow {', '.join(agent_profile.focus_areas[:2])} best practices

**Implementation:**
[Complete solution would be provided here]

**Architecture Decisions:** [Professional design choices explained]

Implemented by: Expert {agent_profile.role.title}""",
            
            'debugging_scenario': f"""**Debugging Scenario:**

**Problem Description:** [Issue description based on code]

**Debugging Process:**
1. **Problem Analysis:** Applied systematic debugging approach
2. **Root Cause:** Identified the core issue
3. **Solution:** Implemented proper fix
4. **Prevention:** Recommended best practices

Debugged by: Expert {agent_profile.role.title}""",
            
            'multi_turn_conversation': f"""**Multi-Turn Conversation:**

**Turn 1:**
*Client:* [Initial request]
*Expert {agent_profile.role.title}:* [Professional guidance]

**Turn 2:**
*Client:* [Follow-up question]
*Expert {agent_profile.role.title}:* [Detailed technical response]

[Additional turns would continue here]

**Conversation Summary:**
Technologies Discussed: {', '.join(agent_profile.technologies[:3])}
Key Insights: Professional expertise demonstrated throughout"""
        }
        
        return responses.get(template_type, f"Professional response from Expert {agent_profile.role.title}")
    
    def save_dataset_batches(self, 
                           dataset_batches: List[DatasetBatch],
                           format: str = "jsonl") -> List[Path]:
        """Save dataset batches to files"""
        
        saved_files = []
        
        for batch in dataset_batches:
            # Create filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{batch.agent_name}_{batch.template_type}_{timestamp}.{format}"
            file_path = self.output_dir / filename
            
            if format == "jsonl":
                self._save_as_jsonl(batch, file_path)
            elif format == "json":
                self._save_as_json(batch, file_path)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            saved_files.append(file_path)
            print(f"💾 Saved {len(batch.samples)} samples to: {file_path}")
        
        return saved_files
    
    def _save_as_jsonl(self, batch: DatasetBatch, file_path: Path):
        """Save batch as JSONL format (one JSON object per line)"""
        with open(file_path, 'w', encoding='utf-8') as f:
            for sample in batch.samples:
                json.dump(asdict(sample), f, ensure_ascii=False)
                f.write('\n')
    
    def _save_as_json(self, batch: DatasetBatch, file_path: Path):
        """Save batch as JSON format"""
        batch_data = asdict(batch)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(batch_data, f, indent=2, ensure_ascii=False)
    
    def get_generation_stats(self) -> Dict[str, Any]:
        """Get dataset generation statistics"""
        return self.generation_stats.copy()
    
    def create_distilabel_format(self, 
                                dataset_batches: List[DatasetBatch],
                                output_file: Path = None) -> Path:
        """Convert dataset to Distilabel format for further processing"""
        
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"distilabel_dataset_{timestamp}.jsonl"
        
        distilabel_samples = []
        
        for batch in dataset_batches:
            for sample in batch.samples:
                # Convert to Distilabel format
                distilabel_sample = {
                    "instruction": sample.prompt,
                    "output": sample.expected_response,
                    "input": "",  # Empty for instruction-following format
                    "metadata": {
                        "agent_name": sample.agent_name,
                        "template_type": sample.template_type,
                        "sample_id": sample.id,
                        **sample.metadata
                    }
                }
                distilabel_samples.append(distilabel_sample)
        
        # Save in Distilabel format
        with open(output_file, 'w', encoding='utf-8') as f:
            for sample in distilabel_samples:
                json.dump(sample, f, ensure_ascii=False)
                f.write('\n')
        
        print(f"🎯 Created Distilabel dataset: {output_file}")
        print(f"   Total samples: {len(distilabel_samples)}")
        
        return output_file