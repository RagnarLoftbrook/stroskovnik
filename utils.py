import base64
import io
import json
import os

def validate_inputs(
    machine_cost_per_hour,
    material_cost_per_unit,
    production_time_minutes,
    labor_cost_per_hour,
    overhead_percentage,
    profit_margin_percentage,
    batch_size
):
    """
    Validate the user inputs for the manufacturing calculator.
    
    Parameters:
    -----------
    machine_cost_per_hour : float
        Cost of running the machine per hour
    material_cost_per_unit : float
        Cost of material per unit/piece
    production_time_minutes : float
        Time in minutes to produce one piece
    labor_cost_per_hour : float
        Cost of labor per hour
    overhead_percentage : float
        Overhead percentage
    profit_margin_percentage : float
        Profit margin percentage
    batch_size : int
        Number of pieces in the batch
        
    Returns:
    --------
    tuple
        (is_valid, message) - Boolean indicating if inputs are valid and an error message if not
    """
    # Check for negative values
    if machine_cost_per_hour < 0:
        return False, "Machine cost per hour cannot be negative."
    
    if material_cost_per_unit < 0:
        return False, "Material cost per unit cannot be negative."
    
    if production_time_minutes <= 0:
        return False, "Production time must be greater than zero."
    
    if labor_cost_per_hour < 0:
        return False, "Labor cost per hour cannot be negative."
    
    if overhead_percentage < 0 or overhead_percentage > 100:
        return False, "Overhead percentage must be between 0 and 100."
    
    if profit_margin_percentage < 0 or profit_margin_percentage > 100:
        return False, "Profit margin percentage must be between 0 and 100."
    
    if batch_size <= 0:
        return False, "Batch size must be greater than zero."
    
    # If we get here, inputs are valid
    return True, "Inputs valid"

def get_download_link(content, filename, link_text):
    """
    Generate a download link for a file with the given content.
    
    Parameters:
    -----------
    content : str
        Content of the file to be downloaded
    filename : str
        Name of the file to be downloaded
    link_text : str
        Text to display for the download link
        
    Returns:
    --------
    str
        HTML anchor tag for downloading the file
    """
    # Encode the content as base64
    b64 = base64.b64encode(content.encode()).decode()
    
    # Create the download link
    href = f'<a href="data:file/txt;base64,{b64}" download="{filename}" class="btn" style="text-decoration:none;padding:8px 16px;color:white;background-color:#0066cc;border-radius:5px;cursor:pointer;">{link_text}</a>'
    
    return href

# Preset management functions
def get_presets_directory():
    """
    Returns the directory where presets are stored.
    Creates the directory if it doesn't exist.
    
    Returns:
    --------
    str
        Path to the presets directory
    """
    presets_dir = "presets"
    if not os.path.exists(presets_dir):
        os.makedirs(presets_dir)
    return presets_dir

def save_preset(preset_name, preset_data):
    """
    Save a calculation preset to a JSON file.
    
    Parameters:
    -----------
    preset_name : str
        Name of the preset (will be used as filename)
    preset_data : dict
        Dictionary containing preset data
    
    Returns:
    --------
    bool
        True if saved successfully, False otherwise
    """
    try:
        # Get the presets directory
        presets_dir = get_presets_directory()
        
        # Create a sanitized filename
        sanitized_name = preset_name.replace(" ", "_").lower()
        if not sanitized_name.endswith(".json"):
            sanitized_name += ".json"
        
        # Full path to the preset file
        preset_path = os.path.join(presets_dir, sanitized_name)
        
        # Write the preset data to file
        with open(preset_path, 'w') as f:
            json.dump(preset_data, f, indent=4)
        
        return True
    except Exception as e:
        print(f"Error saving preset: {e}")
        return False

def load_preset(preset_name):
    """
    Load a calculation preset from a JSON file.
    
    Parameters:
    -----------
    preset_name : str
        Name of the preset
    
    Returns:
    --------
    dict or None
        Dictionary containing preset data, or None if not found/error
    """
    try:
        # Get the presets directory
        presets_dir = get_presets_directory()
        
        # Create a sanitized filename
        sanitized_name = preset_name
        if not sanitized_name.endswith(".json"):
            sanitized_name += ".json"
        
        # Full path to the preset file
        preset_path = os.path.join(presets_dir, sanitized_name)
        
        # Read the preset data from file
        if os.path.exists(preset_path):
            with open(preset_path, 'r') as f:
                preset_data = json.load(f)
            return preset_data
        else:
            return None
    except Exception as e:
        print(f"Error loading preset: {e}")
        return None

def get_all_presets():
    """
    Get a list of all available presets.
    
    Returns:
    --------
    list
        List of preset names without the .json extension
    """
    try:
        # Get the presets directory
        presets_dir = get_presets_directory()
        
        # Get all JSON files in the directory
        preset_files = [f for f in os.listdir(presets_dir) if f.endswith('.json')]
        
        # Remove the .json extension from file names
        preset_names = [os.path.splitext(f)[0] for f in preset_files]
        
        return preset_names
    except Exception as e:
        print(f"Error getting presets: {e}")
        return []

def delete_preset(preset_name):
    """
    Delete a calculation preset.
    
    Parameters:
    -----------
    preset_name : str
        Name of the preset to delete
    
    Returns:
    --------
    bool
        True if deleted successfully, False otherwise
    """
    try:
        # Get the presets directory
        presets_dir = get_presets_directory()
        
        # Create a sanitized filename
        sanitized_name = preset_name
        if not sanitized_name.endswith(".json"):
            sanitized_name += ".json"
        
        # Full path to the preset file
        preset_path = os.path.join(presets_dir, sanitized_name)
        
        # Delete the file if it exists
        if os.path.exists(preset_path):
            os.remove(preset_path)
            return True
        else:
            return False
    except Exception as e:
        print(f"Error deleting preset: {e}")
        return False
