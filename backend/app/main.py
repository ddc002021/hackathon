from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import shutil
import tempfile
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

from .models import QueryRequest, QueryResponse, GraphResponse, FeatureDetailResponse
from .code_parser import CodeParser
from .graph_builder import GraphBuilder
from .llm_analyzer import LLMAnalyzer
from .query_engine import QueryEngine
from .graph_query_engine import GraphQueryEngine  # NEW: Graph-powered query engine
from .function_executor import FunctionExecutor
from .feature_extractor import FeatureExtractor
from .paper_parser import PaperParser
from .cross_modal_mapper import CrossModalMapper
from .llm_paper_extractor import LLMPaperExtractor

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="CodeBase Cartographer")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state (for hackathon simplicity - use Redis for production)
current_graph = None
current_query_engine = None
function_executor = None
uploaded_repo_path = None
uploaded_paper_path = None
current_paper_data = None
parser = CodeParser()
graph_builder = GraphBuilder()
llm_analyzer = LLMAnalyzer()
feature_extractor = FeatureExtractor(llm_analyzer)
paper_parser = PaperParser()
cross_modal_mapper = CrossModalMapper(llm_analyzer)
llm_paper_extractor = LLMPaperExtractor(llm_analyzer)

# Configuration: Choose extraction method
# "regex" = old rule-based parser
# "llm" = new LLM-first context-aware extraction (RECOMMENDED)
PAPER_EXTRACTION_METHOD = os.getenv('PAPER_EXTRACTION_METHOD', 'llm')

@app.get("/")
async def root():
    return {"message": "CodeBase Cartographer API"}

@app.get("/health")
async def health():
    return {"status": "healthy", "graph_loaded": current_graph is not None}

@app.post("/upload-paper")
async def upload_paper(file: UploadFile = File(...)):
    """Upload and parse a research paper (PDF or TXT)"""
    global uploaded_paper_path, current_paper_data, current_graph, graph_builder
    
    logger.info(f"Received paper: {file.filename}")
    
    # Create persistent temp directory
    persistent_dir = Path(tempfile.gettempdir()) / "codebase_cartographer"
    persistent_dir.mkdir(exist_ok=True)
    
    # Save uploaded file
    paper_path = persistent_dir / file.filename
    with open(paper_path, 'wb') as buffer:
        shutil.copyfileobj(file.file, buffer)
    logger.info(f"Saved paper to temp location")
    
    # Store the paper path globally
    uploaded_paper_path = paper_path
    
    # Parse paper
    logger.info("Parsing paper...")
    current_paper_data = paper_parser.parse_paper(str(paper_path))
    logger.info(f"Parsed paper: {current_paper_data['total_sections']} sections")
    
    # Log paper sections
    logger.info("=" * 80)
    logger.info("PAPER SECTIONS EXTRACTED:")
    for idx, section in enumerate(current_paper_data.get('sections', [])):
        logger.info(f"\n  Section {idx}: {section['title']}")
        logger.info(f"    Content length: {len(section.get('content', ''))} chars")
    logger.info("=" * 80)
    
    # Only build cross-modal graph if we already have code
    if current_graph is not None and graph_builder.parsed_data:
        logger.info("Creating cross-modal graph...")
        logger.info(f"   Current graph has {current_graph.number_of_nodes()} nodes")
        
        # Extract features for cross-modal mapping
        code_features = [
            {
                'id': node_id,
                **data
            }
            for node_id, data in current_graph.nodes(data=True)
            if data.get('modality') == 'code'
        ]
        
        logger.info(f"   Extracted {len(code_features)} code features")
        
        # Choose extraction method based on config
        if PAPER_EXTRACTION_METHOD == 'llm':
            logger.info("Using LLM-First Context-Aware Extraction")
            
            # Extract raw text from paper
            paper_text = llm_paper_extractor.extract_paper_text(str(paper_path))
            
            # LLM extracts relevant sections AND creates mappings in one step
            cross_modal_data = llm_paper_extractor.extract_with_code_context(
                paper_text,
                code_features
            )
            
            # Add code_nodes to result
            cross_modal_data['code_nodes'] = code_features
            
            logger.info(f"   LLM extracted {len(cross_modal_data['paper_nodes'])} relevant sections")
            logger.info(f"   Created {len(cross_modal_data['cross_modal_edges'])} cross-modal edges")
        else:
            logger.info("Using Traditional Regex-Based Parsing")
            logger.info(f"   Paper has {len(current_paper_data['sections'])} sections")
            
            # Old approach: parse then map
            cross_modal_data = cross_modal_mapper.map_paper_to_code(
                current_paper_data,
                code_features
            )
        
        # Rebuild graph with paper + code + paper edges
        current_graph = graph_builder.build_unified_graph(
            cross_modal_data['paper_nodes'],
            code_features,
            cross_modal_data['cross_modal_edges'],
            paper_edges=cross_modal_data.get('paper_edges', [])
        )
        
        logger.info(f"   Unified graph has {current_graph.number_of_nodes()} nodes, {current_graph.number_of_edges()} edges")
        
        viz_data = graph_builder.export_for_visualization()
        stats = graph_builder.get_graph_stats()
        stats['has_paper'] = True
        stats['extraction_method'] = PAPER_EXTRACTION_METHOD
        
        logger.info(f"Returning {len(viz_data['nodes'])} nodes, {len(viz_data['edges'])} edges to frontend")
        
        return {
            'nodes': viz_data['nodes'],
            'edges': viz_data['edges'],
            'stats': stats,
            'message': f'Paper uploaded and mapped to code using {PAPER_EXTRACTION_METHOD.upper()} extraction!'
        }
    
    logger.info("Paper uploaded but no code yet. Waiting for code upload to build cross-modal graph.")
    
    return {
        'message': 'Paper uploaded successfully! Please upload code repository to see cross-modal mappings.',
        'sections': current_paper_data['total_sections'],
        'paper_only': True
    }

