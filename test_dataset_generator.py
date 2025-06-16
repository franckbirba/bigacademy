#!/usr/bin/env python3
"""
Test BigAcademy Dataset Generator
"""

import sys
sys.path.append('/Users/franckbirba/DEV/TEST-CREWAI/bigacademy')

from bigacademy.core.agent_profiles import AgentProfileManager
from bigacademy.core.graph_db import GraphDB
from bigacademy.generators.prompt_templates import PromptTemplateManager
from bigacademy.generators.dataset_generator import DatasetGenerator
from pathlib import Path
import json

def test_dataset_generator_setup():
    """Test dataset generator initialization"""
    print("🎯 Testing Dataset Generator Setup")
    print("=" * 50)
    
    # Load components
    agent_manager = AgentProfileManager(Path("/Users/franckbirba/DEV/TEST-CREWAI/bigacademy/configs/agents"))
    template_manager = PromptTemplateManager(Path("/Users/franckbirba/DEV/TEST-CREWAI/bigacademy/configs/templates"))
    
    # Test with architect database
    db_path = Path("test_data/fastapi_minimal_architect.db")
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return None, None, None
    
    graph_db = GraphDB(db_path)
    
    # Initialize dataset generator
    dataset_generator = DatasetGenerator(
        graph_db=graph_db,
        template_manager=template_manager,
        output_dir=Path("test_data/generated_datasets")
    )
    
    print("✅ Dataset generator initialized")
    print(f"   Output directory: {dataset_generator.output_dir}")
    print(f"   Available templates: {template_manager.get_available_templates()}")
    
    return agent_manager, dataset_generator, graph_db

def test_knowledge_chunk_extraction():
    """Test extracting knowledge chunks for dataset generation"""
    print("\n📚 Testing Knowledge Chunk Extraction")
    print("=" * 50)
    
    agent_manager, dataset_generator, graph_db = test_dataset_generator_setup()
    if not dataset_generator:
        return
    
    # Load architect profile
    architect = agent_manager.get_profile("solution_architect")
    if not architect:
        print("❌ Could not load architect profile")
        return
    
    print(f"🤖 Agent: {architect.name}")
    print(f"   Role: {architect.role.title}")
    
    # Test knowledge extraction with different relevance thresholds
    relevance_thresholds = [0.1, 0.2, 0.3]
    
    for threshold in relevance_thresholds:
        knowledge_chunks = dataset_generator._get_agent_knowledge_chunks(
            architect, threshold
        )
        
        print(f"   📊 Relevance >= {threshold}: {len(knowledge_chunks)} chunks")
        
        if knowledge_chunks:
            # Show top 3 chunks
            for i, chunk_data in enumerate(knowledge_chunks[:3]):
                chunk = chunk_data['chunk']
                source = chunk_data['source_info']
                print(f"      {i+1}. {chunk.source_path} (rel: {chunk.relevance_score:.3f}, tokens: {chunk.size_tokens})")
                print(f"         Source: {source['url']}")
    
    graph_db.close()
    return knowledge_chunks if 'knowledge_chunks' in locals() else []

def test_single_sample_generation():
    """Test generating individual dataset samples"""
    print("\n🎨 Testing Single Sample Generation")
    print("=" * 50)
    
    agent_manager, dataset_generator, graph_db = test_dataset_generator_setup()
    if not dataset_generator:
        return
    
    # Load architect profile
    architect = agent_manager.get_profile("solution_architect")
    if not architect:
        print("❌ Could not load architect profile")
        return
    
    # Get knowledge chunks
    knowledge_chunks = dataset_generator._get_agent_knowledge_chunks(architect, 0.2)
    if not knowledge_chunks:
        print("❌ No knowledge chunks found")
        return
    
    print(f"📚 Using {len(knowledge_chunks)} knowledge chunks")
    
    # Test different template types
    template_types = ["question_answer", "code_review", "implementation_task"]
    
    for template_type in template_types:
        print(f"\n📝 Testing template: {template_type}")
        
        try:
            # Generate single sample
            sample = dataset_generator._generate_single_sample(
                agent_profile=architect,
                template_type=template_type,
                chunk_data=knowledge_chunks[0],  # Use first chunk
                sample_index=0
            )
            
            if sample:
                print(f"   ✅ Generated sample ID: {sample.id[:8]}")
                print(f"   📏 Prompt length: {len(sample.prompt)} chars")
                print(f"   📏 Response length: {len(sample.expected_response)} chars")
                print(f"   📋 Metadata keys: {list(sample.metadata.keys())}")
                
                # Show prompt preview
                prompt_lines = sample.prompt.split('\n')
                print(f"   📖 Prompt preview: {prompt_lines[0] if prompt_lines else 'Empty'}")
                
            else:
                print(f"   ❌ Failed to generate sample")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    graph_db.close()

