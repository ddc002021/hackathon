from typing import Any, Dict, Optional
import ast
import json
import time
import timeout_decorator
from .llm_analyzer import LLMAnalyzer
from .execution_tracer import ExecutionTracer


class FunctionExecutor:
    """Safely execute Python functions with LLM-generated arguments"""
    
    def __init__(self, llm_analyzer: LLMAnalyzer):
        self.llm = llm_analyzer
        self.safe_globals = self._create_safe_environment()
        self.tracer = ExecutionTracer()
    
    def _create_safe_environment(self) -> Dict[str, Any]:
        """Create execution environment with common Python builtins and modules"""
        import hashlib
        import re
        import json as json_module
        from datetime import datetime, timedelta
        from collections import defaultdict, Counter
        
        return {
            '__builtins__': __builtins__,
            # Common modules that are generally safe
            'hashlib': hashlib,
            're': re,
            'json': json_module,
            'datetime': datetime,
            'timedelta': timedelta,
            'defaultdict': defaultdict,
            'Counter': Counter,
        }
    
    def generate_walkthrough_only(
        self,
        function_code: str,
        function_name: str,
        file_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate code walkthrough WITHOUT execution
        
        Args:
            function_code: Source code of the function
            function_name: Name of the function
            file_context: Optional full file content for imports
            
        Returns:
            Dictionary with walkthrough and args
        """
        try:
            # Step 1: Extract function signature
            signature = self._extract_function_signature(function_code)
            
            # Step 2: LLM generates dummy arguments
            args = self._generate_dummy_args(function_code, function_name, signature)
            
            # Step 3: Generate code walkthrough (NO EXECUTION)
            walkthrough = self._generate_walkthrough(function_code, function_name, args, file_context)
            
            # Step 4: Generate execution trace graph (static analysis)
            trace_graph = self.tracer.trace_execution(
                function_code=function_code,
                function_name=function_name,
                args=args,
                file_context=file_context
            )
            
            return {
                'success': True,
                'args': args,
                'walkthrough': walkthrough,
                'executed': False,
                'trace_graph': trace_graph
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'{type(e).__name__}: {str(e)}',
                'executed': False
            }
    
    @timeout_decorator.timeout(5, timeout_exception=TimeoutError)
    def execute_function(
        self, 
        function_code: str, 
        function_name: str,
        file_context: Optional[str] = None,
        repo_files: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Execute a function with LLM-generated arguments
        
        Args:
            function_code: Source code of the function
            function_name: Name of the function to execute
            file_context: Optional full file content for imports
            repo_files: Dict of {filename: content} for cross-file dependencies
            
        Returns:
            Dictionary with execution results
        """
        args = {}
        walkthrough = None
        try:
            # Step 1: Ask LLM if function is safe to execute
            safety_check = self._llm_safety_check(function_code, function_name)
            
            if not safety_check['is_safe']:
                return {
                    'success': False,
                    'error': f"LLM Safety Check Failed: {safety_check['reason']}",
                    'args': {},
                    'safety_check': 'failed'
                }
            
            # Step 2: Extract function signature
            signature = self._extract_function_signature(function_code)
            
            # Step 3: LLM generates dummy arguments
            args = self._generate_dummy_args(function_code, function_name, signature)
            
            # Step 4: Generate code walkthrough (ALWAYS generate, even if execution fails)
            walkthrough = self._generate_walkthrough(function_code, function_name, args, file_context)
            
            # Step 5: Generate execution trace graph
            trace_graph = self.tracer.trace_execution(
                function_code=function_code,
                function_name=function_name,
                args=args,
                file_context=file_context
            )
            
            # Step 6: Execute with full context
            result = self._execute_with_context(function_code, function_name, args, file_context, repo_files)
            
            return {
                'success': True,
                'args': args,
                'result': result['value'],
                'result_type': result['type'],
                'execution_time': result.get('time', 0),
                'safety_check': 'passed',
                'walkthrough': walkthrough,
                'trace_graph': trace_graph
            }
            
        except TimeoutError:
            return {
                'success': False,
                'error': 'Function execution timed out (5 second limit)',
                'args': args,
                'walkthrough': walkthrough  # Include walkthrough even on timeout
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'{type(e).__name__}: {str(e)}',
                'args': args,
                'walkthrough': walkthrough  # Include walkthrough even on error
            }
    
    def _extract_function_signature(self, function_code: str) -> Dict[str, Any]:
        """Extract function parameters and types"""
        try:
            tree = ast.parse(function_code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    params = []
                    for arg in node.args.args:
                        param_info = {
                            'name': arg.arg,
                            'annotation': ast.unparse(arg.annotation) if arg.annotation else None
                        }
                        params.append(param_info)
                    
                    return {
                        'params': params,
                        'has_defaults': len(node.args.defaults) > 0,
                        'return_annotation': ast.unparse(node.returns) if node.returns else None
                    }
            return {'params': [], 'has_defaults': False, 'return_annotation': None}
        except:
            return {'params': [], 'has_defaults': False, 'return_annotation': None}
    
    def _generate_dummy_args(
        self, 
        function_code: str, 
        function_name: str,
        signature: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Use LLM to generate realistic dummy arguments"""
        
        if not signature['params']:
            return {}
        
        params_desc = "\n".join([
            f"- {p['name']}: {p.get('annotation', 'no type hint')}" 
            for p in signature['params']
        ])
        
        prompt = f"""Generate realistic dummy arguments for this Python function.

Function code:
```python
{function_code}
```

Function name: {function_name}
Parameters:
{params_desc}

Requirements:
1. Return ONLY a valid JSON object
2. Keys must match parameter names exactly
3. Values should be realistic examples that would work with the function
4. If a parameter has a type hint, respect it
5. Keep values simple (no complex objects)

Example format: {{"username": "alice", "age": 25, "active": true}}

Return ONLY the JSON object, nothing else:"""
        
        response = self.llm._call_llm(prompt)
        
        # Parse JSON from LLM response
        try:
            # Extract JSON if LLM wrapped it in markdown
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0]
            elif '```' in response:
                response = response.split('```')[1].split('```')[0]
            
            args = json.loads(response.strip())
            return args
        except json.JSONDecodeError:
            # Fallback: generate basic args based on parameter names
            return self._generate_fallback_args(signature['params'])
    
    def _generate_fallback_args(self, params: list) -> Dict[str, Any]:
        """Generate basic fallback arguments if LLM fails"""
        args = {}
        for param in params:
            name = param['name']
            annotation = param.get('annotation', '')
            
            # Simple heuristics based on parameter name
            if 'id' in name.lower():
                args[name] = 1
            elif 'name' in name.lower():
                args[name] = "example"
            elif 'email' in name.lower():
                args[name] = "user@example.com"
            elif 'age' in name.lower():
                args[name] = 25
            elif 'count' in name.lower() or 'num' in name.lower():
                args[name] = 10
            elif 'str' in annotation.lower():
                args[name] = "test"
            elif 'int' in annotation.lower():
                args[name] = 42
            elif 'float' in annotation.lower():
                args[name] = 3.14
            elif 'bool' in annotation.lower():
                args[name] = True
            elif 'list' in annotation.lower():
                args[name] = [1, 2, 3]
            elif 'dict' in annotation.lower():
                args[name] = {"key": "value"}
            else:
                args[name] = None
        
        return args
    
    def _llm_safety_check(self, function_code: str, function_name: str) -> Dict[str, Any]:
        """Use LLM to determine if function is safe to execute"""
        
        prompt = f"""Analyze this Python function and determine if it's safe to execute in a demo/testing environment.

Function name: {function_name}

Function code:
```python
{function_code}
```

Determine if this function is SAFE to execute. Consider:
- Does it try to access the file system (open, write, delete files)?
- Does it try to make network requests (socket, requests, urllib)?
- Does it try to execute system commands (os.system, subprocess)?
- Does it try to modify system state in dangerous ways?
- Does it contain infinite loops or excessive resource usage?

Simple computational functions, string manipulation, math operations, and data processing are SAFE.
Functions that interact with external systems (file I/O, network, system commands) are UNSAFE.

Respond with ONLY a JSON object:
{{"is_safe": true/false, "reason": "brief explanation"}}

Return ONLY the JSON object:"""
        
        response = self.llm._call_llm(prompt)
        
        try:
            # Extract JSON from response
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0]
            elif '```' in response:
                response = response.split('```')[1].split('```')[0]
            
            result = json.loads(response.strip())
            return {
                'is_safe': result.get('is_safe', False),
                'reason': result.get('reason', 'No reason provided')
            }
        except json.JSONDecodeError:
            # If LLM doesn't return valid JSON, be conservative
            return {
                'is_safe': True,  # Allow execution by default for demo
                'reason': 'Could not parse LLM response, allowing execution'
            }
    
    def _generate_walkthrough(
        self,
        function_code: str,
        function_name: str,
        args: Dict[str, Any],
        file_context: Optional[str]
    ) -> str:
        """Generate LLM walkthrough of code execution"""
        
        context_section = ""
        if file_context:
            context_section = f"\nFile Context (other functions/classes in same file):\n```python\n{file_context[:500]}...\n```"
        
        prompt = f"""You are a code execution analyzer. Walk through this function line by line and explain what happens when executed with the given arguments.

Function:
```python
{function_code}
```

Arguments: {json.dumps(args)}
{context_section}

Provide a BRIEF step-by-step walkthrough:
1. Start with "Function called with arguments: ..."
2. For each significant line, explain what it does and intermediate values
3. End with "Expected return value: ..."

Keep it concise and focused on the execution flow. Max 5-7 steps."""
        
        response = self.llm._call_llm(prompt)
        return response.strip()
    
    def _execute_with_context(
        self, 
        function_code: str, 
        function_name: str, 
        args: Dict[str, Any],
        file_context: Optional[str],
        repo_files: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Execute function with full file context and cross-file dependencies"""
        
        # Prepare execution context
        exec_globals = self.safe_globals.copy()
        
        # Load cross-file dependencies if provided
        if repo_files:
            for filename, content in repo_files.items():
                try:
                    # Execute each file to load its functions/classes
                    exec(content, exec_globals)
                except Exception as e:
                    # Skip files that fail to execute
                    pass
        
        # If file context provided, execute the entire file to get all dependencies
        if file_context:
            try:
                # Execute the full file context to load all helper functions/classes
                exec(file_context, exec_globals)
            except Exception as e:
                # If full context fails, try just executing the function
                pass
        
        # Execute the function definition (may overwrite if already in context)
        exec(function_code, exec_globals)
        
        # Get the function object
        func = exec_globals[function_name]
        
        # Execute the function with timing
        start_time = time.time()
        result = func(**args)
        execution_time = time.time() - start_time
        
        return {
            'value': str(result),  # Convert to string for JSON serialization
            'type': type(result).__name__,
            'time': round(execution_time, 4)
        }