@app.post("/upload", response_model=GraphResponse)
async def upload_repository(file: UploadFile = File(...)):
    """Upload and parse a repository ZIP file"""
    global current_graph, current_query_engine, uploaded_repo_path, current_paper_data
    
    logger.info(f"Received file: {file.filename}")
    
    # Create persistent temp directory for this session
    persistent_dir = Path(tempfile.gettempdir()) / "codebase_cartographer"
    persistent_dir.mkdir(exist_ok=True)
    
    # Save uploaded file
    zip_path = persistent_dir / file.filename
    with open(zip_path, 'wb') as buffer:
        shutil.copyfileobj(file.file, buffer)
    logger.info(f"Saved ZIP to temp location")
    
    # Extract ZIP
    import zipfile
    extract_dir = persistent_dir / "repo"
    if extract_dir.exists():
        shutil.rmtree(extract_dir)
    extract_dir.mkdir()
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    logger.info(f"Extracted ZIP contents")
    
    # Find the actual repo directory
    repo_dirs = [d for d in extract_dir.iterdir() if d.is_dir()]
    actual_repo = repo_dirs[0] if repo_dirs else extract_dir
    logger.info(f"Found repo directory: {actual_repo}")
    
    # Store the repo path globally
    uploaded_repo_path = actual_repo
    
    # Parse repository
    logger.info("Starting code parsing...")
    parsed_data = parser.parse_repository(str(actual_repo))
    logger.info(f"Parsed {parsed_data['total_files']} files")
    
    # Extract features
    logger.info("Extracting features...")
    feature_data = feature_extractor.extract_features(parsed_data)
    logger.info(f"Extracted {len(feature_data['features'])} features")
    
    # Build feature graph
    logger.info("Building feature graph...")
    current_graph = graph_builder.build_graph(feature_data, parsed_data)
    stats = graph_builder.get_graph_stats()
    logger.info(f"Built graph: {stats['total_nodes']} nodes, {stats['total_edges']} edges")
    
    # Initialize graph-powered query engine
    current_query_engine = GraphQueryEngine(current_graph, llm_analyzer)
    logger.info("Graph-powered query engine initialized")
    
    # If we have paper data, create cross-modal mappings
    if current_paper_data and uploaded_paper_path:
        logger.info("Creating cross-modal graph with existing paper...")
        logger.info(f"   Code graph has {current_graph.number_of_nodes()} nodes")
        
        code_features = [
            {
                'id': node_id,
                **data
            }
            for node_id, data in current_graph.nodes(data=True)
            if data.get('modality') == 'code'
        ]
        
        logger.info(f"   Extracted {len(code_features)} code features")
        
        # Choose extraction method based on config
        if PAPER_EXTRACTION_METHOD == 'llm':
            logger.info("Using LLM-First Context-Aware Extraction")
            
            # Extract raw text from paper
            paper_text = llm_paper_extractor.extract_paper_text(str(uploaded_paper_path))
            
            # LLM extracts relevant sections AND creates mappings in one step
            cross_modal_data = llm_paper_extractor.extract_with_code_context(
                paper_text,
                code_features
            )
            
            # Add code_nodes to result
            cross_modal_data['code_nodes'] = code_features
            
            logger.info(f"   LLM extracted {len(cross_modal_data['paper_nodes'])} relevant sections")
            logger.info(f"   Created {len(cross_modal_data['cross_modal_edges'])} cross-modal edges")
        else:
            logger.info("Using Traditional Regex-Based Parsing")
            logger.info(f"   Paper has {len(current_paper_data['sections'])} sections")
            
            # Old approach: parse then map
            cross_modal_data = cross_modal_mapper.map_paper_to_code(
                current_paper_data,
                code_features
            )
        
        # Rebuild graph with paper + code + paper edges
        current_graph = graph_builder.build_unified_graph(
            cross_modal_data['paper_nodes'],
            code_features,
            cross_modal_data['cross_modal_edges'],
            paper_edges=cross_modal_data.get('paper_edges', [])
        )
        
        logger.info(f"   Unified graph has {current_graph.number_of_nodes()} nodes, {current_graph.number_of_edges()} edges")
        
        stats = graph_builder.get_graph_stats()
        stats['has_paper'] = True
        stats['extraction_method'] = PAPER_EXTRACTION_METHOD
        
        logger.info(f"Cross-modal graph created using {PAPER_EXTRACTION_METHOD.upper()} extraction")
    
    # Get visualization data
    logger.info("Generating visualization...")
    viz_data = graph_builder.export_for_visualization()
    logger.info("Upload complete!")
    
    return GraphResponse(
        nodes=viz_data['nodes'],
        edges=viz_data['edges'],
        stats=stats
    )