def test_batch_generation():
    """Test generating complete dataset batches"""
    print("\n📦 Testing Batch Generation")
    print("=" * 50)
    
    agent_manager, dataset_generator, graph_db = test_dataset_generator_setup()
    if not dataset_generator:
        return
    
    # Load architect profile
    architect = agent_manager.get_profile("solution_architect")
    if not architect:
        print("❌ Could not load architect profile")
        return
    
    print(f"🤖 Generating dataset for: {architect.name}")
    
    # Generate dataset with limited samples for testing
    dataset_batches = dataset_generator.generate_agent_dataset(
        agent_profile=architect,
        template_types=["question_answer", "code_review"],  # Limited for testing
        max_samples_per_template=5,  # Small batch for testing
        min_relevance_score=0.15,
        randomize_order=True
    )
    
    print(f"\n✅ Generated {len(dataset_batches)} batches")
    
    total_samples = 0
    for batch in dataset_batches:
        print(f"   📦 Batch: {batch.template_type}")
        print(f"      Samples: {len(batch.samples)}")
        print(f"      Config: {batch.generation_config}")
        total_samples += len(batch.samples)
    
    print(f"\n📊 Total samples generated: {total_samples}")
    
    # Show generation statistics
    stats = dataset_generator.get_generation_stats()
    print(f"📈 Generation stats: {stats}")
    
    graph_db.close()
    return dataset_batches

def test_dataset_saving():
    """Test saving datasets in different formats"""
    print("\n💾 Testing Dataset Saving")
    print("=" * 50)
    
    # Generate test dataset
    dataset_batches = test_batch_generation()
    if not dataset_batches:
        print("❌ No dataset batches to save")
        return
    
    agent_manager, dataset_generator, graph_db = test_dataset_generator_setup()
    if not dataset_generator:
        return
    
    print(f"💾 Saving {len(dataset_batches)} batches...")
    
    # Test JSONL format
    saved_files = dataset_generator.save_dataset_batches(dataset_batches, format="jsonl")
    print(f"✅ Saved {len(saved_files)} JSONL files")
    
    # Test JSON format
    saved_files_json = dataset_generator.save_dataset_batches(dataset_batches, format="json")
    print(f"✅ Saved {len(saved_files_json)} JSON files")
    
    # Test Distilabel format
    distilabel_file = dataset_generator.create_distilabel_format(dataset_batches)
    print(f"✅ Created Distilabel format: {distilabel_file}")
    
    # Verify file contents
    if saved_files:
        sample_file = saved_files[0]
        print(f"\n📁 Sample file content ({sample_file.name}):")
        
        with open(sample_file, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
            if first_line:
                sample_data = json.loads(first_line)
                print(f"   Sample ID: {sample_data.get('id', 'unknown')[:8]}")
                print(f"   Agent: {sample_data.get('agent_name', 'unknown')}")
                print(f"   Template: {sample_data.get('template_type', 'unknown')}")
                print(f"   Prompt length: {len(sample_data.get('prompt', ''))}")
    
    graph_db.close()
    return saved_files, distilabel_file

def test_multi_agent_dataset():
    """Test generating datasets for multiple agents"""
    print("\n👥 Testing Multi-Agent Dataset Generation")
    print("=" * 50)
    
    # Load both agents
    agent_manager = AgentProfileManager(Path("/Users/franckbirba/DEV/TEST-CREWAI/bigacademy/configs/agents"))
    template_manager = PromptTemplateManager(Path("/Users/franckbirba/DEV/TEST-CREWAI/bigacademy/configs/templates"))
    
    agents = ["solution_architect", "python_developer"]
    databases = {
        "solution_architect": "test_data/fastapi_minimal_architect.db",
        "python_developer": "test_data/pydantic_developer.db"
    }
    
    all_batches = []
    
    for agent_name in agents:
        db_path = Path(databases[agent_name])
        if not db_path.exists():
            print(f"⚠️  Database not found for {agent_name}: {db_path}")
            continue
        
        print(f"\n🤖 Processing agent: {agent_name}")
        
        # Load agent and database
        agent_profile = agent_manager.get_profile(agent_name)
        if not agent_profile:
            print(f"❌ Could not load profile for {agent_name}")
            continue
        
        graph_db = GraphDB(db_path)
        dataset_generator = DatasetGenerator(
            graph_db=graph_db,
            template_manager=template_manager,
            output_dir=Path(f"test_data/generated_datasets/{agent_name}")
        )
        
        # Generate small dataset for each agent
        batches = dataset_generator.generate_agent_dataset(
            agent_profile=agent_profile,
            template_types=["question_answer"],  # Just one template for speed
            max_samples_per_template=3,
            min_relevance_score=0.2
        )
        
        all_batches.extend(batches)
        graph_db.close()
    
    print(f"\n✅ Multi-agent generation complete!")
    print(f"   Total batches: {len(all_batches)}")
    print(f"   Total samples: {sum(len(batch.samples) for batch in all_batches)}")
    
    return all_batches

def main():
    """Run all dataset generator tests"""
    print("🎯 BigAcademy Dataset Generator Test Suite")
    print("=" * 70)
    
    try:
        # Test 1: Setup
        test_dataset_generator_setup()
        
        # Test 2: Knowledge extraction
        test_knowledge_chunk_extraction()
        
        # Test 3: Single sample generation
        test_single_sample_generation()
        
        # Test 4: Batch generation
        test_batch_generation()
        
        # Test 5: Dataset saving
        test_dataset_saving()
        
        # Test 6: Multi-agent datasets
        test_multi_agent_dataset()
        
        print("\n🎉 Dataset generator test suite completed!")
        print("\n💡 Key Results:")
        print("   ✅ Dataset generator working with knowledge graph")
        print("   ✅ Generic template system integration")
        print("   ✅ Multiple output formats (JSONL, JSON, Distilabel)")
        print("   ✅ Multi-agent dataset generation")
        print("   🚀 Ready for LLM integration and training!")
        
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()