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
        
        # Paths to files (directly in the copied folder, no subdirectory)
        input_dir = copy_path
        
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
                    modify_func(cases_dict[case_key], file_path)
                    print(f"  [{copy_num:3d}] {filename}: {case_key}")
                except Exception as e:
                    print(f"  [{copy_num:3d}] {filename}: ERROR - {str(e)}")
        
        # Progress indicator
        if copy_num % 50 == 0:
            print(f"  ✓ Progress: {copy_num}/{TOTAL_COPIES} copies created")
    
    print()
    print("=" * 60)
    print(f"✓ Successfully created {TOTAL_COPIES} copies!")
    print(f"  - Copies 001-{NUM_COPIES_PER_SOURCE:03d}: from {SOURCE_FOLDER_1}")
    print(f"  - Copies {NUM_COPIES_PER_SOURCE + 1:03d}-{TOTAL_COPIES:03d}: from {SOURCE_FOLDER_2}")
    print(f"Location: {OUTPUT_DIRECTORY}")
    print("=" * 60)
