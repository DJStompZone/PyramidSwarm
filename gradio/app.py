import gradio as gr
import requests

def submit_inference(prompt, resolution, temperature, guidance_scale, video_guidance_scale, fps, num_inference_steps, num_video_inference_steps):
    data = {
        "prompt": prompt,
        "resolution": resolution,
        "temperature": temperature,
        "guidance_scale": guidance_scale,
        "video_guidance_scale": video_guidance_scale,
        "fps": fps,
        "num_inference_steps": num_inference_steps,
        "num_video_inference_steps": num_video_inference_steps,
    }
    response = requests.post("http://backend_worker_1:5000/infer", json=data)
    if response.status_code == 200:
        return "Inference successful. Video generated."
    else:
        return "Failed to perform inference."

iface = gr.Interface(
    fn=submit_inference,
    inputs=[
        "text",
        gr.Dropdown(choices=["High", "Low"], label="Resolution"),
        gr.Slider(1, 31, step=1, label="Temperature"),
        gr.Slider(1, 15, step=0.1, label="Guidance Scale"),
        gr.Slider(1, 15, step=0.1, label="Video Guidance Scale"),
        gr.Slider(8, 24, step=1, label="Frames Per Second"),
        gr.Slider(5, 50, step=1, label="Number of Inference Steps"),
        gr.Slider(3, 30, step=1, label="Number of Video Inference Steps"),
    ],
    outputs="text",
    title="PyramidFlow Inference",
)

iface.launch(server_name="0.0.0.0", server_port=7860)
