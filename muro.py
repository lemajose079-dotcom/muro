import math
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Diseño Sísmico y Geotécnico de Muros - NEC-15 / ACI 318-19",
    page_icon="🧱",
    layout="wide",
)

st.title("🧱 Diseño Geotécnico y Estructural de Muros de Contención")
st.caption(
    "Normativa: **NEC-15 (Ecuador)** | **ACI 318-19** | Acción Sísmica Automática **Mononobe-Okabe ($k_h$ y $k_v$)**"
)

# ---------------------------------------------------------
# TABLA DE FACTORES DE SITIO Fa (NEC-SE-DS 2015 - Tabla 2)
# ---------------------------------------------------------
FA_NEC_2015 = {
    "Perfil A (Roca Rígida)": {0.15: 0.9, 0.25: 0.9, 0.30: 0.9, 0.35: 0.9, 0.40: 0.9, 0.50: 0.9},
    "Perfil B (Roca)": {0.15: 1.0, 0.25: 1.0, 0.30: 1.0, 0.35: 1.0, 0.40: 1.0, 0.50: 1.0},
    "Perfil C (Suelo Denso)": {0.15: 1.4, 0.25: 1.3, 0.30: 1.25, 0.35: 1.2, 0.40: 1.15, 0.50: 1.1},
    "Perfil D (Suelo Rígido)": {0.15: 1.6, 0.25: 1.4, 0.30: 1.3, 0.35: 1.2, 0.40: 1.1, 0.50: 1.0},
    "Perfil E (Suelo Blando)": {0.15: 1.8, 0.25: 1.5, 0.30: 1.35, 0.35: 1.2, 0.40: 1.0, 0.50: 0.85},
}

VARILLAS_EC = {
    "Ø 8 mm": {"area": 0.503, "db": 8.0},
    "Ø 10 mm": {"area": 0.785, "db": 10.0},
    "Ø 12 mm": {"area": 1.131, "db": 12.0},
    "Ø 14 mm": {"area": 1.539, "db": 14.0},
    "Ø 16 mm": {"area": 2.011, "db": 16.0},
    "Ø 18 mm": {"area": 2.545, "db": 18.0},
    "Ø 20 mm": {"area": 3.142, "db": 20.0},
    "Ø 22 mm": {"area": 3.801, "db": 22.0},
    "Ø 25 mm": {"area": 4.909, "db": 25.0},
    "Ø 28 mm": {"area": 6.158, "db": 28.0},
    "Ø 32 mm": {"area": 8.042, "db": 32.0},
}

# ---------------------------------------------------------
# BARRA LATERAL: ENTRADA DE DATOS
# ---------------------------------------------------------
st.sidebar.header("⚙️ Entradas del Proyecto")

tab_geo, tab_suelo, tab_cargas, tab_sismo, tab_acero = st.sidebar.tabs(
    ["📐 Geometría", "🌱 Suelo/NF", "📦 Cargas", "🌋 Sismo", "🦾 Acero"]
)

# 1. GEOMETRÍA
with tab_geo:
    st.subheader("Geometría Principal del Muro (m)")
    H = st.number_input("Altura total H (m)", 1.5, 12.0, 6.0, 0.1)
    hz = st.number_input("Espesor zapata hz (m)", 0.3, 1.5, 0.70, 0.05)
    Bp = st.number_input("Puntera Bp (m)", 0.1, 3.0, 0.70, 0.1)
    Bt = st.number_input("Talón Bt (m)", 0.3, 4.0, 2.20, 0.1)
    ts = st.number_input("Espesor sup. pantalla ts (m)", 0.15, 0.80, 0.30, 0.05)
    ti = st.number_input("Espesor inf. pantalla ti (m)", 0.20, 1.50, 0.60, 0.05)
    gamma_c_kn = st.number_input("Peso específico concreto (kN/m³)", 20.0, 25.0, 23.58, 0.01)

    B = Bp + ti + Bt
    hp = H - hz

    st.markdown("---")
    st.subheader("⚙️ Dentellón Base (Key)")
    tiene_dentellon = st.checkbox("¿Incluir Dentellón contra deslizamiento?")
    dk, tk, x_key = 0.0, 0.0, 0.0
    if tiene_dentellon:
        c_k1, c_k2 = st.columns(2)
        with c_k1:
            dk = st.number_input("Profundidad dk (m)", 0.20, 1.50, 0.50, 0.05)
        with c_k2:
            tk = st.number_input("Ancho dentellón tk (m)", 0.10, 1.50, 0.40, 0.05)

        x_key_def = float(B - tk)
        x_key_min = float(Bp)
        x_key_max = float(B - tk)
        if x_key_max < x_key_min:
            x_key_max = x_key_min

        x_key = st.slider(
            "Posición X de inicio del dentellón (m)",
            x_key_min,
            x_key_max,
            x_key_def,
            0.05,
        )

# 2. SUELO DE RELLENO Y CIMENTACIÓN
with tab_suelo:
    st.subheader("📋 Suelo de Relleno (Detrás del Muro)")
    gamma1_kn = st.number_input("Peso Esp. Relleno γ1 (kN/m³)", 10.0, 25.0, 18.0, 0.1)
    phi1_deg = st.number_input("Ángulo Fricción Relleno φ1 (°)", 10.0, 50.0, 30.0, 0.5)
    c1_kn = st.number_input("Cohesión Relleno c1 (kPa)", 0.0, 100.0, 0.0, 1.0)

    st.markdown("---")
    st.subheader("📋 Suelo de Cimentación (Debajo de la Base)")
    gamma2_kn = st.number_input("Peso Esp. Cimentación γ2 (kN/m³)", 10.0, 25.0, 19.0, 0.1)
    phi2_deg = st.number_input("Ángulo Fricción Cimentación φ2 (°)", 0.0, 50.0, 20.0, 0.5)
    c2_kn = st.number_input("Cohesión Cimentación c2 (kPa)", 0.0, 200.0, 40.0, 1.0)
    q_adm_kpa = st.number_input("Capacidad Admisible q_adm (kPa)", 50.0, 1000.0, 200.0, 10.0)
    Es_mod_kpa = st.number_input("Módulo Elasticidad Es (kPa)", 1000.0, 100000.0, 25000.0, 1000.0)
    nu_s = st.number_input("Coeficiente de Poisson ν", 0.1, 0.5, 0.30, 0.05)

    st.markdown("---")
    st.subheader("💧 Nivel Freático (NF)")
    tiene_nf = st.checkbox("¿Incluir Nivel Freático?")
    znf = float(H)
    if tiene_nf:
        znf = st.number_input("Profundidad NF desde superficie (m)", 0.0, float(H), float(H / 2), 0.5)

