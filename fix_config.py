#!/usr/bin/env python3
"""Fix config.yaml issues: mixed data types, duplicate keys, naming consistency"""

import yaml
import sys
from collections import OrderedDict

def fix_pages_field(value):
    """Convert pages field to proper type - integer or null"""
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        if value in ["N/A", "N/A (external document)"]:
            return None
        try:
            return int(value)
        except:
            return None
    return None

def fix_version_field(value):
    """Standardize version field - string or null"""
    if value in ["N/A", "n/a", ""]:
        return None
    return str(value) if value else None

def determine_access(item):
    """Determine access type based on file field"""
    file_val = item.get('file', '')
    if isinstance(file_val, str):
        if file_val.startswith('Available'):
            return 'external'
        elif 'requires registration' in file_val.lower():
            return 'requires_registration'
        elif file_val.startswith('http'):
            return 'external'
    return 'local'

def process_document(doc):
    """Process a spec or test plan document to fix fields"""
    # Fix pages
    if 'pages' in doc:
        doc['pages'] = fix_pages_field(doc['pages'])
    
    # Fix version
    if 'version' in doc:
        doc['version'] = fix_version_field(doc['version'])
    
    # Add access field if missing
    if 'access' not in doc:
        doc['access'] = determine_access(doc)
    
    # Add organization if standard exists but org doesn't
    if 'standard' in doc and 'organization' not in doc:
        std = doc['standard']
        if std.startswith('IEEE'):
            doc['organization'] = 'IEEE'
        elif std.startswith('RFC'):
            doc['organization'] = 'IETF'
        elif std.startswith('USB'):
            doc['organization'] = 'USB-IF'
    
    return doc

def process_category(category_data):
    """Process a category and all its versions"""
    if 'versions' in category_data:
        for version_key, version_data in category_data['versions'].items():
            # Process specs
            if 'specs' in version_data:
                version_data['specs'] = [
                    process_document(doc) for doc in version_data['specs']
                ]
            
            # Process test_plans
            if 'test_plans' in version_data:
                version_data['test_plans'] = [
                    process_document(doc) for doc in version_data['test_plans']
                ]
            
            # Handle nested structures (like NVMe)
            for key in version_data:
                if key not in ['specs', 'test_plans'] and isinstance(version_data[key], dict):
                    if 'specs' in version_data[key]:
                        version_data[key]['specs'] = [
                            process_document(doc) for doc in version_data[key]['specs']
                        ]
                    if 'test_plans' in version_data[key]:
                        version_data[key]['test_plans'] = [
                            process_document(doc) for doc in version_data[key]['test_plans']
                        ]
    
    return category_data

def main():
    # Read the current config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Process each category
    categories_to_process = [
        'ethernet', 'switching', 'fibre_channel', 'ieee1588', 'ipv6', 
        'iscsi', 'storage', 'usb', 'wifi', 'lorawan', 'onvif', 'sdn',
        'redfish', 'auth', 'rdma', 'nvme', 'ethernet_poe', 
        'automotive_ethernet', 'khronos', 'fips_security', 'ipv6_ready',
        'pcie_storage'
    ]
    
    for category in categories_to_process:
        if category in config:
            config[category] = process_category(config[category])
    
    # Rename fips_security to security_certifications
    if 'fips_security' in config:
        config['security_certifications'] = config.pop('fips_security')
        config['security_certifications']['description'] = "Security certification test specifications"
    
    # Split pcie_storage into pcie and ufs
    if 'pcie_storage' in config:
        pcie_data = config.pop('pcie_storage')
        
        # Create pcie category
        config['pcie'] = {
            'category': 'connectivity',
            'description': 'PCIe interface test specifications',
            'versions': {}
        }
        
        # Create ufs category
        config['ufs'] = {
            'category': 'storage',
            'description': 'Universal Flash Storage interface test specifications',
            'versions': {}
        }
        
        # Split the content
        if 'versions' in pcie_data:
            for version_key, version_data in pcie_data['versions'].items():
                if 'Gen' in version_key or 'PCIe' in version_key:
                    config['pcie']['versions'][version_key] = version_data
                elif 'UFS' in version_key:
                    config['ufs']['versions'][version_key] = version_data
    
    # Write the fixed config
    with open('config_fixed.yaml', 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False, width=120)
    
    print("Fixed config written to config_fixed.yaml")
    print("Main fixes applied:")
    print("- Converted pages field to integers or null")
    print("- Standardized version fields")
    print("- Added access field to documents")
    print("- Renamed fips_security to security_certifications")
    print("- Split pcie_storage into pcie and ufs categories")

if __name__ == '__main__':
    main()