@app.post("/query", response_model=QueryResponse)
async def query_codebase(request: QueryRequest):
    """Process natural language query about the codebase using graph algorithms"""
    global current_query_engine
    
    if current_query_engine is None:
        raise HTTPException(status_code=400, detail="No repository uploaded yet")
    
    logger.info(f"Processing query: {request.query}")
    result = current_query_engine.process_query(request.query)
    logger.info(f"Query complete ({result.get('query_type', 'unknown')}), highlighting {len(result['highlighted_nodes'])} nodes")
    
    return QueryResponse(
        query=result['query'],
        answer=result['answer'],
        intent=result.get('intent', {}),
        highlighted_nodes=result['highlighted_nodes'],
        query_type=result.get('query_type'),
        graph_evidence=result.get('graph_evidence'),
        paths=result.get('paths', [])
    )

@app.get("/feature/{feature_id}", response_model=FeatureDetailResponse)
async def get_feature_details(feature_id: str):
    """Get detailed information about a feature"""
    global graph_builder, current_graph
    
    if current_graph is None:
        raise HTTPException(status_code=400, detail="No repository uploaded yet")
    
    logger.info(f"Getting details for feature: {feature_id}")
    
    details = graph_builder.get_feature_details(feature_id)
    
    if not details:
        raise HTTPException(status_code=404, detail="Feature not found")
    
    return FeatureDetailResponse(**details)

