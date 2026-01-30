import base64
import io
from dataclasses import dataclass
from typing import Dict, List, Tuple

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt


@dataclass
class SectionResult:
    image_base64: str
    inertia_cm4: float
    area_cm2: float
    value_ratio: float
    equivalent_solid_height_cm: float


def _polygon_inertia(vertices: List[Tuple[float, float]]) -> Tuple[float, float, float]:
    """Return (Ix centroidal, area, centroid_y)."""
    area = 0.0
    ix = 0.0
    cy = 0.0
    n = len(vertices)
    for i in range(n):
        x0, y0 = vertices[i]
        x1, y1 = vertices[(i + 1) % n]
        det = x0 * y1 - x1 * y0
        area += det
        cy += (y0 + y1) * det
        ix += (y0 ** 2 + y0 * y1 + y1 ** 2) * det
    area *= 0.5
    if area == 0:
        return 0.0, 0.0, 0.0
    cy /= (6.0 * area)
    ix /= 12.0
    ix_centroidal = ix - area * (cy ** 2)
    return ix_centroidal, area, cy


def _build_vertices(section_type: str, bf: float, bs: float, bw: float, hv: float, hf: float, he: float) -> List[Tuple[float, float]]:
    section_type = section_type.lower()
    if section_type == 'maciza':
        # Simple rectangle width bf, height he
        return [(0.0, 0.0), (bf, 0.0), (bf, he), (0.0, he)]

    # Default to aligerada (waffle slab T-section)
    x1 = 0.0
    x2 = (bf - bs) / 2.0
    x3 = x2 + ((bs - bw) / 2.0)
    x4 = x3 + bw
    x5 = x4 + ((bs - bw) / 2.0)
    x6 = bf

    y1 = 0.0
    y2 = hv
    y3 = hv + hf

    return [
        (x1, y2),
        (x2, y2),
        (x3, y1),
        (x4, y1),
        (x5, y2),
        (x6, y2),
        (x6, y3),
        (x1, y3),
    ]


def _plot_section(vertices: List[Tuple[float, float]], section_type: str) -> str:
    closed_vertices = vertices + [vertices[0]]
    xs = [v[0] for v in closed_vertices]
    ys = [v[1] for v in closed_vertices]

    fig, ax = plt.subplots(figsize=(6, 3))
    ax.set_facecolor('#f8fafc')
    ax.fill(xs, ys, color='#a5b4fc', alpha=0.65, edgecolor='#1e1b4b', linewidth=2)
    ax.plot(xs, ys, color='#312e81', linewidth=2)
    ax.scatter(xs[:-1], ys[:-1], color='#ef4444', s=15, zorder=5)

    span = max(max(xs) - min(xs), 1e-3)
    offset = span * 0.015
    for idx, (x, y) in enumerate(vertices, start=1):
        ax.text(x + offset, y + offset, f"V{idx}", fontsize=8, color='#0f172a')

    ax.set_aspect('equal', adjustable='box')
    ax.set_xlabel('X (cm)')
    ax.set_ylabel('Y (cm)')
    ax.set_title(f'Sección {"Maciza" if section_type.lower() == "maciza" else "Aligerada"}', fontsize=12)
    ax.grid(True, linestyle='--', linewidth=0.4, alpha=0.6)

    buffer = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buffer, format='png', dpi=150)
    plt.close(fig)

    buffer.seek(0)
    return f"data:image/png;base64,{base64.b64encode(buffer.read()).decode('utf-8')}"


def generate_section_plot(section_type: str, bf: float, bs: float, bw: float, hv: float, hf: float, he: float) -> SectionResult:
    vertices = _build_vertices(section_type, bf, bs, bw, hv, hf, he)
    ix_centroidal, area, _ = _polygon_inertia(vertices)

    if section_type.lower() == 'maciza':
        # Simple rectangle inertia (about base) then convert to centroidal already handled
        inertia_cm4 = bf * (he ** 3) / 12.0
        value_ratio = bf / inertia_cm4 * 1000 if inertia_cm4 else 0.0
        equivalent_height = he
    else:
        inertia_cm4 = ix_centroidal
        value_ratio = bf / inertia_cm4 * 1000 if inertia_cm4 else 0.0
        equivalent_height = (inertia_cm4 * 12 / bf) ** (1 / 3) if bf and inertia_cm4 > 0 else 0.0

    image = _plot_section(vertices, section_type)
    return SectionResult(
        image_base64=image,
        inertia_cm4=inertia_cm4,
        area_cm2=area,
        value_ratio=value_ratio,
        equivalent_solid_height_cm=equivalent_height,
    )
