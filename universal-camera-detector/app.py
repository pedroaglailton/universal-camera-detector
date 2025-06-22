# app.py

import streamlit as st
from universal_camera_detector.detector import UniversalCameraDetector
from universal_camera_detector.exporters import export_to_excel_with_images, export_to_csv_with_base64
import pandas as pd
import io
from datetime import datetime

st.set_page_config(page_title="🎥 Detector de Câmeras", layout="wide")
st.title("🎥 Detector Universal de Câmeras com Thumbnails")

# Sidebar
st.sidebar.header("⚙️ Configurações")
username_input = st.sidebar.text_input("Usuários", value="admin,user,root")
password_input = st.sidebar.text_input("Senhas", value="admin,admin123,password")
protocol = st.sidebar.selectbox("Protocolo", ["http", "https"])
port = st.sidebar.number_input("Porta", min_value=1, max_value=65535, value=80)
timeout = st.sidebar.slider("Timeout", 1, 30, 10)
max_workers = st.sidebar.slider("Threads", 1, 20, 10)

ip_file = st.sidebar.file_uploader("Upload de IPs (.txt)", type=["txt"])

if ip_file:
    content = ip_file.read().decode("utf-8")
    ip_list = parse_ip_file(content)
    if ip_list:
        st.success(f"✅ {len(ip_list)} IPs carregados")
        if st.button("🚀 Iniciar Detecção"):
            username_list = [u.strip() for u in username_input.split(',') if u.strip()]
            password_list = [p.strip() for p in password_input.split(',') if p.strip()]

            detector = UniversalCameraDetector()
            discovered = []

            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_ip = {
                    executor.submit(detector.detect_camera_brand, ip, username_list, password_list, protocol, port, timeout): ip
                    for ip in ip_list
                }

                for future in concurrent.futures.as_completed(future_to_ip):
                    ip = future_to_ip[future]
                    try:
                        result = future.result()
                        if result:
                            net_info = detector.get_network_info(result, ip, protocol, port, timeout)
                            result.update(net_info)
                            result["Status"] = "✅ Online"
                        else:
                            result = {
                                "IP": ip,
                                "Marca": "❌ Offline",
                                "Modelo": "—",
                                "Serial": "—",
                                "IP Atual": "—",
                                "Máscara": "—",
                                "Gateway": "—",
                                "DHCP": "—",
                                "Status": "❌ Offline"
                            }
                        discovered.append(result)
                    except Exception as e:
                        discovered.append({
                            "IP": ip,
                            "Marca": "⚠️ Erro",
                            "Modelo": "—",
                            "Serial": "—",
                            "IP Atual": "—",
                            "Máscara": "—",
                            "Gateway": "—",
                            "DHCP": "—",
                            "Status": "⚠️ Erro"
                        })

            st.session_state['discovered'] = discovered
    else:
        st.error("❌ Nenhum IP válido encontrado.")

if 'discovered' in st.session_state:
    st.markdown("### 📋 Resultados")
    df = pd.DataFrame(st.session_state['discovered'])
    st.dataframe(df)

    col1, col2 = st.columns(2)
    with col1:
        csv_data = df.to_csv(index=False).encode("utf-8")
        st.download_button("📄 Baixar CSV", csv_data, "cameras.csv", "text/csv")

    with col2:
        try:
            excel_data = export_to_excel_with_images(st.session_state['discovered'], "relatorio.xlsx")
            st.download_button("📊 Baixar Excel", excel_data, "cameras.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        except Exception as e:
            st.warning("⚠️ Excel não disponível. Instale openpyxl.")
