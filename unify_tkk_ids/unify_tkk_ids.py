#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unify TKK Group IDs - Pure Python Script
Made by Eli (lili041 --Github) with Google Gemini

This script unifies TKK group IDs in JSON textcritic files and corresponding SVG files.
You need to fill in the path to the JSON textcritics file and the SVG folder path.

ACHTUNG: TODO entries are skipped, but they are also not counted within a block,
and counting continues as if nothing happened: g-tkk-1, g-tkk-2, g-tkk-3, g-tkk-4, TODO, g-tkk-5, g-tkk-6, ...
"""

import json
import os
import re
import sys


def extract_moldenhauer_number(text):
    """Extract the Moldenhauer catalog number from entry ID strings.
    
    Supports both underscore and non-underscore patterns:
    - 'M_143_TF1' -> '143' (classic format with underscore)
    - 'M143_Textfassung1' -> '143' (filename format without underscore)
    - 'Mx_136_Sk1' -> '136' (Mx variant with underscore)
    - 'Mx789_file' -> '789' (Mx variant without underscore)
    
    Args:
        text (str): The entry ID or filename to extract number from.
                   None values are converted to string automatically.
        
    Returns:
        str: The extracted Moldenhauer number as string, or empty string if no match found.
    """
    match = re.search(r'Mx?_?(\d+)', str(text))
    return match.group(1) if match else ""


def display_uncertainties(data, prefix, loaded_svgs):
    """Validate and report the success of TKK ID unification process.
    
    Performs post-processing validation to ensure all TKK-related IDs have been
    properly updated with the specified prefix. Identifies and reports:
    - JSON entries with unchanged svgGroupId values (excluding "TODO" entries)
    - SVG elements with class="tkk" that retain old ID values
    
    Generates a comprehensive error report with specific file locations and
    entry IDs for debugging purposes.
    
    Args:
        data (dict): The processed JSON textcritics data structure containing
                    textcritics entries with commentary and blockComments.
        prefix (str): The target prefix that all updated IDs should start with
                     (e.g., "g-tkk-").
        loaded_svgs (dict): Dictionary mapping SVG filenames to their content
                           and path information from the processing cache.
                           
    Returns:
        None: Prints validation results directly to stdout. Does not return values.
    """
    print(f"\n--- UNCERTAINTY & ERROR REPORT ---")
    errors_found = 0
    
    all_entries = data.get('textcritics', data) if isinstance(data, dict) else data
    for entry in all_entries:
        entry_id = entry.get('id', 'Unknown')
        comments_list = entry.get('commentary', {}).get('comments', [])
        for comment_group in comments_list:
            for b_comment in comment_group.get('blockComments', []):
                val = b_comment.get('svgGroupId')
                if val and not val.startswith(prefix) and val != "TODO":
                    print(f"  [!] JSON ERROR: Unchanged ID '{val}' in Entry: {entry_id}")
                    errors_found += 1

    tkk_id_regex = re.compile(r'<[^>]+?class=["\']tkk["\'][^>]+?id=["\']([^"\']+)["\']|<[^>]+?id=["\']([^"\']+)["\'][^>]+?class=["\']tkk["\']')
    
    for filename, sdata in loaded_svgs.items():
        matches = tkk_id_regex.findall(sdata["content"])
        for match in matches:
            found_id = match[0] if match[0] else match[1]
            if not found_id.startswith(prefix):
                print(f"  [!] SVG ORPHAN: ID '{found_id}' with class 'tkk' in {filename} was NOT updated.")
                errors_found += 1
    
    if errors_found == 0:
        print("  [✓] All JSON and SVG 'tkk' IDs successfully updated.")
    else:
        print(f"  [!] Total issues found: {errors_found}")


def load_and_validate_inputs(json_path, svg_folder):
    """Load and validate input files and directories.
    
    Args:
        json_path (str): Path to the JSON textcritics file
        svg_folder (str): Path to the folder containing SVG files
        
    Returns:
        tuple: (data, all_svg_files) - loaded JSON data and list of SVG files
        
    Raises:
        FileNotFoundError: If JSON file or SVG folder doesn't exist
    """
    # Check if paths exist
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"JSON file not found: {json_path}")
    
    if not os.path.exists(svg_folder):
        raise FileNotFoundError(f"SVG folder not found: {svg_folder}")

    # Load JSON data
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
  
    # Get SVG files and validate folder content
    try:
        all_files = os.listdir(svg_folder)
        all_svg_files = [f for f in all_files if f.lower().endswith('.svg')]
    except OSError as e:
        raise PermissionError(f"Cannot list contents of SVG folder: {svg_folder} - {e}")
    
    if not all_svg_files:
        raise ValueError(f"No SVG files found in folder: {svg_folder}")
    
    print(f"Loaded JSON with {len(data.get('textcritics', [])) if isinstance(data, dict) else 'nested'} entries")
    print(f"Found {len(all_svg_files)} SVG files in folder")

    return data, all_svg_files


def create_svg_loader(svg_folder, final_svg_cache, loaded_svg_texts):
    """Create a closure function for loading SVG files with caching.
    
    Args:
        svg_folder (str): Path to the folder containing SVG files
        final_svg_cache (dict): Cache for final SVG results
        loaded_svg_texts (dict): Cache for currently loaded SVG texts
        
    Returns:
        function: A function that loads and caches SVG content
    """
    def get_svg_text(filename):
        if filename not in loaded_svg_texts:
            path = os.path.join(svg_folder, filename)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            loaded_svg_texts[filename] = {"content": content, "path": path}
            final_svg_cache[filename] = loaded_svg_texts[filename]
        return loaded_svg_texts[filename]
    return get_svg_text


def process_block_comment(b_comment, entry_id, relevant_svgs_for_block, 
                         get_svg_text, id_mapping, prefix):
    """Process a single block comment and update IDs if found in SVG.
    
    Args:
        b_comment (dict): Block comment containing svgGroupId
        entry_id (str): Current entry ID for logging
        relevant_svgs_for_block (list): List of relevant SVG files for this block
        get_svg_text (function): Function to load SVG content
        id_mapping (dict): Mapping of old IDs to new IDs
        prefix (str): Prefix for new IDs
        
    Returns:
        bool: True if processing was successful, False if skipped due to issues
    """
    old_val = b_comment.get('svgGroupId')
    if not old_val or old_val == "TODO": 
        return True

    # Only match the ID if the same tag contains class="tkk"
    pattern = rf'(<[^>]+?id=["\']{re.escape(old_val)}["\'][^>]+?class=["\']tkk["\']|<[^>]+?class=["\']tkk["\'][^>]+?id=["\']{re.escape(old_val)}["\'][^>]*?>)'
    
    found_in_svg = None
    for svg_filename in relevant_svgs_for_block:
        svg_data = get_svg_text(svg_filename)
        if re.search(pattern, svg_data["content"]):
            found_in_svg = svg_filename
            break
    
    if found_in_svg:
        svg_data = get_svg_text(found_in_svg)
        
        # Check for duplicates before updating
        updated_content, error = update_svg_id(svg_data["content"], old_val, "temp_id")
        if error:
            print(f"    [WARNING] {error} in {found_in_svg}")
            print(f"              Skipping update to prevent data corruption")
            return False
        
        if old_val not in id_mapping:
            id_mapping[old_val] = f"{prefix}{len(id_mapping) + 1}"
        
        new_val = id_mapping[old_val]
        
        print(f"    [JSON] Changing: '{old_val}' -> '{new_val}'")
        b_comment['svgGroupId'] = new_val
        
        # Update the SVG content
        svg_data["content"], _ = update_svg_id(svg_data["content"], old_val, new_val)
        print(f"    [SVG]  Changing: '{old_val}' -> '{new_val}' in {found_in_svg}")
        return True
    else:
        print(f"    [ERROR] ID '{old_val}' with class 'tkk' not found in relevant SVGs for {entry_id}")
        return False


def process_entry(entry, all_svg_files, get_svg_text, loaded_svg_texts, prefix):
    """Process a single textcritics entry and all its block comments.
    
    Args:
        entry (dict): Single textcritics entry
        all_svg_files (list): List of all available SVG files
        get_svg_text (function): Function to load SVG content
        loaded_svg_texts (dict): Cache for currently loaded SVG texts
        prefix (str): Prefix for new IDs
        
    Returns:
        None: Modifies entry in place and handles file operations
    """
    if not isinstance(entry, dict): 
        return

    new_id = entry.get('id', '')
    id_mapping = {}
    
    if new_id:
        # Save any previously loaded SVGs
        for fname, sdata in loaded_svg_texts.items():
            with open(sdata['path'], 'w', encoding='utf-8') as f:
                f.write(sdata['content'])
        
        loaded_svg_texts.clear()
        
        current_main_number = extract_moldenhauer_number(new_id)
        print(f"\nProcessing Entry ID: {new_id} (Main number: {current_main_number})")
        
        relevant_svgs_for_block = get_relevant_svgs(new_id, all_svg_files, current_main_number)
        
        if "SkRT" in new_id:
            print(f"\n SkRT anchor detected: {new_id}")
        else:
            print(f"\n Standard anchor: {new_id}")
            
        print(f"   Assigned SVGs: {relevant_svgs_for_block}")
    else:
        relevant_svgs_for_block = []

    # Process all block comments for this entry
    comments_list = entry.get('commentary', {}).get('comments', [])
    for comment_group in comments_list:
        for b_comment in comment_group.get('blockComments', []):
            process_block_comment(
                b_comment, new_id, relevant_svgs_for_block, 
                get_svg_text, id_mapping, prefix
            )


def save_results(data, loaded_svg_texts, json_path, prefix, final_svg_cache):
    """Save all modified files and display final validation report.
    
    Args:
        data (dict): Modified JSON data to save
        loaded_svg_texts (dict): Currently loaded SVG texts to save
        json_path (str): Path to save the JSON file
        prefix (str): Prefix used for validation
        final_svg_cache (dict): Final SVG cache for validation
        
    Returns:
        None: Saves files and prints validation results
    """
    # Final save of any remaining SVG files
    for fname, sdata in loaded_svg_texts.items():
        with open(sdata['path'], 'w', encoding='utf-8') as f:
            f.write(sdata['content'])

    # Display validation report
    display_uncertainties(data, prefix, final_svg_cache)

    # Save updated JSON
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def process_tkk_ids(json_path, svg_folder, prefix="g-tkk-"):
    """Process TKK IDs in JSON and SVG files.
    
    Main orchestration function that coordinates the TKK ID unification process
    by delegating to specialized sub-functions for better maintainability.
    
    Args:
        json_path (str): Path to the JSON textcritics file
        svg_folder (str): Path to the folder containing SVG files
        prefix (str): Prefix to use for new IDs (default: "g-tkk-")
        
    Returns:
        tuple: (updated_data, final_svg_cache, success)
    """
    print(f"--- Starting processing with SkRT special logic ---")
    
    # Load and validate inputs
    data, all_svg_files = load_and_validate_inputs(json_path, svg_folder)
    
    # Initialize caches and create SVG loader
    final_svg_cache = {}
    loaded_svg_texts = {}
    get_svg_text = create_svg_loader(svg_folder, final_svg_cache, loaded_svg_texts)
    
    # Get entries from data structure
    all_entries = data.get('textcritics', data) if isinstance(data, dict) else data
    
    # Process each entry
    for entry in all_entries:
        process_entry(entry, all_svg_files, get_svg_text, loaded_svg_texts, prefix)
    
    # Save results and generate final report
    save_results(data, loaded_svg_texts, json_path, prefix, final_svg_cache)
    
    return data, final_svg_cache, True


def get_relevant_svgs(new_id, all_svg_files, current_main_number):
    """Get relevant SVG files for a given entry ID.
    
    Args:
        new_id (str): The entry ID
        all_svg_files (list): List of all SVG files
        current_main_number (str): Extracted number from the ID
        
    Returns:
        list: List of relevant SVG filenames
    """
    # Helper function for candidate filtering
    def matches_moldenhauer_number(filename):
        return current_main_number == extract_moldenhauer_number(filename)
    
    # SkRT entries: only row table files
    if "SkRT" in new_id:
        return [
            f for f in all_svg_files 
            if matches_moldenhauer_number(f) and "Reihentabelle" in f
        ]
    
    # Filter candidate files: matching Moldenhauer number, excluding row table files
    candidate_svg_files = [
        f for f in all_svg_files 
        if matches_moldenhauer_number(f) and "Reihentabelle" not in f
    ]
    
    # TF entries: specific Textfassung
    tf_match = re.search(r'TF(\d+)', new_id)
    if tf_match:
        tf_number = tf_match.group(1)
        return [f for f in candidate_svg_files if f"Textfassung{tf_number}" in f]
    
    # Sk entries: specific Sketch with exact matching
    sk_match = re.search(r'(Sk\d+(?:_\d+)*)', new_id) 
    if sk_match:
        sk_identifier = sk_match.group(1)
        pattern = rf'{re.escape(sk_identifier)}(?!_)'
        return [f for f in candidate_svg_files if re.search(pattern, f)]
    
    # Default: all non-Reihentabelle files for this Moldenhauer number
    return candidate_svg_files


def update_svg_id(svg_content, old_val, new_val):
    """Update an ID in SVG content while preserving class="tkk" tags.
    
    Args:
        svg_content (str): The SVG content
        old_val (str): The old ID value
        new_val (str): The new ID value
        
    Returns:
        tuple: (updated_content, error_message)
               error_message is None if successful, string if error occurred
    """
    # Only match the ID if the same tag contains class="tkk"
    escaped_id = re.escape(old_val)
    
    # Create patterns for both quote styles and both attribute orders
    patterns = [
        # Double quotes for both attributes
        f'<[^>]*?id="{escaped_id}"[^>]*?class="tkk"[^>]*?>',
        f'<[^>]*?class="tkk"[^>]*?id="{escaped_id}"[^>]*?>',
        # Single quotes for both attributes  
        f"<[^>]*?id='{escaped_id}'[^>]*?class='tkk'[^>]*?>",
        f"<[^>]*?class='tkk'[^>]*?id='{escaped_id}'[^>]*?>",
    ]
    
    # Count total tkk matches first
    total_tkk_matches = 0
    for pattern in patterns:
        total_tkk_matches += len(re.findall(pattern, svg_content))
    
    if total_tkk_matches > 1:
        return svg_content, f"Multiple class='tkk' elements found with ID '{old_val}' ({total_tkk_matches} occurrences)"
    
    def replace_id(match):
        full_tag = match.group(0)
        return full_tag.replace(f'id="{old_val}"', f'id="{new_val}"').replace(f"id='{old_val}'", f"id='{new_val}'")
    
    # Apply all patterns
    content = svg_content
    for pattern in patterns:
        content = re.sub(pattern, replace_id, content)
    return content, None


def main():
    """Main function to process tkk IDs"""
    
    # --- CONFIGURATION ---
    
    ##### fill in:
    json_path = './tests/data/textcritics.json'

    ##### fill in:
    svg_folder = './tests/img/' 

    prefix = "g-tkk-"
    
    try:
        data, final_svg_cache, success = process_tkk_ids(json_path, svg_folder, prefix)
        if success:
            print(f"\n Finished!")
        else:
            print(f"\n Processing completed with warnings.")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()