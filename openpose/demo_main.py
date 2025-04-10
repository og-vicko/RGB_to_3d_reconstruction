import base64
import streamlit as st
import subprocess
import os
import time
import json
import cv2
import shutil
import warnings
from PIL import Image

warnings.filterwarnings("ignore")


def extract_frames(video_file, output_dir, max_frames=1):
    """
    Extracts frames from a video file and saves them as images in the specified output directory.

    This function writes the uploaded video file to a temporary location, then reads it using OpenCV,
    extracting and saving a limited number of frames (default: 2).

    Args:
        video_file (BytesIO): Video file uploaded by user.
        output_dir (str): The path to the directory where extracted frames will be saved.
        max_frames (int, optional): The maximum number of frames to extract. Defaults to 1.

    Returns:
        str: Path to the directory containing the extracted frame images.

    Notes:
        - The function also creates a temporary directory '../openpose/DATA_FOLDER/video' to store
          the uploaded video as 'temp_video.mp4'.
        - If fewer than `max_frames` are available, only available frames will be saved.
        - Each saved frame is named 'frame_0.jpg', 'frame_1.jpg', etc.
    """    

    os.makedirs(output_dir, exist_ok=True)
    video_output_dir = "../openpose/DATA_FOLDER/video"
    os.makedirs(video_output_dir, exist_ok=True)

    temp_video_path = os.path.join(video_output_dir, "temp_video.mp4")
    with open(temp_video_path, "wb") as f:
        f.write(video_file.getbuffer())
    
    cap = cv2.VideoCapture(temp_video_path)
    frame_count = 0
    
    while frame_count < max_frames:
        success, frame = cap.read()
        if not success:
            break
        frame_filename = os.path.join(output_dir, f"frame_{frame_count}.jpg")
        cv2.imwrite(frame_filename, frame)
        frame_count += 1
    
    cap.release()
    return output_dir  # Return directory where frames are stored

def run_openpose(image_file=None, image_output_dir="../openpose/DATA_FOLDER/images",
                 keypoints_output_dir="../openpose/DATA_FOLDER/keypoints", is_image=False):
    """
    Runs the OpenPose executable on an input image and saves the extracted keypoints.

    This function prepares the necessary folders, optionally saves an uploaded image to disk,
    and then invokes OpenPose with the appropriate flags to detect hand, face, and body keypoints.

    Args:
        image_file (BytesIO, optional): Image or frames extracted from video.
        image_output_dir (str, optional): Path where the image will be stored before OpenPose processes it.
        keypoints_output_dir (str, optional): Path where OpenPose will store the resulting keypoints in JSON format.
        is_image (bool, optional): Flag indicating if the uploaded file is a single image.

    Returns:
        bool: True if keypoints were generated successfully, else False

    Notes:
        - Assumes OpenPose is built and the executable exists at '../openpose/build/x64/Release/OpenPoseDemo.exe'.
        - Assumes you’re running this on Windows. For Linux/Mac, update the command syntax accordingly.
        - Make sure that OpenPose environment dependencies (like models) are properly configured.
    """    
    os.makedirs(image_output_dir, exist_ok=True)
    os.makedirs(keypoints_output_dir, exist_ok=True)

    if is_image:
        # Save the uploaded image to the specified directory
        temp_image_path = os.path.join(image_output_dir, "temp_image.jpg")
        with open(temp_image_path, "wb") as f:
            f.write(image_file.getbuffer())
    
    openpose_root = os.path.join('..', 'openpose')
    command = f"cd {openpose_root} && .\\build\\x64\\Release\\OpenPoseDemo.exe --image_dir {image_output_dir} --hand --face --write_json {keypoints_output_dir}"
    subprocess.run(command, shell=True)

    return os.path.isdir(keypoints_output_dir) and os.listdir(keypoints_output_dir)


