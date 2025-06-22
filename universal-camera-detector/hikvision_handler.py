# universal_camera_detector/hikvision_handler.py

import requests
from requests.auth import HTTPDigestAuth
import xml.etree.ElementTree as ET
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class HikvisionHandler:
    """Handler para câmeras Hikvision"""

    NAMESPACES = {
        'hikvision_v20': {'ns': 'http://www.hikvision.com/ver20/XMLSchema'},
        'hikvision_v10': {'ns': 'http://www.hikvision.com/ver10/XMLSchema'},
        'isapi_v20': {'ns': 'http://www.isapi.org/ver20/XMLSchema'}
    }

    def detect_camera(self, ip: str, username: str, password: str, protocol: str, port: int, timeout: int) -> (bool, Dict):
        """Detecta câmera Hikvision"""
        url = f"{protocol}://{ip}:{port}/ISAPI/System/deviceInfo"
        auth = HTTPDigestAuth(username, password)

        try:
            response = requests.get(url, auth=auth, timeout=timeout, verify=False)
            if response.status_code == 200:
                try:
                    xml = ET.fromstring(response.content)
                    for ns_name, namespace in self.NAMESPACES.items():
                        model_elem = xml.find('.//model', namespaces=namespace)
                        serial_elem = xml.find('.//serialNumber', namespaces=namespace)
                        if model_elem is not None:
                            return True, {
                                'brand': 'Hikvision',
                                'model': model_elem.text or 'Desconhecido',
                                'serial': serial_elem.text or 'Desconhecido',
                                'namespace': namespace,
                                'auth_type': 'digest'
                            }
                    return True, {
                        'brand': 'Hikvision',
                        'model': 'Modelo Desconhecido',
                        'serial': 'Desconhecido',
                        'namespace': self.NAMESPACES['hikvision_v20'],
                        'auth_type': 'digest'
                    }
                except Exception as e:
                    logger.debug(f"Erro ao parsear XML de {ip}: {e}")
        except Exception as e:
            logger.debug(f"Erro ao detectar Hikvision {ip}: {e}")

        return False, {}

    def get_network_info(self, ip: str, username: str, password: str, auth_info: Dict, protocol: str, port: int, timeout: int) -> Dict:
        """Obtém configuração de rede Hikvision"""
        url = f"{protocol}://{ip}:{port}/ISAPI/System/Network/interfaces/1/ipAddress"
        auth = HTTPDigestAuth(username, password)

        try:
            response = requests.get(url, auth=auth, timeout=timeout, verify=False)
            if response.status_code == 200:
                xml = ET.fromstring(response.content)
                namespace = auth_info.get('namespace', self.NAMESPACES['hikvision_v20'])

                ip_atual = xml.find('.//ipAddress', namespaces=namespace)
                mascara = xml.find('.//subnetMask', namespaces=namespace)
                gateway_elem = xml.find('.//DefaultGateway/ipAddress', namespaces=namespace)

                return {
                    'ip_atual': ip_atual.text if ip_atual is not None else ip,
                    'mascara': mascara.text if mascara is not None else '—',
                    'gateway': gateway_elem.text if gateway_elem is not None else '—',
                    'dhcp': '—'
                }
        except Exception as e:
            logger.error(f"Erro ao obter config Hikvision {ip}: {e}")

        return {'ip_atual': ip, 'mascara': '—', 'gateway': '—', 'dhcp': '—'}

    def apply_network_config(self, ip: str, new_ip: str, mask: str, gateway: str, username: str, password: str, auth_info: Dict, protocol: str, port: int, timeout: int) -> bool:
        """Aplica nova configuração de rede em câmera Hikvision"""
        url = f"{protocol}://{ip}:{port}/ISAPI/System/Network/interfaces/1/ipAddress"
        headers = {'Content-Type': 'application/xml'}
        auth = HTTPDigestAuth(username, password)

        xml_data = f"""<?xml version="1.0" encoding="UTF-8"?>
<IPAddress version="2.0" xmlns="http://www.hikvision.com/ver20/XMLSchema">
    <ipVersion>dual</ipVersion>
    <addressingType>static</addressingType>
    <ipAddress>{new_ip}</ipAddress>
    <subnetMask>{mask}</subnetMask>
    <ipv6Address>::</ipv6Address>
    <bitMask>0</bitMask>
    <DefaultGateway>
        <ipAddress>{gateway}</ipAddress>
        <ipv6Address>::</ipv6Address>
    </DefaultGateway>
    <PrimaryDNS><ipAddress>8.8.8.8</ipAddress></PrimaryDNS>
    <SecondaryDNS><ipAddress>8.8.4.4</ipAddress></SecondaryDNS>
</IPAddress>"""

        try:
            response = requests.put(url, auth=auth, data=xml_data, headers=headers, timeout=timeout, verify=False)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Erro ao configurar {ip}: {e}")
            return False

    def capture_snapshot(self, ip: str, username: str, password: str, auth_info: Dict, protocol: str, port: int, timeout: int) -> Optional[bytes]:
        """Captura snapshot da câmera Hikvision"""
        endpoints = ['/ISAPI/Streaming/channels/1/picture', '/cgi-bin/snapshot.cgi']
        auth = HTTPDigestAuth(username, password)

        for endpoint in endpoints:
            try:
                url = f"{protocol}://{ip}:{port}{endpoint}"
                response = requests.get(url, auth=auth, timeout=timeout, verify=False)
                if response.status_code == 200 and response.headers.get('content-type', '').startswith('image/'):
                    return response.content
            except Exception as e:
                logger.debug(f"Erro no endpoint {endpoint} para {ip}: {e}")
        return None
