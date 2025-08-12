"""
Financial RAG (Retrieval Augmented Generation) system.
"""

import os
import re
import logging
from typing import Dict, List
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import PyPDF2

logger = logging.getLogger(__name__)


class FinancialRAG:
    """Financial RAG with hardcoded rules + PDF textbook integration"""
    
    def __init__(self, textbook_path: str = None):
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.textbook_path = textbook_path
        
        # Start with hardcoded financial rules
        self.knowledge_chunks = self._get_financial_rules()
        
        # Add PDF content if available
        if textbook_path and os.path.exists(textbook_path):
            logger.info(f"Loading PDF textbook: {textbook_path}")
            pdf_chunks = self._process_pdf_textbook(textbook_path)
            self.knowledge_chunks.extend(pdf_chunks)
            logger.info(f"Added {len(pdf_chunks)} chunks from PDF")
        
        # Create embeddings for all chunks
        chunk_texts = [chunk['text'] for chunk in self.knowledge_chunks]
        self.chunk_embeddings = self.embedder.encode(chunk_texts)
        logger.info(f"Total knowledge chunks: {len(self.knowledge_chunks)}")
    
    def _get_financial_rules(self) -> List[Dict]:
        """Core financial calculation rules from FinanceQA paper and common practices"""
        return [
            {
                'text': 'For Accounts Payable Days: use AVERAGE accounts payable balance, not end-of-period. Formula: (Average AP / COGS) * 365',
                'topic': 'working_capital'
            },
            {
                'text': 'Diluted shares = Basic shares + dilutive securities (options, warrants, convertibles). Only include if dilutive (exercise price < current price).',
                'topic': 'diluted_shares'
            },
            {
                'text': 'EBITDA adjustments: Add back operating lease costs under new accounting standards (ASC 842). Operating leases are now capitalized.',
                'topic': 'ebitda'
            },
            {
                'text': 'Variable lease assets estimation: If not stated, assume ratio of variable lease assets to operating lease assets equals ratio of variable lease costs to total operating lease costs.',
                'topic': 'lease_analysis'
            },
            {
                'text': 'Working cash assumption: Use 2% of revenue when specific working cash requirements not provided. Take minimum of total cash or calculated amount.',
                'topic': 'working_capital'
            }
        ]
    
    def query(self, question: str, top_k: int = 2) -> List[Dict]:
        """Get relevant financial rules"""
        query_embedding = self.embedder.encode([question])
        similarities = cosine_similarity(query_embedding, self.chunk_embeddings)[0]
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        return [self.knowledge_chunks[idx] for idx in top_indices if similarities[idx] > 0.3]
    
    def _process_pdf_textbook(self, pdf_path: str) -> List[Dict]:
        """Extract and chunk content from PDF textbook"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Extract all text
                full_text = ""
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():
                            full_text += f"\n--- Page {page_num + 1} ---\n{page_text}"
                    except Exception as e:
                        logger.warning(f"Error extracting page {page_num + 1}: {e}")
                        continue
                
                if not full_text.strip():
                    logger.warning("No text extracted from PDF")
                    return []
                
                # Try to identify table of contents for better chunking
                toc_sections = self._extract_toc_sections(full_text)
                
                if toc_sections:
                    logger.info(f"Found {len(toc_sections)} sections from table of contents")
                    return self._create_section_chunks(full_text, toc_sections)
                else:
                    logger.info("No clear table of contents found, using paragraph-based chunking")
                    return self._create_paragraph_chunks(full_text)
                    
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {e}")
            return []
    
    def _extract_toc_sections(self, text: str) -> List[str]:
        """Extract section titles from table of contents"""
        # Look for table of contents patterns
        toc_patterns = [
            r'(?i)table\s+of\s+contents.*?(?=chapter|section|page|\n\n)',
            r'(?i)contents.*?(?=chapter|section|page|\n\n)',
        ]
        
        sections = []
        
        for pattern in toc_patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            if matches:
                toc_text = matches[0]
                # Extract chapter/section titles
                section_patterns = [
                    r'(?i)(chapter\s+\d+[:\s]+[^\n\r]+)',
                    r'(?i)(\d+\.\d*\s+[A-Z][^\n\r]+)',
                    r'(?i)([A-Z][A-Z\s]+[A-Z])\s+\d+',  # ALL CAPS sections
                ]
                
                for sec_pattern in section_patterns:
                    found_sections = re.findall(sec_pattern, toc_text)
                    sections.extend([s.strip() for s in found_sections])
                
                if sections:
                    break
        
        # Clean and filter sections
        cleaned_sections = []
        for section in sections[:20]:  # Limit to first 20 sections
            if len(section) > 10 and len(section) < 100:  # Reasonable length
                cleaned_sections.append(section)
        
        return cleaned_sections
    
    def _create_section_chunks(self, text: str, sections: List[str]) -> List[Dict]:
        """Create chunks based on identified sections"""
        chunks = []
        
        for i, section_title in enumerate(sections):
            try:
                # Find section content
                section_pattern = re.escape(section_title.strip())
                
                # Look for the section and extract content until next section or end
                if i < len(sections) - 1:
                    next_section = re.escape(sections[i + 1].strip())
                    pattern = f'{section_pattern}(.*?)(?={next_section}|$)'
                else:
                    pattern = f'{section_pattern}(.*?)$'
                
                matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
                
                if matches:
                    content = matches[0].strip()
                    if len(content) > 100:  # Only include substantial content
                        # Split large sections into smaller chunks
                        if len(content) > 2000:
                            # Split by paragraphs
                            paragraphs = content.split('\n\n')
                            current_chunk = ""
                            
                            for para in paragraphs:
                                if len(current_chunk) + len(para) > 1500:
                                    if current_chunk:
                                        chunks.append({
                                            'text': f"{section_title}\n\n{current_chunk}",
                                            'topic': 'textbook_section',
                                            'source': 'pdf_valuation',
                                            'section': section_title
                                        })
                                    current_chunk = para
                                else:
                                    current_chunk += "\n\n" + para if current_chunk else para
                            
                            # Add remaining content
                            if current_chunk:
                                chunks.append({
                                    'text': f"{section_title}\n\n{current_chunk}",
                                    'topic': 'textbook_section',
                                    'source': 'pdf_valuation',
                                    'section': section_title
                                })
                        else:
                            chunks.append({
                                'text': f"{section_title}\n\n{content}",
                                'topic': 'textbook_section',
                                'source': 'pdf_valuation',
                                'section': section_title
                            })
                            
            except Exception as e:
                logger.warning(f"Error processing section '{section_title}': {e}")
                continue
        
        return chunks
    
    def _create_paragraph_chunks(self, text: str) -> List[Dict]:
        """Create chunks based on paragraphs when no clear sections found"""
        # Split into paragraphs
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        chunks = []
        current_chunk = ""
        chunk_count = 0
        
        for para in paragraphs:
            # Skip very short paragraphs or page headers
            if len(para) < 50 or 'Page' in para[:20]:
                continue
            
            # Check if adding this paragraph would make chunk too long
            if len(current_chunk) + len(para) > 1500 and current_chunk:
                chunks.append({
                    'text': current_chunk,
                    'topic': 'textbook_content',
                    'source': 'pdf_valuation',
                    'section': f'chunk_{chunk_count}'
                })
                current_chunk = para
                chunk_count += 1
            else:
                current_chunk += "\n\n" + para if current_chunk else para
        
        # Add final chunk
        if current_chunk:
            chunks.append({
                'text': current_chunk,
                'topic': 'textbook_content',
                'source': 'pdf_valuation',
                'section': f'chunk_{chunk_count}'
            })
        
        return chunks
