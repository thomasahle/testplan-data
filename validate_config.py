#!/usr/bin/env python3
"""
Validation script for config.yaml test plan repository.

This script validates that:
1. All files referenced in config.yaml exist
2. PDF files have the expected number of pages
3. File paths are correctly formatted
4. No broken references exist

Usage:
    python validate_config.py [--fix-pages] [--verbose]
    
Options:
    --fix-pages    Update config.yaml with actual page counts for mismatches
    --verbose      Show detailed output for all checks
"""

import yaml
import os
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

def get_pdf_page_count(file_path: str) -> Optional[int]:
    """Get page count of a PDF file."""
    if not PYPDF2_AVAILABLE:
        # Try using pdfinfo command
        import subprocess
        try:
            result = subprocess.run(['pdfinfo', file_path], 
                                  capture_output=True, text=True, check=True)
            for line in result.stdout.split('\n'):
                if line.startswith('Pages:'):
                    return int(line.split(':')[1].strip())
        except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
            pass
        return None
    
    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            return len(reader.pages)
    except Exception as e:
        print(f"Warning: Could not read {file_path}: {e}")
        return None

def extract_files_from_config(config: Dict[str, Any]) -> List[Tuple[str, Any, str]]:
    """
    Extract all file references from config.yaml.
    Returns list of (file_path, expected_pages, category) tuples.
    """
    files = []
    
    def process_section(section_data: Any, section_name: str, subsection: str = ""):
        """Recursively process config sections to find file references."""
        if isinstance(section_data, dict):
            # Check for specs
            if 'specs' in section_data and section_data['specs'] is not None:
                for spec in section_data['specs']:
                    if isinstance(spec, dict) and 'file' in spec:
                        pages = spec.get('pages', 'unknown')
                        category = f"{section_name}.specs{subsection}"
                        files.append((spec['file'], pages, category))
            
            # Check for test_plans
            if 'test_plans' in section_data and section_data['test_plans'] is not None:
                for plan in section_data['test_plans']:
                    if isinstance(plan, dict) and 'file' in plan:
                        pages = plan.get('pages', 'unknown')
                        category = f"{section_name}.test_plans{subsection}"
                        files.append((plan['file'], pages, category))
            
            # Check for spec (single spec in subsections)
            if 'spec' in section_data and section_data['spec'] is not None:
                for spec in section_data['spec']:
                    if isinstance(spec, dict) and 'file' in spec:
                        pages = spec.get('pages', 'unknown')
                        category = f"{section_name}.spec{subsection}"
                        files.append((spec['file'], pages, category))
            
            # Recursively process other dict items
            for key, value in section_data.items():
                if key not in ['specs', 'test_plans', 'spec', 'category', 'description']:
                    process_section(value, section_name, f"{subsection}.{key}")
        
        elif isinstance(section_data, list):
            for item in section_data:
                process_section(item, section_name, subsection)
    
    # Process main sections
    for section_name, section_data in config.items():
        if section_name not in ['version', 'last_updated', 'description', 'stats', 'directories']:
            process_section(section_data, section_name)
    
    return files

def validate_files(files: List[Tuple[str, Any, str]], verbose: bool = False) -> Tuple[List[str], List[str], List[Tuple[str, int, Any]]]:
    """
    Validate file existence and page counts.
    Returns (missing_files, invalid_files, page_mismatches).
    """
    missing_files = []
    invalid_files = []
    page_mismatches = []
    
    for file_path, expected_pages, category in files:
        if verbose:
            print(f"Checking {file_path} ({category})")
        
        # Check if file exists
        if not os.path.exists(file_path):
            missing_files.append(f"{file_path} (from {category})")
            continue
        
        # Check if it's a PDF file
        if not file_path.lower().endswith('.pdf'):
            if verbose:
                print(f"  → Skipping non-PDF file: {file_path}")
            continue
        
        # Check if the file is actually a PDF
        try:
            with open(file_path, 'rb') as f:
                header = f.read(4)
                if header != b'%PDF':
                    invalid_files.append(f"{file_path} (not a valid PDF file)")
                    continue
        except Exception as e:
            invalid_files.append(f"{file_path} (cannot read file: {e})")
            continue
        
        # Skip files with download errors or unknown page counts
        if isinstance(expected_pages, str):
            if "error" in expected_pages.lower() or expected_pages.lower() in ['unknown', 'n/a']:
                if verbose:
                    print(f"  → Skipping {file_path}: {expected_pages}")
                continue
        
        # Get actual page count
        actual_pages = get_pdf_page_count(file_path)
        if actual_pages is None:
            if verbose:
                print(f"  → Could not determine page count for {file_path}")
            continue
        
        # Compare with expected
        try:
            expected_int = int(expected_pages)
            if actual_pages != expected_int:
                page_mismatches.append((file_path, actual_pages, expected_pages))
                if verbose:
                    print(f"  → Page mismatch: {file_path} has {actual_pages} pages, expected {expected_int}")
            elif verbose:
                print(f"  ✓ {file_path}: {actual_pages} pages (correct)")
        except (ValueError, TypeError):
            if verbose:
                print(f"  → Cannot validate pages for {file_path}: expected_pages={expected_pages}")
    
    return missing_files, invalid_files, page_mismatches

