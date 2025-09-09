#!/usr/bin/env python3
"""
Device Mappings Report Generator

This script generates comprehensive reports from the device-mappings.yaml file:
1. Coverage report showing devices with specs and test plans
2. Category breakdown
3. Orphaned files analysis
4. Markdown and CSV export options

Usage:
    python3 generate_report.py [--format markdown|csv|console]
    python3 generate_report.py --help
"""

import yaml
import csv
import argparse
from pathlib import Path
from typing import Dict, List, Tuple
import sys
from datetime import datetime


def load_device_mappings() -> Dict:
    """Load the device mappings from YAML file."""
    try:
        with open("device-mappings.yaml", "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print("ERROR: device-mappings.yaml file not found!")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"ERROR: Invalid YAML in device-mappings.yaml: {e}")
        sys.exit(1)


def generate_console_report() -> None:
    """Generate a console-formatted report."""
    data = load_device_mappings()
    
    print("=" * 70)
    print("DEVICE COVERAGE REPORT")
    print("=" * 70)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    devices = data.get("devices", [])
    orphaned_specs = data.get("orphaned_specs", [])
    orphaned_tests = data.get("orphaned_test_plans", [])
    
    print(f"\n📊 OVERVIEW:")
    print(f"   Total devices with both specs & test plans: {len(devices)}")
    print(f"   Total orphaned specs: {len(orphaned_specs)}")
    print(f"   Total orphaned test plans: {len(orphaned_tests)}")
    
    # Group devices by category
    by_category = {}
    for device in devices:
        category = device.get("category", "Uncategorized")
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(device)
    
    print(f"\n📁 DEVICES BY CATEGORY:")
    for category, category_devices in sorted(by_category.items()):
        print(f"\n   {category} ({len(category_devices)} devices):")
        for device in category_devices:
            spec_count = len(device.get("specs", []))
            test_count = len(device.get("test_plans", []))
            print(f"   • {device.get('name', 'Unnamed')} ({device.get('id', 'no-id')})")
            print(f"     Specs: {spec_count}, Test Plans: {test_count}")
    
    # Orphaned specs by category
    if orphaned_specs:
        print(f"\n📄 ORPHANED SPECS BY CATEGORY:")
        orphan_by_category = {}
        for spec in orphaned_specs:
            category = spec.get("category", "Uncategorized")
            if category not in orphan_by_category:
                orphan_by_category[category] = []
            orphan_by_category[category].append(spec)
        
        for category, specs in sorted(orphan_by_category.items()):
            print(f"\n   {category} ({len(specs)} specs):")
            for spec in specs:
                print(f"   • {spec.get('standard', 'Unknown')} - {spec.get('description', 'No description')}")
                print(f"     File: {spec.get('path', 'No path')}")
    
    # Orphaned test plans by category
    if orphaned_tests:
        print(f"\n🧪 ORPHANED TEST PLANS BY CATEGORY:")
        test_by_category = {}
        for test in orphaned_tests:
            category = test.get("category", "Uncategorized")
            if category not in test_by_category:
                test_by_category[category] = []
            test_by_category[category].append(test)
        
        for category, tests in sorted(test_by_category.items()):
            print(f"\n   {category} ({len(tests)} test plans):")
            for test in tests:
                print(f"   • {test.get('type', 'Unknown type')}")
                if test.get('version'):
                    print(f"     Version: {test['version']}")
                if test.get('note'):
                    print(f"     Note: {test['note']}")
                print(f"     File: {test.get('path', 'No path')}")
    
    print("\n" + "=" * 70)


def generate_markdown_report() -> str:
    """Generate a Markdown-formatted report."""
    data = load_device_mappings()
    
    devices = data.get("devices", [])
    orphaned_specs = data.get("orphaned_specs", [])
    orphaned_tests = data.get("orphaned_test_plans", [])
    
    md = []
    md.append("# Device Coverage Report")
    md.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Overview
    md.append("\n## Overview")
    md.append(f"- **Total devices with both specs & test plans:** {len(devices)}")
    md.append(f"- **Total orphaned specs:** {len(orphaned_specs)}")
    md.append(f"- **Total orphaned test plans:** {len(orphaned_tests)}")
    
    # Devices by category
    md.append("\n## Devices with Both Specs and Test Plans")
    
    by_category = {}
    for device in devices:
        category = device.get("category", "Uncategorized")
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(device)
    
    for category, category_devices in sorted(by_category.items()):
        md.append(f"\n### {category} ({len(category_devices)} devices)")
        
        for device in category_devices:
            spec_count = len(device.get("specs", []))
            test_count = len(device.get("test_plans", []))
            md.append(f"- **{device.get('name', 'Unnamed')}** (`{device.get('id', 'no-id')}`)")
            md.append(f"  - Specs: {spec_count}, Test Plans: {test_count}")
            
            # List specs
            if device.get("specs"):
                md.append("  - Specifications:")
                for spec in device["specs"]:
                    standard = spec.get("standard", "Unknown")
                    path = spec.get("path", "")
                    md.append(f"    - {standard}: `{path}`")
            
            # List test plans
            if device.get("test_plans"):
                md.append("  - Test Plans:")
                for test in device["test_plans"]:
                    test_type = test.get("type", "Unknown")
                    path = test.get("path", "")
                    version = test.get("version", "")
                    version_str = f" ({version})" if version else ""
                    md.append(f"    - {test_type}{version_str}: `{path}`")
    
    # Orphaned specs
    if orphaned_specs:
        md.append("\n## Orphaned Specifications")
        md.append("*Specifications without corresponding test plans*")
        
        orphan_by_category = {}
        for spec in orphaned_specs:
            category = spec.get("category", "Uncategorized")
            if category not in orphan_by_category:
                orphan_by_category[category] = []
            orphan_by_category[category].append(spec)
        
        for category, specs in sorted(orphan_by_category.items()):
            md.append(f"\n### {category} ({len(specs)} specs)")
            for spec in specs:
                standard = spec.get("standard", "Unknown")
                description = spec.get("description", "No description")
                path = spec.get("path", "No path")
                md.append(f"- **{standard}**: {description}")
                md.append(f"  - File: `{path}`")
    
    # Orphaned test plans
    if orphaned_tests:
        md.append("\n## Orphaned Test Plans")
        md.append("*Test plans without corresponding specifications*")
        
        test_by_category = {}
        for test in orphaned_tests:
            category = test.get("category", "Uncategorized")
            if category not in test_by_category:
                test_by_category[category] = []
            test_by_category[category].append(test)
        
        for category, tests in sorted(test_by_category.items()):
            md.append(f"\n### {category} ({len(tests)} test plans)")
            for test in tests:
                test_type = test.get("type", "Unknown type")
                version = test.get("version", "")
                version_str = f" ({version})" if version else ""
                path = test.get("path", "No path")
                note = test.get("note", "")
                
                md.append(f"- **{test_type}{version_str}**")
                md.append(f"  - File: `{path}`")
                if note:
                    md.append(f"  - Note: {note}")
    
    return "\n".join(md)


def generate_csv_report() -> Tuple[str, str, str]:
    """Generate CSV reports for devices, orphaned specs, and orphaned tests."""
    data = load_device_mappings()
    
    # Devices CSV
    devices_csv = []
    devices_csv.append(["Device ID", "Device Name", "Category", "Standard", "Spec Path", "Test Plan Type", "Test Plan Path"])
    
    for device in data.get("devices", []):
        device_id = device.get("id", "")
        device_name = device.get("name", "")
        category = device.get("category", "")
        
        specs = device.get("specs", [])
        test_plans = device.get("test_plans", [])
        
        # Handle case where device has multiple specs/tests
        max_items = max(len(specs), len(test_plans))
        
        for i in range(max_items):
            spec = specs[i] if i < len(specs) else {}
            test = test_plans[i] if i < len(test_plans) else {}
            
            devices_csv.append([
                device_id if i == 0 else "",  # Only show device info on first row
                device_name if i == 0 else "",
                category if i == 0 else "",
                spec.get("standard", ""),
                spec.get("path", ""),
                test.get("type", ""),
                test.get("path", "")
            ])
    
    # Orphaned specs CSV
    specs_csv = []
    specs_csv.append(["Standard", "Description", "Category", "Path"])
    for spec in data.get("orphaned_specs", []):
        specs_csv.append([
            spec.get("standard", ""),
            spec.get("description", ""),
            spec.get("category", ""),
            spec.get("path", "")
        ])
    
    # Orphaned tests CSV
    tests_csv = []
    tests_csv.append(["Test Type", "Version", "Category", "Path", "Note"])
    for test in data.get("orphaned_test_plans", []):
        tests_csv.append([
            test.get("type", ""),
            test.get("version", ""),
            test.get("category", ""),
            test.get("path", ""),
            test.get("note", "")
        ])
    
    return devices_csv, specs_csv, tests_csv


def save_csv_reports(devices_csv: List, specs_csv: List, tests_csv: List) -> None:
    """Save CSV reports to files."""
    # Save devices report
    with open("device_coverage_report.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(devices_csv)
    print("✅ Saved: device_coverage_report.csv")
    
    # Save orphaned specs report
    with open("orphaned_specs_report.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(specs_csv)
    print("✅ Saved: orphaned_specs_report.csv")
    
    # Save orphaned tests report
    with open("orphaned_tests_report.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(tests_csv)
    print("✅ Saved: orphaned_tests_report.csv")


def main():
    """Main function with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Generate device mapping reports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 generate_report.py                    # Console output
  python3 generate_report.py --format markdown  # Save as Markdown
  python3 generate_report.py --format csv       # Save as CSV files
  python3 generate_report.py --format console   # Console output (default)
        """
    )
    
    parser.add_argument(
        "--format", "-f",
        choices=["console", "markdown", "csv"],
        default="console",
        help="Output format (default: console)"
    )
    
    args = parser.parse_args()
    
    try:
        if args.format == "console":
            generate_console_report()
        
        elif args.format == "markdown":
            markdown_content = generate_markdown_report()
            with open("device_coverage_report.md", "w", encoding="utf-8") as f:
                f.write(markdown_content)
            print("✅ Saved: device_coverage_report.md")
        
        elif args.format == "csv":
            devices_csv, specs_csv, tests_csv = generate_csv_report()
            save_csv_reports(devices_csv, specs_csv, tests_csv)
    
    except KeyboardInterrupt:
        print("\n\nReport generation interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: Report generation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()