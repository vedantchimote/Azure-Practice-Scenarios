"""
Architecture Diagram — Scenario 3: Expert
Hub-Spoke Network Architecture with Azure Firewall
"""

import os

graphviz_bin = r"C:\Program Files\Graphviz\bin"
if graphviz_bin not in os.environ.get("PATH", ""):
    os.environ["PATH"] = graphviz_bin + ";" + os.environ["PATH"]

from diagrams import Diagram, Cluster, Edge
from diagrams.azure.network import (
    ApplicationGateway,
    PublicIpAddresses,
    NetworkSecurityGroupsClassic,
    Firewall,
    LoadBalancers,
    VirtualNetworks,
    VirtualNetworkGateways,
    RouteTables,
    DNSZones,
)
from diagrams.azure.compute import VMLinux
from diagrams.azure.database import DatabaseForMysqlServers
from diagrams.azure.storage import StorageAccounts
from diagrams.azure.monitor import Monitor, LogAnalyticsWorkspaces
from diagrams.azure.security import KeyVaults
from diagrams.onprem.client import Users
from diagrams.onprem.network import Internet

graph_attr = {
    "fontsize": "22",
    "fontname": "Segoe UI Semibold",
    "bgcolor": "white",
    "pad": "0.8",
    "ranksep": "0.9",
    "nodesep": "0.7",
    "splines": "spline",
    "label": "",
    "dpi": "150",
}
node_attr = {"fontsize": "10", "fontname": "Segoe UI", "fontcolor": "#1a1a1a"}
edge_attr = {"color": "#333333", "penwidth": "1.4", "arrowsize": "0.7"}

# Cluster styles
hub_vnet = {
    "bgcolor": "#e8eaf6", "style": "rounded", "pencolor": "#283593",
    "penwidth": "2", "fontname": "Segoe UI Semibold", "fontsize": "12", "fontcolor": "#1a237e",
}
hub_sub = {
    "bgcolor": "#c5cae9", "style": "rounded", "pencolor": "#3949ab",
    "penwidth": "1.2", "fontname": "Segoe UI", "fontsize": "10", "fontcolor": "#283593",
}
spoke1_vnet = {
    "bgcolor": "#e8f5e9", "style": "rounded", "pencolor": "#2e7d32",
    "penwidth": "2", "fontname": "Segoe UI Semibold", "fontsize": "12", "fontcolor": "#1b5e20",
}
spoke1_sub = {
    "bgcolor": "#c8e6c9", "style": "rounded", "pencolor": "#43a047",
    "penwidth": "1.2", "fontname": "Segoe UI", "fontsize": "10", "fontcolor": "#2e7d32",
}
spoke2_vnet = {
    "bgcolor": "#fff3e0", "style": "rounded", "pencolor": "#e65100",
    "penwidth": "2", "fontname": "Segoe UI Semibold", "fontsize": "12", "fontcolor": "#bf360c",
}
spoke2_sub = {
    "bgcolor": "#ffe0b2", "style": "rounded", "pencolor": "#f57c00",
    "penwidth": "1.2", "fontname": "Segoe UI", "fontsize": "10", "fontcolor": "#e65100",
}
shared_style = {
    "bgcolor": "#fce4ec", "style": "rounded,dashed", "pencolor": "#c62828",
    "penwidth": "1.2", "fontname": "Segoe UI", "fontsize": "11", "fontcolor": "#b71c1c",
}
onprem_style = {
    "bgcolor": "#f5f5f5", "style": "rounded,dashed", "pencolor": "#616161",
    "penwidth": "1.5", "fontname": "Segoe UI", "fontsize": "11", "fontcolor": "#424242",
}

