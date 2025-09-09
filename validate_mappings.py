#!/usr/bin/env python3
"""
Device Mappings Validation Script

This script validates the device-mappings.yaml file by:
1. Checking that all referenced spec and test plan files exist
2. Finding orphaned files (files not referenced in any mapping)
3. Providing a summary of the validation results

Usage:
    python3 validate_mappings.py
"""

import yaml
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple
import sys


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


def validate_mappings() -> Dict[str, List]:
    """Validate all device mappings and return results."""
    data = load_device_mappings()
    
    results = {
        "valid_devices": [],
        "missing_specs": [],
        "missing_tests": [],
        "orphan_specs": [],
        "orphan_tests": [],
        "errors": []
    }
    
    # Track all mapped files
    mapped_specs: Set[str] = set()
    mapped_tests: Set[str] = set()
    
    # Validate each device mapping
    for device in data.get("devices", []):
        device_id = device.get("id", "unknown")
        device_valid = True
        
        # Check specs exist
        for spec in device.get("specs", []):
            spec_path = spec.get("path", "")
            if not spec_path:
                results["errors"].append(f"Device {device_id}: spec missing path")
                device_valid = False
                continue
                
            mapped_specs.add(spec_path)
            if not Path(spec_path).exists():
                results["missing_specs"].append({
                    "device": device_id,
                    "path": spec_path,
                    "standard": spec.get("standard", "unknown")
                })
                device_valid = False
        
        # Check test plans exist
        for test in device.get("test_plans", []):
            test_path = test.get("path", "")
            if not test_path:
                results["errors"].append(f"Device {device_id}: test plan missing path")
                device_valid = False
                continue
                
            mapped_tests.add(test_path)
            if not Path(test_path).exists():
                results["missing_tests"].append({
                    "device": device_id,
                    "path": test_path,
                    "type": test.get("type", "unknown")
                })
                device_valid = False
        
        if device_valid:
            results["valid_devices"].append({
                "id": device_id,
                "name": device.get("name", ""),
                "category": device.get("category", ""),
                "spec_count": len(device.get("specs", [])),
                "test_count": len(device.get("test_plans", []))
            })
    
    # Find orphaned files
    results["orphan_specs"] = find_orphaned_files("specs", mapped_specs)
    results["orphan_tests"] = find_orphaned_files("test-plans", mapped_tests)
    
    return results


def find_orphaned_files(directory: str, mapped_files: Set[str]) -> List[Dict]:
    """Find files in directory that aren't mapped to any device."""
    orphaned = []
    
    if not Path(directory).exists():
        return orphaned
    
    # Find all PDF and text files
    for file_path in Path(directory).rglob("*.pdf"):
        if str(file_path) not in mapped_files:
            orphaned.append({
                "path": str(file_path),
                "size_mb": round(file_path.stat().st_size / (1024*1024), 2)
            })
    
    for file_path in Path(directory).rglob("*.txt"):
        if str(file_path) not in mapped_files:
            orphaned.append({
                "path": str(file_path),
                "size_mb": round(file_path.stat().st_size / (1024*1024), 2)
            })
    
    return sorted(orphaned, key=lambda x: x["path"])


def print_validation_results(results: Dict[str, List]) -> None:
    """Print formatted validation results."""
    print("=" * 60)
    print("DEVICE MAPPINGS VALIDATION REPORT")
    print("=" * 60)
    
    # Summary
    print(f"\n📊 SUMMARY:")
    print(f"  ✅ Valid devices (with all files present): {len(results['valid_devices'])}")
    print(f"  ❌ Missing spec files: {len(results['missing_specs'])}")
    print(f"  ❌ Missing test plan files: {len(results['missing_tests'])}")
    print(f"  ⚠️  Orphaned spec files: {len(results['orphan_specs'])}")
    print(f"  ⚠️  Orphaned test plan files: {len(results['orphan_tests'])}")
    if results['errors']:
        print(f"  🚨 Configuration errors: {len(results['errors'])}")
    
    # Valid devices
    if results['valid_devices']:
        print(f"\n✅ VALID DEVICES ({len(results['valid_devices'])}):")
        by_category = {}
        for device in results['valid_devices']:
            category = device['category'] or 'Uncategorized'
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(device)
        
        for category, devices in sorted(by_category.items()):
            print(f"\n  📁 {category}:")
            for device in devices:
                print(f"     • {device['name']} ({device['id']})")
                print(f"       Specs: {device['spec_count']}, Test Plans: {device['test_count']}")
    
    # Missing files
    if results['missing_specs']:
        print(f"\n❌ MISSING SPEC FILES ({len(results['missing_specs'])}):")
        for missing in results['missing_specs']:
            print(f"   • {missing['path']} (for {missing['device']})")
    
    if results['missing_tests']:
        print(f"\n❌ MISSING TEST PLAN FILES ({len(results['missing_tests'])}):")
        for missing in results['missing_tests']:
            print(f"   • {missing['path']} (for {missing['device']})")
    
    # Orphaned files
    if results['orphan_specs']:
        print(f"\n⚠️  ORPHANED SPEC FILES ({len(results['orphan_specs'])}):")
        print("   (These spec files exist but aren't mapped to any device)")
        for orphan in results['orphan_specs']:
            print(f"   • {orphan['path']} ({orphan['size_mb']} MB)")
    
    if results['orphan_tests']:
        print(f"\n⚠️  ORPHANED TEST PLAN FILES ({len(results['orphan_tests'])}):")
        print("   (These test plan files exist but aren't mapped to any device)")
        for orphan in results['orphan_tests']:
            print(f"   • {orphan['path']} ({orphan['size_mb']} MB)")
    
    # Configuration errors
    if results['errors']:
        print(f"\n🚨 CONFIGURATION ERRORS ({len(results['errors'])}):")
        for error in results['errors']:
            print(f"   • {error}")
    
    # Final status
    print(f"\n{'='*60}")
    total_issues = (len(results['missing_specs']) + 
                   len(results['missing_tests']) + 
                   len(results['errors']))
    
    if total_issues == 0:
        print("🎉 VALIDATION PASSED - All mapped files exist!")
    else:
        print(f"⚠️  VALIDATION ISSUES - {total_issues} problems found")
    
    orphan_count = len(results['orphan_specs']) + len(results['orphan_tests'])
    if orphan_count > 0:
        print(f"📋 NOTE: {orphan_count} orphaned files found (not critical)")
    
    print("="*60)


def generate_stats() -> None:
    """Generate and print quick statistics."""
    data = load_device_mappings()
    
    total_devices = len(data.get("devices", []))
    total_orphan_specs = len(data.get("orphaned_specs", []))
    total_orphan_tests = len(data.get("orphaned_test_plans", []))
    
    print(f"\n📈 QUICK STATS:")
    print(f"   Devices with matched specs & test plans: {total_devices}")
    print(f"   Orphaned specs (documented): {total_orphan_specs}")
    print(f"   Orphaned test plans (documented): {total_orphan_tests}")


if __name__ == "__main__":
    try:
        results = validate_mappings()
        print_validation_results(results)
        generate_stats()
        
        # Exit with error code if validation failed
        total_issues = (len(results['missing_specs']) + 
                       len(results['missing_tests']) + 
                       len(results['errors']))
        sys.exit(1 if total_issues > 0 else 0)
        
    except KeyboardInterrupt:
        print("\n\nValidation interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: Validation failed with exception: {e}")
        sys.exit(1)