# 🐳 BigAcademy Docker Stack

Complete Docker environment for BigAcademy with Argilla UI integration for dataset review and enhancement.

## 🚀 Quick Start

```bash
# Start the complete stack
docker-compose up -d

# View logs
docker-compose logs -f

# Stop stack
docker-compose down
```

## 🌐 Services & Access

| Service | URL | Credentials |
|---------|-----|-------------|
| **Argilla UI** | http://localhost:6900 | admin / bigacademy123 |
| **Jupyter Lab** | http://localhost:8888?token=bigacademy | Token: bigacademy |
| **Elasticsearch** | http://localhost:9200 | No auth |

## 📋 Complete Workflow

### 1. Generate Datasets
```bash
# Enter BigAcademy CLI container
docker exec -it bigacademy-cli bash

# Generate sample datasets
python test_dataset_generator.py

# Or generate custom datasets
python -c "
from bigacademy.generators.dataset_generator import DatasetGenerator
# Your custom generation code here
"
```

### 2. Upload to Argilla
```bash
# Upload generated datasets to Argilla UI
python scripts/upload_to_argilla.py datasets/solution_architect_question_answer_*.jsonl

# Upload with custom name
python scripts/upload_to_argilla.py datasets/my_dataset.jsonl --name="custom_dataset"
```

### 3. Review in Argilla UI
1. Open http://localhost:6900
2. Login with: admin / bigacademy123
3. Navigate to BigAcademy workspace
4. Review and rate samples (excellent/good/fair/poor/terrible)
5. Edit responses to improve quality
6. Add tags and annotations

### 4. Download Enhanced Dataset
```bash
# Download reviewed dataset with analysis
python scripts/download_from_argilla.py solution_architect_question_answer --analyze

# Download in Distilabel format for training
python scripts/download_from_argilla.py solution_architect_question_answer --format=distilabel
```

### 5. Train with BigTune
```bash
# Use enhanced dataset for training
bigtune train --dataset="enhanced_solution_architect_*.jsonl" \
              --base-model="llama-3.1-8b" \
              --technique="lora"
```

## 📊 Jupyter Integration

Open http://localhost:8888?token=bigacademy and use the provided notebook:
- `BigAcademy_Argilla_Integration.ipynb` - Complete workflow demonstration

## 🔧 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ARGILLA_API_URL` | http://argilla:6900 | Argilla server URL |
| `ARGILLA_API_KEY` | bigacademy-api-key | API key for authentication |
| `ARGILLA_WORKSPACE` | bigacademy | Default workspace |

## 📁 Volume Mounts

```
./configs     → /app/configs      # Agent profiles & templates
./datasets    → /app/datasets     # Generated datasets
./test_data   → /app/test_data    # Knowledge graphs
./scripts     → /app/scripts      # Integration scripts
./notebooks   → Jupyter workspace # Analysis notebooks
```

## 🎯 Integration Benefits

### ✅ Before (BigAcademy only):
Generate → Hope it's good → Train → Maybe poor results

### 🚀 After (BigAcademy + Argilla):
Generate → Human review → Quality control → Train → Better agents

## 🔄 Quality Enhancement Cycle

```
BigAcademy → Argilla → Human Review → Enhanced Dataset → Training
    ↑                                                        ↓
Template Updates ← Analysis ← Annotation Patterns ← Better Model
```

## 🛠️ Troubleshooting

### Container Issues
```bash
# Check container status
docker-compose ps

# View specific service logs
docker-compose logs argilla
docker-compose logs bigacademy-cli

# Restart specific service
docker-compose restart argilla
```

### Argilla Connection Issues
```bash
# Test Argilla connection
docker exec bigacademy-cli python -c "
import argilla as rg
rg.init(api_url='http://argilla:6900', api_key='bigacademy-api-key')
print('✅ Connected to Argilla')
"
```

### Reset Everything
```bash
# ⚠️  This will delete all data
docker-compose down -v
docker-compose up -d
```

## 📈 Resource Requirements

### Minimum:
- RAM: 4GB
- CPU: 2 cores  
- Disk: 5GB

### Recommended:
- RAM: 8GB
- CPU: 4 cores
- Disk: 20GB

## 🎉 Success Indicators

✅ Argilla UI loads at http://localhost:6900  
✅ Can login with admin/bigacademy123  
✅ BigAcademy CLI responds to commands  
✅ Datasets upload/download successfully  
✅ Jupyter notebooks run without errors  

**Ready to create expert AI agents with human-enhanced datasets!** 🤖✨