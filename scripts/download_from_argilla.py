#!/usr/bin/env python3
"""
Download enhanced datasets from Argilla after human review
"""

import argparse
import json
import os
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

import argilla as rg

def setup_argilla_connection():
    """Setup connection to Argilla server"""
    api_url = os.getenv('ARGILLA_API_URL', 'http://localhost:6900')
    api_key = os.getenv('ARGILLA_API_KEY', 'bigacademy-api-key')
    workspace = os.getenv('ARGILLA_WORKSPACE', 'bigacademy')
    
    rg.init(api_url=api_url, api_key=api_key, workspace=workspace)
    print(f"✅ Connected to Argilla at {api_url}")
    print(f"   Workspace: {workspace}")

def download_from_argilla(dataset_name: str) -> List[Dict[str, Any]]:
    """Download annotated dataset from Argilla"""
    try:
        # Load dataset from Argilla
        dataset = rg.load(dataset_name)
        print(f"📥 Downloaded {len(dataset)} records from '{dataset_name}'")
        
        enhanced_samples = []
        
        for record in dataset:
            try:
                # Extract original data from metadata
                metadata = record.metadata or {}
                original_prompt = metadata.get('original_prompt', '')
                original_response = metadata.get('original_response', '')
                
                # Get human annotation (quality rating)
                annotation = None
                quality_score = None
                
                if record.annotation:
                    annotation = record.annotation
                    # Convert quality label to numeric score
                    quality_mapping = {
                        'excellent': 5,
                        'good': 4,
                        'fair': 3,
                        'poor': 2,
                        'terrible': 1
                    }
                    quality_score = quality_mapping.get(annotation, 3)
                
                # Create enhanced sample
                enhanced_sample = {
                    'id': metadata.get('sample_id', f'enhanced_{len(enhanced_samples)}'),
                    'agent_name': metadata.get('agent_name', 'unknown'),
                    'template_type': metadata.get('template_type', 'unknown'),
                    'prompt': original_prompt,
                    'expected_response': original_response,
                    'metadata': {
                        **metadata,
                        'human_annotation': annotation,
                        'quality_score': quality_score,
                        'reviewed_at': datetime.now().isoformat(),
                        'argilla_dataset': dataset_name
                    },
                    'created_at': datetime.now().isoformat()
                }
                
                enhanced_samples.append(enhanced_sample)
                
            except Exception as e:
                print(f"⚠️  Error processing record: {e}")
                continue
        
        print(f"🔄 Processed {len(enhanced_samples)} enhanced samples")
        return enhanced_samples
        
    except Exception as e:
        print(f"❌ Download failed: {e}")
        raise

def save_enhanced_dataset(samples: List[Dict[str, Any]], 
                         output_path: Path,
                         format: str = 'jsonl') -> None:
    """Save enhanced dataset to file"""
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if format == 'jsonl':
        # Save as JSONL (one JSON object per line)
        with open(output_path, 'w', encoding='utf-8') as f:
            for sample in samples:
                json.dump(sample, f, ensure_ascii=False)
                f.write('\n')
    
    elif format == 'json':
        # Save as JSON array
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(samples, f, indent=2, ensure_ascii=False)
    
    elif format == 'distilabel':
        # Save in Distilabel format for training
        distilabel_samples = []
        for sample in samples:
            distilabel_sample = {
                "instruction": sample['prompt'],
                "output": sample['expected_response'],
                "input": "",
                "metadata": sample['metadata']
            }
            distilabel_samples.append(distilabel_sample)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for sample in distilabel_samples:
                json.dump(sample, f, ensure_ascii=False)
                f.write('\n')
    
    else:
        raise ValueError(f"Unsupported format: {format}")
    
    print(f"💾 Saved {len(samples)} enhanced samples to {output_path}")

