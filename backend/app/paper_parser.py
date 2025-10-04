"""
Paper Parser - Extract structure from research papers (PDF)
"""

import re
from typing import Dict, Any, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class PaperParser:
    """Parse research papers to extract structure and content"""
    
    def __init__(self):
        self.section_patterns = [
            r'^(?:\d+\.?\s+)?([A-Z][A-Za-z\s]+)$',  # "1. Introduction" or "Introduction"
            r'^(?:[A-Z]+\s*\d*\.?\s*)([A-Z][A-Za-z\s]+)$',  # "SECTION 1 Introduction"
        ]
    
    def parse_paper(self, file_path: str) -> Dict[str, Any]:
        """
        Parse paper and extract structure
        
        For hackathon: simplified text-based parsing
        In production: would use proper PDF libraries
        """
        try:
            # Try PDF parsing first
            text = self._extract_text_from_pdf(file_path)
        except:
            # Fallback: treat as text file
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
            except Exception as e:
                logger.error(f"Failed to read paper: {e}")
                return self._create_empty_paper()
        
        # Extract structure
        all_sections = self._extract_sections(text)
        
        # Filter for implementation-relevant sections only
        relevant_sections = self._filter_implementation_sections(all_sections)
        
        code_references = self._extract_code_references(text)
        algorithms = self._extract_algorithms(text)
        
        logger.info(f"📊 Filtered {len(all_sections)} sections → {len(relevant_sections)} implementation-relevant sections")
        
        return {
            'text': text[:10000],  # First 10k chars for LLM
            'sections': relevant_sections,
            'code_references': code_references,
            'algorithms': algorithms,
            'total_sections': len(relevant_sections),
            'all_sections_count': len(all_sections)
        }
    
    def _extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF - simplified for hackathon"""
        try:
            import PyPDF2
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = ""
                for page in reader.pages[:20]:  # First 20 pages
                    text += page.extract_text() + "\n"
                return text
        except ImportError:
            # PyPDF2 not available, try pdfplumber
            try:
                import pdfplumber
                with pdfplumber.open(file_path) as pdf:
                    text = ""
                    for page in pdf.pages[:20]:
                        text += page.extract_text() + "\n"
                    return text
            except ImportError:
                logger.warning("No PDF library available, treating as text")
                raise
    
    def _extract_sections(self, text: str) -> List[Dict[str, Any]]:
        """Extract sections from paper text"""
        sections = []
        lines = text.split('\n')
        
        current_section = None
        current_content = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Check if this looks like a section header (more strict)
            is_header = False
            
            # Only match if it's a numbered section or common section name
            # Pattern 1: "1 Introduction" or "1. Introduction"
            numbered_section = re.match(r'^\d+\.?\s+[A-Z]', line)
            
            # Pattern 2: Common section names at start of line, all caps or title case
            common_sections = [
                'abstract', 'introduction', 'related work', 'methodology',
                'methods', 'approach', 'implementation', 'experiments',
                'results', 'discussion', 'conclusion', 'conclusions',
                'references', 'background', 'evaluation', 'limitations'
            ]
            
            # Check if line is a common section (must be at start and short)
            is_common_section = False
            line_lower = line.lower()
            for section in common_sections:
                # Match if the line IS the section name (maybe with number)
                if line_lower == section or line_lower.startswith(section + ' ') or numbered_section:
                    if len(line) < 50:  # Section headers are short
                        is_common_section = True
                        break
            
            # Only mark as header if it matches strict criteria
            if numbered_section and len(line) < 100:
                is_header = True
            elif is_common_section:
                is_header = True
            
            if is_header:
                # Save previous section (only if it has reasonable content)
                if current_section and len(current_content) > 0:
                    full_content = ' '.join(current_content)
                    # Only add section if it has substantial content (>50 chars)
                    if len(full_content) > 50:
                        sections.append({
                            'title': current_section,
                            'content': full_content,  # Full content
                            'summary': full_content[:200] + '...' if len(full_content) > 200 else full_content,
                            'line_number': i - len(current_content)
                        })
                
                # Start new section
                current_section = line
                current_content = []
            else:
                if current_section:
                    current_content.append(line)
        
        # Add last section (only if has reasonable content)
        if current_section and len(current_content) > 0:
            full_content = ' '.join(current_content)
            if len(full_content) > 50:
                sections.append({
                    'title': current_section,
                    'content': full_content,  # Full content
                    'summary': full_content[:200] + '...' if len(full_content) > 200 else full_content,
                    'line_number': len(lines) - len(current_content)
                })
        
        return sections[:12]  # Limit to 12 best sections
    
    def _filter_implementation_sections(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter sections to keep only implementation-relevant ones.
        Exclude: introduction, related work, references, ablation studies, etc.
        Keep: methodology, architecture, model, implementation, approach, algorithm
        """
        # Keywords that indicate implementation-relevant sections
        relevant_keywords = [
            'method', 'approach', 'architecture', 'model', 'algorithm',
            'implementation', 'design', 'framework', 'system', 'network',
            'training', 'optimization', 'learning', 'procedure', 'technique',
            'encoder', 'decoder', 'attention', 'layer', 'module', 'component'
        ]
        
        # Keywords that indicate sections to exclude
        exclude_keywords = [
            'introduction', 'related work', 'references', 'acknowledgment',
            'conclusion', 'future work', 'discussion', 'limitation',
            'ablation', 'analysis', 'experiment', 'result', 'evaluation',
            'background', 'motivation', 'contribution', 'abstract'
        ]
        
        filtered_sections = []
        
        for section in sections:
            title_lower = section['title'].lower()
            
            # Check if section should be excluded
            should_exclude = any(keyword in title_lower for keyword in exclude_keywords)
            
            if should_exclude:
                logger.info(f"  Excluding: {section['title']}")
                continue
            
            # Check if section is relevant
            is_relevant = any(keyword in title_lower for keyword in relevant_keywords)
            
            # Also check content for relevance if title is ambiguous
            if not is_relevant:
                content_lower = section['content'].lower()
                # Check if content discusses implementation details
                impl_indicators = ['function', 'class', 'algorithm', 'we implement', 
                                 'our model', 'architecture', 'layer', 'training']
                has_impl_content = any(indicator in content_lower for indicator in impl_indicators)
                
                if has_impl_content and len(section['content']) > 200:
                    is_relevant = True
                    logger.info(f"  ✓ Including (by content): {section['title']}")
            else:
                logger.info(f"  ✓ Including: {section['title']}")
            
            if is_relevant:
                filtered_sections.append(section)
        
        # If no sections were kept (too strict filtering), keep sections with substantial content
        if not filtered_sections and sections:
            logger.warning("No sections matched filters, keeping longest sections")
            sorted_sections = sorted(sections, key=lambda s: len(s['content']), reverse=True)
            filtered_sections = sorted_sections[:5]
        
        return filtered_sections
    
    def _extract_code_references(self, text: str) -> List[Dict[str, Any]]:
        """Extract references to code in the paper"""
        references = []
        
        # Look for common code reference patterns
        patterns = [
            r'(?:see|refer to|implemented in|code in|function|class|method)\s+([a-zA-Z_][a-zA-Z0-9_\.]*)',
            r'`([a-zA-Z_][a-zA-Z0-9_\.]*)`',  # Markdown code
            r'\\texttt\{([^}]+)\}',  # LaTeX code
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                ref = match.group(1)
                if len(ref) > 2 and len(ref) < 50:  # Reasonable length
                    references.append({
                        'reference': ref,
                        'context': text[max(0, match.start()-50):match.end()+50]
                    })
        
        # Remove duplicates
        unique_refs = []
        seen = set()
        for ref in references:
            if ref['reference'] not in seen:
                seen.add(ref['reference'])
                unique_refs.append(ref)
        
        return unique_refs[:20]  # Limit to 20
    
    def _extract_algorithms(self, text: str) -> List[Dict[str, Any]]:
        """Extract algorithm descriptions"""
        algorithms = []
        
        # Look for explicit algorithm blocks only (much stricter)
        # Must have "Algorithm" followed by a number or colon
        algo_pattern = r'(?:Algorithm\s+\d+|Algorithm\s*:|Procedure\s+\d+|Procedure\s*:)\s*([^\n]+)'
        matches = re.finditer(algo_pattern, text, re.IGNORECASE)
        
        for match in matches:
            name = match.group(1).strip()
            # Only include if name looks reasonable (not too long, not empty)
            if 5 < len(name) < 100:
                # Get next few lines as description
                start = match.end()
                end = min(start + 300, len(text))
                description = text[start:end]
                
                algorithms.append({
                    'name': name,
                    'description': description.strip()
                })
        
        return algorithms[:5]  # Limit to 5 real algorithms
    
    def _create_empty_paper(self) -> Dict[str, Any]:
        """Create empty paper structure"""
        return {
            'text': '',
            'sections': [],
            'code_references': [],
            'algorithms': [],
            'total_sections': 0
        }

