# universal_camera_detector/utils.py

import ipaddress
from typing import List

def is_valid_ip(ip_str: str) -> bool:
    """Valida se uma string é um IP válido"""
    try:
        ipaddress.ip_address(ip_str.strip())
        return True
    except ValueError:
        return False

def parse_ip_file(txt_content: str) -> List[str]:
    """Lê IPs de um arquivo TXT (um por linha)"""
    lines = txt_content.splitlines()
    ip_list = []

    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        ip = line.split(',')[0].strip()
        if is_valid_ip(ip):
            ip_list.append(ip)
        else:
            print(f"Linha {line_num}: IP inválido ignorado - {ip}")
    return ip_list