@app.post("/walkthrough-function")
async def walkthrough_function(request: dict):
    """Generate code walkthrough WITHOUT execution"""
    global function_executor, llm_analyzer, uploaded_repo_path
    
    logger.info(f"Received walkthrough request: {list(request.keys())}")
    
    # Initialize executor if needed
    if function_executor is None:
        function_executor = FunctionExecutor(llm_analyzer)
        logger.info("Function executor initialized")
    
    function_name = request.get('function_name')
    function_code = request.get('function_code')
    file_path = request.get('file_path')
    
    logger.info(f"function_name: {function_name}")
    logger.info(f"function_code length: {len(function_code) if function_code else 0}")
    
    if not function_name:
        logger.error("Missing function_name")
        raise HTTPException(status_code=400, detail="function_name is required")
    
    if not function_code:
        logger.error("Missing function_code")
        raise HTTPException(status_code=400, detail="function_code is required")
    
    # Try to read the full file for context
    file_context = None
    
    if uploaded_repo_path and file_path:
        try:
            # Read the current file
            full_file_path = uploaded_repo_path / file_path
            if full_file_path.exists():
                with open(full_file_path, 'r', encoding='utf-8') as f:
                    file_context = f.read()
                logger.info(f"Loaded file context: {file_path} ({len(file_context)} chars)")
        except Exception as e:
            logger.warning(f"Could not load file context: {e}")
    
    try:
        logger.info(f"Generating walkthrough for: {function_name}")
        result = function_executor.generate_walkthrough_only(
            function_code=function_code,
            function_name=function_name,
            file_context=file_context
        )
        logger.info(f"Walkthrough generated: success={result['success']}")
        return result
        
    except Exception as e:
        logger.error(f"Walkthrough error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/execute-function")
async def execute_function(request: dict):
    """Execute a function with LLM-generated arguments"""
    global function_executor, llm_analyzer, uploaded_repo_path
    
    logger.info(f"Received execute request: {list(request.keys())}")
    
    # Initialize executor if needed
    if function_executor is None:
        function_executor = FunctionExecutor(llm_analyzer)
        logger.info("Function executor initialized")
    
    function_name = request.get('function_name')
    function_code = request.get('function_code')
    file_path = request.get('file_path')
    
    logger.info(f"function_name: {function_name}")
    logger.info(f"function_code length: {len(function_code) if function_code else 0}")
    
    if not function_name:
        logger.error("Missing function_name")
        raise HTTPException(status_code=400, detail="function_name is required")
    
    if not function_code:
        logger.error("Missing function_code")
        raise HTTPException(status_code=400, detail="function_code is required")
    
    # Try to read the full file for context
    file_context = None
    repo_files = {}
    
    if uploaded_repo_path and file_path:
        try:
            # Read the current file
            full_file_path = uploaded_repo_path / file_path
            if full_file_path.exists():
                with open(full_file_path, 'r', encoding='utf-8') as f:
                    file_context = f.read()
                logger.info(f"Loaded file context: {file_path} ({len(file_context)} chars)")
            
            # Load all Python files in the repo for cross-file dependencies
            for py_file in uploaded_repo_path.rglob('*.py'):
                if py_file.name != '__pycache__':
                    try:
                        with open(py_file, 'r', encoding='utf-8') as f:
                            relative_path = py_file.relative_to(uploaded_repo_path)
                            repo_files[str(relative_path)] = f.read()
                    except:
                        pass
            
            logger.info(f"Loaded {len(repo_files)} repository files")
            
        except Exception as e:
            logger.warning(f"Could not load file context: {e}")
    
    try:
        logger.info(f"Executing function: {function_name}")
        result = function_executor.execute_function(
            function_code=function_code,
            function_name=function_name,
            file_context=file_context,
            repo_files=repo_files
        )
        logger.info(f"Function executed: success={result['success']}")
        return result
        
    except Exception as e:
        logger.error(f"Execution error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

