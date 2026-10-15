import os
import uvicorn
import gradio as gr
from fastapi.middleware.cors import CORSMiddleware
from database.database import init_db
from app.backend.main import app as fastapi_app

# ZeroGPU requirement: at least one function decorated with @spaces.GPU
try:
    import spaces

    @spaces.GPU
    def zero_gpu_heartbeat():
        return "ZeroGPU initialized"
except Exception as e:
    print(f"ZeroGPU notice: {e}")

# Initialize database
try:
    init_db()
except Exception as e:
    print(f"Database init notice: {e}")

# Build Gradio Blocks for status check
with gr.Blocks(title="AI Interview Coach Backend API") as demo:
    gr.Markdown("# 🚀 AI Interview Coach Backend API\nFastAPI backend is live, connected, and healthy.")
    btn = gr.Button("ZeroGPU Status", visible=False)
    if "spaces" in locals() and hasattr(spaces, "GPU"):
        btn.click(zero_gpu_heartbeat, outputs=[])

# Mount Gradio onto FastAPI so FastAPI handles root routes (/health, /users, /resumes, /jobs, etc.)
app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio")

if __name__ == "__main__":
    # In Hugging Face ZeroGPU, port 7860 is used by ZeroGPU broker daemon; user app listens on 7861
    port = int(os.environ.get("PORT", 7861))
    if port == 7860:
        port = 7861
    uvicorn.run(app, host="0.0.0.0", port=port)