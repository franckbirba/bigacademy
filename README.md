# BigAcademy - AI Agent Knowledge & Dataset Generator with RAG Training

**BigAcademy** extracts knowledge from multiple sources and generates high-quality datasets for training specialized AI agents with **BigTune**, now enhanced with **RAG-aware training capabilities**.

## ✨ New: RAG Training Integration

BigAcademy now supports creating datasets specifically designed for RAG (Retrieval-Augmented Generation) training:

- 🎯 **RAG-Aware Templates**: Generate training examples that teach models to follow provided documentation
- 📚 **Context-Following Datasets**: Create instruction-following datasets for RAG scenarios
- 🔄 **Argilla Integration**: Human-in-the-loop feedback for RAG model improvement
- 🚀 **BigTune Compatibility**: Seamless integration with BigTune's RAG training pipeline

## 🎯 Mission

Transform knowledge sources (APIs, documentation, local files) into expert-level training datasets for specialized AI agents, with special focus on creating models that can accurately follow provided context and documentation.

## 🏗️ Architecture

```
Knowledge Sources → GraphDB → Expert Validation → RAG Datasets → BigTune Training → RAG Models
     📚              🧠           👨‍💼              📊           🔥            🤖
```

## 🚀 Quick Start

### Standard Dataset Generation

1. **Install BigAcademy**:
   ```bash
   pip install -e .
   ```

2. **Create an expert agent profile**:
   ```bash
   bigacademy profile create solution_architect
   ```

3. **Extract knowledge from sources**:
   ```bash
   bigacademy extract github --profile architect --repo joaomdmoura/crewai
   bigacademy extract docs --profile architect --url https://docs.crewai.com
   ```

4. **Generate training dataset**:
   ```bash
   bigacademy generate dataset --profile architect --size 500
   ```

### RAG Training Dataset Generation

5. **Generate RAG-specific datasets**:
   ```bash
   # For API documentation following
   bigacademy generate rag-dataset --type api-assistant --samples 200
   
   # For knowledge base Q&A
   bigacademy generate rag-dataset --type knowledge-qa --samples 300
   ```

6. **Export for BigTune RAG training**:
   ```bash
   bigacademy export bigtune-rag --dataset api_assistant_v1
   ```

## 🎓 Expert Agent Profiles

### Standard Profiles
- **Solution Architect**: System design, microservices, scalability
- **Python Developer**: Clean code, testing, frameworks
- **DevOps Engineer**: Infrastructure, deployment, monitoring

### RAG-Specific Profiles
- **API Assistant**: Provides accurate API guidance from documentation
- **Knowledge Expert**: Answers questions using provided context exactly
- **Support Agent**: Customer support using current help documents
- **Code Assistant**: Programming help following current API specifications

## 🧠 Knowledge Sources

- **GitHub Repositories**: Code patterns, best practices, real implementations
- **API Documentation**: Swagger/OpenAPI specs, endpoint documentation
- **Official Documentation**: Authoritative guides, tutorials, references  
- **Local Files**: Project code, configs, documentation (.py, .md, .yaml, .json, etc.)

## 📊 Dataset Quality

### Standard Features
- **GraphDB Knowledge Organization**: Hierarchical knowledge mapping
- **Expert-Level Content**: All agents trained as domain experts
- **Human Validation**: User review and approval of knowledge chunks
- **Role-Aware Responses**: Agents know their professional identity

### RAG-Specific Quality
- **Context-Following Training**: Examples that teach exact documentation adherence
- **Anti-Hallucination Patterns**: Training data that prevents making up information
- **Endpoint Accuracy**: Precise API path and parameter extraction
- **Documentation Fidelity**: Models learn to respect provided context exactly

## 🔗 Integration with BigTune

### Standard Integration
BigAcademy generates datasets in BigTune-compatible format for seamless training:

```bash
# BigAcademy: Generate dataset
bigacademy export bigtune --output ./datasets/architect_expert.jsonl

# BigTune: Train the agent  
bigtune train --dataset ./datasets/architect_expert.jsonl
```

### RAG Training Integration
Complete RAG training pipeline:

```bash
# BigAcademy: Generate RAG training dataset
bigacademy generate rag-dataset --type api-assistant --samples 200 \
  --swagger-url http://localhost:5050/api/swagger.json

# BigTune: Train RAG-aware model
CONFIG_FILE=./config/rag-model.yaml bigtune train

# BigTune: Test with RAG system
./bigtune-rag query "What is the endpoint to get all users?"
```

