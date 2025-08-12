#!/usr/bin/env python3
"""
CSS Bundle Analyzer
Comprehensive analysis tool for CSS bundle composition, optimization opportunities,
and performance insights.
"""

import os
import re
import json
import gzip
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict
from datetime import datetime
import argparse


@dataclass
class CSSFileInfo:
    """Information about a single CSS file."""
    path: str
    size_bytes: int
    size_gzipped: int
    lines: int
    rules: int
    selectors: int
    properties: int
    comments: int
    category: str
    
    
@dataclass
class CSSSelector:
    """CSS selector information."""
    selector: str
    specificity: int
    file_path: str
    line_number: int
    properties_count: int
    

@dataclass
class CSSVariable:
    """CSS custom property (variable) information."""
    name: str
    value: str
    file_path: str
    line_number: int
    usage_count: int = 0
    

@dataclass
class DuplicateRule:
    """Duplicate CSS rule information."""
    selector: str
    properties: List[str]
    locations: List[Tuple[str, int]]  # (file_path, line_number)
    

@dataclass
class AnalysisResult:
    """Complete CSS bundle analysis result."""
    timestamp: str
    total_files: int
    total_size_bytes: int
    total_size_gzipped: int
    files: List[CSSFileInfo]
    selectors: List[CSSSelector]
    variables: List[CSSVariable]
    duplicates: List[DuplicateRule]
    unused_variables: List[str]
    performance_metrics: Dict[str, Any]
    recommendations: List[str]