gamma_s = gamma1_kn
gamma_c = gamma_c_kn
q_adm = q_adm_kpa
Es_mod = Es_mod_kpa

# 3. CARGAS EXTERNAS
with tab_cargas:
    st.subheader("Sobrecargas")
    tiene_carga = st.checkbox("¿Incluir Carga sobre Relleno?", value=False)
    tipo_carga, q_val, P_val, x_p, dist_a, dist_b = "Ninguna", 0.0, 0.0, 0.0, 0.0, 0.0

    if tiene_carga:
        tipo_carga = st.radio(
            "Tipo de Carga",
            ["Distribuida Infinita", "Distribuida de Ancho Finito (Franja)", "Puntual / Lineal"],
            index=0,
        )
        if tipo_carga == "Distribuida Infinita":
            q_val = st.number_input("Sobrecarga q (kN/m²)", 0.1, 200.0, 10.0, 1.0)
        elif tipo_carga == "Distribuida de Ancho Finito (Franja)":
            q_val = st.number_input("Sobrecarga q (kN/m²)", 0.1, 200.0, 15.0, 1.0)
            dist_a = st.number_input("Distancia inicio 'a' (m)", 0.0, 10.0, 0.5, 0.1)
            dist_b = st.number_input("Distancia fin 'b' (m)", dist_a + 0.1, 15.0, dist_a + 1.5, 0.1)
        elif tipo_carga == "Puntual / Lineal":
            P_val = st.number_input("Carga Lineal P (kN/m)", 0.1, 500.0, 20.0, 1.0)
            x_p = st.number_input("Distancia 'x' desde pared posterior (m)", 0.1, 10.0, 1.0, 0.1)

# 4. SISMICIDAD (NEC-15)
with tab_sismo:
    st.subheader("Parámetros Sísmicos Automáticos (NEC-15)")
    incluir_sismo = st.checkbox("¿Incluir Análisis Sísmico?", value=False)

    if incluir_sismo:
        z_nec = st.selectbox(
            "Zona Sísmica Z (PGA en Roca)",
            [0.15, 0.25, 0.30, 0.35, 0.40, 0.50],
            index=4,
            format_func=lambda x: f"Z = {x:.2f} g",
        )
        tipo_suelo = st.selectbox("Tipo de Perfil de Suelo", list(FA_NEC_2015.keys()), index=3)
        fa_nec = FA_NEC_2015[tipo_suelo][z_nec]
        st.success(f"⚡ **Factor de Sitio $F_a$:** `{fa_nec:.2f}` (NEC-15)")

        kh = (z_nec * fa_nec) / 2.0
        kv = (2.0 / 3.0) * kh
        st.info(f"🤖 **$k_h$:** `{kh:.3f}` | **$k_v$:** `{kv:.3f}`")
    else:
        kh, kv = 0.0, 0.0

# 5. REFUERZO Y MATERIALES (ACI 318-19)
with tab_acero:
    st.subheader("Propiedades Estructurales")
    fc = st.selectbox("Resistencia a compresión f'c (MPa)", [21, 24, 28, 35], index=0)
    fy = st.number_input("Esfuerzo de fluencia fy (MPa)", 280, 500, 420, 10)
    rec_cm = st.number_input("Recubrimiento libre (cm)", 3.0, 10.0, 7.5, 0.5)

    st.markdown("---")
    st.subheader("Selección de Armaduras")
    lista_v = list(VARILLAS_EC.keys())

    c_v1, c_v2 = st.columns(2)
    with c_v1:
        v_pantalla = st.selectbox("Varilla Pantalla (Tracción)", lista_v, index=4)
        v_puntera = st.selectbox("Varilla Puntera (Inferior)", lista_v, index=3)
        v_talon = st.selectbox("Varilla Talón (Superior)", lista_v, index=4)
        v_temp = st.selectbox("Varilla Distribución/Temp.", lista_v, index=1)
    with c_v2:
        s_pantalla = st.number_input("s Pantalla (cm)", 5.0, 30.0, 15.0, 1.0)
        s_puntera = st.number_input("s Puntera (cm)", 5.0, 30.0, 20.0, 1.0)
        s_talon = st.number_input("s Talón (cm)", 5.0, 30.0, 15.0, 1.0)
        s_temp = st.number_input("s Temp. (cm)", 5.0, 30.0, 20.0, 1.0)


# ---------------------------------------------------------
# FUNCIONES AUXILIARES DE CÁLCULO
# ---------------------------------------------------------
def calcular_mononobe_okabe(phi_deg, kh, kv):
    phi = math.radians(phi_deg)
    denom_theta = 1.0 - kv
    if denom_theta <= 0:
        return math.tan(math.radians(45 - phi_deg / 2)) ** 2

    theta = math.atan(kh / denom_theta)
    if phi < theta:
        return math.tan(math.radians(45 - phi_deg / 2)) ** 2

    num = math.cos(phi - theta) ** 2
    den = math.cos(theta) * (1 + math.sqrt((math.sin(phi) * math.sin(phi - theta)) / math.cos(theta))) ** 2
    return num / den


