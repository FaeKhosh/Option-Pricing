import os
import shutil
import re

# ==================== CONFIGURATION ====================
# Source folder to copy
SOURCE_FOLDER = r"C:\path\to\Benchmark_deal"  # Change this to your Benchmark_deal path
OUTPUT_DIRECTORY = r"C:\new_directory"  # Change this to your output directory
NUM_COPIES = 612

# ==================== CASE DEFINITIONS ====================

# Replines.txt cases
REPLINES_CASES = {
    "case_1": {  # Dual Currency = N
        "dual_currency": "N",
        "eur_pct": "",
        "fixed_usa": "N",
        "fixed_eur": "N",
        "changes": None  # No changes
    },
    "case_2": {  # Dual Currency = Y, EUR % = 15%
        "dual_currency": "Y",
        "eur_pct": "15%",
        "fixed_usa": "N",
        "fixed_eur": "N",
        "changes": {
            "Floating Loans - Quarterly": 850000000,
            "EUR": 150000000
        }
    },
    "case_3": {  # Dual Currency = Y, EUR % = 30%
        "dual_currency": "Y",
        "eur_pct": "30%",
        "fixed_usa": "N",
        "fixed_eur": "N",
        "changes": {
            "Floating Loans - Quarterly": 700000000
        }
    }
}

# Deal_info.txt cases
DEAL_INFO_CASES = {
    "case_1": {  # Reinvestment period = 3
        "reinvestment_period": 3,
        "end_reinvestment_date": "2027-07-28"
    },
    "case_2": {  # Reinvestment period = 7
        "reinvestment_period": 7,
        "end_reinvestment_date": "2028-07-28"
    },
    "case_3": {  # Reinvestment period = 15
        "reinvestment_period": 15,
        "end_reinvestment_date": "2027-07-30"
    }
}

# Scenario_Default_Rates.txt cases
SCENARIO_RATES_CASES = {
    "port1": {
        "desired_rating": 1,
        "scenario_default_rate": 0,
        "largest_obligor_test_monetary": 0,
        "largest_industry_test_monetary": 0,
        "largest_sov_test_monetary": 0,
        "largest_tc_test_monetary": 0
    },
    "port2": {
        "desired_rating": 1,
        "scenario_default_rate": 0,
        "largest_obligor_test_monetary": 0,
        "largest_industry_test_monetary": 0,
        "largest_sov_test_monetary": 0,
        "largest_tc_test_monetary": 0
    }
}

# Tranch.txt cases
TRANCH_CASES = {
    "case_1": {  # A=75%, B=85%, C=90%
        "percentages": "A=75%,B=85%,C=90%",
        "balances": {
            "A": 750000000,
            "B": 212500000,
            "C": 33750000,
            "Subordinated Notes": 37500000
        }
    },
    "case_2": {  # A=60%, B=67.5%, C=80%
        "percentages": "A=60%,B=67.5%,C=80%",
        "balances": {
            "A": 600000000,
            "B": 212500000,
            "C": 33750000,
            "Subordinated Notes": 37500000
        }
    }
}

# Tranches.txt cases (PIK values)
TRANCHES_PIK_CASES = {
    "pik_all": {  # A PIK = Y
        "A": 1,
        "B": 1,
        "C": 1
    },
    "pik_bc_only": {  # A PIK = N
        "A": 0,
        "B": 1,
        "C": 1
    }
}

# Waterfall_Selection.txt cases
WATERFALL_CASES = {
    "oc_yes": {  # OC tests = Y
        "no_changes": True
    },
    "oc_no": {  # OC tests = N
        "waterfall_ignore": 1,
        "waterfall_no_oc_test_ignore": 0
    }
}

# Tranches_Tests.txt cases (test thresholds)
TRANCHES_TESTS_CASES = {
    "test_85_92_95": {
        "A": 1/0.85,  # 0.85 -> 1.176
        "B": 1/0.925,  # 0.925 -> 1.081
        "C": 1/0.95   # 0.95 -> 1.053
    }
}

# Forward_Rates.txt cases
FORWARD_RATES_CASES = {
    "usd_0_5_eur_0_5": {
        "usd_rate": 0.005,
        "eur_rate": 0.005
    }
}

# ==================== HELPER FUNCTIONS ====================