## 📁 Project Structure

```
bigacademy/
├── bigacademy/           # Core package
│   ├── core/            # GraphDB, knowledge engine
│   ├── extractors/      # GitHub, docs, file extractors
│   ├── analyzers/       # Pattern analysis, skill mapping
│   ├── templates/       # RAG training templates (NEW)
│   └── exporters/       # BigTune format export
├── templates/           # RAG training templates (NEW)
│   ├── console_bocal_guide.yaml
│   ├── api_guidance.yaml
│   ├── faq_response.yaml
│   └── ...
├── data/                # Knowledge base and datasets
├── configs/             # Agent and extractor configs
├── datasets/            # Generated training datasets
├── docker-compose.yml   # Argilla + Elasticsearch stack
└── tests/               # Test suite
```

## 🤝 Workflow

### Standard Workflow
1. **Profile Definition**: Define expert agent roles and responsibilities
2. **Source Discovery**: Find relevant GitHub repos, docs, local files
3. **Knowledge Extraction**: Parse and analyze content for patterns
4. **Graph Organization**: Store in GraphDB with relationships
5. **Human Validation**: Review and approve knowledge chunks
6. **Dataset Generation**: Create training examples from validated knowledge
7. **BigTune Export**: Format for LoRA fine-tuning

### RAG Training Workflow
1. **API Documentation Analysis**: Parse Swagger/OpenAPI specifications
2. **RAG Template Selection**: Choose appropriate training templates
3. **Context-Following Dataset Generation**: Create examples that teach documentation adherence
4. **Argilla Feedback Collection**: Gather human feedback on model responses
5. **Iterative Improvement**: Retrain models with improved datasets
6. **RAG Deployment**: Deploy models with document retrieval capabilities

## 🎯 RAG Training Templates

BigAcademy includes specialized templates for RAG training:

### Console Bocal API Assistant
```yaml
name: console_bocal_guide
description: "Train models to provide accurate Console Bocal API guidance"
focus: "Exact endpoint extraction from provided documentation"
```

### Generic API Assistant
```yaml
name: api_guidance
description: "Train models for any API documentation following"
focus: "HTTP method and parameter accuracy"
```

### FAQ Response System
```yaml
name: faq_response
description: "Answer questions using only provided FAQ context"
focus: "Context adherence and no hallucination"
```

## 📈 Success Metrics

### Standard Models
- Knowledge accuracy and depth
- Professional response quality
- Domain expertise demonstration

### RAG Models
- **Endpoint Accuracy**: 100% correct API paths
- **Context Adherence**: Never ignores provided documentation
- **Anti-Hallucination**: Zero made-up information
- **Parameter Precision**: Exact required/optional parameter identification

## 🔧 Development Tools

### Argilla Integration
BigAcademy includes a complete Argilla stack for RAG model feedback:

```bash
# Start Argilla stack
docker-compose up -d

# Access Argilla UI
open http://localhost:6900
# Default: admin / bigacademy123
```

### Template Development
Create custom RAG training templates:

```yaml
# templates/my_assistant.yaml
name: "my_custom_assistant"
description: "Custom RAG assistant for my domain"
system_prompt: "You are an expert..."
templates:
  - instruction: "Extract exact information from documentation"
    input_format: "Question: {question}\nDocumentation: {context}"
    output_format: "Answer: {exact_answer}"
```

## 🌟 Success Stories

### Console Bocal RAG Expert
- **Problem**: Model provided wrong API endpoints like `/email/aliases`
- **Solution**: RAG training with BigAcademy templates
- **Result**: 100% accurate responses like `GET /api/{domain}/aliases`

### Documentation Bot
- **Challenge**: AI hallucinating outdated API information
- **Approach**: Context-following training datasets
- **Outcome**: Bot never provides information not in provided docs

## 🚀 Future Roadmap

- **Multi-Modal RAG**: Support for code, images, and documentation
- **Auto-Template Generation**: Automatically create templates from API specs
- **Continuous Learning**: Real-time model updates from user feedback
- **Enterprise Integration**: Support for private documentation sources

---

**BigAcademy** → Knowledge → **BigTune** → Expert RAG-Aware AI Agents 🎓🤖📚

**Ready to create intelligent, documentation-aware AI assistants that never hallucinate!**