def run_smplifyx(data_folder, output_folder, model_folder, vposer_ckpt):
    """
    Runs SMPLify-X on the OpenPose keypoints for 3D mesh fitting.

    Args:
        data_folder (str): Directory containing OpenPose keypoints.
        output_folder (str): Directory to store the 3D mesh output.
        model_folder (str): Path to SMPL-X model files.
        vposer_ckpt (str): Path to VPoser checkpoint file.

    Returns:
        None
    """    
    smplifyx_root = "../smplify-x"
    os.makedirs(output_folder, exist_ok=True)
    command = f"cd {smplifyx_root} && python smplifyx/main.py --config cfg_files/fit_smplx.yaml --data_folder {data_folder} --output_folder {output_folder} --visualize=False --model_folder {model_folder} --vposer_ckpt {vposer_ckpt}"
    subprocess.run(command, shell=True)

# Streamlit UI
st.title("RGB to 3D Demo.")

uploaded_file = st.file_uploader("Upload an image or video", type=["jpg", "png", "jpeg","webp", "mp4", "avi"])
num_frames = st.number_input("Number of frames to process", min_value=1, max_value=30, value=1)

# Handle the uploaded file and run OpenPose models when Run button is clicked
if st.button("Run") and uploaded_file is not None:
    start = time.time()
    file_extension = uploaded_file.name.split(".")[-1].lower()
    image_output_dir = "../openpose/DATA_FOLDER/images/"
    keypoints_output_dir = "../openpose/DATA_FOLDER/keypoints"
    
    if file_extension in ["mp4", "avi"]:
        # Extract frames from the video
        with st.spinner("Extracting frames from video..."):
            image_dir = extract_frames(uploaded_file, image_output_dir, max_frames=num_frames)

        with st.spinner("Processing..."):
            # Process video frames with openpose
            json_output = run_openpose(image_file=image_dir, image_output_dir=image_dir, keypoints_output_dir=keypoints_output_dir, is_image=False)
    else:
        # Process image with openpose
        with st.spinner("Processing..."):
            json_output = run_openpose(image_file=uploaded_file, image_output_dir=image_output_dir, keypoints_output_dir=keypoints_output_dir, is_image=True)
        
    if json_output:
        # Run smplify-x on the extracted keypoints
        with st.spinner("Processing Keypoints..."):
            run_smplifyx(data_folder="../openpose/DATA_FOLDER", output_folder="OUTPUT_FOLDER", model_folder="MODEL_FOLDER", vposer_ckpt="VPOSER_FOLDER")
            st.write("Processed successfully.")
    else:
        st.error("Failed to generate JSON output. Make sure OpenPose is correctly installed and configured.")
    end = time.time()
    execution_time = end - start
    st.write(f"It took {execution_time:.2f} seconds to run.")
    
    ################ Display the 3D model and video frame side by side ################
    mesh_dir = "./OUTPUT_FOLDER/meshes/"
    image_output_dir = "../openpose/DATA_FOLDER/images/"
    
    # Build a mapping of folder name -> (obj_file_path, frame_file_path)
    match_dict = {}
    for subdir in os.listdir(mesh_dir):
        subdir_path = os.path.join(mesh_dir, subdir)
        if os.path.isdir(subdir_path):
            obj_file_path = os.path.join(subdir_path, "000.obj")
            frame_file_path = os.path.join(image_output_dir, f"{subdir}.jpg")
            if os.path.exists(obj_file_path) and os.path.exists(frame_file_path):
                match_dict[subdir] = (obj_file_path, frame_file_path)

    # Sort the keys to ensure a consistent order
    ordered_keys = sorted(match_dict.keys())
    obj_files = [match_dict[k][0] for k in ordered_keys]
    frame_files = [match_dict[k][1] for k in ordered_keys]

    obj_base64_list = []
    frame_base64_list = []
    
    for obj_file, frame_file in zip(obj_files, frame_files):
        with open(obj_file, "rb") as file:
            obj_data = file.read()
        obj_base64_list.append(base64.b64encode(obj_data).decode())
        
        with open(frame_file, "rb") as file:
            frame_data = file.read()
        frame_base64_list.append(base64.b64encode(frame_data).decode())

    # Prepare JS list of base64 models and images
    obj_list_js = ", ".join(f'"{obj}"' for obj in obj_base64_list)
    frame_list_js = ", ".join(f'"{frame}"' for frame in frame_base64_list)

    # HTML and JS for 3D rendering in browser using Three.js
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src=\"https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js\"></script>
        <script src=\"https://cdn.jsdelivr.net/npm/three/examples/js/loaders/OBJLoader.js\"></script>
        <script src=\"https://cdn.jsdelivr.net/npm/three/examples/js/controls/OrbitControls.js\"></script>
    </head>
    
    <body>
        <div style="display: flex; flex-direction: row; width: 100%;">
            <div id="viewer" style="width: 50%; height: 600px;"></div>
            <div style="width: 50%; height: 600px;">
                <img id="image" style="width: 100%; height: 100%;" />
            </div>
        </div>
        <script>
            var scene, camera, renderer, controls, currentObject;
            var objList = [{obj_list_js}];
            var frameList = [{frame_list_js}];  // Preloaded frames
            var currentIndex = 0;
            console.log(frameList);
            function init() {{
                scene = new THREE.Scene();
                var viewer = document.getElementById('viewer');
                var aspect = viewer.clientWidth / viewer.clientHeight;
                camera = new THREE.PerspectiveCamera(75, aspect, 0.1, 1000);
                camera.position.set(0, 1, 5);
                renderer = new THREE.WebGLRenderer({{ antialias: true }});
                renderer.setSize(viewer.clientWidth, viewer.clientHeight);
                document.getElementById('viewer').appendChild(renderer.domElement);
                var ambientLight = new THREE.AmbientLight(0xffffff, 1.5);
                scene.add(ambientLight);
                var directionalLight = new THREE.DirectionalLight(0xffffff, 2);
                directionalLight.position.set(2, 2, 5);
                scene.add(directionalLight);
                controls = new THREE.OrbitControls(camera, renderer.domElement);
                controls.enableDamping = true;
                controls.dampingFactor = 0.05;
                controls.screenSpacePanning = false;
                controls.maxDistance = 10;
                controls.minDistance = 1;
                loadObject(objList[currentIndex]);
                animate();
                setTimeout(function() {{
                    updateObject(); // Ensure the image updates initially after a delay
                    setInterval(updateObject, 100);
                }}, 1500);  // 1500ms delay (adjust as needed)
            }}
            function loadObject(objDataBase64) {{
                var loader = new THREE.OBJLoader();
                var objData = atob(objDataBase64);
                var objBlob = new Blob([objData], {{ type: 'text/plain' }});
                var objUrl = URL.createObjectURL(objBlob);
                loader.load(objUrl, function (object) {{
                    if (currentObject) scene.remove(currentObject);
                    currentObject = object;
                    scene.add(object);
                }});
            }}
            function updateObject() {{
                var imageElement = document.getElementById("image");
                // When the image finishes loading, load the corresponding 3D object
                imageElement.onload = function() {{
                     loadObject(objList[currentIndex]);
                     // prepare next index for the following cycle
                     currentIndex = (currentIndex + 1) % objList.length;
                }};
                // Update the image src (this triggers the onload event)
                imageElement.src = "data:image/jpeg;base64," + frameList[currentIndex];
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
    st.components.v1.html(html_code, height=650)
    
if st.button("End"):
    print(os.getcwd())
    smplifyx_root = "OUTPUT_FOLDER/"
    openpose_root = os.path.join('..', 'openpose/DATA_FOLDER/')
    shutil.rmtree(smplifyx_root)
    shutil.rmtree(openpose_root)