def diseno_flexion_aci318(Mu_knm, b_m, d_m, fc_mpa, fy_mpa, db_mm):
    """Calcula el acero requerido por flexión según ACI 318-19."""
    if d_m <= 0:
        return 0.0, 0.0, 0.0, 0.9, "Error en peralte"

    d_cm = d_m * 100.0
    b_cm = b_m * 100.0
    fc_kpa = fc_mpa * 1000.0
    fy_kpa = fy_mpa * 1000.0

    if fc_mpa <= 28:
        beta1 = 0.85
    elif fc_mpa < 55:
        beta1 = 0.85 - 0.05 * (fc_mpa - 28) / 7.0
        beta1 = max(beta1, 0.65)
    else:
        beta1 = 0.65

    phi = 0.90
    rn = (Mu_knm) / (phi * b_m * (d_m ** 2)) if (d_m > 0 and phi > 0) else 0.0

    if rn > (0.85 * beta1 * fc_kpa * (1 - 0.5 * beta1)):
        return 999.0, 0.0, 0.0, phi, "Falla por compresión (Sección muy pequeña)"

    if rn > 0:
        rho_req = (0.85 * fc_kpa / fy_kpa) * (1.0 - math.sqrt(max(0.0, 1.0 - (2.0 * rn) / (0.85 * fc_kpa))))
    else:
        rho_req = 0.0

    As_req = rho_req * b_cm * d_cm

    As_min_flex = (0.25 * math.sqrt(fc_mpa) / fy_mpa) * b_cm * d_cm
    As_min_flex = max(As_min_flex, (1.4 / fy_mpa) * b_cm * d_cm)
    As_min_temp = 0.0018 * b_cm * (d_m * 100.0 + 7.5)

    As_min = max(As_min_flex, As_min_temp)
    As_diseno = max(As_req, As_min)

    a = (As_diseno * (fy_mpa / 10.0)) / (0.85 * (fc_mpa / 10.0) * b_cm)
    c = a / beta1
    et = ((d_cm - c) / c) * 0.003 if c > 0 else 0.05

    if et < 0.004:
        estado = "Sección no dúctil (εt < 0.004)"
    else:
        estado = "Dúctil (OK)"

    return As_diseno, As_req, As_min, phi, estado


def cortante_concreto_aci318_19(fc_mpa, b_m, d_m, As_colocado_cm2):
    """
    Corte resistente nominal sin refuerzo transversal
    ACI 318-19 (Art 22.5.5.1)
    """
    b_mm = b_m * 1000.0
    d_mm = d_m * 1000.0
    if d_mm <= 0:
        return 0.0

    lambda_s = math.sqrt(2.0 / (1.0 + 0.004 * d_mm))
    lambda_s = min(lambda_s, 1.0)

    rho_w = (As_colocado_cm2) / (b_m * 100.0 * d_m * 100.0)
    rho_w = min(rho_w, 0.015)

    Vc_N = 0.66 * 1.0 * lambda_s * (rho_w ** (1 / 3)) * math.sqrt(fc_mpa) * b_mm * d_mm
    Vc_kN = Vc_N / 1000.0

    phi_v = 0.75
    return phi_v * Vc_kN


def agregar_cota(ax, x1, y1, x2, y2, texto, offset=0.3, es_vertical=False, color="#334155"):
    kw_flechas = dict(arrowstyle="<->", color=color, lw=1.2, mutation_scale=10)
    kw_extension = dict(color=color, linestyle=":", linewidth=0.8, alpha=0.7)

    if es_vertical:
        x_cota = x1 + offset
        ax.annotate("", xy=(x_cota, y1), xytext=(x_cota, y2), arrowprops=kw_flechas)
        ax.plot([x1, x_cota + np.sign(offset) * 0.1], [y1, y1], **kw_extension)
        ax.plot([x2, x_cota + np.sign(offset) * 0.1], [y2, y2], **kw_extension)
        ax.text(x_cota + np.sign(offset) * 0.08, (y1 + y2) / 2, texto,
                color=color, fontsize=9, fontweight="bold", va="center",
                ha="left" if offset > 0 else "right", rotation=90)
    else:
        y_cota = y1 + offset
        ax.annotate("", xy=(x1, y_cota), xytext=(x2, y_cota), arrowprops=kw_flechas)
        ax.plot([x1, x1], [y1, y_cota + np.sign(offset) * 0.1], **kw_extension)
        ax.plot([x2, x2], [y2, y_cota + np.sign(offset) * 0.1], **kw_extension)
        ax.text((x1 + x2) / 2, y_cota + np.sign(offset) * 0.08, texto,
                color=color, fontsize=9, fontweight="bold", ha="center",
                va="bottom" if offset > 0 else "top")


# ---------------------------------------------------------
# FUNCIONES DE GRAFICACIÓN MODIFICADAS Y MEJORADAS
# ---------------------------------------------------------

