from typing import Dict, List, Any
import plotly.graph_objects as go


def create_radar_chart(
    technical: float, relevance: float, completeness: float, clarity: float, communication: float
) -> go.Figure:
    categories = ["Technical Depth", "Relevance", "Completeness", "Clarity", "Communication"]
    values = [technical, relevance, completeness, clarity, communication]

    # Close the radar polygon
    categories_closed = categories + [categories[0]]
    values_closed = values + [values[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=categories_closed,
        fill="toself",
        name="Candidate Performance",
        line=dict(color="#4F46E5", width=2),
        fillcolor="rgba(79, 70, 229, 0.25)"
    ))

    # Benchmark trace (Target 85)
    benchmark = [85, 85, 85, 85, 85, 85]
    fig.add_trace(go.Scatterpolar(
        r=benchmark,
        theta=categories_closed,
        name="Target Benchmark",
        line=dict(color="#10B981", dash="dash", width=1.5)
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=10)),
        ),
        showlegend=True,
        title=dict(text="Evaluation Dimension Breakdown", x=0.5, font=dict(size=14)),
        margin=dict(l=40, r=40, t=50, b=40),
        height=320
    )
    return fig


def create_topic_performance_bar(topic_performance: Dict[str, float]) -> go.Figure:
    if not topic_performance:
        topic_performance = {"General Engineering": 75.0}

    topics = list(topic_performance.keys())
    scores = list(topic_performance.values())
    colors = ["#10B981" if s >= 75 else ("#F59E0B" if s >= 60 else "#EF4444") for s in scores]

    fig = go.Figure(go.Bar(
        x=topics,
        y=scores,
        marker_color=colors,
        text=[f"{s}%" for s in scores],
        textposition="auto"
    ))

    fig.update_layout(
        title=dict(text="Proficiency by Topic", x=0.5, font=dict(size=14)),
        yaxis=dict(range=[0, 100], title="Proficiency (%)"),
        xaxis=dict(title="Technical Topic"),
        margin=dict(l=40, r=40, t=50, b=40),
        height=320
    )
    return fig


def create_score_history_chart(score_history: List[Dict[str, Any]]) -> go.Figure:
    if not score_history:
        return go.Figure()

    dates = [f"Session {i+1}" for i in range(len(score_history))]
    scores = [s.get("score") or 0 for s in score_history]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=scores,
        mode="lines+markers+text",
        name="Overall Score",
        line=dict(color="#3B82F6", width=3),
        marker=dict(size=8, color="#1D4ED8"),
        text=[f"{s:.0f}%" for s in scores],
        textposition="top center"
    ))

    fig.update_layout(
        title=dict(text="Score Trajectory Over Time", x=0.5, font=dict(size=14)),
        yaxis=dict(range=[0, 105], title="Score (%)"),
        xaxis=dict(title="Interview Attempts"),
        margin=dict(l=40, r=40, t=50, b=40),
        height=300
    )
    return fig


def create_match_gauge(match_score: float) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=match_score,
        domain={"x": [0, 1], "y": [0, 1]},
        title={"text": "Job Alignment", "font": {"size": 15}},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "#4F46E5"},
            "steps": [
                {"range": [0, 50], "color": "#FEE2E2"},
                {"range": [50, 75], "color": "#FEF3C7"},
                {"range": [75, 100], "color": "#D1FAE5"}
            ],
            "threshold": {
                "line": {"color": "#10B981", "width": 4},
                "thickness": 0.75,
                "value": 75
            }
        }
    ))
    fig.update_layout(height=240, margin=dict(l=30, r=30, t=40, b=20))
    return fig
