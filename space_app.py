import os
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

# Build Gradio Blocks
with gr.Blocks(title="AI Interview Coach Backend API") as demo:
    gr.Markdown("# 🚀 AI Interview Coach Backend API\nFastAPI backend is live, connected, and healthy.")
    btn = gr.Button("ZeroGPU Status", visible=False)
    if "spaces" in locals() and hasattr(spaces, "GPU"):
        btn.click(zero_gpu_heartbeat, outputs=[])

# Add CORS middleware to demo.app
demo.app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all FastAPI routes onto demo.app
demo.app.include_router(fastapi_app.router)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    demo.launch(server_name="0.0.0.0", server_port=port)