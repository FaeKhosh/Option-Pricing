1. 1. TRANCHES_TESTS_CASES 

# Tranches_Tests.txt cases (test thresholds)
TRANCHES_TESTS_CASES = {
    "test_85_92_95": {
        # A=85%, B=92.5%, C=95%
        "A": 1/0.85,      # 1.1765
        "B": 1/0.925,     # 1.0811
        "C": 1/0.95       # 1.0526
    },
    "test_90_100_105": {
        # A=90%, B=100%, C=105%
        "A": 1/0.90,      # 1.1111
        "B": 1/1.00,      # 1.0000
        "C": 1/1.05       # 0.9524
    }
}


2. FORWARD_RATES_CASES  
# Forward_Rates.txt cases - 9 rates for Group 1 (copies 1-9)
FORWARD_RATES_CASES = {
    "usd_0_5_eur_0_5": {
        "usd_rate": 0.005,
        "eur_rate": 0.005
    },
    "usd_1_5_eur_1_5": {
        "usd_rate": 0.015,
        "eur_rate": 0.015
    },
    "usd_2_5_eur_2_5": {
        "usd_rate": 0.025,
        "eur_rate": 0.025
    },
    "usd_3_5_eur_3_5": {
        "usd_rate": 0.035,
        "eur_rate": 0.035
    },
    "usd_4_5_eur_4_5": {
        "usd_rate": 0.045,
        "eur_rate": 0.045
    },
    "usd_5_5_eur_5_5": {
        "usd_rate": 0.055,
        "eur_rate": 0.055
    },
    "usd_6_5_eur_6_5": {
        "usd_rate": 0.065,
        "eur_rate": 0.065
    },
    "usd_7_5_eur_7_5": {
        "usd_rate": 0.075,
        "eur_rate": 0.075
    },
    "usd_8_5_eur_8_5": {
        "usd_rate": 0.085,
        "eur_rate": 0.085
    }
}

3. get_copy_configuration(copy_number) 
def get_copy_configuration(copy_number):
    """
    Get configuration for a specific copy number.
    
    Group 1 (Copies 1-9): PIK_all, 9 forward rate scenarios, test_85_92_95
    Group 2 (Copies 10-14): PIK_bc_only, 5 forward rate scenarios, test_85_92_95
    Group 3 (Copies 15-19): PIK_bc_only, 5 forward rate scenarios, test_90_100_105
    """
    
    # Default configuration (same for all groups)
    config = {
        "replines": "case_1",        # Dual Currency = N
        "deal_info": "case_1",       # Reinvestment period = 3
        "scenario_rates": "port1",
        "tranch": "case_1",          # A=75%, B=85%, C=90%
        "tranches_pik": "pik_all",   # Default: A PIK = Y
        "waterfall": "oc_yes",       # OC tests = Y
        "tranches_tests": "test_85_92_95",
        "forward_rates": "usd_0_5_eur_0_5"
    }
    
    # GROUP 1: Copies 1-9 (9 forward rates: 0.5% to 8.5%)
    if 1 <= copy_number <= 9:
        forward_rates_group1 = [
            "usd_0_5_eur_0_5",   # Copy 1: 0.5%
            "usd_1_5_eur_1_5",   # Copy 2: 1.5%
            "usd_2_5_eur_2_5",   # Copy 3: 2.5%
            "usd_3_5_eur_3_5",   # Copy 4: 3.5%
            "usd_4_5_eur_4_5",   # Copy 5: 4.5%
            "usd_5_5_eur_5_5",   # Copy 6: 5.5%
            "usd_6_5_eur_6_5",   # Copy 7: 6.5%
            "usd_7_5_eur_7_5",   # Copy 8: 7.5%
            "usd_8_5_eur_8_5"    # Copy 9: 8.5%
        ]
        config["tranches_pik"] = "pik_all"           # A PIK = Y
        config["tranches_tests"] = "test_85_92_95"   # A=85%, B=92.5%, C=95%
        config["forward_rates"] = forward_rates_group1[copy_number - 1]
    
    # GROUP 2: Copies 10-14 (5 forward rates: 0.5%, 2.5%, 4.5%, 6.5%, 8.5%)
    elif 10 <= copy_number <= 14:
        forward_rates_group2 = [
            "usd_0_5_eur_0_5",   # Copy 10: 0.5%
            "usd_2_5_eur_2_5",   # Copy 11: 2.5%
            "usd_4_5_eur_4_5",   # Copy 12: 4.5%
            "usd_6_5_eur_6_5",   # Copy 13: 6.5%
            "usd_8_5_eur_8_5"    # Copy 14: 8.5%
        ]
        config["tranches_pik"] = "pik_bc_only"       # A PIK = N
        config["tranches_tests"] = "test_85_92_95"   # A=85%, B=92.5%, C=95%
        config["forward_rates"] = forward_rates_group2[copy_number - 10]
    
    # GROUP 3: Copies 15-19 (5 forward rates: 0.5%, 2.5%, 4.5%, 6.5%, 8.5%)
    elif 15 <= copy_number <= 19:
        forward_rates_group3 = [
            "usd_0_5_eur_0_5",   # Copy 15: 0.5%
            "usd_2_5_eur_2_5",   # Copy 16: 2.5%
            "usd_4_5_eur_4_5",   # Copy 17: 4.5%
            "usd_6_5_eur_6_5",   # Copy 18: 6.5%
            "usd_8_5_eur_8_5"    # Copy 19: 8.5%
        ]
        config["tranches_pik"] = "pik_bc_only"       # A PIK = N
        config["tranches_tests"] = "test_90_100_105" # A=90%, B=100%, C=105%
        config["forward_rates"] = forward_rates_group3[copy_number - 15]
    
    # Add additional groups as needed below this line
    
    return config





