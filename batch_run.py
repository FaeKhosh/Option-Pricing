import os
import shutil
import subprocess

# Configuration
input_folder = r"C:\new_directory\root\input_folder"  # Change this to your input folder
output_directory = r"C:\new_directory"
num_copies = 10
dlls_path = r"C:\new_directory\dlls"

# Step 1: Create 10 copies of the input folder
for i in range(1, num_copies + 1):
    copy_folder = os.path.join(output_directory, f"benchmark_copy_{i}")
    
    # Create copy
    if os.path.exists(copy_folder):
        shutil.rmtree(copy_folder)
    shutil.copytree(input_folder, copy_folder)
    
    # Step 2: Modify .txt files in each copy
    for filename in os.listdir(copy_folder):
        if filename.endswith(".txt"):
            file_path = os.path.join(copy_folder, filename)
            
            with open(file_path, 'r') as f:
                content = f.read()
            
            # CUSTOMIZE THIS PART - Replace your variables
            content = content.replace("VARIABLE_NAME", f"VALUE_{i}")
            # Add more replacements as needed
            
            with open(file_path, 'w') as f:
                f.write(content)
    
    print(f"Created and modified copy {i}")

# Step 3: Run the spiretest command
print("Running spiretest command...")
os.chdir(dlls_path)
command = f"spiretest dfc {output_directory}\\benchmark_test {output_directory}\\root {dlls_path}"
subprocess.run(command, shell=True)

print("Done!")



# ==================== CONFIGURATION ====================
# Source folder to copy
SOURCE_FOLDER = r"C:\path\to\Benchmark_deal"  # Change this to your Benchmark_deal path
OUTPUT_DIRECTORY = r"C:\new_directory"  # Change this to your output directory
NUM_COPIES = 612

# End reinvestment dates for different ranges
END_REINVESTMENT_DATES = {
    "range_1_55": "[2027-07-28, 2028-07-28, 2030-07-28]",
    "range_56_112": "[2028-07-28, 2029-07-28, 2031-07-28]",  # Customize as needed
    "range_113_168": "[2029-07-28, 2030-07-28, 2032-07-28]",  # Customize as needed
    # Add more ranges as needed
}

# ==================== HELPER FUNCTIONS ====================

def copy_folder(src, dest):
    """Copy entire folder structure"""
    if os.path.exists(dest):
        shutil.rmtree(dest)
    shutil.copytree(src, dest)
    print(f"Created folder: {dest}")

def modify_deal_info(file_path, end_reinvestment_date):
    """Modify Deal_info.txt with new end_reinvestment date"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace end_reinvestment pattern
    # Handles: end_reinvestment= [2027-07-28, 2028-07-28, 2030-07-28]
    content = re.sub(
        r'end_reinvestment\s*=\s*\[.*?\]',
        f'end_reinvestment= {end_reinvestment_date}',
        content
    )
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def modify_tranch(file_path, pik_value):
    """Modify Tranch.txt to set pik value for tranch_name= A"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find and replace pik value for tranch_name= A
    # Handles patterns like: tranch_name= A, pik = 0 or pik = 1
    lines = content.split('\n')
    modified_lines = []
    in_tranch_a = False
    
    for line in lines:
        if "tranch_name" in line and "A" in line:
            in_tranch_a = True
            modified_lines.append(line)
        elif in_tranch_a and "pik" in line:
            # Replace pik value
            modified_lines.append(re.sub(
                r"pik\s*=\s*[0-1]",
                f"pik = {pik_value}",
                line
            ))
            in_tranch_a = False
        else:
            modified_lines.append(line)
    
    modified_content = '\n'.join(modified_lines)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(modified_content)

def modify_revenue(file_path, revenue_modification):
    """Modify revenue.txt with custom changes"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Apply custom revenue modifications
    # Example: content = content.replace("OLD_VALUE", "NEW_VALUE")
    content = revenue_modification(content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def get_end_reinvestment_date(copy_number):
    """Determine end_reinvestment date based on copy number"""
    if 1 <= copy_number <= 55:
        return END_REINVESTMENT_DATES["range_1_55"]
    elif 56 <= copy_number <= 112:
        return END_REINVESTMENT_DATES.get("range_56_112", END_REINVESTMENT_DATES["range_1_55"])
    elif 113 <= copy_number <= 168:
        return END_REINVESTMENT_DATES.get("range_113_168", END_REINVESTMENT_DATES["range_1_55"])
    else:
        # Default for remaining copies
        return END_REINVESTMENT_DATES["range_1_55"]

def get_pik_value(copy_number):
    """Determine pik value based on copy number"""
    if 1 <= copy_number <= 10:
        return 1  # First 10 copies: pik = 1
    elif 11 <= copy_number <= 55:
        return 0  # Copies 11-55: pik = 0
    else:
        return 0  # Default

def should_modify_revenue(copy_number):
    """Determine if revenue.txt should be modified for this copy"""
    # Modify for copies 1-100 as example
    # Customize this logic as needed
    return copy_number <= 100

def custom_revenue_modification(content, copy_number):
    """Custom modifications for revenue.txt"""
    # Example: multiply revenue by copy number or change specific values
    # Customize this as needed
    return content

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
        # Create folder name with padding (copy_001, copy_002, etc.)
        folder_name = f"Benchmark_deal_{copy_num:03d}"
        copy_path = os.path.join(OUTPUT_DIRECTORY, folder_name)
        
        # Copy entire folder
        copy_folder(SOURCE_FOLDER, copy_path)
        
        # Paths to files that need modification
        deal_info_path = os.path.join(copy_path, "input", "Deal_info.txt")
        tranch_path = os.path.join(copy_path, "input", "Tranch.txt")
        revenue_path = os.path.join(copy_path, "input", "revenue.txt")
        
        # 1. Modify Deal_info.txt (ALWAYS)
        if os.path.exists(deal_info_path):
            end_date = get_end_reinvestment_date(copy_num)
            modify_deal_info(deal_info_path, end_date)
            print(f"  [{copy_num:3d}] Modified Deal_info.txt with end_reinvestment= {end_date}")
        
        # 2. Modify Tranch.txt (for copies 1-55)
        if copy_num <= 55 and os.path.exists(tranch_path):
            pik = get_pik_value(copy_num)
            modify_tranch(tranch_path, pik)
            print(f"  [{copy_num:3d}] Modified Tranch.txt - pik = {pik} for tranch_name= A")
        
        # 3. Modify revenue.txt (conditional)
        if should_modify_revenue(copy_num) and os.path.exists(revenue_path):
            modify_revenue(revenue_path, lambda c: custom_revenue_modification(c, copy_num))
            print(f"  [{copy_num:3d}] Modified revenue.txt")
        
        # Progress indicator
        if copy_num % 50 == 0:
            print(f"  ✓ Progress: {copy_num}/{NUM_COPIES} copies created")
    
    print()
    print("=" * 60)
    print(f"✓ Successfully created {NUM_COPIES} copies!")
    print(f"Location: {OUTPUT_DIRECTORY}")
    print("=" * 60)
