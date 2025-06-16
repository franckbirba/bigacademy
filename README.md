# BigAcademy - AI Agent Knowledge & Dataset Generator

**BigAcademy** extracts knowledge from multiple sources and generates high-quality datasets for training specialized AI agents with **BigTune**.

## 🎯 Mission

Transform knowledge sources (GitHub repos, documentation, local files) into expert-level training datasets for specialized AI agents like Solution Architects and Python Developers.

## 🏗️ Architecture

```
Knowledge Sources → GraphDB → Expert Validation → Datasets → BigTune Training
     📚              🧠           👨‍💼            📊         🔥
```

## 🚀 Quick Start

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

4. **Review and validate knowledge**:
   ```bash
   bigacademy review --profile architect --show-graph
   bigacademy validate approve --knowledge-id 123
   ```

5. **Generate training dataset**:
   ```bash
   bigacademy generate dataset --profile architect --size 500
   ```

6. **Export for BigTune training**:
   ```bash
   bigacademy export bigtune --dataset architect_v1
   ```

## 🎓 Expert Agent Profiles

- **Solution Architect**: System design, microservices, scalability
- **Python Developer**: Clean code, testing, frameworks
- **DevOps Engineer**: Infrastructure, deployment, monitoring

## 🧠 Knowledge Sources

- **GitHub Repositories**: Code patterns, best practices, real implementations
- **Official Documentation**: Authoritative guides, tutorials, references  
- **Local Files**: Project code, configs, documentation (.py, .md, .yaml, .json, etc.)

## 📊 Dataset Quality

- **GraphDB Knowledge Organization**: Hierarchical knowledge mapping
- **Expert-Level Content**: All agents trained as domain experts
- **Human Validation**: User review and approval of knowledge chunks
- **Role-Aware Responses**: Agents know their professional identity

## 🔗 Integration with BigTune

BigAcademy generates datasets in BigTune-compatible format for seamless training:

```bash
# BigAcademy: Generate dataset
bigacademy export bigtune --output ./datasets/architect_expert.jsonl

# BigTune: Train the agent  
bigtune train --dataset ./datasets/architect_expert.jsonl
```

## 📁 Project Structure

```
bigacademy/
├── bigacademy/           # Core package
│   ├── core/            # GraphDB, knowledge engine
│   ├── extractors/      # GitHub, docs, file extractors
│   ├── analyzers/       # Pattern analysis, skill mapping
│   └── exporters/       # BigTune format export
├── data/                # Knowledge base and datasets
├── configs/             # Agent and extractor configs
└── tests/               # Test suite
```

## 🤝 Workflow

1. **Profile Definition**: Define expert agent roles and responsibilities
2. **Source Discovery**: Find relevant GitHub repos, docs, local files
3. **Knowledge Extraction**: Parse and analyze content for patterns
4. **Graph Organization**: Store in GraphDB with relationships
5. **Human Validation**: Review and approve knowledge chunks
6. **Dataset Generation**: Create training examples from validated knowledge
7. **BigTune Export**: Format for LoRA fine-tuning

---

**BigAcademy** → Knowledge → **BigTune** → Expert AI Agents 🎓🤖