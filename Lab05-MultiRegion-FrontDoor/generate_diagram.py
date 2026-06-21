"""
Architecture Diagram — Scenario 5: Expert+
Multi-Region HA with Azure Front Door + Geo-Replicated SQL + Traffic Failover
"""

import os

graphviz_bin = r"C:\Program Files\Graphviz\bin"
if graphviz_bin not in os.environ.get("PATH", ""):
    os.environ["PATH"] = graphviz_bin + ";" + os.environ["PATH"]

from diagrams import Diagram, Cluster, Edge
from diagrams.azure.network import FrontDoors, ApplicationGateway, DNSZones, TrafficManagerProfiles
from diagrams.azure.compute import AppServices
from diagrams.azure.database import SQLDatabases, DatabaseForMysqlServers
from diagrams.azure.storage import StorageAccounts
from diagrams.azure.monitor import Monitor, ApplicationInsights
from diagrams.azure.security import KeyVaults
from diagrams.azure.general import Resourcegroups
from diagrams.azure.devops import Repos
from diagrams.azure.web import AppServicePlans
from diagrams.onprem.client import Users

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

global_style = {
    "bgcolor": "#ede7f6", "style": "rounded", "pencolor": "#4527a0",
    "penwidth": "2", "fontname": "Segoe UI Semibold", "fontsize": "13", "fontcolor": "#311b92",
}
primary_rg = {
    "bgcolor": "#e8f5e9", "style": "rounded", "pencolor": "#2e7d32",
    "penwidth": "2", "fontname": "Segoe UI Semibold", "fontsize": "12", "fontcolor": "#1b5e20",
}
primary_sub = {
    "bgcolor": "#c8e6c9", "style": "rounded", "pencolor": "#43a047",
    "penwidth": "1.2", "fontname": "Segoe UI", "fontsize": "10", "fontcolor": "#2e7d32",
}
secondary_rg = {
    "bgcolor": "#fff3e0", "style": "rounded", "pencolor": "#e65100",
    "penwidth": "2", "fontname": "Segoe UI Semibold", "fontsize": "12", "fontcolor": "#bf360c",
}
secondary_sub = {
    "bgcolor": "#ffe0b2", "style": "rounded", "pencolor": "#f57c00",
    "penwidth": "1.2", "fontname": "Segoe UI", "fontsize": "10", "fontcolor": "#e65100",
}
shared_style = {
    "bgcolor": "#fce4ec", "style": "rounded,dashed", "pencolor": "#c62828",
    "penwidth": "1.2", "fontname": "Segoe UI", "fontsize": "11", "fontcolor": "#b71c1c",
}

with Diagram(
    "", filename="Lab05-Architecture", outformat="png",
    show=False, direction="TB",
    graph_attr=graph_attr, node_attr=node_attr, edge_attr=edge_attr,
):
    users = Users("Global Users")

    with Cluster("Global Tier", graph_attr=global_style):
        frontdoor = FrontDoors("Azure Front Door\n(Global LB + WAF\n+ SSL Termination)")
        dns = DNSZones("Azure DNS\napp.example.com")

    with Cluster("Primary Region — Central India", graph_attr=primary_rg):
        with Cluster("App Service", graph_attr=primary_sub):
            app1 = AppServices("App Service\n(Primary)\nNode.js / .NET")
            plan1 = AppServicePlans("App Service Plan\nS1 Standard")
        with Cluster("Database", graph_attr=primary_sub):
            sql_primary = SQLDatabases("Azure SQL\n(Primary)\nRead-Write")
        insights1 = ApplicationInsights("App Insights\n(Primary)")
        kv1 = KeyVaults("Key Vault\n(Primary)")

    with Cluster("Secondary Region — South India", graph_attr=secondary_rg):
        with Cluster("App Service", graph_attr=secondary_sub):
            app2 = AppServices("App Service\n(Secondary)\nNode.js / .NET")
            plan2 = AppServicePlans("App Service Plan\nS1 Standard")
        with Cluster("Database", graph_attr=secondary_sub):
            sql_secondary = SQLDatabases("Azure SQL\n(Secondary)\nRead-Only Replica")
        insights2 = ApplicationInsights("App Insights\n(Secondary)")
        kv2 = KeyVaults("Key Vault\n(Secondary)")

    with Cluster("Shared Operations", graph_attr=shared_style):
        monitor = Monitor("Azure Monitor\n+ Action Groups\n(Email/SMS Alerts)")
        storage = StorageAccounts("Storage Account\n(Backups)")

    # ── Connections ──
    users >> Edge(label="HTTPS", style="bold", color="#4527a0") >> dns
    dns >> Edge(color="#4527a0") >> frontdoor

    frontdoor >> Edge(label="Priority 1\n(Active)", style="bold", color="#2e7d32") >> app1
    frontdoor >> Edge(label="Priority 2\n(Standby)", style="dashed", color="#e65100") >> app2

    app1 >> Edge(label="Read/Write", color="#2e7d32") >> sql_primary
    app2 >> Edge(label="Read-Only", color="#e65100", style="dashed") >> sql_secondary

    sql_primary >> Edge(label="Geo-Replication\n(Async)", color="#c62828", style="bold") >> sql_secondary

    app1 >> Edge(style="dotted", color="#888") >> insights1
    app2 >> Edge(style="dotted", color="#888") >> insights2
    app1 >> Edge(style="dotted", color="#888") >> kv1
    app2 >> Edge(style="dotted", color="#888") >> kv2

    monitor >> Edge(style="dotted", color="#c62828") >> app1
    monitor >> Edge(style="dotted", color="#c62828") >> app2

print("Done: Lab05-Architecture.png")
