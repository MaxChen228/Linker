#!/usr/bin/env python3
"""
CSS Variables Usage Analyzer
Identifies CSS variables that are defined but never used in the codebase.
"""

import os
import re
import json
from pathlib import Path
from typing import Set, Dict, List, Tuple

def extract_css_variable_definitions(css_content: str) -> Set[str]:
    """Extract all CSS variable definitions from CSS content."""
    # Pattern to match --variable-name: value;
    pattern = r'--([a-zA-Z0-9-_]+)\s*:'
    matches = re.findall(pattern, css_content)
    return set(matches)

def extract_css_variable_usage(content: str) -> Set[str]:
    """Extract all CSS variable usage from content (var(--variable-name))."""
    # Pattern to match var(--variable-name)
    pattern = r'var\(--([a-zA-Z0-9-_]+)\)'
    matches = re.findall(pattern, content)
    return set(matches)

def extract_css_variable_references(content: str) -> Set[str]:
    """Extract direct CSS variable references (--variable-name without var())."""
    # Pattern to match --variable-name (but not in definitions)
    # This is for cases where variables might be referenced directly
    pattern = r'(?<!:)\s--([a-zA-Z0-9-_]+)(?!\s*:)'
    matches = re.findall(pattern, content)
    return set(matches)

def scan_directory_for_css_files(directory: Path) -> List[Path]:
    """Recursively find all CSS files in directory."""
    css_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.css'):
                css_files.append(Path(root) / file)
    return css_files

def scan_directory_for_all_files(directory: Path, extensions: List[str]) -> List[Path]:
    """Recursively find all files with given extensions."""
    files = []
    for root, dirs, files_list in os.walk(directory):
        for file in files_list:
            if any(file.endswith(ext) for ext in extensions):
                files.append(Path(root) / file)
    return files

