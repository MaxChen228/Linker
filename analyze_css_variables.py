#!/usr/bin/env python3
"""
Analyze CSS variables to identify unused ones that can be safely deleted.
"""

import re
import os
from pathlib import Path
from collections import defaultdict

def extract_css_variables(file_path):
    """Extract all CSS variable definitions from a file."""
    variables = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Find all variable definitions (--var-name: value;)
            pattern = r'--([a-zA-Z0-9-_]+)\s*:'
            matches = re.findall(pattern, content)
            variables.extend([f'--{match}' for match in matches])
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    return variables

def extract_css_usage(file_path):
    """Extract all CSS variable usage from a file."""
    usage = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Find all variable usage (var(--var-name))
            pattern = r'var\((--[a-zA-Z0-9-_]+)\)'
            matches = re.findall(pattern, content)
            usage.extend(matches)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    return usage

def categorize_variable(var_name):
    """Categorize variable by its name."""
    var_lower = var_name.lower()
    
    # Colors
    if any(x in var_lower for x in ['color', 'gray', 'grey', 'accent', 'primary', 'success', 'warning', 'error', 'info', 'surface', 'text', 'bg', 'border']):
        if 'rgb' in var_lower:
            return 'colors-rgb'
        return 'colors'
    
    # Spacing
    if any(x in var_lower for x in ['space', 'spacing', 'margin', 'padding', 'gap']):
        return 'spacing'
    
    # Typography
    if any(x in var_lower for x in ['font', 'text', 'heading', 'body', 'weight', 'size', 'height', 'letter-spacing']):
        return 'typography'
    
    # Shadows
    if any(x in var_lower for x in ['shadow', 'elevation', 'blur']):
        return 'shadows'
    
    # Border radius
    if any(x in var_lower for x in ['radius', 'border-radius']):
        return 'border-radius'
    
    # Animations
    if any(x in var_lower for x in ['animation', 'transition', 'duration', 'ease', 'timing']):
        return 'animations'
    
    # Z-index
    if 'z-' in var_lower or 'z' == var_lower.strip('-'):
        return 'z-index'
    
    # Performance/Glass/Effects
    if any(x in var_lower for x in ['glass', 'will-change', 'backdrop', 'blur', 'opacity', 'hover', 'focus']):
        return 'effects'
    
    return 'other'

def main():
    base_dir = Path('/Users/chenliangyu/Desktop/linker-cli')
    
    # Collect all defined variables
    defined_variables = set()
    used_variables = set()
    
    # Find all CSS files
    css_files = []
    css_files.extend(base_dir.rglob('**/*.css'))
    
    print(f"Found {len(css_files)} CSS files")
    
    # Extract definitions
    for css_file in css_files:
        if 'node_modules' in str(css_file) or 'htmlcov' in str(css_file):
            continue
        vars_defined = extract_css_variables(css_file)
        defined_variables.update(vars_defined)
    
    print(f"Found {len(defined_variables)} defined variables")
    
    # Extract usage
    for css_file in css_files:
        if 'node_modules' in str(css_file) or 'htmlcov' in str(css_file):
            continue
        vars_used = extract_css_usage(css_file)
        used_variables.update(vars_used)
    
    # Also check HTML files
    html_files = list(base_dir.rglob('**/*.html'))
    for html_file in html_files:
        if 'node_modules' in str(html_file) or 'htmlcov' in str(html_file):
            continue
        vars_used = extract_css_usage(html_file)
        used_variables.update(vars_used)
    
    print(f"Found {len(used_variables)} used variables")
    
    # Find unused variables
    unused_variables = defined_variables - used_variables
    
    print(f"Found {len(unused_variables)} unused variables")
    
    # Categorize unused variables
    categories = defaultdict(list)
    for var in sorted(unused_variables):
        category = categorize_variable(var)
        categories[category].append(var)
    
    # Generate report
    report = []
    report.append("# Unused CSS Variables Analysis Report")
    report.append("")
    report.append(f"**Total defined variables:** {len(defined_variables)}")
    report.append(f"**Total used variables:** {len(used_variables)}")
    report.append(f"**Total unused variables:** {len(unused_variables)}")
    report.append("")
    report.append("## Unused Variables by Category")
    report.append("")
    
    for category, variables in sorted(categories.items()):
        if not variables:
            continue
        report.append(f"### {category.title()} ({len(variables)} variables)")
        report.append("")
        for var in sorted(variables):
            report.append(f"- `{var}`")
        report.append("")
    
    # Also show used variables for reference
    used_categories = defaultdict(list)
    for var in sorted(used_variables):
        category = categorize_variable(var)
        used_categories[category].append(var)
    
    report.append("## Used Variables by Category (for reference)")
    report.append("")
    
    for category, variables in sorted(used_categories.items()):
        if not variables:
            continue
        report.append(f"### {category.title()} ({len(variables)} variables)")
        report.append("")
        report.append(f"Variables: {', '.join(['`' + var + '`' for var in sorted(variables)[:10]])}{'...' if len(variables) > 10 else ''}")
        report.append("")
    
    return '\n'.join(report)

if __name__ == '__main__':
    result = main()
    print(result)