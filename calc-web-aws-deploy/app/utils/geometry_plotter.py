import base64
import io
from typing import Dict, List, Tuple

import matplotlib

# Use non-interactive backend for server environments
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

LAYER_COLORS = {
    "superficieTotal": "#4F6F52",
    "superficieVacios": "#D6C15A",
    "superficieMacizos": "#8A4F7D",
    "superficieCasetones": "#3B6EA5",
}


def _plot_polygons(ax, polygons: List[Dict], color: str, numerate: bool = False, label_prefix: str = "P"):
    for poly in polygons:
        coords: List[Tuple[float, float]] = poly.get("coordenadas", [])
        if not coords:
            continue

        xs = [point[0] for point in coords]
        ys = [point[1] for point in coords]

        ax.fill(xs, ys, color=color, alpha=0.55, edgecolor="black", linewidth=0.8)

        if numerate:
            # Skip last duplicated coord (first point repeated)
            inner_xs = xs[:-1]
            inner_ys = ys[:-1]
            if not inner_xs or not inner_ys:
                continue
            cx = sum(inner_xs) / len(inner_xs)
            cy = sum(inner_ys) / len(inner_ys)
            ax.text(
                cx,
                cy,
                f"{label_prefix}{poly.get('id', '')}",
                fontsize=9,
                ha="center",
                va="center",
                bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="black", linewidth=0.6),
            )


def _plot_casetones(ax, casetones: List[Dict]):
    for caseton in casetones:
        x_min = caseton.get("x_min")
        x_max = caseton.get("x_max")
        y_min = caseton.get("y_min")
        y_max = caseton.get("y_max")
        if None in (x_min, x_max, y_min, y_max):
            continue

        width = x_max - x_min
        height = y_max - y_min
        rect = mpatches.Rectangle(
            (x_min, y_min),
            width,
            height,
            linewidth=0.6,
            edgecolor="#1f2937",
            facecolor="#93c5fd",
            alpha=0.65,
        )
        ax.add_patch(rect)


def generate_geometry_preview(geometry_result: Dict) -> Dict:
    """Generate a PNG preview of the DXF geometry and return as base64."""
    geometry_data = geometry_result.get("geometria", {})
    casetones_info = geometry_result.get("casetones", [])

    if not geometry_data:
        return {}

    fig, ax = plt.subplots(figsize=(10, 7))
    ax.set_facecolor("#f8fafc")
    ax.grid(True, linestyle="--", linewidth=0.4, color="#cbd5f5")

    # Draw layers
    for layer, color in LAYER_COLORS.items():
        polygons = geometry_data.get(layer, [])
        if not polygons:
            continue
        numerate = layer == "superficieCasetones"
        _plot_polygons(ax, polygons, color, numerate=numerate)

    if casetones_info:
        _plot_casetones(ax, casetones_info)

    ax.set_aspect("equal", adjustable="box")
    ax.set_title("Distribución geométrica del DXF", fontsize=14, color="#0f172a", pad=16)
    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")

    legend_handles = []
    for layer, color in LAYER_COLORS.items():
        legend_handles.append(mpatches.Patch(color=color, label=layer.replace("superficie", "Superficie ")))
    if casetones_info:
        legend_handles.append(mpatches.Patch(facecolor="#93c5fd", edgecolor="#1f2937", label="Casetones"))

    if legend_handles:
        ax.legend(handles=legend_handles, loc="lower right", fontsize=9, frameon=True)

    buffer = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buffer, format="png", dpi=150)
    plt.close(fig)

    buffer.seek(0)
    encoded = base64.b64encode(buffer.read()).decode("utf-8")
    return {
        "image_base64": f"data:image/png;base64,{encoded}",
    }
