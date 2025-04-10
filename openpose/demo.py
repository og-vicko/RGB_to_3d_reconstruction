import streamlit as st
import subprocess
import os
import json
from PIL import Image
import warnings
warnings.filterwarnings("ignore")


def run_openpose(image_path, output_dir="output_json_folder/"):
    os.makedirs(output_dir, exist_ok=True)
    command = f"build\\x64\\Release\\OpenPoseDemo.exe --image_dir test_images/ --hand --write_json {output_dir}"
    subprocess.run(command, shell=True)
    
    json_filename = os.path.join(output_dir, os.path.splitext(os.path.basename(image_path))[0] + '_keypoints.json')
    if os.path.exists(json_filename):
        with open(json_filename, 'r') as f:
            return json.load(f)
    else:
        return None

st.title("OpenPose Streamlit Demo")

uploaded_file = st.file_uploader("Upload an image", type=["jpg", "png", "jpeg"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", use_column_width=True)
    
    save_dir = "test_images"
    os.makedirs(save_dir, exist_ok=True)
    image_path = os.path.join(save_dir, uploaded_file.name)
    
    with open(image_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    if st.button("Run OpenPose"):
        st.write("Processing image...")
        output = run_openpose(image_path)
        
        if output:
            st.json(output)
        else:
            st.error("Failed to generate JSON output. Make sure OpenPose is correctly installed and configured.")

    if st.button("3D-Demo"):
        import base64

        # Load the 3D model
        obj_file = "adam.obj"
        with open(obj_file, "r") as file:
            obj_data = file.read()

        # Convert the OBJ model to base64 (for embedding in HTML)
        obj_base64 = base64.b64encode(obj_data.encode()).decode()

        # HTML + JavaScript for Three.js Viewer
        html_code = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/three/examples/js/loaders/OBJLoader.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/three/examples/js/controls/OrbitControls.js"></script>
        </head>
        <body>
            <div id="viewer" style="width: 100%; height: 600px;"></div>
            <script>
                var scene = new THREE.Scene();
                var camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
                camera.position.set(0, 1, 5);

                var renderer = new THREE.WebGLRenderer({{ antialias: true }});
                renderer.setSize(window.innerWidth, window.innerHeight);
                document.getElementById('viewer').appendChild(renderer.domElement);

                // Lighting (Ambient + Directional)
                var ambientLight = new THREE.AmbientLight(0xffffff, 1.5);
                scene.add(ambientLight);

                var directionalLight = new THREE.DirectionalLight(0xffffff, 2);
                directionalLight.position.set(2, 2, 5);
                scene.add(directionalLight);

                // Load OBJ model
                var loader = new THREE.OBJLoader();
                var objData = atob("{obj_base64}");
                var objBlob = new Blob([objData], {{ type: 'text/plain' }});
                var objUrl = URL.createObjectURL(objBlob);

                loader.load(objUrl, function (object) {{
                    scene.add(object);
                }});

                // Orbit Controls (Allow rotation, zoom, pan)
                var controls = new THREE.OrbitControls(camera, renderer.domElement);
                controls.enableDamping = true;
                controls.dampingFactor = 0.05;
                controls.screenSpacePanning = false;
                controls.maxDistance = 10;
                controls.minDistance = 1;

                // Animation loop
                function animate() {{
                    requestAnimationFrame(animate);
                    controls.update();
                    renderer.render(scene, camera);
                }}
                animate();
            </script>
        </body>
        </html>
        """

        # Display in Streamlit
        st.components.v1.html(html_code, height=650)
