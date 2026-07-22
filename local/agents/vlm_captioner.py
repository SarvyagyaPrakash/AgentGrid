import time
import torch
import cv2
from PIL import Image
from transformers import AutoProcessor, AutoModelForImageTextToText

import threading

_processor = None
_model = None
_device = None
_lock = threading.Lock()

def init_model():
    global _processor, _model, _device
    if _model is not None:
        return
        
    model_id = "HuggingFaceTB/SmolVLM-500M-Instruct"
    
    # Detect best available device
    if torch.backends.mps.is_available():
        _device = "mps"
        dtype = torch.float32  # float32 is safest for MPS
    elif torch.cuda.is_available():
        _device = "cuda"
        dtype = torch.bfloat16
    else:
        _device = "cpu"
        dtype = torch.float32
        
    print(f"[VLMCaptioner] Loading {model_id} on {_device}...")
    start = time.perf_counter()
    _processor = AutoProcessor.from_pretrained(model_id)
    _model = AutoModelForImageTextToText.from_pretrained(
        model_id,
        torch_dtype=dtype
    ).to(_device)
    _model.eval()
    print(f"[VLMCaptioner] Model loaded successfully in {time.perf_counter() - start:.2f} seconds.")

def generate_caption(frame) -> str:
    global _processor, _model, _device
    with _lock:
        try:
            init_model()
            
            # Convert OpenCV BGR frame to PIL RGB Image
            image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(image_rgb)
            
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image"},
                        {"type": "text", "text": "Describe what is happening in this video frame precisely in detail (maximum 99 words)."},
                    ],
                },
            ]
            
            text = _processor.apply_chat_template(messages, add_generation_prompt=True)
            inputs = _processor(text=[text], images=[image], return_tensors="pt").to(_device)
            
            generated_ids = _model.generate(
                **inputs, 
                max_new_tokens=69, 
                repetition_penalty=1.2,
                do_sample=False
            )
            generated_texts = _processor.batch_decode(
                generated_ids, 
                skip_special_tokens=True, 
            )
            
            full_text = generated_texts[0]
            response = full_text
            if "Assistant:" in full_text:
                response = full_text.split("Assistant:")[-1].strip()
            elif "assistant\n" in full_text:
                response = full_text.split("assistant\n")[-1].strip()
                
            return response
        except Exception as e:
            print(f"[VLMCaptioner] Error during captioning: {e}")
            return f"Error: {e}"
