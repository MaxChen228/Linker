#!/usr/bin/env python3
"""
CSS Usage Pattern Analyzer
Analyzes CSS usage patterns, identifies unused CSS, and tracks selector usage
across HTML templates and JavaScript files.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict
import argparse


@dataclass
class UsagePattern:
    """CSS usage pattern information."""
    selector: str
    type: str  # 'class', 'id', 'element', 'attribute'
    usage_count: int
    files_used: List[str]
    css_files: List[str]  # Files where selector is defined
    

@dataclass
class UnusedSelector:
    """Unused CSS selector information."""
    selector: str
    css_file: str
    line_number: int
    estimated_size_bytes: int
    

@dataclass
class CriticalCSS:
    """Critical CSS information for above-the-fold content."""
    selector: str
    css_file: str
    properties: List[str]
    is_critical: bool
    reason: str
    

@dataclass
class UsageAnalysisResult:
    """CSS usage analysis result."""
    timestamp: str
    total_selectors: int
    used_selectors: int
    unused_selectors: int
    usage_patterns: List[UsagePattern]
    unused_css: List[UnusedSelector]
    critical_css: List[CriticalCSS]
    recommendations: List[str]
    potential_savings_bytes: int


class CSSUsageAnalyzer:
    """Analyzes CSS usage patterns across the codebase."""
    
    def __init__(self, css_root: str, template_root: str = None, js_root: str = None):
        self.css_root = Path(css_root)
        self.template_root = Path(template_root) if template_root else None
        self.js_root = Path(js_root) if js_root else None
        
        # Patterns for finding CSS selectors and usage
        self.css_selector_pattern = re.compile(r'([^{]+){([^}]+)}', re.MULTILINE | re.DOTALL)
        self.class_pattern = re.compile(r'\.([a-zA-Z][\w-]*)')
        self.id_pattern = re.compile(r'#([a-zA-Z][\w-]*)')
        self.element_pattern = re.compile(r'\b([a-z][a-z0-9]*)\b')
        
        # HTML/Template patterns
        self.html_class_pattern = re.compile(r'class=["\']([^"\']+)["\']', re.IGNORECASE)
        self.html_id_pattern = re.compile(r'id=["\']([^"\']+)["\']', re.IGNORECASE)
        
        # JavaScript patterns for dynamic classes
        self.js_class_pattern = re.compile(r'["\']([a-zA-Z][\w-]*)["\']')
        self.js_classlist_pattern = re.compile(r'classList\.(?:add|remove|toggle|contains)\(["\']([^"\']+)["\']')
        
        # Critical CSS patterns (above-the-fold indicators)
        self.critical_patterns = [
            r'\.hero',
            r'\.header',
            r'\.nav',
            r'\.menu',
            r'\.logo',
            r'\.banner',
            r'\.main',
            r'\.content',
            r'\.container',
            r'\.wrapper',
            r'body',
            r'html',
            r'\.btn',
            r'\.button',
            r'\.form',
            r'\.input'
        ]
        
        self.selectors_defined: Dict[str, List[Tuple[str, int]]] = defaultdict(list)
        self.selectors_used: Dict[str, Set[str]] = defaultdict(set)
        
    def analyze(self) -> UsageAnalysisResult:
        """Perform complete CSS usage analysis."""
        print("Starting CSS usage analysis...")
        
        # Step 1: Extract all CSS selectors
        self._extract_css_selectors()
        print(f"Found {len(self.selectors_defined)} unique selectors in CSS")
        
        # Step 2: Find selector usage in templates
        if self.template_root and self.template_root.exists():
            self._analyze_template_usage()
        
        # Step 3: Find selector usage in JavaScript
        if self.js_root and self.js_root.exists():
            self._analyze_js_usage()
        
        # Step 4: Identify unused CSS
        unused_css = self._identify_unused_css()
        
        # Step 5: Generate usage patterns
        usage_patterns = self._generate_usage_patterns()
        
        # Step 6: Identify critical CSS
        critical_css = self._identify_critical_css()
        
        # Step 7: Calculate potential savings
        potential_savings = self._calculate_potential_savings(unused_css)
        
        # Step 8: Generate recommendations
        recommendations = self._generate_recommendations(unused_css, usage_patterns)
        
        return UsageAnalysisResult(
            timestamp=self._get_timestamp(),
            total_selectors=len(self.selectors_defined),
            used_selectors=len([s for s in self.selectors_defined if self.selectors_used[s]]),
            unused_selectors=len(unused_css),
            usage_patterns=usage_patterns,
            unused_css=unused_css,
            critical_css=critical_css,
            recommendations=recommendations,
            potential_savings_bytes=potential_savings
        )
    
    def _extract_css_selectors(self) -> None:
        """Extract all CSS selectors from CSS files."""
        css_files = list(self.css_root.glob('**/*.css'))
        
        for css_file in css_files:
            try:
                with open(css_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Remove comments
                content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
                
                # Find all CSS rules
                for match in self.css_selector_pattern.finditer(content):
                    selector_group = match.group(1).strip()
                    properties = match.group(2).strip()
                    
                    # Split multiple selectors
                    selectors = [s.strip() for s in selector_group.split(',')]
                    
                    for selector in selectors:
                        if selector and not selector.startswith('@'):
                            line_number = content[:match.start()].count('\n') + 1
                            self.selectors_defined[selector].append((str(css_file), line_number))
                            
            except Exception as e:
                print(f"Error reading CSS file {css_file}: {e}")
    
    def _analyze_template_usage(self) -> None:
        """Analyze CSS usage in HTML templates."""
        template_patterns = ['**/*.html', '**/*.jinja2', '**/*.j2', '**/*.template']
        template_files = []
        
        for pattern in template_patterns:
            template_files.extend(self.template_root.glob(pattern))
        
        print(f"Analyzing {len(template_files)} template files...")
        
        for template_file in template_files:
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find class usage
                for match in self.html_class_pattern.finditer(content):
                    classes = match.group(1).split()
                    for class_name in classes:
                        class_selector = f".{class_name}"
                        self.selectors_used[class_selector].add(str(template_file))
                
                # Find ID usage
                for match in self.html_id_pattern.finditer(content):
                    id_name = match.group(1)
                    id_selector = f"#{id_name}"
                    self.selectors_used[id_selector].add(str(template_file))
                
                # Find element usage (basic check)
                elements = re.findall(r'<(\w+)', content)
                for element in set(elements):
                    if element.lower() in ['div', 'span', 'p', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 
                                         'button', 'input', 'form', 'ul', 'ol', 'li', 'table', 'tr', 'td', 'th']:
                        self.selectors_used[element.lower()].add(str(template_file))
                        
            except Exception as e:
                print(f"Error reading template file {template_file}: {e}")
    
    def _analyze_js_usage(self) -> None:
        """Analyze CSS usage in JavaScript files."""
        js_files = list(self.js_root.glob('**/*.js')) + list(self.js_root.glob('**/*.ts'))
        
        print(f"Analyzing {len(js_files)} JavaScript files...")
        
        for js_file in js_files:
            try:
                with open(js_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find classList operations
                for match in self.js_classlist_pattern.finditer(content):
                    class_name = match.group(1)
                    class_selector = f".{class_name}"
                    self.selectors_used[class_selector].add(str(js_file))
                
                # Find querySelector usage
                query_patterns = [
                    r'querySelector\(["\']([^"\']+)["\']',
                    r'querySelectorAll\(["\']([^"\']+)["\']',
                    r'getElementById\(["\']([^"\']+)["\']',
                    r'getElementsByClassName\(["\']([^"\']+)["\']'
                ]
                
                for pattern in query_patterns:
                    for match in re.finditer(pattern, content):
                        selector = match.group(1)
                        if selector.startswith('.'):
                            self.selectors_used[selector].add(str(js_file))
                        elif selector.startswith('#'):
                            self.selectors_used[selector].add(str(js_file))
                        elif pattern.endswith('getElementById'):
                            id_selector = f"#{selector}"
                            self.selectors_used[id_selector].add(str(js_file))
                        elif pattern.endswith('getElementsByClassName'):
                            class_selector = f".{selector}"
                            self.selectors_used[class_selector].add(str(js_file))
                            
            except Exception as e:
                print(f"Error reading JavaScript file {js_file}: {e}")
    
    def _identify_unused_css(self) -> List[UnusedSelector]:
        """Identify unused CSS selectors."""
        unused_selectors = []
        
        for selector, definitions in self.selectors_defined.items():
            if not self.selectors_used[selector] and not self._is_pseudo_or_dynamic(selector):
                for css_file, line_number in definitions:
                    # Estimate size
                    estimated_size = len(selector) * 2  # Rough estimate
                    
                    unused_selector = UnusedSelector(
                        selector=selector,
                        css_file=css_file,
                        line_number=line_number,
                        estimated_size_bytes=estimated_size
                    )
                    unused_selectors.append(unused_selector)
        
        return unused_selectors
    
    def _is_pseudo_or_dynamic(self, selector: str) -> bool:
        """Check if selector is pseudo, dynamic, or might be used indirectly."""
        dynamic_indicators = [
            ':hover', ':focus', ':active', ':visited', ':before', ':after',
            ':first-child', ':last-child', ':nth-child', ':not(',
            '[data-', '.is-', '.has-', '.js-'
        ]
        
        return any(indicator in selector for indicator in dynamic_indicators)
    
    def _generate_usage_patterns(self) -> List[UsagePattern]:
        """Generate usage patterns for CSS selectors."""
        patterns = []
        
        for selector, usage_files in self.selectors_used.items():
            if usage_files:  # Only include used selectors
                # Determine selector type
                selector_type = 'element'
                if selector.startswith('.'):
                    selector_type = 'class'
                elif selector.startswith('#'):
                    selector_type = 'id'
                elif '[' in selector:
                    selector_type = 'attribute'
                
                # Get CSS files where it's defined
                css_files = [file for file, _ in self.selectors_defined.get(selector, [])]
                
                pattern = UsagePattern(
                    selector=selector,
                    type=selector_type,
                    usage_count=len(usage_files),
                    files_used=list(usage_files),
                    css_files=css_files
                )
                patterns.append(pattern)
        
        return sorted(patterns, key=lambda p: p.usage_count, reverse=True)
    
    def _identify_critical_css(self) -> List[CriticalCSS]:
        """Identify critical CSS for above-the-fold content."""
        critical_css = []
        
        for selector in self.selectors_defined:
            is_critical = False
            reason = ""
            
            # Check against critical patterns
            for pattern in self.critical_patterns:
                if re.search(pattern, selector, re.IGNORECASE):
                    is_critical = True
                    reason = f"Matches critical pattern: {pattern}"
                    break
            
            # Check if used in multiple files (likely important)
            if not is_critical and len(self.selectors_used[selector]) >= 3:
                is_critical = True
                reason = "Used in multiple files"
            
            # Check for layout-related selectors
            if not is_critical and any(keyword in selector.lower() for keyword in 
                                     ['container', 'wrapper', 'layout', 'grid', 'flex']):
                is_critical = True
                reason = "Layout-related selector"
            
            for css_file, line_number in self.selectors_defined[selector]:
                critical_css_item = CriticalCSS(
                    selector=selector,
                    css_file=css_file,
                    properties=[],  # TODO: Extract actual properties
                    is_critical=is_critical,
                    reason=reason if is_critical else "Not critical"
                )
                critical_css.append(critical_css_item)
        
        return critical_css
    
    def _calculate_potential_savings(self, unused_css: List[UnusedSelector]) -> int:
        """Calculate potential size savings from removing unused CSS."""
        return sum(selector.estimated_size_bytes for selector in unused_css)
    
    def _generate_recommendations(self, unused_css: List[UnusedSelector], 
                                usage_patterns: List[UsagePattern]) -> List[str]:
        """Generate optimization recommendations."""
        recommendations = []
        
        # Unused CSS recommendations
        if unused_css:
            total_unused = len(unused_css)
            savings_kb = self._calculate_potential_savings(unused_css) / 1024
            recommendations.append(
                f"Remove {total_unused} unused CSS selectors to save ~{savings_kb:.1f}KB"
            )
        
        # Usage pattern recommendations
        single_use_classes = [p for p in usage_patterns if p.type == 'class' and p.usage_count == 1]
        if len(single_use_classes) > 10:
            recommendations.append(
                f"Consider inlining {len(single_use_classes)} single-use CSS classes"
            )
        
        # High-usage patterns
        high_usage = [p for p in usage_patterns if p.usage_count > 10]
        if high_usage:
            recommendations.append(
                f"Optimize {len(high_usage)} frequently-used selectors for better performance"
            )
        
        # Critical CSS recommendations
        recommendations.append(
            "Consider extracting critical CSS for above-the-fold content optimization"
        )
        
        return recommendations
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Analyze CSS usage patterns')
    parser.add_argument('css_root', help='Root directory containing CSS files')
    parser.add_argument('--templates', help='Root directory containing template files')
    parser.add_argument('--javascript', help='Root directory containing JavaScript files')
    parser.add_argument('--output', '-o', help='Output file for JSON results')
    
    args = parser.parse_args()
    
    # Run analysis
    analyzer = CSSUsageAnalyzer(args.css_root, args.templates, args.javascript)
    result = analyzer.analyze()
    
    # Output results
    output_file = args.output or 'css_usage_analysis.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(asdict(result), f, indent=2, ensure_ascii=False)
    
    print(f"Analysis complete. Results saved to: {output_file}")
    print(f"Total selectors: {result.total_selectors}")
    print(f"Used selectors: {result.used_selectors}")
    print(f"Unused selectors: {result.unused_selectors}")
    print(f"Potential savings: {result.potential_savings_bytes / 1024:.1f}KB")


if __name__ == '__main__':
    main()