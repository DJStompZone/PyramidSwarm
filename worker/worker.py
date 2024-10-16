import datetime as dt
from dataclasses import dataclass
from hashlib import sha256

import torch # type: ignore
import redis # type: ignore
import mutagen # type: ignore
from flask import Flask, request, jsonify

from pyramid_dit import PyramidDiTForVideoGeneration # type: ignore
from diffusers.utils import export_to_video # type: ignore

app = Flask(__name__)

redis_client = redis.Redis(host="redis", port=6379)

model_path = "/app/models/pyramid-flow"
model_dtype = torch.bfloat16
variant = "diffusion_transformer_768p"

model = PyramidDiTForVideoGeneration(model_path, model_dtype, model_variant=variant)
model.vae.to("cuda")
model.dit.to("cuda")
model.text_encoder.to("cuda")
model.vae.enable_tiling()

@dataclass
class TagOptions:
    description: str
    comment: str
    date: str
    title: str
    artist: str
    genre: str

@dataclass
class InferenceOptions:
    prompt: str
    filename: str
    tags: TagOptions
    num_inference_steps: list[int]
    video_num_inference_steps: list[int]
    temp: float
    guidance_scale: float
    video_guidance_scale: float
    fps: int
    resolution: str

def add_tags_to_inference_output(options: InferenceOptions):
    description = f"Prompt: {options.prompt}"
    tags = TagOptions(
        description=description,
        comment="Generated using PyramidFlow",
        date=dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        title=f"pyramidSWARM_{sha256(options.prompt.encode()).hexdigest()[:5]}",
        artist="pyramidSWARM",
        genre="AI Generated"
    )

    audio = mutagen.File(options.filename, easy=True)
    tag_data = {
        "description": tags.description,
        "comment": tags.comment,
        "date": tags.date,
        "title": tags.title,
        "artist": tags.artist,
        "genre": tags.genre
    }

    for tag, value in tag_data.items():
        audio[tag] = value

    audio.save()
    return options.filename

@app.route('/infer', methods=['POST'])
def perform_inference():
    data = request.json
    options = InferenceOptions(
        prompt=data["prompt"],
        filename="/app/outputs/pyramidSWARM_video_{}.mp4".format(sha256(data["prompt"].encode()).hexdigest()),
        tags=None,
        num_inference_steps=[data["num_inference_steps"]] * 3,
        video_num_inference_steps=[data["num_video_inference_steps"]] * 3,
        temp=data["temperature"],
        guidance_scale=data["guidance_scale"],
        video_guidance_scale=data["video_guidance_scale"],
        fps=data["fps"],
        resolution=data["resolution"]
    )

    with torch.no_grad(), torch.autocast("cuda", dtype=torch.bfloat16):
        frames = model.generate(
            prompt=options.prompt,
            num_inference_steps=options.num_inference_steps,
            video_num_inference_steps=options.video_num_inference_steps,
            temp=options.temp,
            guidance_scale=options.guidance_scale,
            video_guidance_scale=options.video_guidance_scale,
            height=1280 if options.resolution == "High" else 640,
            width=768 if options.resolution == "High" else 384,
            output_type="pil"
        )

    export_to_video(frames, options.filename, fps=options.fps)
    
    options.filename = add_tags_to_inference_output(options)
    
    return jsonify({"status": "success", "output": options.filename})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
