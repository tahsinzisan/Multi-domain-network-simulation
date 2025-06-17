import telnetlib
import time
import yaml
import sys

try:
    with open("r.yaml", "r") as f:
        topology = yaml.safe_load(f)
except Exception as e:
    print(f"[ERROR] Failed to load r.yaml: {e}")
    sys.exit(1)

def opencli(tl, id, timeout):
    try:
        end_time = time.time() + timeout
        while time.time() < end_time:
            output_lines = tl.read_very_eager().decode("ascii").strip().splitlines()
            output = output_lines[-1] if output_lines else ""
            if "initial configuration dialog" in output.lower():
                tl.write(b"no\r\n")
                time.sleep(1)
                continue
            if ">" in output or "#" in output:
                return True
            tl.write(b"\r\n")
            time.sleep(1)
        return False
    except Exception as e:
        print(f"[ERROR] CLI readiness check failed on router {id}: {e}")
        return False



def conf(id, host):
    try:
        port = topology[id]["port"]
        tl = telnetlib.Telnet(host, port, timeout=10)
    except Exception as e:
        print(f"[ERROR] Telnet connection failed for router {id} at {host}:{port} - {e}")
        return

    def ipassign(id, inf):
        try:
            nei = topology[id][inf]["nei"]
            subnet = int(nei) + int(id)
            address = f"192.168.{subnet}.{id}"
            netmask = "255.255.255.0"
            tl.write(f"interface f{inf}/0\r\n".encode('ascii'))
            time.sleep(1)
            tl.write(f"ip address {address} {netmask}\r\n".encode('ascii'))
            time.sleep(1)
            tl.write(b"no shut\r\n")
            time.sleep(1)
            tl.write(b"exit\r\n")
            time.sleep(1)
        except Exception as e:
            print(f"[ERROR] IP assignment failed on router {id}, interface {inf}: {e}")

    def loopback_assign(id):
        try:
            address = f"10.10.{id}.{id}"
            netmask = "255.255.255.0"
            tl.write(b"interface loopback0\r\n")
            time.sleep(1)
            tl.write(f"ip address {address} {netmask}\r\n".encode('ascii'))
            time.sleep(1)
            tl.write(b"no shut\r\n")
            time.sleep(1)
            tl.write(b"exit\r\n")
            time.sleep(1)
        except Exception as e:
            print(f"[ERROR] Loopback assignment failed on router {id}: {e}")

    def ospf(id, inf, loopback):
        try:
            nei = "0" if loopback else topology[id][inf]["nei"]
            area = "0" if loopback else topology[id][inf]["area"]
            subnet = int(nei) + int(id)
            address = f"10.10.{id}.0" if loopback else f"192.168.{subnet}.0"
            wildmask = "0.0.0.255"
            tl.write(b"router ospf 1\r\n")
            time.sleep(1)
            tl.write(f"network {address} {wildmask} area {area}\r\n".encode('ascii'))
            time.sleep(1)
        except Exception as e:
            print(f"[ERROR] OSPF configuration failed on router {id}, interface {inf}: {e}")

    try:
        if not opencli(tl, id, 60):
            print(f"[ERROR] CLI not ready on router {id}")
            return

        tl.write(b"enable\r\n")
        time.sleep(0.5)
        tl.write(b"configure terminal\r\n")
        time.sleep(0.5)

        loopback_assign(id)
        ospf(id, "loopback0", True)

        inf_list = []
        for key in topology[id]:
            if key in ["port", "asn"]:
                continue
            inf_list.append(key)
            ipassign(id, key)
            ospf(id, key, False)

        tl.write(b"end\r\n")
        tl.write(b"write memory\r\n")
        tl.write(b"exit\r\n")
        print(f"[OK] Successfully configured router {id}")

    except Exception as e:
        print(f"[ERROR] General failure on router {id}: {e}")
    finally:
        try:
            tl.close()
        except:
            pass


def as_100(tl, id, afi):

    def bgp_nei(id, nei_id):
        if id==nei_id: return
        address = f"10.10.{nei_id}.{nei_id}"
        if not afi:
            tl.write(f"neighbor {address} remote-as 100\r\n".encode('ascii'))
            time.sleep(2)
            return
        
        if id == "63":
            tl.write(f"neighbor {address} route-reflector-client\r\n".encode('ascii'))
        else:
            tl.write(f"neighbor {address} activate\r\n".encode('ascii'))
        time.sleep(2)



    def nei_search():
        for nei_id in topology.keys():
            if topology[nei_id]["asn"]=="100":
                bgp_nei(id, nei_id)

    if id == "63":
        nei_search()
    else:
        bgp_nei(id, "63")


def bgp_conf(id, host):    

    def nei_search(asn, afi, tl):
        for nei_id in topology.keys():
            temp_as = topology[nei_id]["asn"]
            if temp_as == asn:
                bgp_nei(id, nei_id, temp_as, afi, tl)
        for inf in topology[id].keys(): # To configure neighbor
            if inf == "port" or inf == "asn":
                continue
            nei_id = topology[id][inf]["nei"]        
            if nei_id not in topology or topology[nei_id]["asn"]==asn:
                continue
            bgp_nei(id, nei_id, topology[nei_id]["asn"], afi, tl)
    

    def bgp_nei(id, nei_id, nei_asn, afi, tl):
        if id==nei_id: return
        nei_address = f"10.10.{nei_id}.{nei_id}" if nei_asn==topology[id]["asn"] else f"192.168.{str(int(id)+int(nei_id))}.{nei_id}"
        if not afi:
            tl.write(f"neighbor {nei_address} remote-as {nei_asn}\r\n".encode('ascii'))
            if nei_asn==topology[id]["asn"]:
                time.sleep(2)
                tl.write(f"neighbor {nei_address} update-source Loopback0\r\n".encode('ascii'))
        else:
            tl.write(f"neighbor {nei_address} activate\r\n".encode('ascii'))
        time.sleep(2)



    
    port = topology[id]["port"]
    tl = telnetlib.Telnet(host, port)

    if not opencli(tl, id, 90):
        if not opencli(tl, id, 30):
            return

    asn = topology[id]["asn"]
    tl.write(f"router bgp {asn}\r\n".encode('ascii'))
    time.sleep(2)
    if asn == "100":
        as_100(tl, id, False)
    else:
        nei_search(asn, False, tl)
    
    tl.write(b"address-family ipv4\r\n")
    time.sleep(2)
    if asn == "100":
        as_100(tl, id, True)
    else:
        nei_search(asn, True, tl)
    
    tl.write(b"exit-address-family\r\n")
    time.sleep(2)
    tl.write(b"end\r\n")
    time.sleep(2)
    tl.write(b"write memory\r\n")
    time.sleep(2)
    tl.write(b"exit\r\n")

    tl.close()
    



HOST = "192.168.0.12"

for id in topology:
    conf(id, HOST)
for id in topology:
    bgp_conf(id, HOST)