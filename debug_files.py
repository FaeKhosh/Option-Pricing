1. 

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find column indices from header
    if not lines:
        return
    
    header_columns = lines[0].rstrip('\n').split('\t')
    tranche_name_col = None
    balance_col = None
    
    # Find column indices
    try:
        tranche_name_col = header_columns.index('tranche_name')
        balance_col = header_columns.index('balance')
    except ValueError as e:
        print(f"[ERROR] modify_tranch: Could not find required columns - {e}")
        return
    
    # Process each data row
    for i in range(1, len(lines)):
        columns = lines[i].rstrip('\n').split('\t')
        
        if len(columns) > max(tranche_name_col, balance_col):
            tranche_name = columns[tranche_name_col].strip()
            
            # Check if this tranche needs to be updated
            if tranche_name in case["balances"]:
                new_balance = case["balances"][tranche_name]
                columns[balance_col] = str(new_balance)
                lines[i] = '\t'.join(columns) + '\n'
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)



2.



    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find column indices from header
    if not lines:
        return
    
    header_columns = lines[0].rstrip('\n').split('\t')
    tranche_name_col = None
    pik_col = None
    
    # Find column indices
    try:
        tranche_name_col = header_columns.index('tranche_name')
        pik_col = header_columns.index('pik')
    except ValueError as e:
        print(f"[ERROR] modify_tranches_pik: Could not find required columns - {e}")
        return
    
    # Process each data row
    for i in range(1, len(lines)):
        columns = lines[i].rstrip('\n').split('\t')
        
        if len(columns) > max(tranche_name_col, pik_col):
            tranche_name = columns[tranche_name_col].strip()
            
            # Check if this tranche needs to be updated
            if tranche_name in case:
                pik_value = case[tranche_name]
                columns[pik_col] = str(pik_value)
                lines[i] = '\t'.join(columns) + '\n'
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)


3.
    """Modify Waterfall_Selection.txt (TSV format)"""
    if case.get("no_changes"):
        return  # No changes needed
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find column indices from header
    if not lines:
        return
    
    header_columns = lines[0].rstrip('\n').split('\t')
    ignore_col = None
    waterfall_name_col = None
    
    # Find column indices
    try:
        ignore_col = header_columns.index('ignore')
        waterfall_name_col = header_columns.index('waterfall_name')
    except ValueError as e:
        print(f"[ERROR] modify_waterfall_selection: Could not find required columns - {e}")
        return
    
    # Process each data row
    for i in range(1, len(lines)):
        columns = lines[i].rstrip('\n').split('\t')
        
        if len(columns) > max(ignore_col, waterfall_name_col):
            waterfall_name = columns[waterfall_name_col].strip()
            
            # Update ignore value for Waterfall
            if waterfall_name == "Waterfall" and "waterfall_ignore" in case:
                columns[ignore_col] = str(case["waterfall_ignore"])
                lines[i] = '\t'.join(columns) + '\n'
            
            # Update ignore value for Waterfall_No_OC_Test
            elif waterfall_name == "Waterfall_No_OC_Test" and "waterfall_no_oc_test_ignore" in case:
                columns[ignore_col] = str(case["waterfall_no_oc_test_ignore"])
                lines[i] = '\t'.join(columns) + '\n'
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)



4.

    """Modify Tranches_Tests.txt test thresholds (TSV format)"""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find column indices from header
    if not lines:
        return
    
    header_columns = lines[0].rstrip('\n').split('\t')
    tranche_name_col = None
    test_threshold_col = None
    
    # Find column indices
    try:
        tranche_name_col = header_columns.index('tranche_name')
        test_threshold_col = header_columns.index('test_threshold')
    except ValueError as e:
        print(f"[ERROR] modify_tranches_tests: Could not find required columns - {e}")
        return
    
    # Process each data row
    for i in range(1, len(lines)):
        columns = lines[i].rstrip('\n').split('\t')
        
        if len(columns) > max(tranche_name_col, test_threshold_col):
            tranche_name = columns[tranche_name_col].strip()
            
            # Check if this tranche needs to be updated
            if tranche_name in case:
                threshold_value = case[tranche_name]
                columns[test_threshold_col] = f"{threshold_value:.4f}"
                lines[i] = '\t'.join(columns) + '\n'
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)


5. 


    """Modify Forward_Rates.txt interest rates (TSV format)"""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find column indices from header
    if not lines:
        return
    
    header_columns = lines[0].rstrip('\n').split('\t')
    index_type_col = None
    interest_rate_col = None
    
    # Find column indices
    try:
        index_type_col = header_columns.index('index_type')
        interest_rate_col = header_columns.index('interest_rate')
    except ValueError as e:
        print(f"[ERROR] modify_forward_rates: Could not find required columns - {e}")
        return
    
    # Process each data row
    for i in range(1, len(lines)):
        columns = lines[i].rstrip('\n').split('\t')
        
        if len(columns) > max(index_type_col, interest_rate_col):
            index_type = columns[index_type_col].strip()
            
            # Update USD rates (3MSOFR or 3MSOFR_T)
            if "usd_rate" in case and ("3MSOFR" in index_type):
                columns[interest_rate_col] = str(case["usd_rate"])
                lines[i] = '\t'.join(columns) + '\n'
            
            # Update EUR rates (3MEUR)
            elif "eur_rate" in case and ("3MEUR" in index_type):
                columns[interest_rate_col] = str(case["eur_rate"])
                lines[i] = '\t'.join(columns) + '\n'
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)


6. 