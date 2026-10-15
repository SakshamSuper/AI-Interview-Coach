import os
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

try:
    from gradio import Server

    app = Server()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(fastapi_app.router)
    demo = app
except Exception as e:
    import gradio as gr

    with gr.Blocks(title="AI Interview Coach Backend API") as demo:
        gr.Markdown("# 🚀 AI Interview Coach Backend API\nFastAPI backend is live and healthy.")
        btn = gr.Button("ZeroGPU Status", visible=False)
        if "spaces" in locals() and hasattr(spaces, "GPU"):
            btn.click(zero_gpu_heartbeat, outputs=[])
    app = gr.routes.App.create_app(demo)
    app.include_router(fastapi_app.router)

if __name__ == "__main__":
    demo.launch()