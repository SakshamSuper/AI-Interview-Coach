import os
import uvicorn
from app.backend.main import app as fastapi_app

try:
    import gradio as gr
    demo = gr.Blocks(title="AI Interview Coach Backend API")
    with demo:
        gr.Markdown("# 🚀 AI Interview Coach Backend API\nFastAPI backend is live and healthy.")
    app = gr.mount_gradio_app(fastapi_app, demo, path="/status")
except Exception:
    app = fastapi_app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)