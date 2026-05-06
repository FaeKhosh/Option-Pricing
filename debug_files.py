    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    if case["changes"] is None:
        return  # No changes for case 1
    
    # Process each line
    for i, line in enumerate(lines):
        # Skip header line
        if i == 0:
            continue
        
        # Split by tabs to get columns
        columns = line.rstrip('\n').split('\t')
        
        # Column 1 (index 1) is repline_id
        if len(columns) > 1:
            repline_id = columns[1].strip()
            
            # Check if this repline_id needs to be changed
            if repline_id in case["changes"]:
                new_balance = case["changes"][repline_id]
                
                if i == 0:
                    continue
                
                for j in range(len(columns)):
                    if j > 4:  # Starting balance should be after initial columns
                        try:
                            # Try to parse as float
                            float(columns[j])
                            # This is likely the starting balance, replace it
                            columns[j] = str(new_balance)
                            break
                        except ValueError:
                            continue
                
                # Reconstruct the line
                lines[i] = '\t'.join(columns) + '\n'
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)