def dibujar_muro_completo(
        H, hz, Bp, Bt, ti, ts, B, rec_cm, tiene_nf, znf, tipo_carga, q_val, P_val, x_p, dist_a, dist_b, kh, kv,
        tiene_dentellon, dk, tk, x_key
):
    fig, ax = plt.subplots(figsize=(8, 8), dpi=100)
    hp = H - hz

    if tiene_dentellon and dk > 0:
        x_muro = [0, x_key, x_key, x_key + tk, x_key + tk, B, B, Bp + ti, Bp + ts, Bp, Bp, 0]
        y_muro = [0, 0, -dk, -dk, 0, 0, hz, hz, H, H, hz, hz]
    else:
        x_muro = [0, B, B, Bp + ti, Bp + ts, Bp, Bp, 0]
        y_muro = [0, 0, hz, hz, H, H, hz, hz]

    muro = patches.Polygon(list(zip(x_muro, y_muro)), closed=True, lw=2, edgecolor="#1E293B", facecolor="#E2E8F0",
                           zorder=3)
    ax.add_patch(muro)

    ancho_relleno = max(2.5, Bt + max(dist_b, x_p) + 1.0)
    x_fin_relleno = B + ancho_relleno

    ax.fill_between([Bp + ti, Bp + ts, x_fin_relleno], [hz, H, H], [hz, hz, hz], color="#FDE68A", alpha=0.4,
                    hatch="...", label="Relleno Terreno")

    if tiene_nf and znf < H:
        y_nf = max(H - znf, hz)
        ax.axhline(y_nf, color="#0284C7", ls="--", lw=1.5, label=f"N.F. (-{znf:.1f}m)")
        x_nf_pantalla = (Bp + ti) + (ts - ti) * ((y_nf - hz) / hp) if hp > 0 else Bp + ti
        ax.fill_between([x_nf_pantalla, x_fin_relleno], [y_nf, y_nf], [hz, hz], color="#7DD3FC", alpha=0.35)

    if tipo_carga == "Distribuida Infinita":
        ax.annotate(f"q = {q_val:.1f} kN/m²", xy=(Bp + ts + 0.5, H + 0.05), xytext=(Bp + ts + 0.5, H + 0.6),
                    arrowprops=dict(arrowstyle="->", color="#2563EB", lw=1.5), fontweight="bold", color="#2563EB",
                    fontsize=8, ha="center")
    elif tipo_carga == "Distribuida de Ancho Finito (Franja)":
        x_inicio, x_fin = Bp + ts + dist_a, Bp + ts + dist_b
        rect_carga = patches.Rectangle((x_inicio, H), x_fin - x_inicio, 0.3, facecolor="#93C5FD", edgecolor="#1D4ED8",
                                       hatch="///")
        ax.add_patch(rect_carga)
        ax.text((x_inicio + x_fin) / 2, H + 0.4, f"q = {q_val:.1f} kN/m²", color="#1D4ED8", fontsize=8, ha="center",
                fontweight="bold")
    elif tipo_carga == "Puntual / Lineal":
        x_carga = Bp + ts + x_p
        ax.annotate(f"P = {P_val:.1f} kN/m", xy=(x_carga, H), xytext=(x_carga, H + 0.7),
                    arrowprops=dict(arrowstyle="->", color="#DC2626", lw=2.5), fontweight="bold", color="#DC2626",
                    fontsize=8, ha="center")

    # ---------------------------------------------------------
    # UBICACIÓN Y DIBUJO DE CARGAS SÍSMICAS (MODIFICADO)
    # ---------------------------------------------------------
    if kh > 0:
        # Punto exacto de aplicación en el muro (Centro de masa / Centro de presión sísmica)
        y_sis = hz + (hp * 0.5)
        x_sis = Bp + (ti + ts) / 4.0

        # Punto rojo en el muro donde se aplica la carga sísmica
        ax.scatter(x_sis, y_sis, color="red", s=80, zorder=6, edgecolor="black", label="Carga Sísmica")

        # Flecha indicadora de la fuerza sísmica apuntando al punto rojo
        ax.annotate("", xy=(x_sis, y_sis), xytext=(x_sis - 1.2, y_sis),
                    arrowprops=dict(arrowstyle="->", color="#DC2626", lw=2.5), zorder=5)

        # Textos con valores de kh y kv colocados al LADO DERECHO DEL MURO
        x_txt_sismo = B + 0.5
        y_txt_sismo = H * 0.5
        info_sismo_txt = f"**Acción Sísmica**\n$k_h = {kh:.3f}$\n$k_v = {kv:.3f}$"
        ax.text(x_txt_sismo, y_txt_sismo, info_sismo_txt, color="#DC2626", fontweight="bold", fontsize=9,
                ha="left", va="center",
                bbox=dict(boxstyle="round,pad=0.4", facecolor="#FEE2E2", edgecolor="#DC2626", alpha=0.9), zorder=5)

    # ---------------------------------------------------------
    # COTAS DIMENSIONALES BÁSICAS Y COMPLETAS
    # ---------------------------------------------------------
    cota_col = "#0F172A"
    # Anchos superiores e inferiores
    agregar_cota(ax, Bp + ts, H, Bp, H, f"$t_s$={ts:.2f}m", offset=0.4, color=cota_col)
    agregar_cota(ax, Bp, hz, Bp + ti, hz, f"$t_i$={ti:.2f}m", offset=0.3, color=cota_col)
    agregar_cota(ax, 0, 0, Bp, 0, f"$B_p$={Bp:.2f}m", offset=-0.4, color=cota_col)
    agregar_cota(ax, Bp + ti, 0, B, 0, f"$B_t$={Bt:.2f}m", offset=-0.4, color=cota_col)
    agregar_cota(ax, 0, 0, B, 0, f"$B$={B:.2f}m", offset=-1.1, color=cota_col)

    # Alturas
    agregar_cota(ax, 0, 0, 0, hz, f"$h_z$={hz:.2f}m", offset=-0.5, es_vertical=True, color=cota_col)
    agregar_cota(ax, 0, hz, 0, H, f"$h_p$={hp:.2f}m", offset=-0.5, es_vertical=True, color=cota_col)
    agregar_cota(ax, 0, 0, 0, H, f"$H$={H:.2f}m", offset=-1.2, es_vertical=True, color=cota_col)

    # Dentellón
    if tiene_dentellon and dk > 0:
        agregar_cota(ax, x_key, -dk, x_key + tk, -dk, f"$t_k$={tk:.2f}m", offset=-0.3, color=cota_col)
        agregar_cota(ax, x_key, 0, x_key, -dk, f"$d_k$={dk:.2f}m", offset=-0.4, es_vertical=True, color=cota_col)

    ax.set_xlim(-2.0, x_fin_relleno + 1.2)
    ax.set_ylim(-1.2 - dk, H + 1.5)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.legend(loc="upper left", frameon=True, fontsize=8)
    return fig


