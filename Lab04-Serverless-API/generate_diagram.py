"""
Architecture Diagram — Scenario 4: Advanced-Expert
Serverless API with Azure Functions + Cosmos DB + API Management + Static Web App
"""

import os

graphviz_bin = r"C:\Program Files\Graphviz\bin"
if graphviz_bin not in os.environ.get("PATH", ""):
    os.environ["PATH"] = graphviz_bin + ";" + os.environ["PATH"]

from diagrams import Diagram, Cluster, Edge
from diagrams.azure.network import CDNProfiles, ApplicationGateway, DNSZones, FrontDoors
from diagrams.azure.compute import FunctionApps
from diagrams.azure.database import CosmosDb
from diagrams.azure.integration import APIManagement
from diagrams.azure.web import AppServices
from diagrams.azure.storage import StorageAccounts, BlobStorage
from diagrams.azure.monitor import Monitor, ApplicationInsights
from diagrams.azure.security import KeyVaults
from diagrams.azure.general import Resourcegroups
from diagrams.onprem.client import Users

graph_attr = {
    "fontsize": "22",
    "fontname": "Segoe UI Semibold",
    "bgcolor": "white",
    "pad": "0.8",
    "ranksep": "1.0",
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
frontend_style = {
    "bgcolor": "#e3f2fd", "style": "rounded", "pencolor": "#1565c0",
    "penwidth": "1.5", "fontname": "Segoe UI", "fontsize": "12", "fontcolor": "#0d47a1",
}
api_style = {
    "bgcolor": "#f3e5f5", "style": "rounded", "pencolor": "#7b1fa2",
    "penwidth": "1.5", "fontname": "Segoe UI", "fontsize": "12", "fontcolor": "#4a148c",
}
compute_style = {
    "bgcolor": "#e8f5e9", "style": "rounded", "pencolor": "#2e7d32",
    "penwidth": "1.5", "fontname": "Segoe UI", "fontsize": "12", "fontcolor": "#1b5e20",
}
data_style = {
    "bgcolor": "#fff3e0", "style": "rounded", "pencolor": "#e65100",
    "penwidth": "1.5", "fontname": "Segoe UI", "fontsize": "12", "fontcolor": "#bf360c",
}
monitor_style = {
    "bgcolor": "#fce4ec", "style": "rounded,dashed", "pencolor": "#c62828",
    "penwidth": "1.2", "fontname": "Segoe UI", "fontsize": "11", "fontcolor": "#b71c1c",
}

with Diagram(
    "", filename="Lab04-Architecture", outformat="png",
    show=False, direction="TB",
    graph_attr=graph_attr, node_attr=node_attr, edge_attr=edge_attr,
):
    users = Users("End Users\n(Browser)")

    with Cluster("Resource Group:  serverless-dev-rg  |  Central India", graph_attr=rg):

        with Cluster("Frontend Tier", graph_attr=frontend_style):
            cdn = CDNProfiles("Azure CDN\n(Global Cache)")
            static_web = AppServices("Static Web App\n(React/HTML)")
            storage_web = BlobStorage("Blob Storage\n($web container)")

        with Cluster("API Tier", graph_attr=api_style):
            apim = APIManagement("API Management\n(Rate Limiting\nAuth, Caching)")

        with Cluster("Compute Tier — Serverless", graph_attr=compute_style):
            func_crud = FunctionApps("Function App\n(CRUD API)\nNode.js / Python")
            func_events = FunctionApps("Function App\n(Event Processor)\nCosmos DB Trigger")

        with Cluster("Data Tier", graph_attr=data_style):
            cosmos = CosmosDb("Cosmos DB\n(NoSQL)\nServerless Tier")
            blob_data = BlobStorage("Blob Storage\n(File Uploads)")

        with Cluster("Operations", graph_attr=monitor_style):
            app_insights = ApplicationInsights("Application\nInsights")
            keyvault = KeyVaults("Key Vault\n(Connection Strings)")
            monitor = Monitor("Azure Monitor\nAlerts")

    # Connections
    users >> Edge(label="HTTPS", style="bold", color="#0078d4") >> cdn
    cdn >> Edge(color="#1565c0") >> static_web
    static_web >> Edge(style="dashed", color="#666") >> storage_web

    users >> Edge(label="API Calls", style="bold", color="#7b1fa2") >> apim
    apim >> Edge(label="/api/*", color="#7b1fa2") >> func_crud

    func_crud >> Edge(label="Read/Write", color="#e65100") >> cosmos
    func_crud >> Edge(label="Upload", color="#e65100", style="dashed") >> blob_data

    cosmos >> Edge(label="Change Feed\nTrigger", color="#2e7d32", style="dashed") >> func_events

    func_crud >> Edge(style="dotted", color="#c62828") >> app_insights
    func_events >> Edge(style="dotted", color="#c62828") >> app_insights
    func_crud >> Edge(style="dotted", color="#888") >> keyvault

print("Done: Lab04-Architecture.png")
