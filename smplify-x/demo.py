import streamlit as st
import subprocess
import os
import json
from PIL import Image
import warnings
warnings.filterwarnings("ignore")

def run_openpose(image_file, image_output_dir="../openpose/DATA_FOLDER/images", keypoints_output_dir="../openpose/DATA_FOLDER/keypoints"):
    os.makedirs(image_output_dir, exist_ok=True)
    os.makedirs(keypoints_output_dir, exist_ok=True)

    # Save the uploaded image to the image output directory
    temp_image_path = os.path.join(image_output_dir, "temp_image.jpg")
    with open(temp_image_path, "wb") as f:
        f.write(image_file.getbuffer())

    # Change to the OpenPose root directory and run the command
    openpose_root = os.path.join('..', 'openpose')
    command = f"cd {openpose_root} && .\\build\\x64\\Release\\OpenPoseDemo.exe --image_dir {image_output_dir} --write_json {keypoints_output_dir}"
    subprocess.run(command, shell=True)
    
    json_filename = os.path.join(keypoints_output_dir, 'temp_image_keypoints.json')
    if os.path.exists(json_filename):
        with open(json_filename, 'r') as f:
            return json.load(f)
    else:
        return None

def run_smplifyx(data_folder, output_folder, model_folder, vposer_ckpt):
    smplifyx_root = os.path.join('..', 'smplify-x')
    command = f"cd {smplifyx_root} && python smplifyx/main.py --config cfg_files/fit_smplx.yaml --data_folder {data_folder} --output_folder {output_folder} --visualize=False --model_folder {model_folder} --vposer_ckpt {vposer_ckpt}"
    subprocess.run(command, shell=True)

# Custom CSS to change the background color of the file uploader
st.markdown("""
    <style>
        /* Change background color of the outer container */
        div.stFileUploader {
            background-color: #2e3b4e !important; /* Match background */
            padding: 10px;
            border-radius: 10px;
        }

        /* Change background color of the inner upload box */
        div.stFileUploader > div {
            background-color: #2e3b4e !important; /* Same as outer container */
            border: 2px dashed #555 !important; /* Optional border styling */
            color: white !important; /* Change text color */
        }

        /* Style the browse button */
        div.stFileUploader button {
            background-color: #111 !important; /* Dark button */
            color: white !important;
            border-radius: 5px;
        }
    </style>
""", unsafe_allow_html=True)    

st.title("Streamlit Demo")

uploaded_file = st.file_uploader("Upload an image", type=["jpg", "png", "jpeg"])

if st.button("Run OpenPose") and uploaded_file is not None:
    st.write("Processing image...")
    output = run_openpose(uploaded_file)
    
    if output:
        st.json(output)
        st.write("Running SMPLify-X...")
        run_smplifyx(data_folder="../openpose/DATA_FOLDER", output_folder="OUTPUT_FOLDER", model_folder="MODEL_FOLDER", vposer_ckpt="VPOSER_FOLDER")
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


import streamlit as st
import os
import base64
import time

if st.button("3D-Demo"):
    mesh_dir = "./OUTPUT_FOLDER/meshes/"
    
    obj_files = []
    for subdir in os.listdir(mesh_dir):
        subdir_path = os.path.join(mesh_dir, subdir)
        if os.path.isdir(subdir_path):
            obj_file_path = os.path.join(subdir_path, "000.obj")
            if os.path.exists(obj_file_path):
                obj_files.append(obj_file_path)

    # Preload all OBJ files
    obj_base64_list = []
    for obj_file in obj_files:
        with open(obj_file, "r") as file:
            obj_data = file.read()
        obj_base64 = base64.b64encode(obj_data.encode()).decode()
        obj_base64_list.append(obj_base64)

    # Convert list to JavaScript array format
    obj_list_js = ", ".join(f'"{obj}"' for obj in obj_base64_list)

    # HTML + JavaScript for Three.js Viewer with Auto-Updating Objects
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
            var scene, camera, renderer, controls, currentObject;
            var objList = [{obj_list_js}];  // Preloaded objects
            var currentIndex = 0;

            function init() {{
                scene = new THREE.Scene();
                camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
                camera.position.set(0, 1, 5);

                renderer = new THREE.WebGLRenderer({{ antialias: true }});
                renderer.setSize(window.innerWidth, window.innerHeight);
                document.getElementById('viewer').appendChild(renderer.domElement);

                // Lighting
                var ambientLight = new THREE.AmbientLight(0xffffff, 1.5);
                scene.add(ambientLight);

                var directionalLight = new THREE.DirectionalLight(0xffffff, 2);
                directionalLight.position.set(2, 2, 5);
                scene.add(directionalLight);

                // Controls
                controls = new THREE.OrbitControls(camera, renderer.domElement);
                controls.enableDamping = true;
                controls.dampingFactor = 0.05;
                controls.screenSpacePanning = false;
                controls.maxDistance = 10; 
                controls.minDistance = 1;

                loadObject(objList[currentIndex]); // Load first object
                animate();

                // Auto-update object every second
                setInterval(updateObject, 1000);
            }}

            function loadObject(objDataBase64) {{
                var loader = new THREE.OBJLoader();
                var objData = atob(objDataBase64);
                var objBlob = new Blob([objData], {{ type: 'text/plain' }});
                var objUrl = URL.createObjectURL(objBlob);

                loader.load(objUrl, function (object) {{
                    if (currentObject) {{
                        scene.remove(currentObject); // Remove old object
                    }}
                    currentObject = object;
                    scene.add(object);
                }});
            }}

            function updateObject() {{
                currentIndex = (currentIndex + 1) % objList.length; // Loop through objects
                loadObject(objList[currentIndex]);
            }}

            function animate() {{
                requestAnimationFrame(animate);
                controls.update();
                renderer.render(scene, camera);
            }}

            init();
        </script>
    </body>
    </html>
    """

    # Display in Streamlit
    st.components.v1.html(html_code, height=650)
