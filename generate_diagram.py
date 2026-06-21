"""
Azure Web Infrastructure Diagram Generator
Uses the 'diagrams' library to produce a PNG architecture diagram with official Azure icons.
"""

import os

# Ensure Graphviz is on PATH (winget installs to Program Files\Graphviz)
graphviz_bin = r"C:\Program Files\Graphviz\bin"
if graphviz_bin not in os.environ.get("PATH", ""):
    os.environ["PATH"] = graphviz_bin + ";" + os.environ["PATH"]

from diagrams import Diagram, Cluster, Edge
from diagrams.azure.network import (
    VirtualNetworks,
    Subnets,
    LoadBalancers,
    PublicIpAddresses,
    NetworkSecurityGroupsClassic,
)
from diagrams.azure.compute import VMLinux, AvailabilitySets

# Graph attributes for a clean, professional look
graph_attr = {
    "fontsize": "28",
    "fontname": "Segoe UI",
    "bgcolor": "#f8f9fa",
    "pad": "0.8",
    "ranksep": "1.2",
    "nodesep": "0.8",
    "splines": "ortho",
    "label": "Azure Web Server Infrastructure\nDeployed via Terraform",
    "labelloc": "t",
    "fontcolor": "#1a1a2e",
}

node_attr = {
    "fontsize": "12",
    "fontname": "Segoe UI",
    "fontcolor": "#1a1a2e",
}

edge_attr = {
    "color": "#0078d4",
    "penwidth": "2.0",
}

with Diagram(
    "azure_web_infra",
    filename="azure_web_infra",
    outformat="png",
    show=False,
    direction="TB",
    graph_attr=graph_attr,
    node_attr=node_attr,
    edge_attr=edge_attr,
):
    # --- External entry point ---
    public_ip = PublicIpAddresses("Public IP\n(Static)")
    lb = LoadBalancers("Standard\nLoad Balancer")

    with Cluster(
        "Resource Group: webdemo-dev-rg\nRegion: Central India",
        graph_attr={"bgcolor": "#e8f0fe", "style": "rounded", "pencolor": "#0078d4", "penwidth": "2"},
    ):
        with Cluster(
            "Virtual Network — 10.0.0.0/16",
            graph_attr={"bgcolor": "#d4e6f9", "style": "rounded", "pencolor": "#005a9e"},
        ):
            with Cluster(
                "Public Subnet — 10.0.1.0/24",
                graph_attr={"bgcolor": "#c8e6c9", "style": "rounded", "pencolor": "#2e7d32"},
            ):
                nsg_pub = NetworkSecurityGroupsClassic("NSG\nHTTP | HTTPS | SSH")
                avset = AvailabilitySets("Availability Set\nFD:2 / UD:5")
                vm1 = VMLinux("VM-1\nUbuntu 22.04\nApache2")
                vm2 = VMLinux("VM-2\nUbuntu 22.04\nApache2")

            with Cluster(
                "Private Subnet — 10.0.2.0/24  (Reserved)",
                graph_attr={"bgcolor": "#fff3e0", "style": "rounded,dashed", "pencolor": "#e65100"},
            ):
                nsg_priv = NetworkSecurityGroupsClassic("NSG\nInternal Only")

    # --- Connections ---
    public_ip >> Edge(label="HTTP:80", color="#0078d4") >> lb
    lb >> Edge(label="Backend Pool", color="#2e7d32") >> vm1
    lb >> Edge(label="Backend Pool", color="#2e7d32") >> vm2

    # Availability Set relationships
    avset >> Edge(style="dashed", color="#666666") >> vm1
    avset >> Edge(style="dashed", color="#666666") >> vm2

print("Diagram generated: azure_web_infra.png")
