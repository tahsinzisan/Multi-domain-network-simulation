# Multi-Homed, Multi-Domain Network Simulation

## Quick Overview

This is a **network simulation project** built using **EVE-NG Community Edition**, simulating **four Autonomous Systems (AS100, AS200, AS300, AS400)** with **Cisco C7200 Dynamips routers**.

- **AS100** serves as the **core enterprise AS**.
- A **3-tier LAN topology** is deployed within AS100 using **Cisco IOL Layer 2 and Layer 3 switch images**.

---

## ⚙️ Automation

To eliminate repetitive CLI tasks, a **Python-based automation tool** was developed using the `telnetlib` module. It establishes **Telnet sessions** to routers and switches and automates the following configurations:

### Automated Configuration

- **Interface configuration (Layer 3)**
- **IP address assignment**, including **subinterfaces for ROAS**
- **OSPF configuration**
  - Neighbor formation
  - Area configuration
- **BGP configuration**
  - Neighbor establishment
  - Address-family (IPv4 unicast)
  - Route Reflector setup
- **Layer 2 switch configuration**
  - VLAN access port setup
  - VLAN trunk port setup with **802.1Q tagging**

### Manually Configured

- **DHCP relay** configuration
- **DHCP server provisioning**
- **VLSM-based IP planning**
- **BGP prefix advertisements**
- **BGP traffic engineering and policy control**

---

## BGP Architecture

- Four ASes: **AS100, AS200, AS300, AS400**
- **AS100** uses a **Route Reflector (RR)** architecture.
- **AS200, AS300, and AS400** use **full mesh iBGP**.
- **AS100** peers upstream with **AS200 and AS300**.

#### Prefix Exchange

- **AS100** receives `192.168.4.0/24` (from AS400) via AS200 and AS300.
- **AS400** receives `192.168.1.0/24` (from AS100) via AS200 and AS300.

### BGP Traffic Engineering

- **AS-path prepending** on **AS300 eBGP speaker** to make **AS200** the preferred path for reaching `192.168.4.0/24`.
- **Prefix filtering** on **AS400** to block `192.168.2.0/24` (AS300 LAN) from AS300, forcing route learning via **AS200**.

### Additional BGP Configurations

- **BGP synchronization** is **disabled** on all ASes.
- **Next-hop-self** enabled on ASBRs for proper iBGP routing.
- All **eBGP peers** are reachable and **not isolated or stubbed** by design.

---

## 🔁 OSPF Design

- All ASes run **OSPF internally**.
- **AS100** is divided into **four areas** including **area 0 (backbone)**.
- Each area in AS100 connects to **area 0 via an ABR**.
- **AS200, AS300, AS400** use a **single area (area 0)**.

### 🧩 Key OSPF Configurations

- **Loopback interfaces** are used for:
  - Stable **OSPF router IDs**
  - **iBGP peerings**
- **LAN-connected interfaces** set as `passive-interface`.
- Hierarchical area design ensures **OSPF scalability and stability**.

---

## LAN Architecture – `192.168.1.0/24`

The enterprise LAN under AS100 is divided as follows:

- **VLANs**:  
  - `VLAN 100`  
  - `VLAN 200`  
  - `VLAN 300`
- **ROAS (Router-on-a-Stick)**:
  - Configured on gateway router using **subinterfaces**
- **802.1Q Trunking**:
  - Configured on switch uplinks
- **Access Ports**:
  - Assigned via **automation**
- **DHCP**:
  - Gateway router acts as **DHCP relay agent**
  - **DHCP server** resides in **AS100 backbone**

---

##  Project Highlights

- ✅ Telnet-based **Python automation**
- ✅ Real-world **BGP traffic engineering**
- ✅ Scalable **OSPF multi-area design**
- ✅ Realistic enterprise **VLAN segmentation**
- ✅ Cross-AS prefix distribution and manipulation
- 

## Requirements
- EVE-NG
- Cisco iol switch images
- Cisco dynamips router images
- pyyaml installed
