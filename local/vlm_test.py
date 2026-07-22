import os
import sys
import time
import torch
import argparse
import random
import cv2
from PIL import Image
from transformers import AutoProcessor, AutoModelForImageTextToText

def main():
    # Set up argument parsing to accept dynamic image or video sources
    parser = argparse.ArgumentParser(description="Standalone dynamic VLM testing script for SmolVLM.")
    parser.add_argument(
        "--image", 
        type=str, 
        default=None, 
        help="Path to an image file to run captioning on."
    )
    parser.add_argument(
        "--video",
        type=str,
        default=None,
        help="Path to a video file or RTSP stream URL to dynamically extract a frame from."
    )
    args = parser.parse_args()

    image_path = None
    
    if args.image:
        image_path = args.image
    elif args.video:
        print(f"Opening video/stream source: {args.video}...")
        cap = cv2.VideoCapture(args.video)
        if not cap.isOpened():
            print(f"Error: Could not open video/stream at {args.video}")
            return
        
        # Check if it's a file with multiple frames, or a live stream
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames > 1:
            # Local video file: Pick a random frame (skip first 60 to bypass black screens)
            start_f = min(60, total_frames - 1)
            end_f = max(start_f, total_frames - 1)
            frame_idx = random.randint(start_f, end_f)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            print(f"Dynamically extracting frame {frame_idx}/{total_frames}...")
        else:
            # RTSP/Live stream: grab the latest live frame
            print("Extracting live frame from RTSP stream...")

        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            print("Error: Failed to read frame from video/stream source.")
            return
        
        # Save frame to a temporary file
        image_path = "temp_dynamic_frame.png"
        cv2.imwrite(image_path, frame)
        print(f"Extracted frame saved temporary as: {image_path}")
    else:
        # Default fallback: check if test_frame.png exists, otherwise extract it from default video
        image_path = "test_frame.png"
        if not os.path.exists(image_path):
            print("No inputs provided. Automatically extracting default frame from CCTV1.mp4...")
            cap = cv2.VideoCapture("camera_sim/sample_videos/CCTV1.mp4")
            for _ in range(60):
                cap.read()
            ret, frame = cap.read()
            if ret:
                cv2.imwrite(image_path, frame)
                print(f"Saved default frame to {image_path}")
            cap.release()

    if not image_path or not os.path.exists(image_path):
        print(f"Error: Target image file {image_path} does not exist.")
        return

    model_id = "HuggingFaceTB/SmolVLM-500M-Instruct"
    
    # Detect best available device
    if torch.backends.mps.is_available():
        device = "mps"
        dtype = torch.float32  # float32 is safest for MPS/CPU compatibility
    elif torch.cuda.is_available():
        device = "cuda"
        dtype = torch.bfloat16
    else:
        device = "cpu"
        dtype = torch.float32
        
    print(f"Using device: {device} with dtype: {dtype}")

    print(f"Loading image from {image_path}...")
    try:
        image = Image.open(image_path)
    except Exception as e:
        print(f"Failed to load image: {e}")
        return

    print(f"Loading SmolVLM processor and model '{model_id}'...")
    start_load = time.perf_counter()
    try:
        processor = AutoProcessor.from_pretrained(model_id)
        model = AutoModelForImageTextToText.from_pretrained(
            model_id,
            torch_dtype=dtype
        ).to(device)
        model.eval()
    except Exception as e:
        print(f"Error loading model: {e}")
        return
        
    print(f"Model loaded successfully in {time.perf_counter() - start_load:.2f} seconds.")
    
    # Define prompt for image captioning
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image"},
                {"type": "text", "text": "Describe what is happening in this video frame precisely in detail (maximum 99 words)."},
            ],
        },
    ]
    
    print("Running captioning on the image...")
    start_caption = time.perf_counter()
    try:
        # Process input
        text = processor.apply_chat_template(messages, add_generation_prompt=True)
        inputs = processor(text=[text], images=[image], return_tensors="pt").to(device)
        
        # Generate caption with constraints (maximum 99 words, repetition penalty to avoid loops)
        generated_ids = model.generate(
            **inputs, 
            max_new_tokens=69, 
            repetition_penalty=1.2,
            do_sample=False
        )
        generated_texts = processor.batch_decode(
            generated_ids, 
            skip_special_tokens=True, 
        )
        
        duration = time.perf_counter() - start_caption
        
        full_text = generated_texts[0]
        # Extract assistant output if present
        response = full_text
        if "Assistant:" in full_text:
            response = full_text.split("Assistant:")[-1].strip()
        elif "assistant\n" in full_text:
            response = full_text.split("assistant\n")[-1].strip()
            
        print("\n" + "="*60)
        print(f"Source Image: {image_path}")
        print(f"Extracted Caption: {response}")
        print(f"Time Taken: {duration:.4f} seconds")
        print("="*60 + "\n")
        
        # Clean up temporary frames if they were created from video
        if args.video and os.path.exists("temp_dynamic_frame.png"):
            os.remove("temp_dynamic_frame.png")
            print("Removed temporary frame: temp_dynamic_frame.png")
            
    except Exception as e:
        print(f"Error during captioning: {e}")

if __name__ == "__main__":
    main()
