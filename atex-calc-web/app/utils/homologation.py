import sqlite3
import re
from typing import List, Dict, Optional

from app.utils.section_plotter import generate_section_plot

DEFAULT_BF_CM = 80.0
DEFAULT_BS_CM = 12.0
DEFAULT_BW_CM = 12.0
DEFAULT_HV_CM = 20.0
DEFAULT_HF_CM = 5.0

HF_OPTIONS_CM = [5.0, 6.0, 7.0, 7.5, 8.0, 9.0, 10.0, 11.0, 12.0]


def _normalize_caseton_name(value: Optional[str]) -> str:
    if not value:
        return ''
    normalized = str(value).strip().lower()
    normalized = normalized.replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
    normalized = normalized.replace('atex', '')
    normalized = normalized.replace('casetón', '').replace('caseton', '')
    normalized = normalized.replace(' ', '')
    normalized = normalized.replace('-', '')
    return normalized


_CASETON_NAME_PATTERN = re.compile(
    r'^(?P<w>\d+(?:[\.,]\d+)?)(?P<suffix>[a-z]+)?x(?P<h>\d+(?:[\.,]\d+)?)$'
)


def _expand_caseton_keys(value: Optional[str]) -> List[str]:
    normalized = _normalize_caseton_name(value)
    if not normalized:
        return []

    keys = {normalized}
    match = _CASETON_NAME_PATTERN.match(normalized)
    if not match:
        return list(keys)

    raw_w = match.group('w')
    raw_h = match.group('h')
    suffix = match.group('suffix') or ''
    try:
        w = float(raw_w.replace(',', '.'))
        h = float(raw_h.replace(',', '.'))
    except ValueError:
        return list(keys)

    def _add_variant(w_value: float, h_value: float, suffix_value: str) -> None:
        w_int = int(round(w_value))
        h_int = int(round(h_value))
        keys.add(_normalize_caseton_name(f"{w_int}{suffix_value}x{h_int}"))
        keys.add(_normalize_caseton_name(f"{w_int}x{h_int}"))

    _add_variant(w, h, suffix)

    if w >= 200 and h >= 200:
        _add_variant(w / 10.0, h / 10.0, suffix)

    if w <= 200 and h <= 200:
        _add_variant(w * 10.0, h * 10.0, suffix)

    return list(keys)


def _fetch_casetones(database_path: str) -> List[tuple]:
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, side1, side2, height, bw, bs, system, consumption, rental_price FROM casetones ORDER BY name"
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
    allowed_casetones: Optional[List[str]] = None,
    hf_options_cm: Optional[List[float]] = None,
    system: Optional[str] = None,
) -> Dict[str, Optional[Dict]]:
    derived_metrics = _derive_section_metrics(section_metrics, fallback_params)
    target_value_ratio = derived_metrics.get('value_ratio')

    casetones = _fetch_casetones(database_path)
    options: List[Dict] = []
    recommended_option: Optional[Dict] = None
    hf_options = list(hf_options_cm) if hf_options_cm else HF_OPTIONS_CM
    system_key = str(system).strip().lower() if system else None

    allowed_keys = None
    strict_allowed_names = None
    if allowed_casetones is not None:
        raw_allowed = set(
            _normalize_caseton_name(name)
            for name in allowed_casetones
            if name
        )
        db_name_keys = set()
        for row in casetones:
            name = row[1]
            system_label = row[7]
            if system_key is not None and str(system_label or '').strip().lower() != system_key:
                continue
            db_name_keys.add(_normalize_caseton_name(name))

        if raw_allowed.intersection(db_name_keys):
            strict_allowed_names = raw_allowed
            allowed_keys = raw_allowed
        else:
            expanded: List[str] = []
            for name in allowed_casetones:
                expanded.extend(_expand_caseton_keys(name))
            allowed_keys = set(key for key in expanded if key)

    for row in casetones:
        (
            caseton_id,
            name,
            side1,
            side2,
            height,
            bw,
            bs,
            system_label,
            consumption_base,
            rental_price,
        ) = row

        if system_key is not None and str(system_label or '').strip().lower() != system_key:
            continue

        if strict_allowed_names is not None:
            if _normalize_caseton_name(name) not in strict_allowed_names:
                continue

        bf_cm = float(side1) if side1 else float(side2 or 0)
        if bf_cm <= 0:
            continue
        hv_cm = float(height)
        bw_cm = float(bw)
        bs_cm = float(bs)
        consumption_base = float(consumption_base)

        if strict_allowed_names is None and allowed_keys is not None:
            caseton_label_cm = f"{int(round(bf_cm))}x{int(round(hv_cm))}"
            caseton_label_mm = f"{int(round(bf_cm * 10.0))}x{int(round(hv_cm * 10.0))}"
            candidate_keys = set(_expand_caseton_keys(name))
            candidate_keys.update(_expand_caseton_keys(caseton_label_cm))
            candidate_keys.update(_expand_caseton_keys(caseton_label_mm))
            if allowed_keys.isdisjoint(candidate_keys):
                continue

        for hf_cm in hf_options:
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
                'system': system_label,
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
        'hf_options_cm': hf_options,
        'properties': _build_properties(derived_metrics),
        'original_metrics': derived_metrics,
    }