def dibujar_detallado_acero(
        H, hz, Bp, Bt, ti, ts, B, rec_cm, tiene_dentellon, dk, tk, x_key,
        v_pantalla, s_pantalla, v_puntera, s_puntera, v_talon, s_talon, v_temp, s_temp,
        requiere_doble_pantalla=False
):
    fig, ax = plt.subplots(figsize=(8, 9), dpi=120)
    r = rec_cm / 100.0

    # Contorno del Muro
    if tiene_dentellon and dk > 0:
        x_muro = [0, x_key, x_key, x_key + tk, x_key + tk, B, B, Bp + ti, Bp + ts, Bp, Bp, 0]
        y_muro = [0, 0, -dk, -dk, 0, 0, hz, hz, H, H, hz, hz]
    else:
        x_muro = [0, B, B, Bp + ti, Bp + ts, Bp, Bp, 0]
        y_muro = [0, 0, hz, hz, H, H, hz, hz]

    muro_patch = patches.Polygon(list(zip(x_muro, y_muro)), closed=True, lw=2.0, edgecolor="#1E293B",
                                 facecolor="#F1F5F9", zorder=2)
    ax.add_patch(muro_patch)

    # ---------------------------------------------------------
    # MAPA DE COLORES EN FUNCIÓN DEL DIÁMETRO DE LAS VARILLAS
    # ---------------------------------------------------------
    colores_db = {
        8.0: "#22C55E",   # Verde
        10.0: "#16A34A",  # Verde Oscuro
        12.0: "#0284C7",  # Azul Celeste
        14.0: "#2563EB",  # Azul
        16.0: "#4F46E5",  # Indigo
        18.0: "#9333EA",  # Púrpura
        20.0: "#D97706",  # Naranja
        22.0: "#EA580C",  # Naranja Oscuro
        25.0: "#DC2626",  # Rojo
        28.0: "#B91C1C",  # Rojo Oscuro
        32.0: "#881337",  # Granate
    }

    db_p = VARILLAS_EC[v_pantalla]["db"]
    db_pun = VARILLAS_EC[v_puntera]["db"]
    db_tal = VARILLAS_EC[v_talon]["db"]
    db_tmp = VARILLAS_EC[v_temp]["db"]

    color_p = colores_db.get(db_p, "#B91C1C")
    color_pun = colores_db.get(db_pun, "#2563EB")
    color_tal = colores_db.get(db_tal, "#D97706")
    color_tmp = colores_db.get(db_tmp, "#22C55E")

    # ---------------------------------------------------------
    # DIBUJO DE BARRAS DE ACERO CON LÍNEAS
    # ---------------------------------------------------------

    # 1. Acero Principal Pantalla (Tracción - Cara Posterior)
    x_p_bot = Bp + ti - r
    x_p_top = Bp + ts - r
    ax.plot([x_p_bot, x_p_top], [r, H - r], color=color_p, lw=3.0, zorder=4, label=f"Pantalla Principal ({v_pantalla})")
    # Patilla inferior hacia el talón
    ax.plot([x_p_bot, B - r], [r, r], color=color_p, lw=3.0, zorder=4)

    # 2. Acero Cara Anterior Pantalla (Temperatura o Doble Armado Requerido)
    if requiere_doble_pantalla:
        # Armado de refuerzo estructural completo en la cara anterior
        ax.plot([Bp + r, Bp + r], [r, H - r], color=color_p, lw=3.0, zorder=4)
        # Patilla en puntera
        ax.plot([Bp + r, r], [r, r], color=color_p, lw=3.0, zorder=4)
    else:
        # Acero normal por temperatura/montaje
        ax.plot([Bp + r, Bp + r], [r, H - r], color=color_tmp, lw=2.0, zorder=4, label=f"Distribución/Temp ({v_temp})")

    # 3. Acero Inferior Zapata (Puntera/Piso Zapata)
    ax.plot([r, B - r], [r + 0.02, r + 0.02], color=color_pun, lw=2.5, zorder=4, label=f"Puntera ({v_puntera})")
    # Patillas verticales en extremos
    ax.plot([r, r], [r + 0.02, hz - r], color=color_pun, lw=2.5, zorder=4)
    ax.plot([B - r, B - r], [r + 0.02, hz - r], color=color_pun, lw=2.5, zorder=4)

    # 4. Acero Superior Zapata (Talón)
    ax.plot([r, B - r], [hz - r, hz - r], color=color_tal, lw=2.5, zorder=4, label=f"Talón ({v_talon})")

    # Dentellón (si aplica)
    if tiene_dentellon and dk > 0:
        ax.plot([x_key + r, x_key + r], [0, -dk + r], color=color_pun, lw=2.0, zorder=4)
        ax.plot([x_key + tk - r, x_key + tk - r], [0, -dk + r], color=color_pun, lw=2.0, zorder=4)
        ax.plot([x_key + r, x_key + tk - r], [-dk + r, -dk + r], color=color_pun, lw=2.0, zorder=4)

    # ---------------------------------------------------------
    # PUNTOS DE REFUERZO TRANSVERSAL / DISTRIBUCIÓN
    # ---------------------------------------------------------
    y_pts_p = np.linspace(hz + 0.2, H - 0.2, 8)
    for y_pt in y_pts_p:
        x_pt_trac = (Bp + ti - r) + ((Bp + ts - r) - (Bp + ti - r)) * ((y_pt - r) / (H - 2 * r))
        ax.scatter(x_pt_trac - 0.03, y_pt, color=color_tmp, s=20, zorder=5)
        ax.scatter(Bp + r + 0.03, y_pt, color=color_tmp, s=20, zorder=5)

    x_pts_z = np.linspace(r + 0.2, B - r - 0.2, 8)
    for x_pt in x_pts_z:
        ax.scatter(x_pt, r + 0.05, color=color_tmp, s=20, zorder=5)
        ax.scatter(x_pt, hz - r - 0.05, color=color_tmp, s=20, zorder=5)

    # ---------------------------------------------------------
    # DIRECTRICES Y ETIQUETAS DE ACERO
    # ---------------------------------------------------------
    def box_text(color):
        return dict(color=color, fontsize=8.5, fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.9, edgecolor=color))

    arrow_args = lambda col: dict(arrowstyle="->", color=col, lw=1.2)

    # Etiqueta Pantalla (Tracción)
    y_lbl1 = H * 0.65
    x_pt1 = (Bp + ti - r) + ((Bp + ts - r) - (Bp + ti - r)) * ((y_lbl1 - r) / (H - 2 * r))
    ax.annotate(f"Pantalla (Cara Post.): {v_pantalla} @ {s_pantalla:.0f} cm", xy=(x_pt1, y_lbl1),
                xytext=(x_pt1 + 0.8, y_lbl1), arrowprops=arrow_args(color_p), **box_text(color_p))

    # Etiqueta Cara Anterior
    y_lbl2 = H * 0.40
    if requiere_doble_pantalla:
        txt_ant = f"Pantalla (Cara Ant. Requerida): {v_pantalla} @ {s_pantalla:.0f} cm"
        col_ant = color_p
    else:
        txt_ant = f"Cara Ant. (Temp/Montaje): {v_temp} @ {s_temp:.0f} cm"
        col_ant = color_tmp

    ax.annotate(txt_ant, xy=(Bp + r, y_lbl2),
                xytext=(Bp - 2.2, y_lbl2), arrowprops=arrow_args(col_ant), **box_text(col_ant))

    # Etiqueta Puntera (Inf. Zapata)
    x_lbl3 = Bp * 0.5
    ax.annotate(f"Puntera (Inf): {v_puntera} @ {s_puntera:.0f} cm", xy=(x_lbl3, r + 0.02),
                xytext=(x_lbl3 - 1.2, -0.4), arrowprops=arrow_args(color_pun), **box_text(color_pun))

    # Etiqueta Talón (Sup. Zapata)
    x_lbl4 = B - (Bt * 0.4)
    ax.annotate(f"Talón (Sup): {v_talon} @ {s_talon:.0f} cm", xy=(x_lbl4, hz - r),
                xytext=(x_lbl4 - 0.2, hz + 0.5), arrowprops=arrow_args(color_tal), **box_text(color_tal))

    # ---------------------------------------------------------
    # COTAS DE REFERENCIA Y LEYENDA
    # ---------------------------------------------------------
    cota_col = "#0F172A"
    agregar_cota(ax, 0, 0, 0, H, f"H = {H:.2f} m", offset=-0.8, es_vertical=True, color=cota_col)
    agregar_cota(ax, 0, 0, 0, hz, f"hz = {hz:.2f} m", offset=-0.4, es_vertical=True, color=cota_col)

    ax.set_xlim(-2.5, B + 2.5)
    ax.set_ylim(-0.8 - dk, H + 0.8)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.legend(loc="upper right", frameon=True, fontsize=8)

    return fig


