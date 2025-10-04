"""
Feature Extractor - Extract high-level features from codebase using LLM
"""

import json
from typing import Dict, Any, List
from pathlib import Path
from .llm_analyzer import LLMAnalyzer
import logging

logger = logging.getLogger(__name__)


class FeatureExtractor:
    """Extract semantic features from code repository"""
    
    def __init__(self, llm_analyzer: LLMAnalyzer):
        self.llm = llm_analyzer
    
    def extract_features(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract features from parsed repository
        
        Returns:
            {
                'features': [
                    {
                        'id': 'feat_1',
                        'name': 'User Authentication',
                        'description': '...',
                        'files': ['auth.py', 'user.py'],
                        'functions': ['login', 'logout', 'verify_token']
                    }
                ],
                'relationships': [
                    {
                        'source': 'feat_1',
                        'target': 'feat_2',
                        'type': 'depends_on',
                        'description': 'Auth depends on Database',
                        'confidence': 95,
                        'evidence': 'auth.py imports database'
                    }
                ]
            }
        """
        logger.info("Extracting features from codebase...")
        
        # Build codebase summary
        summary = self._build_codebase_summary(parsed_data)
        
        # Use LLM to extract features
        features = self._llm_extract_features(summary, parsed_data)
        
        # Extract relationships between features WITH code context
        relationships = self._extract_relationships(features, parsed_data)
        
        logger.info(f"Extracted {len(features)} features with {len(relationships)} relationships")
        
        return {
            'features': features,
            'relationships': relationships
        }
    
    def _build_codebase_summary(self, parsed_data: Dict[str, Any]) -> str:
        """Build a concise summary of the codebase"""
        lines = ["# Codebase Structure\n"]
        
        for file_data in parsed_data['files'][:20]:  # Limit to first 20 files
            file_path = file_data['path']
            lines.append(f"\n## File: {file_path}")
            
            if file_data['classes']:
                lines.append("Classes: " + ", ".join([c['name'] for c in file_data['classes']]))
            
            if file_data['functions']:
                func_names = [f['name'] for f in file_data['functions'][:10]]
                lines.append("Functions: " + ", ".join(func_names))
            
            if file_data['imports']:
                imp_names = [i['module'] for i in file_data['imports'][:5]]
                lines.append("Imports: " + ", ".join(imp_names))
        
        return "\n".join(lines)
    
    def _llm_extract_features(self, summary: str, parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Use LLM to identify features"""
        
        prompt = f"""Analyze this codebase and identify the main features/functionalities.

{summary}

Identify 5-10 high-level features that this codebase implements. For each feature:
1. Give it a clear name (e.g., "User Authentication", "Data Processing", "API Endpoints")
2. Describe what it does in one sentence
3. List which files are primarily responsible for this feature
4. List key function names involved

Return ONLY a JSON array of features:
[
  {{
    "name": "Feature Name",
    "description": "What this feature does",
    "files": ["file1.py", "file2.py"],
    "functions": ["func1", "func2"]
  }}
]

Return ONLY valid JSON, nothing else:"""
        
        try:
            response = self.llm._call_llm(prompt, max_tokens=2000)
            
            # Extract JSON
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0]
            elif '```' in response:
                response = response.split('```')[1].split('```')[0]
            
            features_data = json.loads(response.strip())
            
            # Format features with IDs
            features = []
            for idx, feat in enumerate(features_data):
                features.append({
                    'id': f'feature_{idx}',
                    'name': feat.get('name', f'Feature {idx}'),
                    'description': feat.get('description', ''),
                    'files': feat.get('files', []),
                    'functions': feat.get('functions', [])
                })
            
            return features
            
        except Exception as e:
            logger.error(f"LLM feature extraction failed: {e}")
            # Fallback: Create features based on file structure
            return self._fallback_feature_extraction(parsed_data)
    
    def _fallback_feature_extraction(self, parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback feature extraction based on file names and structure"""
        logger.info("Using fallback feature extraction")
        
        features = []
        feature_map = {}
        
        for file_data in parsed_data['files']:
            file_path = file_data['path']
            file_name = Path(file_path).stem
            
            # Group by filename patterns
            if 'auth' in file_name.lower():
                key = 'authentication'
            elif 'database' in file_name.lower() or 'db' in file_name.lower():
                key = 'database'
            elif 'api' in file_name.lower() or 'endpoint' in file_name.lower():
                key = 'api'
            elif 'test' in file_name.lower():
                key = 'testing'
            elif 'main' in file_name.lower():
                key = 'core'
            else:
                key = file_name.lower()
            
            if key not in feature_map:
                feature_map[key] = {
                    'files': [],
                    'functions': []
                }
            
            feature_map[key]['files'].append(file_path)
            feature_map[key]['functions'].extend([f['name'] for f in file_data['functions'][:5]])
        
        # Convert to feature list
        for idx, (key, data) in enumerate(feature_map.items()):
            features.append({
                'id': f'feature_{idx}',
                'name': key.replace('_', ' ').title(),
                'description': f'Functionality related to {key}',
                'files': data['files'],
                'functions': data['functions'][:10]
            })
        
        return features
    
    def _extract_relationships(self, features: List[Dict[str, Any]], parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract relationships between features using LLM WITH code context"""
        
        if len(features) < 2:
            return []
        
        # Build detailed evidence from actual code
        code_evidence = []
        for feature in features:
            evidence = f"\n### {feature['id']}: {feature['name']}"
            evidence += f"\nDescription: {feature['description']}"
            evidence += f"\nFiles: {', '.join(feature['files'][:3])}"
            evidence += f"\nFunctions: {', '.join(feature['functions'][:8])}"
            
            # Add import and call information from actual code
            imports_found = set()
            calls_found = set()
            
            for file_path in feature['files'][:3]:  # First 3 files
                file_data = next((f for f in parsed_data['files'] if f['path'] == file_path), None)
                if file_data:
                    # Collect imports
                    for imp in file_data['imports'][:5]:
                        imports_found.add(imp['module'])
                    
                    # Collect function calls
                    for func in file_data['functions'][:3]:
                        for call in func.get('calls', [])[:3]:
                            calls_found.add(call)
            
            if imports_found:
                evidence += f"\nImports: {', '.join(list(imports_found)[:5])}"
            if calls_found:
                evidence += f"\nCalls: {', '.join(list(calls_found)[:5])}"
            
            code_evidence.append(evidence)
        
        prompt = f"""Analyze this codebase to identify relationships between features using ACTUAL CODE EVIDENCE.

FEATURES WITH CODE CONTEXT:
{chr(10).join(code_evidence)}

Your task: Identify relationships by examining imports, function calls, and code structure.

For each relationship provide:
1. source: feature_id that depends/uses another
2. target: feature_id being depended on/used
3. type: depends_on (critical), uses (optional), extends (enhancement), or enables (activates)
4. confidence: 0-100 (based on code evidence strength)
5. evidence: What code proves this relationship (be specific)
6. description: Human-readable explanation

Return ONLY a JSON array:
[
  {{
    "source": "feature_0",
    "target": "feature_1",
    "type": "depends_on",
    "confidence": 95,
    "evidence": "feature_0 imports database module from feature_1",
    "description": "Authentication requires database for user verification"
  }}
]

Return ONLY valid JSON:"""
        
        try:
            response = self.llm._call_llm(prompt, max_tokens=1500)
            
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0]
            elif '```' in response:
                response = response.split('```')[1].split('```')[0]
            
            relationships = json.loads(response.strip())
            
            # Ensure all relationships have required fields
            for rel in relationships:
                rel.setdefault('confidence', 70)
                rel.setdefault('evidence', 'Code analysis')
                rel.setdefault('description', rel.get('type', 'related'))
            
            return relationships
            
        except Exception as e:
            logger.error(f"Relationship extraction failed: {e}")
            # Fallback: Create basic relationships
            return self._fallback_relationships(features, parsed_data)
    
    def _fallback_relationships(self, features: List[Dict[str, Any]], parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create basic relationships based on code analysis"""
        relationships = []
        
        # Build function to feature mapping
        func_to_feature = {}
        for feature in features:
            for func_name in feature['functions']:
                func_to_feature[func_name] = feature['id']
        
        # Analyze actual imports and calls
        for feat1 in features:
            for file_path in feat1['files']:
                file_data = next((f for f in parsed_data['files'] if f['path'] == file_path), None)
                if not file_data:
                    continue
                
                # Check imports
                for imp in file_data['imports']:
                    # See if this import belongs to another feature
                    for feat2 in features:
                        if feat1['id'] == feat2['id']:
                            continue
                        if any(imp['module'] in f for f in feat2['files']):
                            relationships.append({
                                'source': feat1['id'],
                                'target': feat2['id'],
                                'type': 'imports',
                                'confidence': 85,
                                'evidence': f'{file_path} imports {imp["module"]}',
                                'description': f'{feat1["name"]} imports from {feat2["name"]}'
                            })
                
                # Check function calls
                for func in file_data['functions']:
                    for call in func.get('calls', []):
                        if call in func_to_feature:
                            target_feat = func_to_feature[call]
                            if target_feat != feat1['id']:
                                relationships.append({
                                    'source': feat1['id'],
                                    'target': target_feat,
                                    'type': 'calls',
                                    'confidence': 90,
                                    'evidence': f'{func["name"]}() calls {call}()',
                                    'description': f'{feat1["name"]} uses {call}() function'
                                })
        
        # Remove duplicates
        seen = set()
        unique_rels = []
        for rel in relationships:
            key = (rel['source'], rel['target'], rel['type'])
            if key not in seen:
                seen.add(key)
                unique_rels.append(rel)
        
        return unique_rels[:15]  # Limit to 15 relationships

