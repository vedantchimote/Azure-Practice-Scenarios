"""
Architecture Diagram — Scenario 2: Advanced
Online Store with Application Gateway + VMSS + Azure MySQL
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
)
from diagrams.azure.compute import VMLinux, VMScaleSet
from diagrams.azure.database import DatabaseForMysqlServers
from diagrams.azure.storage import StorageAccounts
from diagrams.azure.monitor import Monitor, Metrics
from diagrams.azure.general import Resourcegroups
from diagrams.onprem.client import Users

graph_attr = {
    "fontsize": "22",
    "fontname": "Segoe UI Semibold",
    "bgcolor": "white",
    "pad": "0.8",
    "ranksep": "1.1",
    "nodesep": "0.8",
    "splines": "spline",
    "label": "",
    "dpi": "150",
}
node_attr = {"fontsize": "11", "fontname": "Segoe UI", "fontcolor": "#1a1a1a"}
edge_attr = {"color": "#333333", "penwidth": "1.5", "arrowsize": "0.8"}

rg = {
    "bgcolor": "#ffffff", "style": "rounded", "pencolor": "#0078d4",
    "penwidth": "2", "fontname": "Segoe UI Semibold", "fontsize": "13", "fontcolor": "#0078d4",
}
vnet = {
    "bgcolor": "#f0f6ff", "style": "rounded,dashed", "pencolor": "#0078d4",
    "penwidth": "1.5", "fontname": "Segoe UI", "fontsize": "12", "fontcolor": "#005a9e",
}
appgw_sub = {
    "bgcolor": "#e3f2fd", "style": "rounded", "pencolor": "#1565c0",
    "penwidth": "1.2", "fontname": "Segoe UI", "fontsize": "11", "fontcolor": "#0d47a1",
}
web_sub = {
    "bgcolor": "#e8f5e9", "style": "rounded", "pencolor": "#388e3c",
    "penwidth": "1.2", "fontname": "Segoe UI", "fontsize": "11", "fontcolor": "#2e7d32",
}
db_sub = {
    "bgcolor": "#fce4ec", "style": "rounded", "pencolor": "#c62828",
    "penwidth": "1.2", "fontname": "Segoe UI", "fontsize": "11", "fontcolor": "#b71c1c",
}
mon_style = {
    "bgcolor": "#fff3e0", "style": "rounded,dashed", "pencolor": "#e65100",
    "penwidth": "1.2", "fontname": "Segoe UI", "fontsize": "11", "fontcolor": "#bf360c",
}

with Diagram(
    "", filename="Lab02-Architecture", outformat="png",
    show=False, direction="TB",
    graph_attr=graph_attr, node_attr=node_attr, edge_attr=edge_attr,
):
    users = Users("End Users\n(Browser)")
    pip = PublicIpAddresses("Public IP\n(Static)")

    with Cluster("Resource Group:  onlinestore-dev-rg  |  Central India", graph_attr=rg):
        with Cluster("Virtual Network — 10.2.0.0/16", graph_attr=vnet):

            with Cluster("AppGW Subnet — 10.2.0.0/24", graph_attr=appgw_sub):
                appgw = ApplicationGateway("Application Gateway\nWAF v2 (Layer 7)")

            with Cluster("Web Subnet — 10.2.1.0/24", graph_attr=web_sub):
                nsg_web = NetworkSecurityGroupsClassic("NSG-Web")
                vmss = VMScaleSet("VM Scale Set\n2–4 instances\n(Auto-Scale on CPU)")
                vm1 = VMLinux("VMSS Instance 1\nNginx + App")
                vm2 = VMLinux("VMSS Instance 2\nNginx + App")

            with Cluster("Database Subnet — 10.2.2.0/24", graph_attr=db_sub):
                nsg_db = NetworkSecurityGroupsClassic("NSG-DB\nAllow 3306 from\nWeb Subnet only")
                mysql = DatabaseForMysqlServers("Azure Database\nfor MySQL\nFlexible Server")

        with Cluster("Monitoring & Diagnostics", graph_attr=mon_style):
            monitor = Monitor("Azure Monitor\nAuto-Scale Rules")
            metrics = Metrics("CPU/Memory\nMetrics")

        storage = StorageAccounts("Storage Account\nDiagnostics")

    # Connections
    users >> Edge(label="  HTTPS  ", style="bold", color="#0078d4") >> pip
    pip >> Edge(color="#0078d4") >> appgw

    appgw >> Edge(label="HTTP :80", color="#388e3c") >> vm1
    appgw >> Edge(label="HTTP :80", color="#388e3c") >> vm2

    vmss >> Edge(style="dashed", color="#888888") >> vm1
    vmss >> Edge(style="dashed", color="#888888") >> vm2

    vm1 >> Edge(label="MySQL :3306", color="#c62828") >> mysql
    vm2 >> Edge(label="MySQL :3306", color="#c62828") >> mysql

    monitor >> Edge(style="dotted", color="#e65100") >> vmss
    metrics >> Edge(style="dotted", color="#e65100") >> vm1

    vm1 >> Edge(style="dotted", color="#666666") >> storage

print("Done: scenario2_architecture.png")