# ---------------------------------------------------------
# PROCESAMIENTO GEOTÉCNICO Y ESTRUCTURAL
# ---------------------------------------------------------
if ti < ts:
    st.error("❌ **Error Geométrico:** El espesor inferior (`ti`) debe ser mayor o igual al superior (`ts`).")
else:
    # 1. EMPUJES Y GEOTECNIA
    Ka = math.tan(math.radians(45 - phi1_deg / 2)) ** 2
    Kp2 = math.tan(math.radians(45 + phi2_deg / 2)) ** 2
    Kae = calcular_mononobe_okabe(phi1_deg, kh, kv) if kh > 0 else Ka
    gamma_w = 9.81

    zc = (2 * c1_kn / (gamma_s * math.sqrt(Ka))) if (c1_kn > 0 and Ka > 0) else 0.0
    zc = min(zc, H * 0.5)
    E_cohesion = 2 * c1_kn * math.sqrt(Ka) * H

    E_q, M_q = 0.0, 0.0
    if tiene_carga:
        if tipo_carga == "Distribuida Infinita":
            E_q = Ka * q_val * H
            M_q = E_q * (H / 2)
        elif tipo_carga == "Puntual / Lineal":
            m = x_p / H
            E_q = (0.55 * P_val) if m <= 0.4 else ((0.64 * P_val) / ((m ** 2) + 1))
            h_act = (0.6 * H) if m <= 0.4 else (H * (1 - (0.4 * m)))
            M_q = E_q * h_act
        elif tipo_carga == "Distribuida de Ancho Finito (Franja)":
            a_rel, b_rel = dist_a / H, dist_b / H
            E_q = q_val * (b_rel - a_rel) * 1.2 * Ka * H
            y_centro = max(0.3 * H, min(H - ((dist_a + dist_b) / 2), 0.7 * H))
            M_q = E_q * y_centro

    if not tiene_nf or znf >= H:
        E_estatico = max(0.0, (0.5 * Ka * gamma_s * (H ** 2)) - E_cohesion)
        M_s = E_estatico * (H / 3)
        E_w, M_w = 0.0, 0.0
    else:
        h1, h2 = znf, H - znf
        gamma_sat = gamma_s + 2.0
        gamma_sub = gamma_sat - gamma_w
        p1 = Ka * gamma_s * h1
        E1, E2, E3 = 0.5 * Ka * gamma_s * (h1 ** 2), p1 * h2, 0.5 * Ka * gamma_sub * (h2 ** 2)
        E_estatico = max(0.0, (E1 + E2 + E3) - E_cohesion)
        M_s = E1 * (h2 + h1 / 3) + E2 * (h2 / 2) + E3 * (h2 / 3)
        E_w = 0.5 * gamma_w * (h2 ** 2)
        M_w = E_w * (h2 / 3)

    E_ae_total = 0.5 * Kae * gamma_s * (1.0 - kv) * (H ** 2)
    Delta_Eae = max(0.0, E_ae_total - (0.5 * Ka * gamma_s * (H ** 2)))
    M_ae = Delta_Eae * (0.6 * H)

    E_horiz_total = E_estatico + E_w + E_q + Delta_Eae
    M_volco_total = M_s + M_w + M_q + M_ae

    factor_peso = (1.0 - kv) if kh > 0 else 1.0
    w1 = ts * hp * gamma_c * factor_peso
    x1 = Bp + (ti - ts) + ts / 2
    w2 = 0.5 * (ti - ts) * hp * gamma_c * factor_peso
    x2 = Bp + (2 / 3) * (ti - ts)
    w3 = B * hz * gamma_c * factor_peso
    x3 = B / 2
    w_key = (tk * dk) * gamma_c * factor_peso if tiene_dentellon else 0.0
    x_key_c = x_key + (tk / 2) if tiene_dentellon else 0.0

    if not tiene_nf or znf >= H:
        w4 = Bt * hp * gamma_s * factor_peso
    else:
        h1_s = znf
        h2_s = hp - znf if hp > znf else 0.0
        w4 = (Bt * h1_s * gamma_s + Bt * h2_s * (gamma_s + 2.0)) * factor_peso
    x4 = B - Bt / 2

    W_concreto = (w1 + w2 + w3 + w_key)
    W_total = W_concreto + w4

    P_ir = kh * (W_concreto / factor_peso if factor_peso > 0 else W_concreto)
    M_ir = P_ir * (H / 2)
    M_volco_total += M_ir

    M_estabilizador = (w1 * x1) + (w2 * x2) + (w3 * x3) + (w4 * x4) + (w_key * x_key_c)

    E_pasivo = 0.0
    if tiene_dentellon and dk > 0:
        E_pasivo = 0.5 * Kp2 * gamma2_kn * ((hz + dk) ** 2 - hz ** 2)

    fs_volco_limite = 1.15 if kh > 0 else 2.0
    fs_desli_limite = 1.15 if kh > 0 else 1.5

    delta_base = (2.0 / 3.0) * math.radians(phi2_deg)
    c_base = (2.0 / 3.0) * c2_kn

    FS_v = M_estabilizador / M_volco_total if M_volco_total > 0 else 999.0
    F_resistente = (W_total * math.tan(delta_base)) + (c_base * B) + E_pasivo
    FS_d = F_resistente / E_horiz_total if E_horiz_total > 0 else 999.0

    x_res = (M_estabilizador - M_volco_total) / W_total if W_total > 0 else 0.0
    ecc = (B / 2) - x_res

    if abs(ecc) <= B / 6:
        q_max = (W_total / B) * (1 + (6 * ecc / B))
        q_min = (W_total / B) * (1 - (6 * ecc / B))
    else:
        q_max = (2 * W_total) / (3 * x_res) if x_res > 0 else 999.0
        q_min = 0.0

    FS_cap = q_adm / q_max if q_max > 0 else 999.0
    q_prom = (q_max + q_min) / 2.0
    asentamiento_mm = ((q_prom * B * (1.0 - nu_s ** 2) * 0.88) / Es_mod) * 1000.0 if Es_mod > 0 else 0.0

    # ---------------------------------------------------------
    # 2. CÁLCULO ESTRUCTURAL CORREGIDO (ACI 318-19)
    # ---------------------------------------------------------

    # A. PANTALLA (BASE DEL VÁSTAGO)
    E_est_p = 0.5 * Ka * gamma_s * (hp ** 2)
    E_q_p = Ka * q_val * hp if tipo_carga == "Distribuida Infinita" else 0.0
    E_ae_p = max(0.0, (0.5 * Kae * gamma_s * (1.0 - kv) * (hp ** 2)) - E_est_p) if kh > 0 else 0.0

    Vu_pantalla_est = 1.6 * (E_est_p + E_q_p)
    Mu_pantalla_est = 1.6 * (E_est_p * (hp / 3) + E_q_p * (hp / 2))

    Vu_pantalla_sis = 1.2 * (E_est_p + E_q_p) + 1.0 * E_ae_p
    Mu_pantalla_sis = 1.2 * (E_est_p * (hp / 3) + E_q_p * (hp / 2)) + 1.0 * (E_ae_p * 0.6 * hp)

    Vu_pantalla = max(Vu_pantalla_est, Vu_pantalla_sis)
    Mu_pantalla = max(Mu_pantalla_est, Mu_pantalla_sis)

    db_p = VARILLAS_EC[v_pantalla]["db"] / 10.0
    d_p = ti - (rec_cm / 100.0) - (db_p / 200.0)

    hp_corte = max(0.1, hp - d_p)
    E_est_p_d = 0.5 * Ka * gamma_s * (hp_corte ** 2)
    Vu_pantalla_crit = 1.6 * E_est_p_d

    As_req_p, As_req_p_raw, As_min_p, phi_p, est_p = diseno_flexion_aci318(
        Mu_pantalla, 1.0, d_p, fc, fy, VARILLAS_EC[v_pantalla]["db"]
    )
    As_col_p = (VARILLAS_EC[v_pantalla]["area"] / s_pantalla) * 100.0
    phi_Vc_p = cortante_concreto_aci318_19(fc, 1.0, d_p, As_col_p)

    # Evaluación de requerimiento de armado en dos capas / caras de la pantalla
    requiere_doble_pantalla = (hp >= 4.5) or (ti >= 0.50) or (est_p == "Falla por compresión (Sección muy pequeña)")

    # B. PUNTERA (TOE - REFUERZO INFERIOR ZAPATA)
    q_puntera_ext = q_max
    q_puntera_int = q_min + (q_max - q_min) * ((B - Bp) / B) if B > 0 else q_max

    W_zap_puntera = 1.2 * (hz * gamma_c)
    q_puntera_ext_u = 1.6 * q_puntera_ext - W_zap_puntera
    q_puntera_int_u = 1.6 * q_puntera_int - W_zap_puntera

    Vu_puntera = 0.5 * (q_puntera_ext_u + q_puntera_int_u) * Bp
    Mu_puntera = (q_puntera_int_u * (Bp ** 2) / 2.0) + ((q_puntera_ext_u - q_puntera_int_u) * (Bp ** 2) / 3.0)
    Mu_puntera = max(0.0, Mu_puntera)

    db_pun = VARILLAS_EC[v_puntera]["db"] / 10.0
    d_pun = hz - (rec_cm / 100.0) - (db_pun / 200.0)

    As_req_pun, _, As_min_pun, _, est_pun = diseno_flexion_aci318(
        Mu_puntera, 1.0, d_pun, fc, fy, VARILLAS_EC[v_puntera]["db"]
    )
    As_col_pun = (VARILLAS_EC[v_puntera]["area"] / s_puntera) * 100.0
    phi_Vc_pun = cortante_concreto_aci318_19(fc, 1.0, d_pun, As_col_pun)

    # C. TALÓN (HEEL - REFUERZO SUPERIOR ZAPATA)
    q_suelo_talon = 1.2 * (hp * gamma_s) + 1.6 * (q_val if tipo_carga == "Distribuida Infinita" else 0.0)
    q_propio_talon = 1.2 * (hz * gamma_c)
    w_descendente_u = q_suelo_talon + q_propio_talon

    q_talon_ext = q_min
    q_talon_int = q_min + (q_max - q_min) * (Bt / B) if B > 0 else q_min

    w_ascendente_u = 0.9 * (0.5 * (q_talon_ext + q_talon_int))
    w_neto_talon_u = w_descendente_u - w_ascendente_u

    Vu_talon = w_neto_talon_u * Bt
    Mu_talon = w_neto_talon_u * (Bt ** 2) / 2.0
    Mu_talon = max(0.0, Mu_talon)

    db_tal = VARILLAS_EC[v_talon]["db"] / 10.0
    d_tal = hz - (rec_cm / 100.0) - (db_tal / 200.0)

    As_req_tal, _, As_min_tal, _, est_tal = diseno_flexion_aci318(
        Mu_talon, 1.0, d_tal, fc, fy, VARILLAS_EC[v_talon]["db"]
    )
    As_col_tal = (VARILLAS_EC[v_talon]["area"] / s_talon) * 100.0
    phi_Vc_tal = cortante_concreto_aci318_19(fc, 1.0, d_tal, As_col_tal)

    # D. ACERO DE DISTRIBUCIÓN / TEMPERATURA
    As_temp_req = 0.0018 * 100.0 * (ti * 100.0)
    As_col_temp = (VARILLAS_EC[v_temp]["area"] / s_temp) * 100.0

