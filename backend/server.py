import base64
from io import BytesIO
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import numpy as np

# Import your existing backend logic
from backend_api import BackendAPI

app = Flask(__name__)
# Enable CORS to allow requests from your React frontend (port 5173)
CORS(app, resources={r"/*": {"origins": "*"}})

# Initialize the logic layer
api = BackendAPI()

def numpy_to_base64(arr):
    """Helper: Convert numpy array to base64 string for frontend display."""
    try:
        if arr is None:
            return None
        # Ensure array is uint8
        if arr.dtype != np.uint8:
            arr = arr.astype(np.uint8)
        
        img = Image.fromarray(arr)
        buff = BytesIO()
        img.save(buff, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buff.getvalue()).decode("utf-8")
    except Exception as e:
        print(f"Error converting to base64: {e}")
        return None

@app.route('/upload/<int:slot_id>', methods=['POST'])
def upload_image(slot_id):
    """Handle image upload for a specific slot[cite: 6]."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    try:
        # Load image using PIL to get numpy array
        image = Image.open(file.stream)
        img_array = np.array(image)
        
        # Load into backend (handles grayscale conversion automatically )
        result = api.load_image_from_array(slot_id, img_array)
        
        # Enforce "One Size" rule 
        api.resize_all_images()
        
        # Return the processed (grayscale/resized) image to verify upload
        processed_data = api.get_image_data(slot_id)
        if processed_data['success']:
            b64_img = numpy_to_base64(processed_data['image_array'])
            return jsonify({'success': True, 'imageUrl': b64_img})
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/view/<int:slot_id>/<component_type>', methods=['GET'])
def get_component_view(slot_id, component_type):
    """
    Get a specific component view.
    Brightness/contrast handled in frontend only.
    """
    try:
        # Map frontend component names to backend data
        # 'Original' = colored RGB image
        # 'Greyscale' = grayscale image
        if component_type == 'Original':
            # Return colored original image
            data = api.get_component_data(slot_id, 'color')
            key = 'component_array'
        elif component_type == 'Greyscale':
            # Return grayscale image
            data = api.get_image_data(slot_id)
            key = 'image_array'
        else:
            # FFT components
            data = api.get_component_data(slot_id, component_type.lower())
            key = 'component_array'
            
        if not data.get('success'):
            return jsonify(data), 400
            
        b64_img = numpy_to_base64(data[key])
        return jsonify({'success': True, 'imageUrl': b64_img})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/mix', methods=['POST'])
def start_mixing():
    """Trigger async mixing process[cite: 27]."""
    settings = request.json
    
    # Define a callback (though in HTTP we rely on polling)
    def mixing_done(result):
        pass 
        
    api.mix_images_async(settings, mixing_done)
    return jsonify({'success': True, 'status': 'started'})

@app.route('/progress', methods=['GET'])
def get_progress():
    """Poll for progress bar updates."""
    return jsonify(api.get_mixing_progress())

@app.route('/cancel', methods=['POST'])
def cancel_mixing():
    """Cancel current operation[cite: 27]."""
    return jsonify(api.cancel_mixing())

@app.route('/output/<int:port_id>', methods=['GET'])
def get_output(port_id):
    """Get the mixed result for a specific port. Brightness/contrast handled in frontend."""
    data = api.get_output_image(port_id)
    if not data.get('success'):
        # If empty, return a null success to clear viewer
        return jsonify({'success': False, 'error': 'Empty'})
        
    b64_img = numpy_to_base64(data['output_array'])
    return jsonify({'success': True, 'imageUrl': b64_img})

if __name__ == '__main__':
    print("🚀 Flask Backend Running on http://localhost:5000")
    app.run(debug=True, port=5000)