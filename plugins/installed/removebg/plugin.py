"""
Remove Background Plugin for AbdullahHub
Uses Remove.bg API to remove backgrounds from images
"""

PLUGIN_NAME = "Remove Background"
PLUGIN_DESCRIPTION = "Remove backgrounds from images using AI"
PLUGIN_VERSION = "1.0.0"
PLUGIN_AUTHOR = "AbdullahHub"
PLUGIN_CATEGORY = "Image Processing"

import requests
import base64
from io import BytesIO
from PIL import Image
import os

def execute(context):
    """
    Execute the Remove Background plugin
    
    Required in context:
    - api_key: Remove.bg API key
    - input.image: Base64 encoded image or URL
    
    Returns:
    - Base64 encoded image with background removed
    """
    
    api_key = context.get('api_key') or os.environ.get('REMOVEBG_API_KEY')
    if not api_key:
        return {
            "success": False,
            "error": "API key required. Please configure Remove.bg API key in plugin settings."
        }
    
    input_data = context.get('input', {})
    image_data = input_data.get('image')
    
    if not image_data:
        return {
            "success": False,
            "error": "No image provided. Please provide image data or URL."
        }
    
    try:
        # Check if image is URL or base64
        if image_data.startswith('http'):
            # Download from URL
            response = requests.get(image_data)
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Failed to download image from URL: {response.status_code}"
                }
            image_bytes = response.content
        else:
            # Assume base64
            if ',' in image_data:
                # Strip data URL prefix
                image_data = image_data.split(',')[1]
            image_bytes = base64.b64decode(image_data)
        
        # Call Remove.bg API
        result = remove_background(image_bytes, api_key)
        
        if result.get('success'):
            return {
                "success": True,
                "image": result['image'],
                "format": result['format'],
                "width": result['width'],
                "height": result['height'],
                "credits_charged": result['credits_charged'],
                "message": "Background removed successfully!"
            }
        else:
            return {
                "success": False,
                "error": result.get('error', 'Unknown error')
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Processing failed: {str(e)}"
        }

def remove_background(image_bytes, api_key):
    """
    Call Remove.bg API to remove background
    """
    try:
        # Remove.bg API endpoint
        url = "https://api.remove.bg/v1.0/removebg"
        
        headers = {
            'X-Api-Key': api_key,
        }
        
        files = {
            'image_file': ('image.png', image_bytes),
            'size': (None, 'auto'),
            'type': (None, 'auto'),
        }
        
        response = requests.post(url, headers=headers, files=files)
        
        if response.status_code == 200:
            # Convert to base64
            result_bytes = response.content
            img_base64 = base64.b64encode(result_bytes).decode('utf-8')
            
            # Get image info
            img = Image.open(BytesIO(result_bytes))
            
            # Parse response headers for credits info
            credits_charged = response.headers.get('X-Credits-Charged', 'Unknown')
            
            return {
                "success": True,
                "image": f"data:image/png;base64,{img_base64}",
                "format": img.format,
                "width": img.width,
                "height": img.height,
                "credits_charged": credits_charged
            }
        else:
            error_msg = f"API Error: {response.status_code}"
            try:
                error_data = response.json()
                if 'errors' in error_data:
                    error_msg = error_data['errors'][0]['title']
            except:
                pass
            
            return {
                "success": False,
                "error": error_msg
            }
            
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Network error: {str(e)}"
        }

# Test function for development
def test():
    """Test the plugin with a sample image"""
    # Replace with your API key
    api_key = "xv5aoeuirxTNZBYS5KykZZEK"
    
    # Sample test - you would normally have an actual image
    print("RemoveBG Plugin Test")
    print(f"API Key: {api_key[:10]}...")
    print("Plugin loaded successfully!")
    
    return {"status": "ready", "api_key_set": bool(api_key)}

if __name__ == "__main__":
    test()