def analyze_annotations(samples: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze human annotations for insights"""
    analysis = {
        'total_samples': len(samples),
        'annotated_samples': 0,
        'quality_distribution': {},
        'template_quality': {},
        'agent_quality': {},
        'avg_quality_score': 0,
        'low_quality_samples': []
    }
    
    quality_scores = []
    
    for sample in samples:
        metadata = sample.get('metadata', {})
        quality_score = metadata.get('quality_score')
        annotation = metadata.get('human_annotation')
        template_type = sample.get('template_type', 'unknown')
        agent_name = sample.get('agent_name', 'unknown')
        
        if annotation:
            analysis['annotated_samples'] += 1
            
            # Quality distribution
            if annotation not in analysis['quality_distribution']:
                analysis['quality_distribution'][annotation] = 0
            analysis['quality_distribution'][annotation] += 1
            
            # Template quality
            if template_type not in analysis['template_quality']:
                analysis['template_quality'][template_type] = []
            analysis['template_quality'][template_type].append(quality_score or 3)
            
            # Agent quality
            if agent_name not in analysis['agent_quality']:
                analysis['agent_quality'][agent_name] = []
            analysis['agent_quality'][agent_name].append(quality_score or 3)
            
            if quality_score:
                quality_scores.append(quality_score)
                
                # Track low quality samples
                if quality_score <= 2:
                    analysis['low_quality_samples'].append({
                        'id': sample.get('id'),
                        'template_type': template_type,
                        'quality_score': quality_score,
                        'relevance_score': metadata.get('relevance_score', 0)
                    })
    
    # Calculate averages
    if quality_scores:
        analysis['avg_quality_score'] = sum(quality_scores) / len(quality_scores)
    
    # Calculate template averages
    for template_type, scores in analysis['template_quality'].items():
        analysis['template_quality'][template_type] = {
            'avg_score': sum(scores) / len(scores),
            'sample_count': len(scores),
            'scores': scores
        }
    
    # Calculate agent averages
    for agent_name, scores in analysis['agent_quality'].items():
        analysis['agent_quality'][agent_name] = {
            'avg_score': sum(scores) / len(scores),
            'sample_count': len(scores),
            'scores': scores
        }
    
    return analysis

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Download enhanced datasets from Argilla")
    parser.add_argument("dataset_name", help="Name of dataset in Argilla")
    parser.add_argument("--output", help="Output file path (default: datasets/enhanced_{dataset_name}.jsonl)")
    parser.add_argument("--format", choices=['jsonl', 'json', 'distilabel'], default='jsonl',
                       help="Output format (default: jsonl)")
    parser.add_argument("--analyze", action="store_true", help="Generate annotation analysis report")
    
    args = parser.parse_args()
    
    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"enhanced_{args.dataset_name}_{timestamp}.{args.format}"
        output_path = Path("datasets") / filename
    
    print(f"📥 Argilla → BigAcademy Download")
    print(f"   Source: {args.dataset_name}")
    print(f"   Target: {output_path}")
    print(f"   Format: {args.format}")
    
    try:
        # Setup Argilla connection
        setup_argilla_connection()
        
        # Download enhanced dataset
        enhanced_samples = download_from_argilla(args.dataset_name)
        if not enhanced_samples:
            print("❌ No samples found")
            return 1
        
        # Save enhanced dataset
        save_enhanced_dataset(enhanced_samples, output_path, args.format)
        
        # Generate analysis if requested
        if args.analyze:
            analysis = analyze_annotations(enhanced_samples)
            analysis_path = output_path.with_suffix('.analysis.json')
            
            with open(analysis_path, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, indent=2, ensure_ascii=False)
            
            print(f"\n📊 Annotation Analysis:")
            print(f"   Total samples: {analysis['total_samples']}")
            print(f"   Annotated: {analysis['annotated_samples']}")
            print(f"   Average quality: {analysis['avg_quality_score']:.2f}/5")
            print(f"   Quality distribution: {analysis['quality_distribution']}")
            print(f"   Analysis saved to: {analysis_path}")
        
        print("\n🎉 Download completed successfully!")
        print(f"📊 Next steps:")
        print(f"   1. Review enhanced dataset: {output_path}")
        if args.analyze:
            print(f"   2. Check analysis report: {analysis_path}")
        print(f"   3. Train with BigTune: bigtune train --dataset={output_path}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())