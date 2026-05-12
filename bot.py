import base64
import socket
from typing import Tuple

# ──────────────────────────────────────────────
# SlipNet URI Generator (v22 config, 60 fields)
# Based on slipgate v1.6.4 internal/clientcfg/
# ──────────────────────────────────────────────

SERVERS = {
    "germany": {
        "name": "Germany",
        "ssh_host": "deu.hackkcah.xyz",
        "dnstt_domain": "deud.hackkcah.xyz",
        "public_key": "a4cc7c552d8b70553b5676be703858aad620008f47b98a1e8c925f2273dc2875",
    },
    "uk": {
        "name": "UK",
        "ssh_host": "gbr.hackkcah.xyz",
        "dnstt_domain": "gbrd.hackkcah.xyz",
        "public_key": "a4cc7c552d8b70553b5676be703858aad620008f47b98a1e8c925f2273dc2875",
    },
}

# Tunnel type mapping (matches slipgate v1.6.4 TunnelTypeMap)
TUNNEL_TYPES = {
    "dnstt_ssh": "dnstt_ssh",      # → SlipNet tunnel type 17
    "sayedns_ssh": "sayedns_ssh",  # → SlipNet tunnel type ? (noizdns variant)
}


def resolve_ip(hostname: str) -> str:
    """Resolve hostname to IP (slipgate's getServerIP() equivalent)."""
    try:
        return socket.gethostbyname(hostname)
    except socket.gaierror:
        return hostname  # fallback to hostname


def generate_slipnet_uri(
    server_key: str,      # "germany" or "uk"
    ssh_user: str,        # from hackkcah.com user account
    ssh_pass: str,        # from hackkcah.com user account
    tunnel_type: str = "dnstt_ssh",
    profile_name: str = None,
) -> str:
    """
    Generate a full 60-field slipnet:// URI for SlipNet v2.5.3+ (config v22).
    """
    server = SERVERS[server_key]
    ssh_ip = resolve_ip(server["ssh_host"])

    if profile_name is None:
        profile_name = f"{server['name']} {tunnel_type}"
    
    # --- Field assignments (indices 0-59) ---
    fields = [""] * 60

    # 0: version
    fields[0] = "22"
    # 1: tunnel type
    fields[1] = tunnel_type
    # 2: profile name
    fields[2] = profile_name
    # 3: DNSTT domain (nameserver)
    fields[3] = server["dnstt_domain"]
    # 4: resolvers
    fields[4] = "8.8.8.8:53:0"
    # 5: auth mode
    fields[5] = "0"
    # 6: keepalive
    fields[6] = "5000"
    # 7: congestion control
    fields[7] = "bbr"
    # 8: TCP listen port
    fields[8] = "1080"
    # 9: TCP listen host
    fields[9] = "127.0.0.1"
    # 10: GSO enabled
    fields[10] = "0"
    # 11: public key (hex)
    fields[11] = server["public_key"]
    # 12: SOCKS user
    fields[12] = ""
    # 13: SOCKS pass
    fields[13] = ""
    # 14: SSH enabled ("1" for SSH backend)
    fields[14] = "1"
    # 15: SSH user
    fields[15] = ssh_user
    # 16: SSH pass
    fields[16] = ssh_pass
    # 17: SSH port
    fields[17] = "22"
    # 18: Forward DNS through SSH (deprecated)
    fields[18] = "0"
    # 19: SSH host (server IP)
    fields[19] = ssh_ip
    # 20: Use server DNS (deprecated)
    fields[20] = "0"
    # 21: DoH URL
    fields[21] = ""
    # 22: DNS transport
    fields[22] = "udp"
    # 23: SSH auth type
    fields[23] = "password"
    # 24: SSH private key (base64)
    fields[24] = ""
    # 25: SSH key passphrase (base64)
    fields[25] = ""
    # 26: Tor bridge lines (base64)
    fields[26] = ""
    # 27: DNSTT authoritative
    fields[27] = "0"
    # 28: NaiveProxy port
    fields[28] = "0"
    # 29: NaiveProxy user
    fields[29] = ""
    # 30: NaiveProxy pass
    fields[30] = ""
    # 31: Is locked
    fields[31] = "0"
    # 32: Lock password hash
    fields[32] = ""
    # 33: Expiration date
    fields[33] = "0"
    # 34: Allow sharing
    fields[34] = "0"
    # 35: Bound device ID
    fields[35] = ""
    # 36: Resolvers hidden
    fields[36] = "0"
    # 37: Hidden resolvers
    fields[37] = ""
    # 38: NoizDNS stealth
    fields[38] = "0"
    # 39: DNS payload size
    fields[39] = "0"
    # 40: SOCKS5 server port
    fields[40] = "1080"
    # 41: VayDNS enabled
    fields[41] = "0"
    # 42: VayDNS listen port
    fields[42] = "0"
    # 43: VayDNS listen address
    fields[43] = "0"
    # 44: VayDNS timeout
    fields[44] = "0"
    # 45: VayDNS dest address
    fields[45] = "0"
    # 46: VayDNS dest port
    fields[46] = "0"
    # 47: VayDNS hellos
    fields[47] = "0"
    # 48: VayDNS key
    fields[48] = "0"
    # 49: VayDNS stage1 address
    fields[49] = "0"
    # 50: SSH over TLS enabled
    fields[50] = "0"
    # 51: SSH TLS SNI
    fields[51] = ""
    # 52: SSH TLS proxy host
    fields[52] = ""
    # 53: SSH TLS proxy port
    fields[53] = ""
    # 54: SSH TLS insecure
    fields[54] = ""
    # 55: SSH over WS enabled
    fields[55] = "0"
    # 56: SSH WS path
    fields[56] = "/"
    # 57: SSH WS use TLS
    fields[57] = "1"
    # 58: SSH WS custom host
    fields[58] = ""
    # 59: SSH payload (base64)
    fields[59] = ""

    # --- Encode: pipe-join → base64 (StdEncoding with padding) ---
    pipe_data = "|".join(fields)
    encoded = base64.b64encode(pipe_data.encode()).decode()

    return f"slipnet://{encoded}"


# ──────────────────────────────────────────────
# Example usage
# ──────────────────────────────────────────────
if __name__ == "__main__":
    # Replace with actual SSH credentials from hackkcah.com
    ssh_user = "your_username"
    ssh_pass = "your_password"

    # Generate Germany config
    uri_de = generate_slipnet_uri("germany", ssh_user, ssh_pass)
    print(f"Germany: {uri_de}")

    # Generate UK config
    uri_uk = generate_slipnet_uri("uk", ssh_user, ssh_pass)
    print(f"UK: {uri_uk}")

    # Test decode
    raw = uri_uk.replace("slipnet://", "")
    decoded = base64.b64decode(raw).decode()
    parts = decoded.split("|")
    print(f"\nFields: {len(parts)}")
    print(f"Version: {parts[0]}")
    print(f"Type: {parts[1]}")
    print(f"SSH Host: {parts[19]}")
    print(f"Domain: {parts[3]}")