with Diagram(
    "", filename="Lab03-Architecture", outformat="png",
    show=False, direction="TB",
    graph_attr=graph_attr, node_attr=node_attr, edge_attr=edge_attr,
):
    users = Users("End Users")

    with Cluster("On-Premises Network (Simulated)", graph_attr=onprem_style):
        onprem_vm = VMLinux("On-Prem\nWorkstation")

    with Cluster("Azure  —  Resource Group: hubspoke-dev-rg", graph_attr={
        "bgcolor": "#ffffff", "style": "rounded", "pencolor": "#0078d4",
        "penwidth": "2.5", "fontname": "Segoe UI Semibold", "fontsize": "14", "fontcolor": "#0078d4",
    }):
        # ── Hub VNet ──
        with Cluster("Hub VNet — 10.0.0.0/16", graph_attr=hub_vnet):
            with Cluster("Firewall Subnet — 10.0.0.0/24", graph_attr=hub_sub):
                firewall = Firewall("Azure Firewall\n(Central Egress)")
                fw_pip = PublicIpAddresses("Firewall\nPublic IP")

            with Cluster("Gateway Subnet — 10.0.255.0/24", graph_attr=hub_sub):
                vpn_gw = VirtualNetworkGateways("VPN Gateway\n(Site-to-Site)")

            with Cluster("Bastion Subnet — 10.0.1.0/24", graph_attr=hub_sub):
                bastion = VMLinux("Azure Bastion\nHost (Jump Box)")

        # ── Spoke 1 VNet ──
        with Cluster("Spoke 1 VNet — 10.1.0.0/16  (Web Workload)", graph_attr=spoke1_vnet):
            with Cluster("Web Subnet — 10.1.1.0/24", graph_attr=spoke1_sub):
                nsg1 = NetworkSecurityGroupsClassic("NSG-Web")
                web_vm1 = VMLinux("Web-VM-1\nNginx")
                web_vm2 = VMLinux("Web-VM-2\nNginx")

            lb = LoadBalancers("Internal LB")
            rt1 = RouteTables("UDR → Firewall")

        # ── Spoke 2 VNet ──
        with Cluster("Spoke 2 VNet — 10.2.0.0/16  (Data Workload)", graph_attr=spoke2_vnet):
            with Cluster("Data Subnet — 10.2.1.0/24", graph_attr=spoke2_sub):
                nsg2 = NetworkSecurityGroupsClassic("NSG-Data")
                db = DatabaseForMysqlServers("Azure MySQL\nFlexible Server")

            rt2 = RouteTables("UDR → Firewall")

        # ── Shared Services ──
        with Cluster("Shared Services", graph_attr=shared_style):
            keyvault = KeyVaults("Azure\nKey Vault")
            logs = LogAnalyticsWorkspaces("Log Analytics\nWorkspace")
            monitor = Monitor("Azure Monitor")
            dns = DNSZones("Private DNS\nZone")

    # ── Connections ──
    # User → Firewall → Web
    users >> Edge(label="HTTPS", style="bold", color="#0078d4") >> fw_pip
    fw_pip >> Edge(color="#283593") >> firewall

    # Hub ↔ Spokes (Peering)
    firewall >> Edge(label="VNet\nPeering", color="#2e7d32", style="bold") >> lb
    firewall >> Edge(label="VNet\nPeering", color="#e65100", style="bold") >> db

    # LB → Web VMs
    lb >> Edge(color="#388e3c") >> web_vm1
    lb >> Edge(color="#388e3c") >> web_vm2

    # Web → DB
    web_vm1 >> Edge(label=":3306", color="#c62828", style="dashed") >> db
    web_vm2 >> Edge(label=":3306", color="#c62828", style="dashed") >> db

    # VPN
    onprem_vm >> Edge(label="IPSec\nVPN", color="#616161", style="dashed") >> vpn_gw
    vpn_gw >> Edge(color="#283593") >> firewall

    # Bastion → VMs
    bastion >> Edge(label="SSH", style="dotted", color="#283593") >> web_vm1

    # Monitoring
    monitor >> Edge(style="dotted", color="#c62828") >> firewall
    logs >> Edge(style="dotted", color="#c62828") >> web_vm1

    # Route tables
    rt1 >> Edge(style="dotted", color="#888") >> firewall
    rt2 >> Edge(style="dotted", color="#888") >> firewall

print("Done: scenario3_architecture.png")
