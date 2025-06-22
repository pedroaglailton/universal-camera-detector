# universal_camera_detector/detector.py

import concurrent.futures
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

from .hikvision_handler import HikvisionHandler
from .dahua_handler import DahuaHandler


class CameraHandler(ABC):
    """Classe base para handlers de diferentes fabricantes"""
    
    @abstractmethod
    def detect_camera(self, ip: str, username: str, password: str, protocol: str, port: int, timeout: int) -> Tuple[bool, Dict]:
        pass

    @abstractmethod
    def get_network_info(self, ip: str, username: str, password: str, auth_info: Dict, protocol: str, port: int, timeout: int) -> Dict:
        pass

    @abstractmethod
    def apply_network_config(self, ip: str, new_ip: str, mask: str, gateway: str, username: str, password: str, auth_info: Dict, protocol: str, port: int, timeout: int) -> bool:
        pass

    @abstractmethod
    def capture_snapshot(self, ip: str, username: str, password: str, auth_info: Dict, protocol: str, port: int, timeout: int) -> Optional[bytes]:
        pass


class UniversalCameraDetector:
    """Detector universal de câmeras com captura de thumbnails"""
    
    def __init__(self):
        self.handlers = {
            'hikvision': HikvisionHandler(),
            'dahua': DahuaHandler()
        }

    def detect_camera_brand(self, ip: str, username_list: List[str], password_list: List[str], protocol: str, port: int, timeout: int) -> Optional[Dict]:
        """Detecta automaticamente a marca da câmera"""
        for username in username_list:
            for password in password_list:
                # Tenta Dahua primeiro
                success, info = self.handlers['dahua'].detect_camera(ip, username, password, protocol, port, timeout)
                if success:
                    info.update({'username': username, 'password': password})
                    return info
                
                # Tenta Hikvision
                success, info = self.handlers['hikvision'].detect_camera(ip, username, password, protocol, port, timeout)
                if success:
                    info.update({'username': username, 'password': password})
                    return info

        return None

    def get_network_info(self, camera_info: Dict, ip: str, protocol: str, port: int, timeout: int) -> Dict:
        brand = camera_info['brand'].lower()
        if brand in self.handlers:
            return self.handlers[brand].get_network_info(
                ip, camera_info['username'], camera_info['password'], 
                camera_info, protocol, port, timeout
            )
        return {'ip_atual': ip, 'mascara': '—', 'gateway': '—', 'dhcp': '—'}

    def capture_snapshot(self, camera_info: Dict, ip: str, protocol: str, port: int, timeout: int) -> Optional[bytes]:
        brand = camera_info['brand'].lower()
        if brand in self.handlers:
            return self.handlers[brand].capture_snapshot(
                ip, camera_info['username'], camera_info['password'], 
                camera_info, protocol, port, timeout
            )
        return None

    def apply_network_config(self, camera_info: Dict, ip: str, new_ip: str, mask: str, gateway: str, protocol: str, port: int, timeout: int) -> bool:
        brand = camera_info['brand'].lower()
        if brand in self.handlers:
            return self.handlers[brand].apply_network_config(
                ip, new_ip, mask, gateway, camera_info['username'], 
                camera_info['password'], camera_info, protocol, port, timeout
            )
        return False
