import telnetlib
import time
import yaml
import sys

# Port mapping for switches/VPCs
port = {
    21: 32789, 22: 32790, 23: 32791, 24: 32792, 25: 32793,
    26: 32794, 27: 32795, 28: 32796, 29: 32797, 30: 32798,
    31: 32799, 32: 32800, 33: 32801, 34: 32802, 35: 32803
}

# Load YAML file
with open("access_port.yaml", "r") as f:
    switchports = yaml.safe_load(f)

access_switch = switchports["access"]
trunk_ports = switchports["trunk"]

# Change this to your EVE-NG host IP
HOST = "127.0.0.1"

def bring_cli(id, tl, timeout):
    """Wait until CLI prompt appears"""
    end_time = time.time() + timeout
    print(f"[{id}] Waiting for CLI prompt...")

    while time.time() < end_time:
        output_lines = tl.read_very_eager().decode("ascii").strip().splitlines()
        output = output_lines[-1] if output_lines else ""
        if ">" in output:
            if not tl.read_very_eager().decode("ascii"):
                print(f"[{id}] CLI prompt detected.")
                return True
        tl.write(b"\r\n")
        time.sleep(3)
    
    print(f"[{id}] ERROR: CLI prompt not found within timeout.")
    return False


def switch_config(tl, id):
    """Configure switch ports"""

    def send_command(command):
        print(f"[{id}] >> {command}")
        tl.write(f"{command}\r\n".encode('ascii'))
        time.sleep(2)

    def access_port_config(inf, vlan):
        print(f"[{id}] Configuring access port e0/{inf} for VLAN {vlan}")
        send_command(f"interface e0/{inf}")
        send_command("switchport mode access")
        send_command(f"switchport access vlan {vlan}")
        send_command("exit")

    def trunk_port_config(inf):
        print(f"[{id}] Configuring trunk port e0/{inf}")
        send_command(f"interface e0/{inf}")
        send_command("switchport trunk encapsulation dot1q")
        send_command("switchport mode trunk")
        send_command("switchport trunk allowed vlan 10,20,30")
        send_command("exit")

    id_str = str(id)

    if id_str in access_switch:
        for inf, vlan in access_switch[id_str].items():
            access_port_config(inf, vlan)
    else:
        print(f"[{id}] No access ports configured.")

    if id_str in trunk_ports:
        for inf in trunk_ports[id_str]:
            trunk_port_config(inf)
    else:
        print(f"[{id}] No trunk ports configured.")


def lan_config(id, host):
    """Connect and configure a switch or VPC"""
    id = str(id)
    print(f"\n==> Connecting to device ID {id} on port {port[int(id)]}...")

    try:
        tl = telnetlib.Telnet(host, port[int(id)])
    except Exception as e:
        print(f"[{id}] ERROR: Failed to connect - {e}")
        return

    if not bring_cli(id, tl, 30):
        tl.close()
        return

    if 21 <= int(id) <= 27:
        print(f"[{id}] Identified as Switch. Starting configuration.")
        switch_config(tl, id)
    else:
        print(f"[{id}] Identified as VPC. Sending DHCP request.")
        tl.write(b"dhcp\r\n")
        time.sleep(2)

    print(f"[{id}] Configuration completed.\n")
    tl.close()


# Run config for all devices
for id in range(21, 36):
    lan_config(id, HOST)
