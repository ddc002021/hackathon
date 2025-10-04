"""
Execution Trace Graph Generator
Converts function execution into a graph representation showing:
- Variable states (nodes)
- Data flow (edges)
- Control flow (edges)
- Function calls (nodes)
"""

import ast
import sys
import json
from typing import Any, Dict, List, Optional
from collections import defaultdict


class ExecutionTracer:
    """Trace function execution and build a graph representation"""
    
    def __init__(self):
        self.nodes = []
        self.edges = []
        self.node_counter = 0
        self.execution_order = []
        self.step_counter = 1
        
    def trace_execution(
        self, 
        function_code: str, 
        function_name: str, 
        args: Dict[str, Any],
        file_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute function while building execution trace graph
        
        Returns:
            Dict with nodes, edges, and execution sequence
        """
        # Reset state
        self.nodes = []
        self.edges = []
        self.node_counter = 0
        self.execution_order = []
        self.step_counter = 1
        
        # Create start node
        args_display = ', '.join([f'{k}={v}' for k, v in args.items()])
        start_node_id = self._create_node(
            node_type='start',
            label=f'START: {function_name}({args_display})',
            value='Function begins execution',
            metadata={'function_name': function_name, 'step': 0}
        )
        
        # Track last node for sequential flow
        last_node_id = start_node_id
        
        # Parse and instrument the code
        try:
            tree = ast.parse(function_code)
            instrumented_code = self._instrument_code(tree, function_name)
            
            # Execute and trace
            trace_context = self._execute_with_tracing(
                instrumented_code, 
                function_name, 
                args,
                file_context,
                last_node_id
            )
            
            # Create result node
            if trace_context['result'] is not None:
                result_node_id = self._create_node(
                    node_type='return',
                    label=f'RETURN',
                    value=f'Returns: {str(trace_context["result"])}',
                    metadata={'result': str(trace_context['result']), 'step': self.step_counter}
                )
                
                # Connect last operation to result
                if len(self.execution_order) > 0:
                    last_node = self.execution_order[-1]
                    self._create_edge(last_node, result_node_id, 'final result')
            
            return {
                'nodes': self.nodes,
                'edges': self.edges,
                'execution_order': self.execution_order,
                'trace_log': trace_context.get('log', [])
            }
            
        except Exception as e:
            # Create error node
            error_node_id = self._create_node(
                node_type='error',
                label='Error',
                value=str(e),
                metadata={'error': str(e)}
            )
            self._create_edge(start_node_id, error_node_id, 'error')
            
            return {
                'nodes': self.nodes,
                'edges': self.edges,
                'execution_order': self.execution_order,
                'error': str(e)
            }
    
    def _instrument_code(self, tree: ast.AST, function_name: str) -> str:
        """Add tracing instrumentation to code (simplified version)"""
        # For simplicity, return original code
        # In a full implementation, we'd insert trace calls
        return ast.unparse(tree)
    
    def _execute_with_tracing(
        self,
        code: str,
        function_name: str,
        args: Dict[str, Any],
        file_context: Optional[str],
        start_node_id: str
    ) -> Dict[str, Any]:
        """Execute code and build trace graph"""
        
        # Create execution environment
        exec_globals = {
            '__builtins__': __builtins__,
            '_trace': self._trace_event
        }
        
        # Load file context
        if file_context:
            try:
                exec(file_context, exec_globals)
            except:
                pass
        
        # Execute function code
        exec(code, exec_globals)
        func = exec_globals[function_name]
        
        # Analyze function to build graph
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == function_name:
                self._trace_function_body(node, args, start_node_id)
                break
        
        # Execute function
        result = func(**args)
        
        return {
            'result': result,
            'log': []
        }
    
    def _trace_function_body(self, func_node: ast.FunctionDef, args: Dict[str, Any], start_node_id: str):
        """Build graph from function body AST"""
        variables = {}  # Track variable node IDs
        last_node_id = start_node_id
        
        for stmt in func_node.body:
            last_node_id = self._trace_statement(stmt, variables, last_node_id)
    
    def _trace_statement(self, stmt: ast.AST, variables: Dict[str, Any], last_node_id: str):
        """Trace a single statement and add to graph. Returns the last node ID."""
        
        if isinstance(stmt, ast.Assign):
            # Variable assignment: x = expr
            for target in stmt.targets:
                if isinstance(target, ast.Name):
                    var_name = target.id
                    expr = ast.unparse(stmt.value)
                    
                    # Create assignment node with clear description
                    assign_node_id = self._create_node(
                        node_type='assignment',
                        label=f'Step {self.step_counter}: Assign {var_name}',
                        value=f'{var_name} = {expr}',
                        metadata={
                            'variable': var_name,
                            'expression': expr,
                            'step': self.step_counter
                        }
                    )
                    self.step_counter += 1
                    
                    # Connect to previous step
                    self._create_edge(last_node_id, assign_node_id, 'then')
                    
                    variables[var_name] = assign_node_id
                    self.execution_order.append(assign_node_id)
                    return assign_node_id
            return last_node_id
        
        elif isinstance(stmt, ast.Return):
            # Return statement
            return_expr = ast.unparse(stmt.value) if stmt.value else 'None'
            return_node_id = self._create_node(
                node_type='operation',
                label=f'Step {self.step_counter}: Compute Return',
                value=f'Calculate: {return_expr}',
                metadata={'expression': return_expr, 'step': self.step_counter}
            )
            self.step_counter += 1
            
            # Connect to previous step
            self._create_edge(last_node_id, return_node_id, 'then')
            
            self.execution_order.append(return_node_id)
            return return_node_id
        
        elif isinstance(stmt, ast.If):
            # Conditional branch
            condition_expr = ast.unparse(stmt.test)
            if_node_id = self._create_node(
                node_type='condition',
                label=f'Step {self.step_counter}: Decision',
                value=f'If {condition_expr}?',
                metadata={'condition': condition_expr, 'step': self.step_counter}
            )
            self.step_counter += 1
            
            # Connect to previous step
            self._create_edge(last_node_id, if_node_id, 'then')
            
            self.execution_order.append(if_node_id)
            current_node = if_node_id
            
            # Trace body (simplified - assume true branch)
            for body_stmt in stmt.body:
                current_node = self._trace_statement(body_stmt, variables, current_node)
            
            return current_node
        
        elif isinstance(stmt, (ast.For, ast.While)):
            # Loop
            loop_type = 'for' if isinstance(stmt, ast.For) else 'while'
            loop_desc = ast.unparse(stmt).split(':')[0]
            
            loop_node_id = self._create_node(
                node_type='loop',
                label=f'Step {self.step_counter}: Loop',
                value=f'{loop_desc}',
                metadata={'loop_type': loop_type, 'step': self.step_counter}
            )
            self.step_counter += 1
            
            # Connect to previous step
            self._create_edge(last_node_id, loop_node_id, 'then')
            
            self.execution_order.append(loop_node_id)
            current_node = loop_node_id
            
            # Trace body (simplified - one iteration)
            for body_stmt in stmt.body:
                current_node = self._trace_statement(body_stmt, variables, current_node)
            
            return current_node
        
        elif isinstance(stmt, ast.Expr):
            # Expression statement (e.g., function call)
            if isinstance(stmt.value, ast.Call):
                call_expr = ast.unparse(stmt.value)
                call_node_id = self._create_node(
                    node_type='call',
                    label=f'Step {self.step_counter}: Call',
                    value=call_expr,
                    metadata={'expression': call_expr, 'step': self.step_counter}
                )
                self.step_counter += 1
                
                # Connect to previous step
                self._create_edge(last_node_id, call_node_id, 'then')
                
                self.execution_order.append(call_node_id)
                return call_node_id
        
        return last_node_id
    
    def _find_dependencies(self, node: ast.AST) -> List[str]:
        """Find all variable names used in an expression"""
        deps = []
        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                deps.append(child.id)
        return deps
    
    def _trace_event(self, event_type: str, data: Any):
        """Callback for runtime tracing"""
        pass
    
    def _create_node(
        self, 
        node_type: str, 
        label: str, 
        value: Any,
        metadata: Dict = None
    ) -> str:
        """Create a node in the execution graph"""
        node_id = f'node_{self.node_counter}'
        self.node_counter += 1
        
        self.nodes.append({
            'id': node_id,
            'type': node_type,
            'label': label,
            'value': value,
            'metadata': metadata or {}
        })
        
        return node_id
    
    def _create_edge(self, source: str, target: str, edge_type: str):
        """Create an edge in the execution graph"""
        self.edges.append({
            'source': source,
            'target': target,
            'type': edge_type
        })

