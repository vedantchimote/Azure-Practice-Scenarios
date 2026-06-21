"""
Architecture Diagram for the Azure Portal Practice Scenario.
Generates a clean, professional PNG matching Microsoft documentation style.

Scenario: High-Availability Nginx Portfolio Website
"""

import os

# Ensure Graphviz is on PATH
graphviz_bin = r"C:\Program Files\Graphviz\bin"
if graphviz_bin not in os.environ.get("PATH", ""):
    os.environ["PATH"] = graphviz_bin + ";" + os.environ["PATH"]

from diagrams import Diagram, Cluster, Edge
from diagrams.azure.network import (
    LoadBalancers,
    PublicIpAddresses,
    NetworkSecurityGroupsClassic,
    Firewall,
)
from diagrams.azure.compute import VMLinux, AvailabilitySets
from diagrams.azure.storage import StorageAccounts
from diagrams.azure.monitor import Monitor
from diagrams.onprem.client import Users

# ──────────────────────────────────────────────────
# Graph styling — clean white background like MS docs
# ──────────────────────────────────────────────────
graph_attr = {
    "fontsize": "24",
    "fontname": "Segoe UI Semibold",
    "bgcolor": "white",
    "pad": "1.0",
    "ranksep": "1.0",
    "nodesep": "0.9",
    "splines": "spline",
    "label": "",
    "dpi": "150",
}

node_attr = {
    "fontsize": "11",
    "fontname": "Segoe UI",
    "fontcolor": "#1a1a1a",
}

edge_attr = {
    "color": "#333333",
    "penwidth": "1.5",
    "arrowsize": "0.8",
}

# Cluster styles
rg_style = {
    "bgcolor": "#ffffff",
    "style": "rounded",
    "pencolor": "#0078d4",
    "penwidth": "2",
    "fontname": "Segoe UI Semibold",
    "fontsize": "14",
    "fontcolor": "#0078d4",
}

vnet_style = {
    "bgcolor": "#f0f6ff",
    "style": "rounded,dashed",
    "pencolor": "#0078d4",
    "penwidth": "1.5",
    "fontname": "Segoe UI",
    "fontsize": "13",
    "fontcolor": "#005a9e",
    "labeljust": "l",
}

web_subnet_style = {
    "bgcolor": "#e8f5e9",
    "style": "rounded",
    "pencolor": "#388e3c",
    "penwidth": "1.2",
    "fontname": "Segoe UI",
    "fontsize": "12",
    "fontcolor": "#2e7d32",
}

mgmt_subnet_style = {
    "bgcolor": "#fff8e1",
    "style": "rounded",
    "pencolor": "#f57f17",
    "penwidth": "1.2",
    "fontname": "Segoe UI",
    "fontsize": "12",
    "fontcolor": "#e65100",
}

monitoring_style = {
    "bgcolor": "#fce4ec",
    "style": "rounded,dashed",
    "pencolor": "#c62828",
    "penwidth": "1.2",
    "fontname": "Segoe UI",
    "fontsize": "12",
    "fontcolor": "#b71c1c",
}


with Diagram(
    "",
    filename="Lab01-Architecture",
    outformat="png",
    show=False,
    direction="TB",
    graph_attr=graph_attr,
    node_attr=node_attr,
    edge_attr=edge_attr,
):
    # External actors
    users = Users("End Users\n(Browser)")

    # Public IP & Load Balancer
    pip = PublicIpAddresses("Public IP\n(Static)")
    lb = LoadBalancers("Standard\nLoad Balancer")

    with Cluster("Resource Group:  portfolio-dev-rg  |  Region: Central India", graph_attr=rg_style):

        with Cluster("Virtual Network  —  10.1.0.0/16", graph_attr=vnet_style):

            with Cluster("Web Subnet  —  10.1.1.0/24", graph_attr=web_subnet_style):
                nsg_web = NetworkSecurityGroupsClassic("NSG-Web\nAllow HTTP / HTTPS")
                avset = AvailabilitySets("Availability Set\nFD:2 / UD:5")
                vm1 = VMLinux("Web-VM-1\nUbuntu 22.04\nNginx")
                vm2 = VMLinux("Web-VM-2\nUbuntu 22.04\nNginx")

            with Cluster("Management Subnet  —  10.1.2.0/24", graph_attr=mgmt_subnet_style):
                nsg_mgmt = NetworkSecurityGroupsClassic("NSG-Mgmt\nAllow SSH only")
                bastion = Firewall("Azure Bastion\n(Secure SSH/RDP)")

        with Cluster("Monitoring & Diagnostics", graph_attr=monitoring_style):
            monitor = Monitor("Azure Monitor\nMetrics & Alerts")

        storage = StorageAccounts("Storage Account\nBoot Diagnostics")

    # ── Connections ──
    users >> Edge(label="  HTTPS  ", style="bold", color="#0078d4") >> pip
    pip >> Edge(color="#0078d4") >> lb

    lb >> Edge(label="Backend Pool", color="#388e3c") >> vm1
    lb >> Edge(label="Backend Pool", color="#388e3c") >> vm2

    avset >> Edge(style="dashed", color="#888888") >> vm1
    avset >> Edge(style="dashed", color="#888888") >> vm2

    bastion >> Edge(label="  SSH  ", style="dashed", color="#e65100") >> vm1
    bastion >> Edge(label="  SSH  ", style="dashed", color="#e65100") >> vm2

    monitor >> Edge(style="dotted", color="#c62828") >> vm1
    monitor >> Edge(style="dotted", color="#c62828") >> vm2

    vm1 >> Edge(style="dotted", color="#666666") >> storage
    vm2 >> Edge(style="dotted", color="#666666") >> storage


print("Done: Lab01-Architecture.png")
