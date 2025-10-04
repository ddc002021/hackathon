import os
from typing import Dict, Any, List
from openai import OpenAI

class LLMAnalyzer:
    """LLM integration for graph enrichment and queries"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = os.getenv('MODEL_NAME', 'gpt-4-turbo-preview')
    
    def answer_query(self, query: str, relevant_subgraph: Dict[str, Any]) -> str:
        """Answer natural language query about the codebase"""
        prompt = f"""
You are a code architecture expert. A user is asking about a codebase.

User Question: {query}

Relevant code structure:
{relevant_subgraph}

Provide a clear, concise answer. Reference specific functions, classes, or files by name.
If the information isn't in the graph, say so.
"""
        
        return self._call_llm(prompt)
    
    def extract_intent(self, query: str) -> Dict[str, Any]:
        """Extract intent and entities from user query"""
        prompt = f"""
Extract the intent from this query about a codebase:

Query: "{query}"

Return a JSON object with:
- intent: one of [explain_flow, find_dependencies, locate_function, understand_architecture, trace_execution]
- entities: list of mentioned code entities (functions, classes, files)
- scope: one of [global, file, function, class]

Example: {{"intent": "explain_flow", "entities": ["authentication"], "scope": "global"}}

Return ONLY valid JSON.
"""
        
        response = self._call_llm(prompt)
        
        # Parse JSON (simple extraction)
        try:
            import json
            return json.loads(response)
        except:
            return {
                'intent': 'explain_flow',
                'entities': [],
                'scope': 'global'
            }
    
    def _call_llm(self, prompt: str, max_tokens: int = 1500) -> str:
        """Call LLM API"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful code analysis assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error calling LLM: {str(e)}"

