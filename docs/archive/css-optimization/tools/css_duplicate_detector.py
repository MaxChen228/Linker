#!/usr/bin/env python3
"""
CSS Duplicate Rule Detector
Advanced detection of duplicate CSS rules, similar selectors, and optimization opportunities.
"""

import os
import re
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict
from datetime import datetime
import argparse


@dataclass
class CSSRule:
    """Represents a CSS rule with its properties."""
    selector: str
    properties: Dict[str, str]
    file_path: str
    line_number: int
    raw_css: str
    specificity: int
    

@dataclass
class DuplicateGroup:
    """Group of duplicate or similar CSS rules."""
    type: str  # 'exact', 'similar_properties', 'similar_selectors'
    rules: List[CSSRule]
    similarity_score: float
    potential_savings_bytes: int
    consolidation_suggestion: str
    

@dataclass
class PropertyAnalysis:
    """Analysis of CSS property usage patterns."""
    property_name: str
    usage_count: int
    unique_values: Set[str]
    most_common_value: str
    files_used: Set[str]
    inconsistent_usage: bool
    

@dataclass
class DuplicateAnalysisResult:
    """Complete duplicate analysis result."""
    timestamp: str
    total_rules: int
    duplicate_groups: List[DuplicateGroup]
    property_analysis: List[PropertyAnalysis]
    consolidation_opportunities: List[str]
    potential_savings_bytes: int
    recommendations: List[str]


