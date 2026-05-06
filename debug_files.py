
def modify_deal_info(file_path, case):
    """Modify Deal_info.txt based on case"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Use date directly (already in DD/MM/YYYY format)
    date_value = case["end_reinvestment_date"]  # e.g., "28/07/2027"
    
    print(f"\n[DEBUG] modify_deal_info:")
    print(f"  File path: {file_path}")
    print(f"  File exists: {os.path.exists(file_path)}")
    print(f"  New date_value: {date_value}")
    print(f"  Type of date_value: {type(date_value)}")
    
    # Find current end_reinvestment_date in file
    import re as regex_module
    match = regex_module.search(r'end_reinvestment_date[\s\t]+(\S+)', content)
    if match:
        old_value = match.group(1)
        print(f"  Current end_reinvestment_date in file: {old_value}")
        print(f"  Type of old_value: {type(old_value)}")
    else:
        print(f"  WARNING: end_reinvestment_date NOT found in file!")
    
    # Show file size before
    file_size_before = len(content)
    print(f"  File size before: {file_size_before} bytes")
    
    # Replace end_reinvestment_date (plain text format: field_name\tvalue)
    content_new = re.sub(
        r'(end_reinvestment_date)\s+\S+',
        rf'\1\t{date_value}',
        content
    )
    
    # Check if regex actually replaced anything
    if content == content_new:
        print(f"  ERROR: Regex did NOT match! No replacement occurred!")
        print(f"  Regex pattern attempted: r'(end_reinvestment_date)\\s+\\S+'")
        # Try to debug - show the actual line
        for i, line in enumerate(content.split('\n'), 1):
            if 'end_reinvestment_date' in line:
                print(f"  Found on line {i}: {repr(line)}")
    else:
        print(f"  SUCCESS: Regex matched and replaced")
    
    # Show file size after
    file_size_after = len(content_new)
    print(f"  File size after: {file_size_after} bytes")
    
    # Write to file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content_new)
    
    # Verify write by reading back
    with open(file_path, 'r', encoding='utf-8') as f:
        verify_content = f.read()
    
    verify_match = regex_module.search(r'end_reinvestment_date[\s\t]+(\S+)', verify_content)
    if verify_match:
        verify_value = verify_match.group(1)
        print(f"  Verified end_reinvestment_date after write: {verify_value}")
        if verify_value == date_value:
            print(f"  ✓ CONFIRMED: Value successfully updated!")
        else:
            print(f"  ✗ FAILED: Value NOT updated correctly (got {verify_value}, expected {date_value})")
    else:
        print(f"  ERROR: Could not find end_reinvestment_date after write!")