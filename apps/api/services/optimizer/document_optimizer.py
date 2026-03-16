"""
Documentation Optimizer Service

This service crawls documentation, analyzes it, and generates
optimized markdown files using AI.
"""

import os
import re
import json
import zipfile
import tempfile
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import logging

import httpx
from bs4 import BeautifulSoup
import openai

logger = logging.getLogger(__name__)

# Initialize OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')


@dataclass
class DocPage:
    """Represents a documentation page."""
    url: str
    title: str
    content: str
    code_blocks: List[Dict]
    headings: List[str]
    links: List[str]
    file_path: Optional[str] = None


@dataclass
class OptimizationConfig:
    """Configuration for document optimization."""
    target_audience: str  # 'beginners', 'intermediate', 'experts', 'mixed'
    tone: str  # 'formal', 'casual', 'technical', 'friendly'
    priorities: List[str]  # e.g., ['code_examples', 'api_reference', 'tutorials']
    include_diagrams: bool = False
    add_troubleshooting: bool = True
    improve_seo: bool = True


@dataclass
class OptimizedDoc:
    """Represents an optimized document."""
    original_url: str
    title: str
    optimized_content: str
    improvements: List[str]
    file_name: str


class DocumentationOptimizer:
    """Optimizes documentation for AI agent consumption."""
    
    def __init__(self, config: OptimizationConfig):
        self.config = config
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def optimize_documentation(
        self, 
        start_url: str,
        progress_callback=None
    ) -> Tuple[List[OptimizedDoc], Dict]:
        """
        Main entry point: crawl, analyze, and optimize documentation.
        
        Returns:
            Tuple of (optimized documents, metadata)
        """
        logger.info(f"Starting optimization of {start_url}")
        
        # Step 1: Crawl documentation
        if progress_callback:
            progress_callback("crawling", 0.1)
        
        pages = await self._crawl_documentation(start_url)
        logger.info(f"Crawled {len(pages)} pages")
        
        # Step 2: Analyze each page
        if progress_callback:
            progress_callback("analyzing", 0.3)
        
        analyzed_pages = []
        for i, page in enumerate(pages):
            analysis = await self._analyze_page(page)
            analyzed_pages.append((page, analysis))
            if progress_callback:
                progress_callback("analyzing", 0.3 + (0.2 * (i + 1) / len(pages)))
        
        # Step 3: Generate optimized content
        if progress_callback:
            progress_callback("optimizing", 0.5)
        
        optimized_docs = []
        for i, (page, analysis) in enumerate(analyzed_pages):
            optimized = await self._optimize_page(page, analysis)
            optimized_docs.append(optimized)
            if progress_callback:
                progress_callback("optimizing", 0.5 + (0.4 * (i + 1) / len(analyzed_pages)))
        
        # Step 4: Generate metadata
        if progress_callback:
            progress_callback("finalizing", 0.9)
        
        metadata = self._generate_metadata(optimized_docs)
        
        if progress_callback:
            progress_callback("complete", 1.0)
        
        return optimized_docs, metadata
    
    async def _crawl_documentation(self, start_url: str) -> List[DocPage]:
        """Crawl documentation site and extract pages."""
        pages = []
        visited = set()
        to_visit = [start_url]
        
        max_pages = 50  # Limit for MVP
        
        while to_visit and len(pages) < max_pages:
            url = to_visit.pop(0)
            if url in visited:
                continue
            
            try:
                page = await self._fetch_page(url)
                if page:
                    pages.append(page)
                    visited.add(url)
                    
                    # Add linked pages
                    for link in page.links:
                        if link not in visited and self._is_same_domain(link, start_url):
                            to_visit.append(link)
            
            except Exception as e:
                logger.warning(f"Failed to fetch {url}: {e}")
        
        return pages
    
    async def _fetch_page(self, url: str) -> Optional[DocPage]:
        """Fetch and parse a single page."""
        try:
            response = await self.client.get(url)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title = soup.find('title')
            title_text = title.get_text(strip=True) if title else "Untitled"
            
            # Extract main content
            main = soup.find('main') or soup.find('article') or soup.find('div', class_='content')
            if not main:
                main = soup.find('body')
            
            content = main.get_text(separator='\n', strip=True) if main else ""
            
            # Extract code blocks
            code_blocks = []
            for pre in soup.find_all('pre'):
                code = pre.find('code')
                if code:
                    language = self._detect_language(code.get('class', []))
                    code_blocks.append({
                        'language': language,
                        'code': code.get_text(strip=True)
                    })
            
            # Extract headings
            headings = []
            for h in soup.find_all(['h1', 'h2', 'h3']):
                headings.append(h.get_text(strip=True))
            
            # Extract links
            links = []
            for a in soup.find_all('a', href=True):
                href = a['href']
                if href.startswith('http'):
                    links.append(href)
            
            return DocPage(
                url=url,
                title=title_text,
                content=content,
                code_blocks=code_blocks,
                headings=headings,
                links=links
            )
        
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    async def _analyze_page(self, page: DocPage) -> Dict:
        """Analyze a page for issues and opportunities."""
        analysis = {
            'has_code_examples': len(page.code_blocks) > 0,
            'code_count': len(page.code_blocks),
            'has_troubleshooting': 'troubleshoot' in page.content.lower() or 'error' in page.content.lower(),
            'has_api_reference': 'api' in page.title.lower() or 'endpoint' in page.content.lower(),
            'word_count': len(page.content.split()),
            'heading_count': len(page.headings),
            'issues': []
        }
        
        # Identify issues
        if analysis['word_count'] < 100:
            analysis['issues'].append('Page is too short - needs more detail')
        
        if analysis['heading_count'] < 2:
            analysis['issues'].append('Missing clear structure - add more headings')
        
        if not analysis['has_code_examples'] and 'how' in page.title.lower():
            analysis['issues'].append('How-to guide missing code examples')
        
        return analysis
    
    async def _optimize_page(self, page: DocPage, analysis: Dict) -> OptimizedDoc:
        """Use AI to optimize a single page."""
        
        # Build the prompt
        prompt = self._build_optimization_prompt(page, analysis)
        
        # Call OpenAI
        try:
            response = await openai.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert technical writer specializing in developer documentation. Your goal is to optimize documentation for AI agent consumption."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=4000
            )
            
            optimized_content = response.choices[0].message.content
            
            # Extract improvements from the response
            improvements = self._extract_improvements(optimized_content)
            
            # Clean up the content
            optimized_content = self._clean_optimized_content(optimized_content)
            
            # Generate file name
            file_name = self._generate_file_name(page.title, page.url)
            
            return OptimizedDoc(
                original_url=page.url,
                title=page.title,
                optimized_content=optimized_content,
                improvements=improvements,
                file_name=file_name
            )
        
        except Exception as e:
            logger.error(f"Error optimizing page {page.url}: {e}")
            # Return original content as fallback
            return OptimizedDoc(
                original_url=page.url,
                title=page.title,
                optimized_content=page.content,
                improvements=["Failed to optimize - using original content"],
                file_name=self._generate_file_name(page.title, page.url)
            )
    
    def _build_optimization_prompt(self, page: DocPage, analysis: Dict) -> str:
        """Build the optimization prompt for OpenAI."""
        
        audience_guidance = {
            'beginners': 'Use simple language, explain concepts thoroughly, avoid jargon',
            'intermediate': 'Assume basic knowledge, focus on practical implementation',
            'experts': 'Be concise, focus on advanced features and edge cases',
            'mixed': 'Balance explanations - provide both quick reference and detailed explanations'
        }
        
        tone_guidance = {
            'formal': 'Professional, precise, academic tone',
            'casual': 'Friendly, conversational, approachable',
            'technical': 'Precise, detailed, specification-focused',
            'friendly': 'Warm, encouraging, helpful'
        }
        
        priority_sections = {
            'code_examples': 'Add comprehensive, runnable code examples',
            'api_reference': 'Document all parameters, return values, and error codes',
            'tutorials': 'Create step-by-step guides with clear instructions',
            'troubleshooting': 'Add common errors and solutions',
            'concepts': 'Explain underlying concepts clearly'
        }
        
        newline = chr(10)
        code_examples = newline.join(
            ["```" + cb['language'] + newline + cb['code'][:500] + newline + "```"
             for cb in page.code_blocks[:3]]
        )
        focus_areas = newline.join(
            [priority_sections.get(p, p) for p in self.config.priorities]
        )
        issues_list = newline.join(
            ['- ' + issue for issue in analysis['issues']]
        )

        prompt = f"""Optimize the following documentation page for AI agent consumption.

## Original Content

Title: {page.title}
URL: {page.url}

Content:
{page.content[:3000]}

## Existing Code Examples
{code_examples}

## Configuration

Target Audience: {self.config.target_audience}
Guidance: {audience_guidance.get(self.config.target_audience, 'General audience')}

Tone: {self.config.tone}
Guidance: {tone_guidance.get(self.config.tone, 'Neutral')}

Priorities: {', '.join(self.config.priorities)}
Focus Areas: {focus_areas}

## Issues Identified
{issues_list}

## Instructions

1. Rewrite the content to be more AI-agent friendly:
   - Use clear, structured headings
   - Include comprehensive code examples
   - Add API parameter tables where relevant
   - Include troubleshooting sections
   - Cross-reference related topics

2. Format as Markdown with:
   - Proper heading hierarchy (# for title, ## for sections, ### for subsections)
   - Code blocks with language tags
   - Tables for API parameters
   - Bullet points for lists
   - Bold for important terms

3. At the end, add a section "## Improvements Made" listing what was changed.

Return ONLY the optimized markdown content."""

        return prompt
    
    def _extract_improvements(self, content: str) -> List[str]:
        """Extract improvements from optimized content."""
        improvements = []
        
        # Look for improvements section
        if "## Improvements Made" in content:
            section = content.split("## Improvements Made")[1]
            for line in section.split('\n'):
                line = line.strip()
                if line.startswith('-') or line.startswith('*'):
                    improvements.append(line.lstrip('- *'))
        
        return improvements if improvements else ["Content restructured for clarity"]
    
    def _clean_optimized_content(self, content: str) -> str:
        """Clean up the optimized content."""
        # Remove improvements section from main content
        if "## Improvements Made" in content:
            content = content.split("## Improvements Made")[0].strip()
        
        return content
    
    def _generate_file_name(self, title: str, url: str) -> str:
        """Generate a clean file name from title or URL."""
        # Try to extract from URL first
        from urllib.parse import urlparse
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        
        if path:
            # Convert path to filename
            file_name = path.replace('/', '-').lower()
            if not file_name.endswith('.md'):
                file_name += '.md'
            return file_name
        
        # Fallback to title
        file_name = re.sub(r'[^\w\s-]', '', title.lower())
        file_name = re.sub(r'[-\s]+', '-', file_name)
        return file_name + '.md'
    
    def _generate_metadata(self, docs: List[OptimizedDoc]) -> Dict:
        """Generate metadata about the optimization."""
        total_improvements = sum(len(doc.improvements) for doc in docs)
        
        return {
            'pages_optimized': len(docs),
            'total_improvements': total_improvements,
            'config': {
                'target_audience': self.config.target_audience,
                'tone': self.config.tone,
                'priorities': self.config.priorities
            },
            'pages': [
                {
                    'title': doc.title,
                    'file_name': doc.file_name,
                    'improvements': doc.improvements
                }
                for doc in docs
            ]
        }
    
    def _detect_language(self, classes: List[str]) -> str:
        """Detect programming language from CSS classes."""
        for cls in classes:
            if 'language-' in cls:
                return cls.replace('language-', '')
            if 'lang-' in cls:
                return cls.replace('lang-', '')
        return 'text'
    
    def _is_same_domain(self, url: str, base_url: str) -> bool:
        """Check if URL is on the same domain."""
        from urllib.parse import urlparse
        return urlparse(url).netloc == urlparse(base_url).netloc
    
    async def create_zip_package(
        self, 
        docs: List[OptimizedDoc], 
        metadata: Dict
    ) -> str:
        """Create a ZIP file with all optimized documentation."""
        
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
            with zipfile.ZipFile(tmp.name, 'w', zipfile.ZIP_DEFLATED) as zf:
                # Add each document
                for doc in docs:
                    zf.writestr(doc.file_name, doc.optimized_content)
                
                # Add metadata file
                zf.writestr('_metadata.json', json.dumps(metadata, indent=2))
                
                # Add README
                readme = self._generate_readme(metadata)
                zf.writestr('README.md', readme)
                
                # Add implementation guide
                guide = self._generate_implementation_guide()
                zf.writestr('IMPLEMENTATION_GUIDE.md', guide)
            
            return tmp.name
    
    def _generate_readme(self, metadata: Dict) -> str:
        """Generate a README for the ZIP package."""
        return f"""# Optimized Documentation

This package contains your AI-optimized documentation.

## Overview

- **Pages Optimized**: {metadata['pages_optimized']}
- **Total Improvements**: {metadata['total_improvements']}
- **Target Audience**: {metadata['config']['target_audience'].title()}
- **Tone**: {metadata['config']['tone'].title()}

## Files

{chr(10).join([f"- `{page['file_name']}` - {page['title']}" for page in metadata['pages']])}

## What's Included

1. **Optimized Documentation** - Each page has been rewritten for AI agent consumption
2. **_metadata.json** - Technical details about the optimization
3. **IMPLEMENTATION_GUIDE.md** - How to deploy your new documentation

## Key Improvements

{chr(10).join([f"- {imp}" for imp in self._get_all_improvements(metadata)])}

## Next Steps

1. Review the optimized content
2. Make any final adjustments
3. Deploy to your documentation platform
4. See the IMPLEMENTATION_GUIDE.md for detailed instructions

---

*Optimized by AgentReadiness - Documentation for AI Agents*
"""
    
    def _get_all_improvements(self, metadata: Dict) -> List[str]:
        """Get all unique improvements."""
        improvements = set()
        for page in metadata['pages']:
            improvements.update(page['improvements'])
        return list(improvements)[:10]  # Limit to 10
    
    def _generate_implementation_guide(self) -> str:
        """Generate an implementation guide."""
        return """# Implementation Guide

## How to Deploy Your Optimized Documentation

### Option 1: GitHub Pages (Free)

1. Create a new GitHub repository
2. Upload the markdown files
3. Enable GitHub Pages in repository settings
4. Your docs will be live at `https://yourusername.github.io/repo-name`

### Option 2: Netlify (Free)

1. Go to https://netlify.com
2. Drag and drop your files
3. Get an instant live site

### Option 3: Vercel (Free)

1. Go to https://vercel.com
2. Import your GitHub repository
3. Deploy with one click

### Option 4: ReadMe (Paid)

1. Go to https://readme.com
2. Upload your markdown files
3. Get a professional documentation site

## Best Practices

1. **Test Your Code Examples** - Make sure all code runs correctly
2. **Add Images/Diagrams** - Visual aids improve understanding
3. **Set Up Analytics** - Track which pages are most visited
4. **Collect Feedback** - Ask users what they find confusing
5. **Keep Updated** - Documentation should evolve with your product

## Measuring Success

Track these metrics:
- Time to first success (how quickly users get value)
- Support ticket reduction
- Developer satisfaction scores
- API adoption rates

---

*Need help? Contact support@agentreadiness.dev*
"""
