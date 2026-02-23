import streamlit as st
import requests

API_URL = "https://pdojme9r9l.execute-api.us-east-1.amazonaws.com/default/funcion-reconocer"

st.set_page_config(page_title="Lector de Placas Ecuador", layout="wide", page_icon="🚗")

st.markdown("""
    <style>
        .titulo { text-align: center; font-size: 2.5rem; font-weight: 800; margin-bottom: 0.2rem; }
        .subtitulo { text-align: center; color: #888; font-size: 1rem; margin-bottom: 2rem; }
        .card {
            background: #1e1e2e;
            border-radius: 16px;
            padding: 1.4rem;
            margin-bottom: 1rem;
            border: 1px solid #2e2e3e;
        }
        .placa-badge {
            display: inline-block;
            background: #f5c518;
            color: #111;
            border-radius: 8px;
            padding: 0.5rem 1.4rem;
            font-weight: 900;
            font-size: 1.6rem;
            letter-spacing: 3px;
            font-family: monospace;
            border: 2px solid #333;
        }
        .confianza { color: #aaa; font-size: 0.9rem; margin-top: 0.6rem; }
        .error-box {
            background: #2e1e1e;
            border: 1px solid #ff4444;
            border-radius: 12px;
            padding: 1rem;
            color: #ff8888;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="titulo">🚗 Lector de Placas Ecuador</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitulo">Sube una foto del vehículo y detectamos la placa automáticamente</div>', unsafe_allow_html=True)

if "historial" not in st.session_state:
    st.session_state.historial = []

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown("#### 📤 Subir imagen del vehículo")
    uploaded_file = st.file_uploader("", type=["jpg", "jpeg", "png"])

    if uploaded_file:
        st.image(uploaded_file, caption="Vista previa", use_container_width=True)
        image_bytes = uploaded_file.read()

        if st.button("🔍 Detectar placa", use_container_width=True):
            try:
                with st.spinner("Analizando imagen..."):
                    response = requests.post(
                        API_URL,
                        data=image_bytes,
                        headers={"Content-Type": "application/octet-stream"}
                    )
                    data = response.json()

                if response.status_code == 200:
                    st.session_state.historial.append({
                        "url": data["image_url"],
                        "placa": data["placa"],
                        "confianza": data["confianza"],
                        "todas": data.get("todas_las_placas", [])
                    })

                    ultimo = st.session_state.historial[-1]
                    st.success("✅ Placa detectada correctamente")
                    st.markdown(f"""
                        <div class="card">
                            <div style="margin-bottom:0.5rem; color:#aaa; font-size:0.85rem;">PLACA DETECTADA</div>
                            <div class="placa-badge">🇪🇨 {ultimo['placa']}</div>
                            <div class="confianza">Confianza: {ultimo['confianza']}%</div>
                        </div>
                    """, unsafe_allow_html=True)

                    # Si detectó múltiples placas, mostrarlas
                    if len(ultimo["todas"]) > 1:
                        with st.expander("Ver todas las detecciones"):
                            for p in ultimo["todas"]:
                                st.markdown(f"- `{p['placa']}` — {p['confianza']}% confianza")

                else:
                    error_msg = data.get("error", "Error desconocido")
                    textos = data.get("textos_detectados", [])
                    st.markdown(f"""
                        <div class="error-box">
                            ❌ {error_msg}
                        </div>
                    """, unsafe_allow_html=True)

                    if textos:
                        with st.expander("📝 Textos detectados en la imagen"):
                            for t in textos:
                                st.markdown(f"- `{t}`")

            except Exception as e:
                st.error(f"❌ Error de conexión: {str(e)}")

with col2:
    st.markdown("#### 🕓 Historial de placas")

    if not st.session_state.historial:
        st.markdown("<div style='color:#666; margin-top:1rem;'>Aún no hay placas detectadas.</div>", unsafe_allow_html=True)
    else:
        for i, item in enumerate(reversed(st.session_state.historial), 1):
            num = len(st.session_state.historial) - i + 1
            with st.container():
                st.markdown(f"""
                    <div class="card">
                        <div style="font-weight:600; margin-bottom:0.5rem;">Detección #{num}</div>
                        <div class="placa-badge">🇪🇨 {item['placa']}</div>
                        <div class="confianza">Confianza: {item['confianza']}%</div>
                    </div>
                """, unsafe_allow_html=True)
                st.image(item["url"], use_container_width=True)
                st.markdown(f"[🔗 Ver imagen completa]({item['url']})")
                st.markdown("---")