def analyze_css_variables():
    """Main analysis function."""
    base_path = Path('/Users/chenliangyu/Desktop/linker-cli')
    css_dir = base_path / 'web' / 'static' / 'css'
    
    # Step 1: Extract all variable definitions from token files
    token_dir = css_dir / 'design-system' / '01-tokens'
    all_defined_vars = set()
    defined_vars_by_file = {}
    
    print("🔍 Scanning CSS token files for variable definitions...")
    for css_file in scan_directory_for_css_files(token_dir):
        try:
            with open(css_file, 'r', encoding='utf-8') as f:
                content = f.read()
                vars_in_file = extract_css_variable_definitions(content)
                all_defined_vars.update(vars_in_file)
                if vars_in_file:
                    defined_vars_by_file[str(css_file.relative_to(base_path))] = list(vars_in_file)
                    print(f"  📄 {css_file.name}: {len(vars_in_file)} variables")
        except Exception as e:
            print(f"  ❌ Error reading {css_file}: {e}")
    
    print(f"\n📊 Total variables defined: {len(all_defined_vars)}")
    
    # Step 2: Find all variable usage across all CSS files
    all_used_vars = set()
    used_vars_by_file = {}
    
    print("\n🔍 Scanning all CSS files for variable usage...")
    for css_file in scan_directory_for_css_files(css_dir):
        try:
            with open(css_file, 'r', encoding='utf-8') as f:
                content = f.read()
                used_vars = extract_css_variable_usage(content)
                ref_vars = extract_css_variable_references(content)
                all_vars_in_file = used_vars.union(ref_vars)
                
                all_used_vars.update(all_vars_in_file)
                if all_vars_in_file:
                    used_vars_by_file[str(css_file.relative_to(base_path))] = list(all_vars_in_file)
                    print(f"  📄 {css_file.name}: {len(all_vars_in_file)} variables used")
        except Exception as e:
            print(f"  ❌ Error reading {css_file}: {e}")
    
    # Step 3: Check for usage in HTML and JS files
    print("\n🔍 Scanning HTML and template files for variable usage...")
    html_js_files = scan_directory_for_all_files(base_path, ['.html', '.js', '.py'])
    
    for file_path in html_js_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                used_vars = extract_css_variable_usage(content)
                ref_vars = extract_css_variable_references(content)
                all_vars_in_file = used_vars.union(ref_vars)
                
                if all_vars_in_file:
                    all_used_vars.update(all_vars_in_file)
                    used_vars_by_file[str(file_path.relative_to(base_path))] = list(all_vars_in_file)
                    print(f"  📄 {file_path.name}: {len(all_vars_in_file)} variables used")
        except Exception as e:
            # Skip binary files or files we can't read
            continue
    
    print(f"\n📊 Total variables used: {len(all_used_vars)}")
    
    # Step 4: Find unused variables
    unused_vars = all_defined_vars - all_used_vars
    
    print(f"\n🚨 Unused variables: {len(unused_vars)}")
    
    # Step 5: Categorize unused variables
    unused_by_category = {
        'spacing': [],
        'colors': [],
        'typography': [],
        'shadows': [],
        'effects': [],
        'z-index': [],
        'border-radius': [],
        'glass': [],
        'buttons': [],
        'animations': [],
        'other': []
    }
    
    for var in unused_vars:
        categorized = False
        for category in unused_by_category.keys():
            if category == 'other':
                continue
            
            # Check if category name is in variable name
            if category in var:
                unused_by_category[category].append(var)
                categorized = True
                break
            
            # Check specific keywords for categorization
            keyword_mapping = {
                'space': 'spacing',
                'text': 'typography', 
                'font': 'typography',
                'heading': 'typography',
                'body': 'typography',
                'caption': 'typography',
                'weight': 'typography',
                'height': 'typography',
                'spacing': 'typography',
                'color': 'colors',
                'primary': 'colors',
                'success': 'colors',
                'error': 'colors',
                'warning': 'colors',
                'gray': 'colors',
                'accent': 'colors',
                'surface': 'colors',
                'border': 'colors',
                'bg': 'colors',
                'shadow': 'shadows',
                'transition': 'effects',
                'ease': 'effects',
                'animation': 'animations',
                'duration': 'animations',
                'radius': 'border-radius',
                'glass': 'glass',
                'btn': 'buttons',
                'z': 'z-index'
            }
            
            for keyword, target_category in keyword_mapping.items():
                if keyword in var and target_category == category:
                    unused_by_category[category].append(var)
                    categorized = True
                    break
            
            if categorized:
                break
        
        if not categorized:
            unused_by_category['other'].append(var)
    
    # Generate detailed report
    print("\n" + "="*80)
    print("🔥 DETAILED UNUSED VARIABLES REPORT")
    print("="*80)
    
    for category, vars_list in unused_by_category.items():
        if vars_list:
            print(f"\n📂 {category.upper()} ({len(vars_list)} unused)")
            print("-" * 40)
            for var in sorted(vars_list):
                print(f"  • --{var}")
    
    # Generate impact analysis
    total_defined = len(all_defined_vars)
    total_unused = len(unused_vars)
    usage_rate = ((total_defined - total_unused) / total_defined) * 100 if total_defined > 0 else 0
    
    print("\n" + "="*80)
    print("📈 IMPACT ANALYSIS")
    print("="*80)
    print(f"Total variables defined: {total_defined}")
    print(f"Total variables used: {len(all_used_vars)}")
    print(f"Total variables unused: {total_unused}")
    print(f"Usage rate: {usage_rate:.1f}%")
    print(f"Cleanup potential: {total_unused} variables can be removed")
    
    # Save detailed JSON report
    report = {
        'summary': {
            'total_defined': total_defined,
            'total_used': len(all_used_vars),
            'total_unused': total_unused,
            'usage_rate': round(usage_rate, 1)
        },
        'defined_variables_by_file': defined_vars_by_file,
        'used_variables_by_file': used_vars_by_file,
        'unused_variables_by_category': unused_by_category,
        'all_unused_variables': list(unused_vars)
    }
    
    report_file = base_path / 'css_variables_analysis_report.json'
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Detailed report saved to: {report_file}")
    
    return report

if __name__ == "__main__":
    analyze_css_variables()