class CSSBundleAnalyzer:
    """Main CSS bundle analyzer class."""
    
    def __init__(self, css_root: str):
        self.css_root = Path(css_root)
        self.files: List[CSSFileInfo] = []
        self.selectors: List[CSSSelector] = []
        self.variables: List[CSSVariable] = []
        self.duplicates: List[DuplicateRule] = []
        self.variable_usage: Dict[str, int] = defaultdict(int)
        
        # CSS parsing patterns
        self.selector_pattern = re.compile(r'([^{]+){', re.MULTILINE)
        self.property_pattern = re.compile(r'([^:]+):\s*([^;]+);')
        self.variable_def_pattern = re.compile(r'--([^:]+):\s*([^;]+);')
        self.variable_use_pattern = re.compile(r'var\(--([^)]+)\)')
        self.comment_pattern = re.compile(r'/\*.*?\*/', re.DOTALL)
        
    def analyze(self) -> AnalysisResult:
        """Perform complete CSS bundle analysis."""
        print("Starting CSS bundle analysis...")
        
        # Find all CSS files
        css_files = self._find_css_files()
        print(f"Found {len(css_files)} CSS files")
        
        # Analyze each file
        for css_file in css_files:
            self._analyze_file(css_file)
            
        # Detect duplicates
        self._detect_duplicates()
        
        # Calculate performance metrics
        performance_metrics = self._calculate_performance_metrics()
        
        # Generate recommendations
        recommendations = self._generate_recommendations()
        
        # Find unused variables
        unused_variables = self._find_unused_variables()
        
        return AnalysisResult(
            timestamp=datetime.now().isoformat(),
            total_files=len(self.files),
            total_size_bytes=sum(f.size_bytes for f in self.files),
            total_size_gzipped=sum(f.size_gzipped for f in self.files),
            files=self.files,
            selectors=self.selectors,
            variables=self.variables,
            duplicates=self.duplicates,
            unused_variables=unused_variables,
            performance_metrics=performance_metrics,
            recommendations=recommendations
        )
    
    def _find_css_files(self) -> List[Path]:
        """Find all CSS files in the root directory."""
        css_files = []
        for pattern in ['**/*.css']:
            css_files.extend(self.css_root.glob(pattern))
        return sorted(css_files)
    
    def _analyze_file(self, file_path: Path) -> None:
        """Analyze a single CSS file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Calculate file metrics
            size_bytes = len(content.encode('utf-8'))
            size_gzipped = len(gzip.compress(content.encode('utf-8')))
            lines = len(content.splitlines())
            
            # Remove comments for analysis
            content_no_comments = self.comment_pattern.sub('', content)
            comments_count = len(self.comment_pattern.findall(content))
            
            # Count CSS rules and selectors
            rules_count = content_no_comments.count('{')
            selectors_matches = self.selector_pattern.findall(content_no_comments)
            selectors_count = len(selectors_matches)
            
            # Count properties
            properties_matches = self.property_pattern.findall(content_no_comments)
            properties_count = len(properties_matches)
            
            # Determine category
            category = self._categorize_file(file_path)
            
            # Store file info
            file_info = CSSFileInfo(
                path=str(file_path.relative_to(self.css_root)),
                size_bytes=size_bytes,
                size_gzipped=size_gzipped,
                lines=lines,
                rules=rules_count,
                selectors=selectors_count,
                properties=properties_count,
                comments=comments_count,
                category=category
            )
            self.files.append(file_info)
            
            # Analyze selectors
            self._analyze_selectors(file_path, content_no_comments, selectors_matches)
            
            # Analyze CSS variables
            self._analyze_variables(file_path, content)
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
    
    def _categorize_file(self, file_path: Path) -> str:
        """Categorize CSS file based on its path."""
        path_str = str(file_path)
        
        if '/01-tokens/' in path_str:
            return 'Design Tokens'
        elif '/02-base/' in path_str:
            return 'Base Styles'
        elif '/03-components/' in path_str:
            return 'Components'
        elif '/04-layouts/' in path_str:
            return 'Layouts'
        elif '/pages/' in path_str:
            return 'Page Styles'
        elif '/dist/' in path_str:
            return 'Compiled/Minified'
        elif 'index.css' in path_str:
            return 'Entry Points'
        else:
            return 'Other'
    
    def _analyze_selectors(self, file_path: Path, content: str, selectors: List[str]) -> None:
        """Analyze CSS selectors in the file."""
        lines = content.splitlines()
        
        for selector_match in selectors:
            selector = selector_match.strip()
            if not selector:
                continue
                
            # Find line number
            line_number = self._find_line_number(lines, selector)
            
            # Calculate specificity
            specificity = self._calculate_specificity(selector)
            
            # Count properties in this rule
            rule_start = content.find(selector + '{')
            if rule_start == -1:
                continue
                
            rule_end = content.find('}', rule_start)
            if rule_end == -1:
                continue
                
            rule_content = content[rule_start:rule_end + 1]
            properties_count = len(self.property_pattern.findall(rule_content))
            
            css_selector = CSSSelector(
                selector=selector,
                specificity=specificity,
                file_path=str(file_path.relative_to(self.css_root)),
                line_number=line_number,
                properties_count=properties_count
            )
            self.selectors.append(css_selector)
    
    def _analyze_variables(self, file_path: Path, content: str) -> None:
        """Analyze CSS custom properties (variables)."""
        lines = content.splitlines()
        
        # Find variable definitions
        for match in self.variable_def_pattern.finditer(content):
            var_name = match.group(1).strip()
            var_value = match.group(2).strip()
            line_number = content[:match.start()].count('\n') + 1
            
            css_variable = CSSVariable(
                name=f"--{var_name}",
                value=var_value,
                file_path=str(file_path.relative_to(self.css_root)),
                line_number=line_number
            )
            self.variables.append(css_variable)
        
        # Count variable usage
        for match in self.variable_use_pattern.finditer(content):
            var_name = f"--{match.group(1).strip()}"
            self.variable_usage[var_name] += 1
    
    def _find_line_number(self, lines: List[str], selector: str) -> int:
        """Find line number of a selector."""
        for i, line in enumerate(lines, 1):
            if selector in line:
                return i
        return 1
    
    def _calculate_specificity(self, selector: str) -> int:
        """Calculate CSS selector specificity."""
        # Simplified specificity calculation
        # IDs = 100, classes/attributes/pseudo-classes = 10, elements = 1
        
        ids = len(re.findall(r'#[\w-]+', selector))
        classes = len(re.findall(r'\.[\w-]+', selector))
        attributes = len(re.findall(r'\[[\w-]+(="[^"]*")?\]', selector))
        pseudo_classes = len(re.findall(r':[\w-]+(?:\([^)]*\))?', selector))
        elements = len(re.findall(r'\b[a-zA-Z][\w-]*(?![#\.])', selector))
        
        return ids * 100 + (classes + attributes + pseudo_classes) * 10 + elements
    
    def _detect_duplicates(self) -> None:
        """Detect duplicate CSS rules."""
        # Group selectors by their normalized form
        selector_groups = defaultdict(list)
        
        for selector in self.selectors:
            normalized = self._normalize_selector(selector.selector)
            selector_groups[normalized].append(selector)
        
        # Find duplicates
        for normalized_selector, group in selector_groups.items():
            if len(group) > 1:
                # Check if they have similar properties (would need to parse the actual rules)
                locations = [(sel.file_path, sel.line_number) for sel in group]
                
                duplicate = DuplicateRule(
                    selector=group[0].selector,
                    properties=[],  # TODO: Extract actual properties
                    locations=locations
                )
                self.duplicates.append(duplicate)
    
    def _normalize_selector(self, selector: str) -> str:
        """Normalize selector for comparison."""
        # Remove extra whitespace and normalize
        return ' '.join(selector.split())
    
    def _find_unused_variables(self) -> List[str]:
        """Find CSS variables that are defined but never used."""
        defined_vars = {var.name for var in self.variables}
        used_vars = set(self.variable_usage.keys())
        return list(defined_vars - used_vars)
    
    def _calculate_performance_metrics(self) -> Dict[str, Any]:
        """Calculate performance-related metrics."""
        total_size = sum(f.size_bytes for f in self.files)
        total_gzipped = sum(f.size_gzipped for f in self.files)
        compression_ratio = (1 - total_gzipped / total_size) * 100 if total_size > 0 else 0
        
        # Category breakdown
        category_sizes = defaultdict(int)
        for file_info in self.files:
            category_sizes[file_info.category] += file_info.size_bytes
        
        # Largest files
        largest_files = sorted(self.files, key=lambda f: f.size_bytes, reverse=True)[:10]
        
        # Selector complexity
        avg_specificity = sum(s.specificity for s in self.selectors) / len(self.selectors) if self.selectors else 0
        high_specificity_selectors = [s for s in self.selectors if s.specificity > 100]
        
        return {
            'total_size_kb': round(total_size / 1024, 2),
            'total_gzipped_kb': round(total_gzipped / 1024, 2),
            'compression_ratio_percent': round(compression_ratio, 2),
            'category_breakdown': dict(category_sizes),
            'largest_files': [
                {
                    'path': f.path,
                    'size_kb': round(f.size_bytes / 1024, 2),
                    'category': f.category
                }
                for f in largest_files
            ],
            'average_specificity': round(avg_specificity, 2),
            'high_specificity_count': len(high_specificity_selectors),
            'total_selectors': len(self.selectors),
            'total_variables': len(self.variables),
            'unused_variables_count': len(self._find_unused_variables()),
            'duplicate_rules_count': len(self.duplicates)
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate optimization recommendations."""
        recommendations = []
        
        # File size recommendations
        large_files = [f for f in self.files if f.size_bytes > 50 * 1024]  # > 50KB
        if large_files:
            recommendations.append(
                f"Consider splitting large files: {', '.join(f.path for f in large_files[:3])}"
            )
        
        # Duplicate recommendations
        if self.duplicates:
            recommendations.append(
                f"Found {len(self.duplicates)} duplicate selectors that could be consolidated"
            )
        
        # Variable usage recommendations
        unused_vars = self._find_unused_variables()
        if unused_vars:
            recommendations.append(
                f"Remove {len(unused_vars)} unused CSS variables to reduce bundle size"
            )
        
        # Specificity recommendations
        high_specificity = [s for s in self.selectors if s.specificity > 100]
        if high_specificity:
            recommendations.append(
                f"Review {len(high_specificity)} high-specificity selectors for potential simplification"
            )
        
        # Category balance recommendations
        category_sizes = defaultdict(int)
        for file_info in self.files:
            category_sizes[file_info.category] += file_info.size_bytes
        
        if category_sizes.get('Page Styles', 0) > category_sizes.get('Components', 0):
            recommendations.append(
                "Page-specific styles are larger than component styles - consider componentization"
            )
        
        # Minification recommendations
        unminified_files = [f for f in self.files if f.category != 'Compiled/Minified' and f.size_bytes > 10 * 1024]
        if unminified_files:
            recommendations.append(
                f"Consider minifying {len(unminified_files)} large CSS files for production"
            )
        
        return recommendations


def main():
    """Main entry point for the CSS bundle analyzer."""
    parser = argparse.ArgumentParser(description='Analyze CSS bundle composition and performance')
    parser.add_argument('css_root', help='Root directory containing CSS files')
    parser.add_argument('--output', '-o', help='Output file for JSON results')
    parser.add_argument('--format', choices=['json', 'report', 'both'], default='both',
                       help='Output format')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.css_root):
        print(f"Error: CSS root directory '{args.css_root}' does not exist")
        return 1
    
    # Run analysis
    analyzer = CSSBundleAnalyzer(args.css_root)
    result = analyzer.analyze()
    
    # Output results
    if args.format in ['json', 'both']:
        json_output = args.output if args.output and args.output.endswith('.json') else 'css_analysis.json'
        with open(json_output, 'w', encoding='utf-8') as f:
            json.dump(asdict(result), f, indent=2, ensure_ascii=False)
        print(f"JSON analysis saved to: {json_output}")
    
    if args.format in ['report', 'both']:
        report_output = args.output if args.output and args.output.endswith('.md') else 'css_analysis_report.md'
        # We'll generate the report in the next step
        print(f"Report will be saved to: {report_output}")
    
    return 0


if __name__ == '__main__':
    exit(main())