# Config Validation Script

The `validate_config.py` script validates the integrity of the `config.yaml` file by checking:

1. **File Existence**: All referenced files exist in the repository
2. **PDF Validity**: PDF files are properly formatted and readable  
3. **Page Counts**: Actual page counts match the documented values

## Usage

```bash
# Basic validation
python3 validate_config.py

# Verbose output showing all checks
python3 validate_config.py --verbose

# Fix page count mismatches automatically
python3 validate_config.py --fix-pages

# Use custom config file
python3 validate_config.py --config my_config.yaml
```

## Output

The script provides a comprehensive report showing:
- ✅ **Successful validations** 
- ❌ **Missing files** that are referenced but don't exist
- ❌ **Invalid PDF files** that aren't properly formatted
- ⚠️ **Page count mismatches** where actual pages differ from documented

## Dependencies

- **Python 3.x**
- **pdfinfo** command (from poppler-utils) for PDF page counting
- **PyPDF2** (optional, falls back to pdfinfo if not available)
- **PyYAML** for parsing config.yaml

## Exit Codes

- `0`: All validations passed
- `1`: Issues found that need attention

This helps maintain repository integrity and ensures all documentation is accurate and accessible.