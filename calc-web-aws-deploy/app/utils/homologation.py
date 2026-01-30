import sqlite3
from typing import List, Dict, Optional

from app.utils.section_plotter import generate_section_plot

DEFAULT_BF_CM = 80.0
DEFAULT_BS_CM = 12.0
DEFAULT_BW_CM = 12.0
DEFAULT_HV_CM = 20.0
DEFAULT_HF_CM = 5.0

HF_OPTIONS_CM = [5.0, 6.0, 7.0, 7.5, 8.0, 9.0, 10.0, 11.0, 12.0]


def _fetch_casetones(database_path: str) -> List[tuple]:
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, side1, side2, height, bw, bs, consumption, rental_price FROM casetones ORDER BY name"
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def _build_properties(section_metrics: Optional[Dict]) -> Optional[List[Dict]]:
    if not section_metrics:
        return None
    bf = section_metrics.get('bf_cm')
    inertia = section_metrics.get('inertia_cm4')
    value_ratio = section_metrics.get('value_ratio')
    if bf is None or inertia is None or value_ratio is None:
        return None
    return [
        {'item': 'Ancho Afer.', 'spec': 'b(o) (cm)', 'value': round(float(bf), 1)},
        {'item': 'Inercia.', 'spec': 'I(o) (cm4)', 'value': round(float(inertia), 2)},
        {'item': 'b(o)/I(o)', 'spec': '(1/cm3) x 10^3', 'value': round(float(value_ratio), 3)},
    ]


def _derive_section_metrics(section_metrics: Optional[Dict], fallback_params: Optional[Dict]) -> Dict:
    if section_metrics and section_metrics.get('value_ratio'):
        return section_metrics

    params = fallback_params or {}
    bf_cm = float(params.get('bf_cm') or params.get('bf') or DEFAULT_BF_CM)
    bs_cm = float(params.get('bs_cm') or params.get('bs') or DEFAULT_BS_CM)
    bw_cm = float(params.get('bw_cm') or params.get('bw') or DEFAULT_BW_CM)
    hv_cm = float(params.get('hv_cm') or params.get('hv') or DEFAULT_HV_CM)
    hf_cm = float(params.get('hf_cm') or params.get('hf') or DEFAULT_HF_CM)
    he_cm = hv_cm + hf_cm

    section = generate_section_plot('aligerada', bf_cm, bs_cm, bw_cm, hv_cm, hf_cm, he_cm)
    return {
        'bf_cm': bf_cm,
        'bs_cm': bs_cm,
        'bw_cm': bw_cm,
        'hv_cm': hv_cm,
        'hf_cm': hf_cm,
        'total_thickness_cm': he_cm,
        'inertia_cm4': section.inertia_cm4,
        'value_ratio': section.value_ratio,
        'area_cm2': section.area_cm2,
        'equivalent_solid_height_cm': section.equivalent_solid_height_cm,
        'slab_type': 'Aligerada',
    }


def generate_homologation_analysis(
    database_path: str,
    section_metrics: Optional[Dict] = None,
    fallback_params: Optional[Dict] = None,
) -> Dict[str, Optional[Dict]]:
    derived_metrics = _derive_section_metrics(section_metrics, fallback_params)
    target_value_ratio = derived_metrics.get('value_ratio')

    casetones = _fetch_casetones(database_path)
    options: List[Dict] = []
    recommended_option: Optional[Dict] = None

    for row in casetones:
        (
            caseton_id,
            name,
            side1,
            side2,
            height,
            bw,
            bs,
            consumption_base,
            rental_price,
        ) = row

        bf_cm = float(side1) if side1 else float(side2 or 0)
        if bf_cm <= 0:
            continue
        hv_cm = float(height)
        bw_cm = float(bw)
        bs_cm = float(bs)
        consumption_base = float(consumption_base)

        for hf_cm in HF_OPTIONS_CM:
            try:
                section = generate_section_plot(
                    'aligerada',
                    bf_cm,
                    bs_cm,
                    bw_cm,
                    hv_cm,
                    hf_cm,
                    hv_cm + hf_cm,
                )
            except Exception:
                continue

            value_ratio = section.value_ratio
            check = True if target_value_ratio is None else value_ratio <= target_value_ratio
            extra_consumption = max((hf_cm / 100.0) - 0.05, 0.0)
            consumption = consumption_base + extra_consumption

            option = {
                'caseton_id': caseton_id,
                'caseton': name,
                'caseton_label': f"{int(round(bf_cm))}x{int(round(hv_cm))}",
                'bf_cm': bf_cm,
                'bs_cm': bs_cm,
                'bw_cm': bw_cm,
                'hv_cm': hv_cm,
                'hf_cm': hf_cm,
                'slab_height_cm': hv_cm + hf_cm,
                'inertia_cm4': section.inertia_cm4,
                'value_ratio': value_ratio,
                'consumption_m3_m2': consumption,
                'check': check,
            }
            options.append(option)

            if check:
                if (
                    recommended_option is None
                    or option['consumption_m3_m2'] < recommended_option['consumption_m3_m2']
                ):
                    recommended_option = option

    options.sort(key=lambda item: (not item['check'], item['consumption_m3_m2']))

    return {
        'options': options,
        'recommended': recommended_option,
        'target_value_ratio': target_value_ratio,
        'hf_options_cm': HF_OPTIONS_CM,
        'properties': _build_properties(derived_metrics),
        'original_metrics': derived_metrics,
    }
