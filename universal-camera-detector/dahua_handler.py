# universal_camera_detector/dahua_handler.py

import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class DahuaHandler:
    """Handler para câmeras Dahua"""
    
    ENDPOINTS = {
        'device_info': '/cgi-bin/configManager.cgi?action=getConfig&name=DeviceInfo',
        'serial_no': '/cgi-bin/magicBox.cgi?action=getSerialNo',
        'machine_name': '/cgi-bin/magicBox.cgi?action=getMachineName',
        'device_type': '/cgi-bin/magicBox.cgi?action=getDeviceInfo',
        'network_info': '/cgi-bin/configManager.cgi?action=getConfig&name=Network',
        'network_config': '/cgi-bin/configManager.cgi?action=setConfig'
    }

    def detect_camera(self, ip: str, username: str, password: str, protocol: str, port: int, timeout: int) -> Tuple[bool, Dict]:
        """Detecta câmera Dahua usando múltiplos endpoints"""
        detection_endpoints = list(self.ENDPOINTS.values())

        for endpoint in detection_endpoints:
            url = f"{protocol}://{ip}:{port}{endpoint}"

            # Testa Basic Auth primeiro
            try:
                response = requests.get(url, auth=HTTPBasicAuth(username, password), timeout=timeout, verify=False)
                if response.status_code == 200 and "Dahua" in response.text.lower():
                    info = self._collect_dahua_info(ip, username, password, 'basic', protocol, port, timeout)
                    return True, {
                        'brand': 'Dahua',
                        'model': info.get('model', 'Desconhecido'),
                        'serial': info.get('serial', 'Desconhecido'),
                        'version': info.get('version', 'Desconhecido'),
                        'auth_type': 'basic'
                    }
            except Exception as e:
                logger.debug(f"Erro com Basic Auth para Dahua {ip} em {endpoint}: {e}")

            # Se falhar, tenta Digest Auth
            try:
                response = requests.get(url, auth=HTTPDigestAuth(username, password), timeout=timeout, verify=False)
                if response.status_code == 200 and "Dahua" in response.text.lower():
                    info = self._collect_dahua_info(ip, username, password, 'digest', protocol, port, timeout)
                    return True, {
                        'brand': 'Dahua',
                        'model': info.get('model', 'Desconhecido'),
                        'serial': info.get('serial', 'Desconhecido'),
                        'version': info.get('version', 'Desconhecido'),
                        'auth_type': 'digest'
                    }
            except Exception as e:
                logger.debug(f"Erro com Digest Auth para Dahua {ip} em {endpoint}: {e}")

        return False, {}

    def _collect_dahua_info(self, ip: str, username: str, password: str, auth_type: str, protocol: str, port: int, timeout: int) -> Dict:
        """Coleta informações detalhadas de uma câmera Dahua"""
        info = {}
        for key, endpoint in self.ENDPOINTS.items():
            try:
                url = f"{protocol}://{ip}:{port}{endpoint}"
                auth = HTTPBasicAuth(username, password) if auth_type == 'basic' else HTTPDigestAuth(username, password)
                response = requests.get(url, auth=auth, timeout=timeout, verify=False)

                if response.status_code == 200:
                    parsed_info = self._parse_dahua_response(response.text)
                    if key == 'device_info':
                        info.update({
                            'model': parsed_info.get('DeviceType', 'Desconhecido'),
                            'serial': parsed_info.get('sn', 'Desconhecido'),
                            'version': parsed_info.get('SoftwareVersion', 'Desconhecido')
                        })
            except Exception as e:
                logger.debug(f"Erro ao coletar info via {key}: {e}")
        
        return info

    def _parse_dahua_response(self, response_text: str) -> Dict:
        """Parse da resposta Dahua formato key=value"""
        info = {}
        lines = response_text.strip().split('\n')
        for line in lines:
            if '=' in line:
                key, value = line.split('=', 1)
                info[key.strip()] = value.strip()
        return info

    def get_network_info(self, ip: str, username: str, password: str, auth_info: Dict, protocol: str, port: int, timeout: int) -> Dict:
        """Obtém configuração de rede Dahua"""
        url = f"{protocol}://{ip}:{port}{self.ENDPOINTS['network_info']}"
        auth_class = HTTPBasicAuth if auth_info.get('auth_type') == 'basic' else HTTPDigestAuth
        auth = auth_class(username, password)

        try:
            response = requests.get(url, auth=auth, timeout=timeout, verify=False)
            if response.status_code == 200:
                config = self._parse_dahua_response(response.text)
                return {
                    'ip_atual': config.get('table.Network.eth0.IPAddress', ip),
                    'mascara': config.get('table.Network.eth0.SubnetMask', '—'),
                    'gateway': config.get('table.Network.eth0.DefaultGateway', '—'),
                    'dhcp': config.get('table.Network.eth0.DhcpEnable', '—')
                }
        except Exception as e:
            logger.error(f"Erro ao obter config Dahua {ip}: {e}")

        return {'ip_atual': ip, 'mascara': '—', 'gateway': '—', 'dhcp': '—'}

    def apply_network_config(self, ip: str, new_ip: str, mask: str, gateway: str, username: str, password: str, auth_info: Dict, protocol: str, port: int, timeout: int) -> bool:
        """Aplica nova configuração de rede em câmera Dahua"""
        url = f"{protocol}://{ip}:{port}{self.ENDPOINTS['network_config']}"
        auth_class = HTTPBasicAuth if auth_info.get('auth_type') == 'basic' else HTTPDigestAuth
        auth = auth_class(username, password)

        config_params = {
            'table.Network.eth0.IPAddress': new_ip,
            'table.Network.eth0.SubnetMask': mask,
            'table.Network.eth0.DefaultGateway': gateway,
            'table.Network.eth0.DhcpEnable': 'false',
            'table.Network.eth0.DnsServers[0]': '8.8.8.8',
            'table.Network.eth0.DnsServers[1]': '8.8.4.4'
        }

        config_string = '&'.join([f"{key}={value}" for key, value in config_params.items()])
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}

        try:
            response = requests.post(url, auth=auth, data=config_string, headers=headers, timeout=timeout, verify=False)
            return response.status_code == 200 and 'OK' in response.text
        except Exception as e:
            logger.error(f"Erro ao aplicar config Dahua {ip}: {e}")
            return False

    def capture_snapshot(self, ip: str, username: str, password: str, auth_info: Dict, protocol: str, port: int, timeout: int) -> Optional[bytes]:
        """Captura snapshot da câmera Dahua"""
        endpoints = ['/cgi-bin/snapshot.cgi', '/cgi-bin/currentpic.cgi']
        auth_class = HTTPBasicAuth if auth_info.get('auth_type') == 'basic' else HTTPDigestAuth
        auth = auth_class(username, password)

        for endpoint in endpoints:
            try:
                url = f"{protocol}://{ip}:{port}{endpoint}"
                response = requests.get(url, auth=auth, timeout=timeout, verify=False)
                if response.status_code == 200 and response.headers.get('content-type', '').startswith('image/'):
                    return response.content
            except Exception as e:
                logger.debug(f"Erro ao capturar imagem de {ip}: {e}")
                continue
        return None
