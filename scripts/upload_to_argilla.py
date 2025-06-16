#!/usr/bin/env python3
"""
Upload BigAcademy datasets to Argilla for review and annotation
"""

import argparse
import json
import os
from pathlib import Path
from typing import List, Dict, Any

import argilla as rg
from argilla import Text, TextClassification

def setup_argilla_connection():
    """Setup connection to Argilla server"""
    api_url = os.getenv('ARGILLA_API_URL', 'http://localhost:6900')
    api_key = os.getenv('ARGILLA_API_KEY', 'bigacademy-api-key')
    workspace = os.getenv('ARGILLA_WORKSPACE', 'bigacademy')
    
    rg.init(api_url=api_url, api_key=api_key, workspace=workspace)
    print(f"✅ Connected to Argilla at {api_url}")
    print(f"   Workspace: {workspace}")

def load_bigacademy_dataset(file_path: Path) -> List[Dict[str, Any]]:
    """Load BigAcademy JSONL dataset"""
    samples = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            try:
                sample = json.loads(line.strip())
                samples.append(sample)
            except json.JSONDecodeError as e:
                print(f"⚠️  Skipping invalid JSON on line {line_num}: {e}")
                continue
    
    print(f"📊 Loaded {len(samples)} samples from {file_path}")
    return samples

def convert_to_argilla_records(samples: List[Dict[str, Any]], 
                               dataset_name: str) -> List[rg.TextClassificationRecord]:
    """Convert BigAcademy samples to Argilla records"""
    records = []
    
    for i, sample in enumerate(samples):
        try:
            # Extract fields from BigAcademy format
            prompt = sample.get('prompt', '')
            response = sample.get('expected_response', '')
            metadata = sample.get('metadata', {})
            
            # Create full text for review
            full_text = f"**PROMPT:**\n{prompt}\n\n**RESPONSE:**\n{response}"
            
            # Create Argilla record
            record = rg.TextClassificationRecord(
                text=full_text,
                metadata={
                    'sample_id': sample.get('id', f'sample_{i}'),
                    'agent_name': sample.get('agent_name', 'unknown'),
                    'template_type': sample.get('template_type', 'unknown'),
                    'relevance_score': metadata.get('relevance_score', 0),
                    'source_path': metadata.get('source_path', ''),
                    'source_url': metadata.get('source_url', ''),
                    'chunk_tokens': metadata.get('chunk_tokens', 0),
                    'prompt_length': len(prompt),
                    'response_length': len(response),
                    'original_prompt': prompt,
                    'original_response': response
                },
                prediction=[('quality', 0.5)],  # Default prediction for rating
                annotation=None  # To be filled by human reviewers
            )
            
            records.append(record)
            
        except Exception as e:
            print(f"⚠️  Error converting sample {i}: {e}")
            continue
    
    print(f"🔄 Converted {len(records)} samples to Argilla format")
    return records

def upload_to_argilla(records: List[rg.TextClassificationRecord], 
                      dataset_name: str, 
                      overwrite: bool = False) -> None:
    """Upload records to Argilla dataset"""
    
    try:
        # Check if dataset exists
        try:
            existing_dataset = rg.load(dataset_name)
            if not overwrite:
                response = input(f"Dataset '{dataset_name}' exists. Overwrite? (y/N): ")
                if response.lower() != 'y':
                    print("❌ Upload cancelled")
                    return
            print(f"🔄 Overwriting existing dataset '{dataset_name}'")
        except:
            print(f"📝 Creating new dataset '{dataset_name}'")
        
        # Define dataset settings for quality rating
        settings = rg.TextClassificationSettings(
            label_schema=[
                "excellent",
                "good", 
                "fair",
                "poor",
                "terrible"
            ]
        )
        
        # Log records to Argilla
        rg.log(
            records=records,
            name=dataset_name,
            settings=settings
        )
        
        print(f"✅ Successfully uploaded {len(records)} records to '{dataset_name}'")
        print(f"🌐 View at: {os.getenv('ARGILLA_API_URL', 'http://localhost:6900')}")
        
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        raise

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Upload BigAcademy datasets to Argilla")
    parser.add_argument("dataset_path", help="Path to BigAcademy JSONL dataset file")
    parser.add_argument("--name", help="Dataset name in Argilla (default: derived from filename)")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing dataset")
    
    args = parser.parse_args()
    
    # Validate dataset file
    dataset_file = Path(args.dataset_path)
    if not dataset_file.exists():
        print(f"❌ Dataset file not found: {dataset_file}")
        return 1
    
    # Derive dataset name
    dataset_name = args.name or dataset_file.stem
    
    print(f"🚀 BigAcademy → Argilla Upload")
    print(f"   Source: {dataset_file}")
    print(f"   Target: {dataset_name}")
    
    try:
        # Setup Argilla connection
        setup_argilla_connection()
        
        # Load BigAcademy dataset
        samples = load_bigacademy_dataset(dataset_file)
        if not samples:
            print("❌ No valid samples found")
            return 1
        
        # Convert to Argilla format
        records = convert_to_argilla_records(samples, dataset_name)
        if not records:
            print("❌ No records to upload")
            return 1
        
        # Upload to Argilla
        upload_to_argilla(records, dataset_name, args.overwrite)
        
        print("\n🎉 Upload completed successfully!")
        print(f"📊 Next steps:")
        print(f"   1. Open Argilla UI: {os.getenv('ARGILLA_API_URL', 'http://localhost:6900')}")
        print(f"   2. Review and annotate samples in '{dataset_name}'")
        print(f"   3. Download enhanced dataset: python scripts/download_from_argilla.py {dataset_name}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())