import ast
import os
from pathlib import Path
from typing import List, Dict, Any
import networkx as nx

class CodeParser:
    """Parse Python code and extract structure"""
    
    def __init__(self):
        # Get supported extensions from env or use defaults (Python only)
        extensions_env = os.getenv('SUPPORTED_EXTENSIONS', '.py')
        self.supported_extensions = [ext.strip() for ext in extensions_env.split(',')]
    
    def parse_repository(self, repo_path: str) -> Dict[str, Any]:
        """Parse entire repository"""
        files_data = []
        
        for root, dirs, files in os.walk(repo_path):
            # Skip common non-code directories
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', 'venv', '.venv']]
            
            for file in files:
                if any(file.endswith(ext) for ext in self.supported_extensions):
                    file_path = os.path.join(root, file)
                    try:
                        file_info = self.parse_file(file_path, repo_path)
                        if file_info:
                            files_data.append(file_info)
                    except Exception as e:
                        print(f"Error parsing {file_path}: {e}")
        
        return {
            'files': files_data,
            'total_files': len(files_data)
        }
    
    def parse_file(self, file_path: str, base_path: str) -> Dict[str, Any]:
        """Parse a single file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        relative_path = os.path.relpath(file_path, base_path)
        
        if file_path.endswith('.py'):
            return self.parse_python_file(content, relative_path)
        elif file_path.endswith(('.js', '.jsx', '.ts', '.tsx')):
            return self.parse_javascript_file(content, relative_path)
        else:
            # For other files, do basic parsing
            return self.parse_generic_file(content, relative_path)
    
    def parse_python_file(self, content: str, file_path: str) -> Dict[str, Any]:
        """Parse Python file using AST"""
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return None
        
        functions = []
        classes = []
        imports = []
        
        # Store content lines for extracting function code
        content_lines = content.split('\n')
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Extract function source code
                function_lines = content_lines[node.lineno - 1:node.end_lineno]
                function_code = '\n'.join(function_lines)
                
                functions.append({
                    'name': node.name,
                    'lineno': node.lineno,
                    'args': [arg.arg for arg in node.args.args],
                    'calls': self._extract_calls(node),
                    'code': function_code  # Store function code
                })
            elif isinstance(node, ast.ClassDef):
                classes.append({
                    'name': node.name,
                    'lineno': node.lineno,
                    'methods': [m.name for m in node.body if isinstance(m, ast.FunctionDef)]
                })
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({'module': alias.name, 'type': 'import'})
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append({'module': node.module, 'type': 'from'})
        
        return {
            'path': file_path,
            'language': 'python',
            'functions': functions,
            'classes': classes,
            'imports': imports
        }
    
    def _extract_calls(self, node) -> List[str]:
        """Extract function calls from AST node"""
        calls = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    calls.append(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    calls.append(child.func.attr)
        return list(set(calls))
    
    def parse_javascript_file(self, content: str, file_path: str) -> Dict[str, Any]:
        """Basic JavaScript/TypeScript parsing (simplified)"""
        import re
        
        # Match function declarations and arrow functions
        functions = re.findall(r'(?:function\s+(\w+)\s*\(|const\s+(\w+)\s*=\s*(?:\([^)]*\)|[^=]+)\s*=>)', content)
        functions = [f[0] or f[1] for f in functions if f[0] or f[1]]
        
        # Match class names
        classes = re.findall(r'class\s+(\w+)', content)
        
        imports = re.findall(r'import\s+.*?from\s+[\'"](.+?)[\'"]', content)
        
        return {
            'path': file_path,
            'language': 'javascript',
            'functions': [{'name': f, 'calls': []} for f in functions],
            'classes': [{'name': c, 'methods': []} for c in classes],
            'imports': [{'module': imp, 'type': 'import'} for imp in imports]
        }
    
    def parse_generic_file(self, content: str, file_path: str) -> Dict[str, Any]:
        """Generic parsing for unsupported languages"""
        import re
        
        # Try to extract function-like patterns
        functions = re.findall(r'(?:def|func|function|fn|fun|public|private|protected)\s+(\w+)\s*\(', content)
        classes = re.findall(r'(?:class|struct|interface|type)\s+(\w+)', content)
        imports = re.findall(r'(?:import|require|include|use)\s+[\'"]?([^\s\'"]+)', content)
        
        return {
            'path': file_path,
            'language': 'generic',
            'functions': [{'name': f, 'calls': []} for f in functions],
            'classes': [{'name': c, 'methods': []} for c in classes],
            'imports': [{'module': imp, 'type': 'import'} for imp in imports]
        }