def print_results(missing_files: List[str], invalid_files: List[str], 
                 page_mismatches: List[Tuple[str, int, Any]], total_files: int):
    """Print validation results."""
    print(f"\n{'='*60}")
    print(f"VALIDATION RESULTS")
    print(f"{'='*60}")
    print(f"Total files checked: {total_files}")
    
    if missing_files:
        print(f"\n❌ MISSING FILES ({len(missing_files)}):")
        for file in missing_files:
            print(f"  • {file}")
    else:
        print(f"\n✅ All files exist ({total_files} files)")
    
    if invalid_files:
        print(f"\n❌ INVALID FILES ({len(invalid_files)}):")
        for file in invalid_files:
            print(f"  • {file}")
    else:
        print(f"\n✅ All PDF files are valid")
    
    if page_mismatches:
        print(f"\n⚠️  PAGE COUNT MISMATCHES ({len(page_mismatches)}):")
        for file_path, actual, expected in page_mismatches:
            print(f"  • {file_path}: has {actual} pages, expected {expected}")
    else:
        print(f"\n✅ All page counts are correct")
    
    # Summary
    issues = len(missing_files) + len(invalid_files) + len(page_mismatches)
    if issues == 0:
        print(f"\n🎉 ALL VALIDATIONS PASSED! Repository is in perfect condition.")
        return True
    else:
        print(f"\n⚠️  Found {issues} issue(s) that need attention.")
        return False

def update_config_with_actual_pages(config_file: str, page_mismatches: List[Tuple[str, int, Any]]) -> bool:
    """Update config.yaml with actual page counts for mismatched files."""
    if not page_mismatches:
        return False
    
    print(f"\nUpdating {config_file} with actual page counts...")
    
    # Read the config file as text to preserve formatting
    with open(config_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Update each mismatch
    changes_made = 0
    for file_path, actual_pages, expected_pages in page_mismatches:
        # Create patterns to find and replace the page count
        old_pattern = f'pages: {expected_pages}'
        new_pattern = f'pages: {actual_pages}'
        
        if old_pattern in content:
            content = content.replace(old_pattern, new_pattern)
            changes_made += 1
            print(f"  ✓ Updated {file_path}: {expected_pages} → {actual_pages} pages")
    
    if changes_made > 0:
        # Write back the updated content
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Successfully updated {changes_made} page counts in {config_file}")
        return True
    else:
        print("No updates were made (could not find page count patterns to update)")
        return False

def main():
    parser = argparse.ArgumentParser(description='Validate config.yaml file references and page counts')
    parser.add_argument('--fix-pages', action='store_true', 
                       help='Update config.yaml with actual page counts for mismatches')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Show detailed output for all checks')
    parser.add_argument('--config', default='config.yaml',
                       help='Path to config.yaml file (default: config.yaml)')
    
    args = parser.parse_args()
    
    # Check if config file exists
    if not os.path.exists(args.config):
        print(f"Error: Config file '{args.config}' not found")
        sys.exit(1)
    
    # Load config
    try:
        with open(args.config, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading {args.config}: {e}")
        sys.exit(1)
    
    print(f"Validating files referenced in {args.config}...")
    if not PYPDF2_AVAILABLE:
        print("Note: PyPDF2 not available, using pdfinfo command for page counts")
    
    # Extract all file references
    files = extract_files_from_config(config)
    print(f"Found {len(files)} file references")
    
    # Validate files
    missing_files, invalid_files, page_mismatches = validate_files(files, args.verbose)
    
    # Print results
    success = print_results(missing_files, invalid_files, page_mismatches, len(files))
    
    # Fix pages if requested
    if args.fix_pages and page_mismatches:
        if update_config_with_actual_pages(args.config, page_mismatches):
            print("\n✅ Config file updated! Please review the changes and commit if appropriate.")
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()