########## 2
1. Configuration
SOURCE_FOLDER_1 = r"C:\path\to\Benchmark_deal"
SOURCE_FOLDER_2 = r"C:\path\to\Benchmark_deal_2"
NUM_COPIES_PER_SOURCE = 306
TOTAL_COPIES = 612


2. Source Selection in Loop

if copy_num <= NUM_COPIES_PER_SOURCE:
    source_folder = SOURCE_FOLDER_1
else:
    source_folder = SOURCE_FOLDER_2

copy_folder(source_folder, copy_path)

3. Verify both source folders exist

if __name__ == "__main__":
    print(f"Starting batch folder creation...")
    print(f"Source folder 1: {SOURCE_FOLDER_1}")
    print(f"Source folder 2: {SOURCE_FOLDER_2}")
    print(f"Output directory: {OUTPUT_DIRECTORY}")
    print(f"Total copies to create: {TOTAL_COPIES} (306 from each source)")
    print()
    
    # Verify both source folders exist
    if not os.path.exists(SOURCE_FOLDER_1):
        print(f"ERROR: Source folder not found: {SOURCE_FOLDER_1}")
        exit(1)
    if not os.path.exists(SOURCE_FOLDER_2):
        print(f"ERROR: Source folder not found: {SOURCE_FOLDER_2}")
        exit(1)
    
    # Create output directory if it doesn't exist
    if not os.path.exists(OUTPUT_DIRECTORY):
        os.makedirs(OUTPUT_DIRECTORY)
    
    # Create 612 copies with modifications (306 from each source)
    for copy_num in range(1, TOTAL_COPIES + 1):
        # Determine which source folder to use
        if copy_num <= NUM_COPIES_PER_SOURCE:
            source_folder = SOURCE_FOLDER_1
        else:
            source_folder = SOURCE_FOLDER_2
        
        # Create folder name
        folder_name = f"Benchmark_deal_{copy_num:03d}"
        copy_path = os.path.join(OUTPUT_DIRECTORY, folder_name)
        
        # Copy entire folder from the appropriate source
        copy_folder(source_folder, copy_path)
        
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
            print(f"  ✓ Progress: {copy_num}/{TOTAL_COPIES} copies created")
    
    print()
    print("=" * 60)
    print(f"Successfully created {TOTAL_COPIES} copies.")
    print(f"  - Copies 001-{NUM_COPIES_PER_SOURCE:03d}: from {SOURCE_FOLDER_1}")
    print(f"  - Copies {NUM_COPIES_PER_SOURCE + 1:03d}-{TOTAL_COPIES:03d}: from {SOURCE_FOLDER_2}")
    print(f"Location: {OUTPUT_DIRECTORY}")
    print("=" * 60)