# ---------------------------------------------------------
# DESPLIEGUE EN PANTALLA
# ---------------------------------------------------------
pestana_main1, pestana_main2 = st.tabs(["🖼️ Vista General & Geotecnia", "🦾 Diseño de Acero (ACI 318-19)"])

with pestana_main1:
    col_izq, col_der = st.columns([1.1, 0.9], gap="large")

    with col_izq:
        st.subheader("Esquema del Muro y Fuerzas")
        figura = dibujar_muro_completo(
            H, hz, Bp, Bt, ti, ts, B, rec_cm, tiene_nf, znf, tipo_carga, q_val, P_val, x_p, dist_a, dist_b, kh, kv,
            tiene_dentellon, dk, tk, x_key
        )
        st.pyplot(figura, use_container_width=True)

    with col_der:
        st.subheader("Diagnóstico Geotécnico")

        k1, k2 = st.columns(2)
        if FS_v >= fs_volco_limite:
            k1.success(f"**FS Volco:** {FS_v:.2f} ≥ {fs_volco_limite}")
        else:
            k1.error(f"**FS Volco:** {FS_v:.2f} < {fs_volco_limite} (FALLA)")

        if FS_d >= fs_desli_limite:
            k2.success(f"**FS Deslizamiento:** {FS_d:.2f} ≥ {fs_desli_limite}")
        else:
            k2.error(f"**FS Deslizamiento:** {FS_d:.2f} < {fs_desli_limite} (FALLA)")

        st.markdown("---")
        st.write("#### 1. Capacidad Portante y Presiones")
        st.write(f"- Presión Máxima ($q_{{max}}$): **{q_max:.2f} kPa**")
        st.write(f"- Presión Mínima ($q_{{min}}$): **{q_min:.2f} kPa**")
        st.write(f"- Capacidad Admisible ($q_{{adm}}$): **{q_adm:.2f} kPa**")

        if q_max <= q_adm:
            st.success(f"✅ **CUMPLE CAPACIDAD PORTANTE**")
        else:
            st.error(f"❌ **SOBREPASA CAPACIDAD PORTANTE**")

        st.markdown("---")
        st.write("#### 2. Excentricidad y Deformación")
        st.write(f"- Excentricidad ($e$): **{ecc:.3f} m** (Límite $B/6$: `{B / 6:.3f}` m)")
        st.write(f"- Asentamiento Elástico Estimado: **{asentamiento_mm:.2f} mm**")

