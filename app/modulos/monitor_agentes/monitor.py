from flask import Blueprint, render_template, jsonify

from app.memoria.execution_trace import get_events


monitor_agentes_bp = Blueprint(
    "monitor_agentes",
    __name__
)


@monitor_agentes_bp.route("/agent_flow")
def agent_flow():

    return render_template(
        "agent_flow.html"
    )


@monitor_agentes_bp.route("/agent_flow/events")
def agent_events():

    return jsonify(
        get_events()
    )