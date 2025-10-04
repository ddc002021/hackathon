# Paper Code Mapper

**Cross-Modal Graph Fusion: Mapping Research Papers to Code Implementations**

## Team Members
- Dany Chahine (ID: 202107582)
- EECE 798S
- American University of Beirut

## Overview

Paper Code Mapper uses AI to create unified graphs connecting research papers and their code implementations. Upload a research paper (PDF) and its code repository (ZIP) to see how paper concepts map to actual code.

## Features

- **Cross-Modal Graph Fusion**: Unified graphs connecting paper concepts and code features  
- **Paper Parsing**: Extract sections, algorithms, and structure from research papers (PDF/TXT)  
- **Code Feature Extraction**: LLM analyzes code to identify high-level features  
- **Intelligent Mapping**: AI-powered connection between paper concepts and implementations  
- **Interactive Exploration**: Click paper sections to see implementing code, and vice versa  
- **Code Walkthrough**: Deep-dive into any function with AI-generated explanations  
- **Execution Trace Graphs**: Visualize function execution as dynamic flow graphs  

## Key Innovation: Cross-Modal Graph Fusion

**The first system to automatically map research papers to their code implementations as a unified, interactive graph.**

### How It Works:
1. **Upload Paper** (PDF or TXT)
   - System extracts sections, algorithms, and key concepts
   - Creates paper nodes: sections, algorithms, references
   
2. **Upload Code** (ZIP repository)
   - LLM analyzes code to identify high-level features
   - Creates code nodes: features, files, functions

3. **AI-Powered Cross-Modal Mapping**
   - LLM identifies connections between paper sections and code features
   - Analyzes imports, function calls, and semantic similarity
   - Provides confidence scores and evidence for each mapping

4. **Interactive Unified Graph**
   - Orange nodes = Paper concepts (left side)
   - Purple nodes = Code features (right side)
   - Animated edges = Cross-modal connections
   - Click any node to explore details

### Multi-Modal Graph Architecture:
1. **Paper Graph** (Text Modality): Research paper structure, sections, algorithms
2. **Code Graph** (Code Modality): Software features, files, functions
3. **Cross-Modal Edges**: Semantic mappings between paper and code
4. **Execution Trace Graph** (Runtime Modality): Dynamic execution flow visualization

### Why This Matters:
- **True Cross-Modal Fusion**: Unifies text (papers) and code in a single graph representation
- **Text-to-Graph + Code-to-Graph**: Transforms both unstructured papers and code into graphs
- **Novel Use Case**: Solves real problem for researchers and engineers reading academic papers
- **Graph Representation Learning**: Demonstrates how different modalities can be unified through graph structures
- **Practical Value**: Makes academic papers with code instantly navigable and understandable

### Alignment with Hackathon Requirements:
- **Graph Representation Learning**: Multi-modal data (paper + code) converted to unified graph  
- **Text-to-Graph Conversion**: Research papers converted to structured graph nodes  
- **Cross-Modal Graph Fusion**: Different modalities unified in one graph  
- **LLM-Based Agent**: AI-powered semantic mapping and feature extraction  

## Demo Video

<video src="./DEMO.mp4" controls width="100%"></video>

## Architecture

```
User Upload → Code Parser → Feature Extractor (LLM) → Feature Graph Builder
                                                            ↓
                                                      Graph Visualization
                                                            ↓
                                  Feature Click → Drill Down → Function Details
                                                            ↓
                                                  Function Execution + Trace Graph
```

## Technology Stack

**Backend**: FastAPI, NetworkX, OpenAI API  
**Frontend**: React, React Flow, Tailwind CSS  
**DevOps**: Docker, Docker Compose

## Configuration

### Environment Variables

- `OPENAI_API_KEY` - Your OpenAI API key
- `MODEL_NAME` - Model to use (default: `gpt-4-turbo-preview`)
- `SUPPORTED_EXTENSIONS` - Comma-separated file extensions to parse (default: `.py`)

**Examples:**
```bash
# Python only (default)
SUPPORTED_EXTENSIONS=.py

# Add JavaScript/TypeScript
SUPPORTED_EXTENSIONS=.py,.js,.jsx,.ts,.tsx

# Multiple languages
SUPPORTED_EXTENSIONS=.py,.js,.java,.go
```

## Quick Start

### Prerequisites
- Docker & Docker Compose
- OpenAI API key

### Installation

1. Clone repository

2. Set environment variables:
```bash
# Create .env file in project root
echo "OPENAI_API_KEY=your-key-here" > .env
echo "MODEL_NAME=gpt-4-turbo-preview" >> .env
echo "SUPPORTED_EXTENSIONS=.py" >> .env
```

3. Start services:
```bash
docker-compose up --build
```

4. Access the application:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Usage

1. **Upload Repository**: 
   - ZIP your code repository
   - Upload via the web interface
   - Wait for AI feature extraction (may take 10-30 seconds)

2. **Explore Feature Graph**:
   - View high-level features as purple nodes
   - Edges show relationships between features
   - Zoom/pan to explore connections

3. **Drill Into Features**:
   - Click any feature node
   - See related files and functions
   - Click functions to execute with AI-generated args
   - View execution trace graphs

4. **Ask Questions**:
   - "What are the main features of this codebase?"
   - "How do features interact?"
   - "Show me the authentication flow"

## API Endpoints

### POST /upload
Upload a repository ZIP file
```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@your_repo.zip"
```

### POST /query
Query the codebase
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "How does authentication work?"}'
```

### GET /graph
Get current graph visualization data
```bash
curl http://localhost:8000/graph
```

## Graph Representation

### Feature Graph
- **Nodes**: High-level features extracted by LLM (purple)
- **Edges**: Relationships between features (depends_on, uses, extends)

### Function Execution Trace Graph
- **Nodes**: Variables, conditions, loops, function calls
- **Edges**: Data flow and control flow
- **Colors**: 
  - Green: Start/Return
  - Blue: Arguments
  - Purple: Assignments
  - Amber: Conditionals
  - Pink: Loops
  - Cyan: Function Calls 