class CSSDuplicateDetector:
    """Advanced CSS duplicate rule detector."""
    
    def __init__(self, css_root: str):
        self.css_root = Path(css_root)
        self.rules: List[CSSRule] = []
        self.property_usage: Dict[str, List[Tuple[str, str, str]]] = defaultdict(list)
        
        # CSS parsing patterns
        self.rule_pattern = re.compile(r'([^{]+){([^}]+)}', re.MULTILINE | re.DOTALL)
        self.property_pattern = re.compile(r'([^:]+):\s*([^;]+);?')
        self.comment_pattern = re.compile(r'/\*.*?\*/', re.DOTALL)
        
        # Normalization patterns
        self.whitespace_pattern = re.compile(r'\s+')
        self.vendor_prefix_pattern = re.compile(r'-(?:webkit|moz|ms|o)-')
        
    def analyze(self) -> DuplicateAnalysisResult:
        """Perform complete duplicate analysis."""
        print("Starting CSS duplicate analysis...")
        
        # Parse all CSS files
        self._parse_css_files()
        print(f"Parsed {len(self.rules)} CSS rules")
        
        # Find duplicate groups
        duplicate_groups = self._find_duplicate_groups()
        print(f"Found {len(duplicate_groups)} duplicate groups")
        
        # Analyze property usage
        property_analysis = self._analyze_property_usage()
        
        # Generate consolidation opportunities
        consolidation_opportunities = self._find_consolidation_opportunities()
        
        # Calculate potential savings
        potential_savings = sum(group.potential_savings_bytes for group in duplicate_groups)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(duplicate_groups, property_analysis)
        
        return DuplicateAnalysisResult(
            timestamp=datetime.now().isoformat(),
            total_rules=len(self.rules),
            duplicate_groups=duplicate_groups,
            property_analysis=property_analysis,
            consolidation_opportunities=consolidation_opportunities,
            potential_savings_bytes=potential_savings,
            recommendations=recommendations
        )
    
    def _parse_css_files(self) -> None:
        """Parse all CSS files and extract rules."""
        css_files = list(self.css_root.glob('**/*.css'))
        
        for css_file in css_files:
            try:
                with open(css_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Remove comments but preserve structure for line numbers
                content_no_comments = self.comment_pattern.sub(lambda m: ' ' * len(m.group(0)), content)
                
                # Parse rules
                for match in self.rule_pattern.finditer(content_no_comments):
                    selector_text = match.group(1).strip()
                    properties_text = match.group(2).strip()
                    
                    # Skip empty rules or at-rules
                    if not selector_text or not properties_text or selector_text.startswith('@'):
                        continue
                    
                    # Parse properties
                    properties = {}
                    for prop_match in self.property_pattern.finditer(properties_text):
                        prop_name = prop_match.group(1).strip()
                        prop_value = prop_match.group(2).strip()
                        properties[prop_name] = prop_value
                        
                        # Track property usage
                        self.property_usage[prop_name].append((prop_value, str(css_file), selector_text))
                    
                    if properties:  # Only add rules with properties
                        # Calculate line number
                        line_number = content[:match.start()].count('\n') + 1
                        
                        # Handle multiple selectors
                        selectors = [s.strip() for s in selector_text.split(',')]
                        
                        for selector in selectors:
                            if selector:
                                rule = CSSRule(
                                    selector=selector,
                                    properties=properties.copy(),
                                    file_path=str(css_file.relative_to(self.css_root)),
                                    line_number=line_number,
                                    raw_css=match.group(0),
                                    specificity=self._calculate_specificity(selector)
                                )
                                self.rules.append(rule)
                                
            except Exception as e:
                print(f"Error parsing CSS file {css_file}: {e}")
    
    def _calculate_specificity(self, selector: str) -> int:
        """Calculate CSS selector specificity."""
        # IDs = 100, classes/attributes/pseudo-classes = 10, elements = 1
        ids = len(re.findall(r'#[\w-]+', selector))
        classes = len(re.findall(r'\.[\w-]+', selector))
        attributes = len(re.findall(r'\[[\w-]+(="[^"]*")?\]', selector))
        pseudo_classes = len(re.findall(r':[\w-]+(?:\([^)]*\))?', selector))
        elements = len(re.findall(r'\b[a-zA-Z][\w-]*(?![#\.])', selector))
        
        return ids * 100 + (classes + attributes + pseudo_classes) * 10 + elements
    
    def _find_duplicate_groups(self) -> List[DuplicateGroup]:
        """Find groups of duplicate and similar CSS rules."""
        duplicate_groups = []
        
        # Group 1: Exact duplicates (same selector and properties)
        exact_duplicates = self._find_exact_duplicates()
        duplicate_groups.extend(exact_duplicates)
        
        # Group 2: Same properties, different selectors
        similar_properties = self._find_similar_properties()
        duplicate_groups.extend(similar_properties)
        
        # Group 3: Similar selectors, different properties
        similar_selectors = self._find_similar_selectors()
        duplicate_groups.extend(similar_selectors)
        
        # Group 4: Vendor prefix duplicates
        vendor_duplicates = self._find_vendor_prefix_duplicates()
        duplicate_groups.extend(vendor_duplicates)
        
        return duplicate_groups
    
    def _find_exact_duplicates(self) -> List[DuplicateGroup]:
        """Find rules with exactly the same selector and properties."""
        groups = []
        rule_groups = defaultdict(list)
        
        for rule in self.rules:
            # Create a hash of selector and properties
            properties_str = '|'.join(f"{k}:{v}" for k, v in sorted(rule.properties.items()))
            key = f"{rule.selector}|{properties_str}"
            rule_groups[key].append(rule)
        
        for key, rules_list in rule_groups.items():
            if len(rules_list) > 1:
                # Calculate potential savings (all but one can be removed)
                total_size = sum(len(rule.raw_css) for rule in rules_list)
                savings = total_size - len(rules_list[0].raw_css)
                
                group = DuplicateGroup(
                    type='exact',
                    rules=rules_list,
                    similarity_score=1.0,
                    potential_savings_bytes=savings,
                    consolidation_suggestion=f"Remove {len(rules_list) - 1} duplicate rules"
                )
                groups.append(group)
        
        return groups
    
    def _find_similar_properties(self) -> List[DuplicateGroup]:
        """Find rules with similar property sets but different selectors."""
        groups = []
        property_groups = defaultdict(list)
        
        for rule in self.rules:
            # Create a hash of just the properties
            properties_str = '|'.join(f"{k}:{v}" for k, v in sorted(rule.properties.items()))
            property_groups[properties_str].append(rule)
        
        for properties_str, rules_list in property_groups.items():
            if len(rules_list) > 1:
                # Check if selectors are different
                selectors = set(rule.selector for rule in rules_list)
                if len(selectors) > 1:
                    # Calculate similarity based on property overlap
                    similarity = self._calculate_property_similarity(rules_list)
                    
                    if similarity > 0.8:  # 80% similarity threshold
                        savings = self._estimate_consolidation_savings(rules_list)
                        
                        # Suggest selector grouping
                        selector_list = list(selectors)
                        suggestion = f"Combine selectors: {', '.join(selector_list[:3])}"
                        if len(selector_list) > 3:
                            suggestion += f" and {len(selector_list) - 3} more"
                        
                        group = DuplicateGroup(
                            type='similar_properties',
                            rules=rules_list,
                            similarity_score=similarity,
                            potential_savings_bytes=savings,
                            consolidation_suggestion=suggestion
                        )
                        groups.append(group)
        
        return groups
    
    def _find_similar_selectors(self) -> List[DuplicateGroup]:
        """Find rules with similar selectors but different properties."""
        groups = []
        selector_groups = defaultdict(list)
        
        for rule in self.rules:
            # Normalize selector for comparison
            normalized = self._normalize_selector(rule.selector)
            selector_groups[normalized].append(rule)
        
        for normalized_selector, rules_list in selector_groups.items():
            if len(rules_list) > 1:
                # Check for property overlaps that could be consolidated
                property_overlap = self._find_property_overlap(rules_list)
                
                if property_overlap:
                    similarity = len(property_overlap) / max(len(rule.properties) for rule in rules_list)
                    
                    if similarity > 0.5:  # 50% property overlap
                        savings = self._estimate_consolidation_savings(rules_list)
                        
                        group = DuplicateGroup(
                            type='similar_selectors',
                            rules=rules_list,
                            similarity_score=similarity,
                            potential_savings_bytes=savings,
                            consolidation_suggestion=f"Consolidate {len(property_overlap)} common properties"
                        )
                        groups.append(group)
        
        return groups
    
    def _find_vendor_prefix_duplicates(self) -> List[DuplicateGroup]:
        """Find duplicate vendor prefix rules."""
        groups = []
        prefix_groups = defaultdict(list)
        
        for rule in self.rules:
            # Remove vendor prefixes for comparison
            normalized_props = {}
            for prop, value in rule.properties.items():
                base_prop = self.vendor_prefix_pattern.sub('', prop)
                normalized_props[base_prop] = value
            
            # Group by normalized properties
            props_key = '|'.join(f"{k}:{v}" for k, v in sorted(normalized_props.items()))
            key = f"{rule.selector}|{props_key}"
            prefix_groups[key].append(rule)
        
        for key, rules_list in prefix_groups.items():
            if len(rules_list) > 1:
                # Check if these are actually vendor prefix variations
                has_vendor_prefixes = any(
                    any(self.vendor_prefix_pattern.search(prop) for prop in rule.properties)
                    for rule in rules_list
                )
                
                if has_vendor_prefixes:
                    savings = self._estimate_consolidation_savings(rules_list)
                    
                    group = DuplicateGroup(
                        type='vendor_prefix',
                        rules=rules_list,
                        similarity_score=0.9,
                        potential_savings_bytes=savings,
                        consolidation_suggestion="Combine vendor prefix variations"
                    )
                    groups.append(group)
        
        return groups
    
    def _calculate_property_similarity(self, rules: List[CSSRule]) -> float:
        """Calculate similarity between rules based on their properties."""
        if len(rules) < 2:
            return 0.0
        
        # Get all unique properties across rules
        all_properties = set()
        for rule in rules:
            all_properties.update(rule.properties.keys())
        
        if not all_properties:
            return 0.0
        
        # Calculate Jaccard similarity
        common_properties = set(rules[0].properties.keys())
        for rule in rules[1:]:
            common_properties.intersection_update(rule.properties.keys())
        
        return len(common_properties) / len(all_properties)
    
    def _normalize_selector(self, selector: str) -> str:
        """Normalize selector for comparison."""
        # Remove extra whitespace
        normalized = self.whitespace_pattern.sub(' ', selector.strip())
        
        # Sort compound selectors for comparison
        if ',' in normalized:
            parts = [part.strip() for part in normalized.split(',')]
            normalized = ', '.join(sorted(parts))
        
        return normalized
    
    def _find_property_overlap(self, rules: List[CSSRule]) -> Set[str]:
        """Find properties that are common across multiple rules."""
        if not rules:
            return set()
        
        common_props = set(rules[0].properties.keys())
        for rule in rules[1:]:
            common_props.intersection_update(rule.properties.keys())
        
        return common_props
    
    def _estimate_consolidation_savings(self, rules: List[CSSRule]) -> int:
        """Estimate bytes saved by consolidating rules."""
        if len(rules) < 2:
            return 0
        
        # Simple estimation: assume 30% savings from consolidation
        total_size = sum(len(rule.raw_css) for rule in rules)
        return int(total_size * 0.3)
    
    def _analyze_property_usage(self) -> List[PropertyAnalysis]:
        """Analyze CSS property usage patterns."""
        analyses = []
        
        for prop_name, usages in self.property_usage.items():
            if len(usages) < 2:  # Skip properties used only once
                continue
            
            values = [usage[0] for usage in usages]
            files = set(usage[1] for usage in usages)
            
            # Find most common value
            value_counts = Counter(values)
            most_common_value = value_counts.most_common(1)[0][0]
            
            # Check for inconsistent usage (many different values)
            unique_values = set(values)
            inconsistent = len(unique_values) > 5 and len(unique_values) > len(usages) * 0.5
            
            analysis = PropertyAnalysis(
                property_name=prop_name,
                usage_count=len(usages),
                unique_values=unique_values,
                most_common_value=most_common_value,
                files_used=files,
                inconsistent_usage=inconsistent
            )
            analyses.append(analysis)
        
        return sorted(analyses, key=lambda a: a.usage_count, reverse=True)
    
    def _find_consolidation_opportunities(self) -> List[str]:
        """Find specific consolidation opportunities."""
        opportunities = []
        
        # Analyze property patterns
        for prop_name, usages in self.property_usage.items():
            values = [usage[0] for usage in usages]
            value_counts = Counter(values)
            
            # If one value dominates, suggest standardization
            if len(value_counts) > 1:
                most_common = value_counts.most_common(1)[0]
                if most_common[1] > len(usages) * 0.7:  # 70% use the same value
                    opportunities.append(
                        f"Standardize '{prop_name}' values - {most_common[1]}/{len(usages)} use '{most_common[0]}'"
                    )
        
        # Look for mergeable utility classes
        utility_patterns = ['.m-', '.p-', '.text-', '.bg-', '.border-']
        for pattern in utility_patterns:
            matching_rules = [rule for rule in self.rules if pattern in rule.selector]
            if len(matching_rules) > 10:
                opportunities.append(
                    f"Consider consolidating {len(matching_rules)} '{pattern}*' utility classes"
                )
        
        return opportunities
    
    def _generate_recommendations(self, duplicate_groups: List[DuplicateGroup], 
                                property_analysis: List[PropertyAnalysis]) -> List[str]:
        """Generate optimization recommendations."""
        recommendations = []
        
        # Duplicate-based recommendations
        exact_duplicates = [g for g in duplicate_groups if g.type == 'exact']
        if exact_duplicates:
            total_duplicates = sum(len(g.rules) - 1 for g in exact_duplicates)
            recommendations.append(
                f"Remove {total_duplicates} exact duplicate rules across {len(exact_duplicates)} groups"
            )
        
        similar_props = [g for g in duplicate_groups if g.type == 'similar_properties']
        if similar_props:
            recommendations.append(
                f"Consolidate {len(similar_props)} groups of rules with similar properties"
            )
        
        # Property usage recommendations
        inconsistent_props = [p for p in property_analysis if p.inconsistent_usage]
        if inconsistent_props:
            recommendations.append(
                f"Standardize {len(inconsistent_props)} properties with inconsistent values"
            )
        
        # High-usage properties
        high_usage_props = [p for p in property_analysis if p.usage_count > 20]
        if high_usage_props:
            recommendations.append(
                f"Consider creating utility classes for {len(high_usage_props)} frequently-used properties"
            )
        
        # Total savings estimate
        total_savings = sum(g.potential_savings_bytes for g in duplicate_groups)
        if total_savings > 1024:
            recommendations.append(
                f"Total potential savings: {total_savings / 1024:.1f}KB from consolidation"
            )
        
        return recommendations


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Detect CSS duplicate rules and consolidation opportunities')
    parser.add_argument('css_root', help='Root directory containing CSS files')
    parser.add_argument('--output', '-o', help='Output file for JSON results')
    parser.add_argument('--threshold', type=float, default=0.8, 
                       help='Similarity threshold for duplicate detection (0.0-1.0)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.css_root):
        print(f"Error: CSS root directory '{args.css_root}' does not exist")
        return 1
    
    # Run analysis
    detector = CSSDuplicateDetector(args.css_root)
    result = detector.analyze()
    
    # Output results
    output_file = args.output or 'css_duplicate_analysis.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(asdict(result), f, indent=2, ensure_ascii=False, default=str)
    
    print(f"Duplicate analysis complete. Results saved to: {output_file}")
    print(f"Total rules analyzed: {result.total_rules}")
    print(f"Duplicate groups found: {len(result.duplicate_groups)}")
    print(f"Potential savings: {result.potential_savings_bytes / 1024:.1f}KB")
    
    # Print top recommendations
    if result.recommendations:
        print("\nTop recommendations:")
        for i, rec in enumerate(result.recommendations[:5], 1):
            print(f"{i}. {rec}")


if __name__ == '__main__':
    main()