def copy_folder(src, dest):
    """Copy entire folder structure"""
    if os.path.exists(dest):
        shutil.rmtree(dest)
    shutil.copytree(src, dest)

def modify_replines(file_path, case):
    """Modify Replines.txt based on case"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if case["changes"] is None:
        return  # No changes for case 1
    
    # For each repline_id that needs changes, update starting_balance
    for repline_id, balance in case["changes"].items():
        # Replace balance value for specific repline_id
        pattern = rf'("repline_id"\s*:\s*"{repline_id}"[^}}]*"starting_balance"\s*:\s*)\d+'
        content = re.sub(pattern, rf'\1{balance}', content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def modify_deal_info(file_path, case):
    """Modify Deal_info.txt based on case"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace end_reinvestment_date
    content = re.sub(
        r'"end_reinvestment_date"\s*:\s*"[^"]+"',
        f'"end_reinvestment_date": "{case["end_reinvestment_date"]}"',
        content
    )
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def modify_scenario_default_rates(file_path, case):
    """Modify Scenario_Default_Rates.txt based on case"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find AAA scenario block and update values
    scenario_block = r'("scenario"\s*:\s*"AAA"[^}]*?)'
    
    # Replace each parameter for AAA scenario
    content = re.sub(
        r'("scenario"\s*:\s*"AAA"[^}]*?"desired_rating"\s*:\s*)\d+',
        rf'\1{case["desired_rating"]}',
        content
    )
    content = re.sub(
        r'("scenario"\s*:\s*"AAA"[^}]*?"scenario_default_rate"\s*:\s*)\d+',
        rf'\1{case["scenario_default_rate"]}',
        content
    )
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def modify_tranch(file_path, case):
    """Modify Tranch.txt with balance values"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Update balance for each tranche
    for tranche_name, balance in case["balances"].items():
        pattern = rf'("tranche_name"\s*:\s*"{tranche_name}"[^}}]*"balance"\s*:\s*)\d+'
        content = re.sub(pattern, rf'\1{balance}', content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def modify_tranches_pik(file_path, case):
    """Modify Tranches.txt PIK values"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Update pik value for each tranche
    for tranche_name, pik_value in case.items():
        pattern = rf'("tranche_name"\s*:\s*"{tranche_name}"[^}}]*"pik"\s*:\s*)\d+'
        content = re.sub(pattern, rf'\1{pik_value}', content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def modify_waterfall_selection(file_path, case):
    """Modify Waterfall_Selection.txt"""
    if case.get("no_changes"):
        return  # No changes needed
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Set ignore values for waterfall entries
    content = re.sub(
        r'("waterfall_name"\s*:\s*"Waterfall"[^}]*"ignore"\s*:\s*)\d+',
        rf'\1{case["waterfall_ignore"]}',
        content
    )
    content = re.sub(
        r'("waterfall_name"\s*:\s*"Waterfall_No_OC_Test"[^}]*"ignore"\s*:\s*)\d+',
        rf'\1{case["waterfall_no_oc_test_ignore"]}',
        content
    )
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def modify_tranches_tests(file_path, case):
    """Modify Tranches_Tests.txt test thresholds"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Update test_threshold for each tranche
    for tranche_name, threshold_value in case.items():
        pattern = rf'("tranche_name"\s*:\s*"{tranche_name}"[^}}]*"test_threshold"\s*:\s*)[0-9.]+'
        content = re.sub(pattern, rf'\1{threshold_value:.4f}', content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def modify_forward_rates(file_path, case):
    """Modify Forward_Rates.txt interest rates"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Update USD rates (3MSOFR_T)
    if "usd_rate" in case:
        pattern = r'("index_type"\s*:\s*"3MSOFR_T"[^}]*"interest_rate"\s*:\s*)[0-9.]+'
        content = re.sub(pattern, rf'\1{case["usd_rate"]}', content)
    
    # Update EUR rates (3MEUR)
    if "eur_rate" in case:
        pattern = r'("index_type"\s*:\s*"3MEUR"[^}]*"interest_rate"\s*:\s*)[0-9.]+'
        content = re.sub(pattern, rf'\1{case["eur_rate"]}', content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def get_copy_configuration(copy_number):
    """
    Get configuration for a specific copy number.
    Customize this to define how 612 copies are distributed among cases.
    """
    # Example distribution: Customize based on your 612 copy requirements
    # This example shows basic cycling through cases
    
    config = {
        "replines": "case_1",  # Default: no changes
        "deal_info": "case_1",
        "scenario_rates": "port1",
        "tranch": "case_1",
        "tranches_pik": "pik_all",
        "waterfall": "oc_yes",
        "tranches_tests": "test_85_92_95",
        "forward_rates": "usd_0_5_eur_0_5"
    }
    
    # Customize distribution logic below:
    # Example: Every 51 copies cycle through Deal_info cases (3 cases, so 204 copies total)
    if copy_number <= 204:
        config["deal_info"] = list(DEAL_INFO_CASES.keys())[(copy_number - 1) % 3]
    
    # Example: Tranch cases alternate every 306 copies
    if copy_number <= 306:
        config["tranch"] = "case_1"
    else:
        config["tranch"] = "case_2"
    
    # Example: PIK cases alternate
    if copy_number % 2 == 1:
        config["tranches_pik"] = "pik_all"
    else:
        config["tranches_pik"] = "pik_bc_only"
    
    return config

# ==================== MAIN EXECUTION ====================

if __name__ == "__main__":
    print(f"Starting batch folder creation...")
    print(f"Source folder: {SOURCE_FOLDER}")
    print(f"Output directory: {OUTPUT_DIRECTORY}")
    print(f"Total copies to create: {NUM_COPIES}")
    print()
    
    # Verify source folder exists
    if not os.path.exists(SOURCE_FOLDER):
        print(f"ERROR: Source folder not found: {SOURCE_FOLDER}")
        exit(1)
    
    # Create output directory if it doesn't exist
    if not os.path.exists(OUTPUT_DIRECTORY):
        os.makedirs(OUTPUT_DIRECTORY)
    
    # Create 612 copies with modifications
    for copy_num in range(1, NUM_COPIES + 1):
        # Create folder name
        folder_name = f"Benchmark_deal_{copy_num:03d}"
        copy_path = os.path.join(OUTPUT_DIRECTORY, folder_name)
        
        # Copy entire folder
        copy_folder(SOURCE_FOLDER, copy_path)
        
        # Get configuration for this copy
        config = get_copy_configuration(copy_num)
        
        # Paths to input files
        input_dir = os.path.join(copy_path, "input")
        
        # List of files to potentially modify
        files_to_modify = {
            "Replines.txt": (modify_replines, REPLINES_CASES, config["replines"]),
            "Deal_info.txt": (modify_deal_info, DEAL_INFO_CASES, config["deal_info"]),
            "Scenario_Default_Rates.txt": (modify_scenario_default_rates, SCENARIO_RATES_CASES, config["scenario_rates"]),
            "Tranch.txt": (modify_tranch, TRANCH_CASES, config["tranch"]),
            "Tranches.txt": (modify_tranches_pik, TRANCHES_PIK_CASES, config["tranches_pik"]),
            "Waterfall_Selection.txt": (modify_waterfall_selection, WATERFALL_CASES, config["waterfall"]),
            "Tranches_Tests.txt": (modify_tranches_tests, TRANCHES_TESTS_CASES, config["tranches_tests"]),
            "Forward_Rates.txt": (modify_forward_rates, FORWARD_RATES_CASES, config["forward_rates"])
        }
        
        # Modify each file
        for filename, (modify_func, cases_dict, case_key) in files_to_modify.items():
            file_path = os.path.join(input_dir, filename)
            
            if os.path.exists(file_path) and case_key in cases_dict:
                try:
                    modify_func(file_path, cases_dict[case_key])
                    print(f"  [{copy_num:3d}] {filename}: {case_key}")
                except Exception as e:
                    print(f"  [{copy_num:3d}] {filename}: ERROR - {str(e)}")
        
        # Progress indicator
        if copy_num % 50 == 0:
            print(f"  ✓ Progress: {copy_num}/{NUM_COPIES} copies created")
    
    print()
    print("=" * 60)
    print(f"✓ Successfully created {NUM_COPIES} copies!")
    print(f"Location: {OUTPUT_DIRECTORY}")
    print("=" * 60)