with pestana_main2:
    st.header("🦾 Verificación Estructural y Armado (ACI 318-19 / NEC-15)")
    st.caption("Resultados ajustados bajo combinación de cargas LRFD y corte por efecto de tamaño (Size Effect).")

    # RESUMEN EJECUTIVO EN MÉTRICAS
    m1, m2, m3, m4 = st.columns(4)
    cumple_p = As_col_p >= As_req_p and phi_Vc_p >= Vu_pantalla_crit
    cumple_pun = As_col_pun >= As_req_pun and phi_Vc_pun >= Vu_puntera
    cumple_tal = As_col_tal >= As_req_tal and phi_Vc_tal >= Vu_talon

    m1.metric("Pantalla", f"{As_col_p:.2f} cm²/m", f"Req: {As_req_p:.2f} cm²/m",
              delta_color="normal" if cumple_p else "inverse")
    m2.metric("Puntera", f"{As_col_pun:.2f} cm²/m", f"Req: {As_req_pun:.2f} cm²/m",
              delta_color="normal" if cumple_pun else "inverse")
    m3.metric("Talón", f"{As_col_tal:.2f} cm²/m", f"Req: {As_req_tal:.2f} cm²/m",
              delta_color="normal" if cumple_tal else "inverse")
    m4.metric("Distribución / Temp.", f"{As_col_temp:.2f} cm²/m", f"Req: {As_temp_req:.2f} cm²/m")

    st.markdown("---")
    col_acero_fig, col_acero_tab = st.columns([1.1, 0.9], gap="large")

    with col_acero_fig:
        st.subheader("Esquema de Detallado del Acero")
        fig_acero = dibujar_detallado_acero(
            H, hz, Bp, Bt, ti, ts, B, rec_cm, tiene_dentellon, dk, tk, x_key,
            v_pantalla, s_pantalla, v_puntera, s_puntera, v_talon, s_talon, v_temp, s_temp,
            requiere_doble_pantalla=requiere_doble_pantalla
        )
        st.pyplot(fig_acero, use_container_width=True)

    with col_acero_tab:
        st.subheader("Tabla de Verificación de Diseño")

        data_estructural = [
            {
                "Elemento": "Pantalla (Base)",
                "Mu (kN·m/m)": f"{Mu_pantalla:.2f}",
                "As Req (cm²/m)": f"{As_req_p:.2f}",
                "As Colocado": f"{v_pantalla} @ {s_pantalla:.0f}cm ({As_col_p:.2f} cm²)",
                "Vu (kN/m)": f"{Vu_pantalla_crit:.2f}",
                "ϕVc (kN/m)": f"{phi_Vc_p:.2f}",
                "Estado Flexión": est_p,
            },
            {
                "Elemento": "Puntera (Zapata)",
                "Mu (kN·m/m)": f"{Mu_puntera:.2f}",
                "As Req (cm²/m)": f"{As_req_pun:.2f}",
                "As Colocado": f"{v_puntera} @ {s_puntera:.0f}cm ({As_col_pun:.2f} cm²)",
                "Vu (kN/m)": f"{Vu_puntera:.2f}",
                "ϕVc (kN/m)": f"{phi_Vc_pun:.2f}",
                "Estado Flexión": est_pun,
            },
            {
                "Elemento": "Talón (Zapata)",
                "Mu (kN·m/m)": f"{Mu_talon:.2f}",
                "As Req (cm²/m)": f"{As_req_tal:.2f}",
                "As Colocado": f"{v_talon} @ {s_talon:.0f}cm ({As_col_tal:.2f} cm²)",
                "Vu (kN/m)": f"{Vu_talon:.2f}",
                "ϕVc (kN/m)": f"{phi_Vc_tal:.2f}",
                "Estado Flexión": est_tal,
            },
            {
                "Elemento": "Distribución/Temp.",
                "Mu (kN·m/m)": "N/A",
                "As Req (cm²/m)": f"{As_temp_req:.2f}",
                "As Colocado": f"{v_temp} @ {s_temp:.0f}cm ({As_col_temp:.2f} cm²)",
                "Vu (kN/m)": "N/A",
                "ϕVc (kN/m)": "N/A",
                "Estado Flexión": "OK (Mínimo)",
            },
        ]

        df_est = pd.DataFrame(data_estructural)
        st.dataframe(df_est, hide_index=True, use_container_width=True)

        if requiere_doble_pantalla:
            st.warning("⚠️ **Atención:** Debido a la altura/geometría del muro, la pantalla requiere **armado de refuerzo automático en ambas caras** (anterior y posterior).")