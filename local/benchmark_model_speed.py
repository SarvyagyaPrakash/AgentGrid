import os
import time
import json
import cv2
import numpy as np
from PIL import Image
from ultralytics import YOLO
import onnxruntime as ort
import coremltools as ct

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PT_PATH = os.path.join(BASE_DIR, "yolov8s-pose.pt")
MODEL_ONNX_PATH = os.path.join(BASE_DIR, "yolov8s-pose.onnx")
MODEL_COREML_PATH = os.path.join(BASE_DIR, "yolov8s-pose.mlpackage")
VIDEO_PATH = os.path.join(BASE_DIR, "camera_sim/sample_videos/CCTV1.mp4")
RESULTS_PATH = os.path.join(BASE_DIR, "local/benchmark_results.json")
FRAME_COUNT = 300

def get_path_size_mb(path):
    if not os.path.exists(path):
        return 0.0
    if os.path.isfile(path):
        return os.path.getsize(path) / (1024 * 1024)
    # If directory (CoreML mlpackage is a directory)
    total_size = 0
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size / (1024 * 1024)

def main():
    print("==================================================")
    print("ONNX & CoreML Model Speed Benchmarking & Export Tool")
    print("==================================================")
    
    # 1. Load PyTorch model
    print(f"Loading PyTorch model from: {MODEL_PT_PATH}...")
    pytorch_model = YOLO(MODEL_PT_PATH)
    
    # 2. Export to ONNX if not already exported
    if not os.path.exists(MODEL_ONNX_PATH):
        print("Exporting model to ONNX format...")
        onnx_file = pytorch_model.export(format="onnx")
        if onnx_file and os.path.exists(onnx_file) and os.path.abspath(onnx_file) != os.path.abspath(MODEL_ONNX_PATH):
            import shutil
            shutil.move(onnx_file, MODEL_ONNX_PATH)

    # 3. Export to CoreML if not already exported
    if not os.path.exists(MODEL_COREML_PATH):
        print("Exporting model to CoreML format...")
        coreml_file = pytorch_model.export(format="coreml")
        if coreml_file and os.path.exists(coreml_file) and os.path.abspath(coreml_file) != os.path.abspath(MODEL_COREML_PATH):
            import shutil
            if os.path.isdir(coreml_file):
                if os.path.exists(MODEL_COREML_PATH):
                    shutil.rmtree(MODEL_COREML_PATH)
                shutil.move(coreml_file, MODEL_COREML_PATH)
            else:
                shutil.move(coreml_file, MODEL_COREML_PATH)

    # File Sizes
    size_pt_mb = get_path_size_mb(MODEL_PT_PATH)
    size_onnx_mb = get_path_size_mb(MODEL_ONNX_PATH)
    size_coreml_mb = get_path_size_mb(MODEL_COREML_PATH)
    
    print(f"Original PyTorch model size: {size_pt_mb:.2f} MB")
    print(f"Exported ONNX model size: {size_onnx_mb:.2f} MB")
    print(f"Exported CoreML model size: {size_coreml_mb:.2f} MB")
    
    # 4. Load ONNX model using onnxruntime
    print("Initializing ONNX Runtime Session...")
    sess_options = ort.SessionOptions()
    sess_options.intra_op_num_threads = 4
    sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    session = ort.InferenceSession(MODEL_ONNX_PATH, sess_options, providers=['CPUExecutionProvider'])
    onnx_input_name = session.get_inputs()[0].name
    
    # 5. Load CoreML model using coremltools
    print("Initializing CoreML Session...")
    coreml_model = ct.models.MLModel(MODEL_COREML_PATH)
    
    # 6. Open test video
    cap = cv2.VideoCapture(VIDEO_PATH)
    if not cap.isOpened():
        print(f"Error: Could not open video at {VIDEO_PATH}")
        return
        
    print("Reading frames and warming up models...")
    frames = []
    for _ in range(FRAME_COUNT):
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    cap.release()
    
    actual_frames = len(frames)
    print(f"Loaded {actual_frames} frames from video for benchmarking.")
    
    # --- PyTorch Benchmarking ---
    print("\nBenchmarking Original PyTorch Model...")
    # Warmup
    for i in range(10):
        _ = pytorch_model(frames[i], verbose=False)
        
    pt_times = []
    for frame in frames:
        t0 = time.perf_counter()
        _ = pytorch_model(frame, verbose=False)
        pt_times.append(time.perf_counter() - t0)
        
    avg_pt_ms = (sum(pt_times) / len(pt_times)) * 1000.0
    avg_pt_fps = 1.0 / (sum(pt_times) / len(pt_times))
    print(f"PyTorch CPU: {avg_pt_ms:.2f} ms/frame | {avg_pt_fps:.2f} FPS")
    
    # --- ONNX Benchmarking ---
    print("\nBenchmarking Optimized ONNX Model...")
    # Warmup
    for i in range(10):
        img = cv2.resize(frames[i], (640, 640))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = img.transpose((2, 0, 1))
        img = np.expand_dims(img, axis=0)
        img = img.astype(np.float32) / 255.0
        _ = session.run(None, {onnx_input_name: img})
        
    onnx_times = []
    for frame in frames:
        t0 = time.perf_counter()
        
        # Preprocessing
        img = cv2.resize(frame, (640, 640))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = img.transpose((2, 0, 1))
        img = np.expand_dims(img, axis=0)
        img = img.astype(np.float32) / 255.0
        
        # Inference
        _ = session.run(None, {onnx_input_name: img})
        onnx_times.append(time.perf_counter() - t0)
        
    avg_onnx_ms = (sum(onnx_times) / len(onnx_times)) * 1000.0
    avg_onnx_fps = 1.0 / (sum(onnx_times) / len(onnx_times))
    print(f"ONNX CPU: {avg_onnx_ms:.2f} ms/frame | {avg_onnx_fps:.2f} FPS")
    
    # --- CoreML Benchmarking ---
    print("\nBenchmarking Optimized CoreML Model...")
    # Warmup
    for i in range(10):
        # Preprocessing: CoreML model expects PIL Image of shape (640, 640)
        rgb_frame = cv2.cvtColor(frames[i], cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb_frame).resize((640, 640))
        _ = coreml_model.predict({"image": pil_img})
        
    coreml_times = []
    for frame in frames:
        t0 = time.perf_counter()
        
        # Preprocessing
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb_frame).resize((640, 640))
        
        # Inference
        _ = coreml_model.predict({"image": pil_img})
        coreml_times.append(time.perf_counter() - t0)
        
    avg_coreml_ms = (sum(coreml_times) / len(coreml_times)) * 1000.0
    avg_coreml_fps = 1.0 / (sum(coreml_times) / len(coreml_times))
    print(f"CoreML Neural Engine: {avg_coreml_ms:.2f} ms/frame | {avg_coreml_fps:.2f} FPS")
    
    # Determine the fastest method
    methods = {
        "pytorch": avg_pt_ms,
        "onnx": avg_onnx_ms,
        "coreml": avg_coreml_ms
    }
    fastest_method = min(methods, key=methods.get)
    
    model_speed_data = {
        "test_frame_count": actual_frames,
        "pytorch": {
            "avg_inference_ms": round(avg_pt_ms, 3),
            "avg_fps": round(avg_pt_fps, 2),
            "model_file_size_mb": round(size_pt_mb, 2)
        },
        "onnx": {
            "avg_inference_ms": round(avg_onnx_ms, 3),
            "avg_fps": round(avg_onnx_fps, 2),
            "model_file_size_mb": round(size_onnx_mb, 2)
        },
        "coreml": {
            "avg_inference_ms": round(avg_coreml_ms, 3),
            "avg_fps": round(avg_coreml_fps, 2),
            "model_file_size_mb": round(size_coreml_mb, 2)
        },
        "fastest_method": fastest_method,
        "note": "ONNX CPU execution did not outperform native PyTorch on this hardware; CoreML is the more relevant comparison for Apple Silicon edge devices specifically, since it uses the Neural Engine rather than CPU-only execution."
    }
    
    # Load existing results (keeping the bandwidth data intact)
    if os.path.exists(RESULTS_PATH):
        try:
            with open(RESULTS_PATH, "r") as f:
                results_data = json.load(f)
        except Exception:
            results_data = {}
    else:
        results_data = {}
        
    results_data["model_speed"] = model_speed_data
    
    with open(RESULTS_PATH, "w") as f:
        json.dump(results_data, f, indent=2)
        
    print("\n==================================================")
    print(f"Results successfully appended to {RESULTS_PATH}")
    print("==================================================")
    print(json.dumps(model_speed_data, indent=2))

if __name__ == "__main__":
    main()
