# 🧪 Scenario 3: Hub-Spoke Network Architecture with Azure Firewall

> **Difficulty:** Expert &nbsp; | &nbsp; **Time:** 2–3 hours &nbsp; | &nbsp; **Estimated Cost:** ~₹800–1,500 (if destroyed within 3 hours)

This is a **real-world enterprise network pattern** used by organizations to centralize security, routing, and shared services. You'll build the **Hub-Spoke** topology — the same architecture used by companies deploying production workloads on Azure.

---

## 🏗️ What is Hub-Spoke Architecture?

```
                    ┌──────────────────────┐
                    │      Hub VNet        │
                    │  ┌────────────────┐  │
   On-Prem ◄──VPN──│  │ Azure Firewall │  │
                    │  │   (Central)    │  │
                    │  └───────┬────────┘  │
                    │     ┌────┴────┐      │
                    │  Bastion   Gateway   │
                    └─────┬──────────┬─────┘
                   Peering│          │Peering
              ┌───────────┘          └───────────┐
              ▼                                  ▼
     ┌────────────────┐                 ┌────────────────┐
     │  Spoke 1 VNet  │                 │  Spoke 2 VNet  │
     │  (Web Workload)│                 │  (Data Workload)│
     │  ┌──────────┐  │                 │  ┌──────────┐  │
     │  │ Web VMs  │  │────:3306───────▶│  │  MySQL   │  │
     │  └──────────┘  │                 │  └──────────┘  │
     └────────────────┘                 └────────────────┘
```

**Hub:** The central VNet containing shared infrastructure — firewall, VPN gateway, bastion host. All traffic between spokes and to/from the internet flows through the hub.

**Spokes:** Isolated VNets for individual workloads. They peer with the hub but not with each other, forcing all inter-spoke traffic through the firewall for inspection.

---

## 📐 Architecture Overview

![Scenario 3 Architecture](./Lab03-Architecture.png)

### What You'll Build

| #  | Resource                     | Name                          | VNet/Subnet            | Purpose                                  |
|----|------------------------------|-------------------------------|------------------------|------------------------------------------|
| 1  | Resource Group               | `hubspoke-dev-rg`             | —                      | Container for everything                 |
| **Hub VNet** | | | | |
| 2  | Virtual Network              | `hub-vnet`                    | 10.0.0.0/16            | Central network hub                      |
| 3  | Azure Firewall Subnet        | `AzureFirewallSubnet`         | 10.0.0.0/24            | **Must** be named exactly this           |
| 4  | Bastion Subnet               | `AzureBastionSubnet`          | 10.0.1.0/24            | **Must** be named exactly this           |
| 5  | Azure Firewall               | `hub-firewall`                | Hub                    | Central egress & inter-spoke inspection  |
| 6  | Firewall Public IP           | `hub-firewall-pip`            | —                      | Public IP for the firewall               |
| 7  | Azure Bastion                | `hub-bastion`                 | Hub                    | Secure browser-based SSH (no public IPs) |
| 8  | Bastion Public IP            | `hub-bastion-pip`             | —                      | Required for Bastion                     |
| **Spoke 1 — Web Workload** | | | | |
| 9  | Virtual Network              | `spoke1-web-vnet`             | 10.1.0.0/16            | Web workload network                     |
| 10 | Web Subnet                   | `web-subnet`                  | 10.1.1.0/24            | For web server VMs                       |
| 11 | NSG — Web                    | `nsg-spoke1-web`              | —                      | Allow HTTP from firewall                 |
| 12 | Route Table                  | `rt-spoke1-to-firewall`       | —                      | Force all traffic through firewall       |
| 13 | VM 1                         | `spoke1-web-vm-1`             | Spoke 1                | Nginx web server                         |
| 14 | VM 2                         | `spoke1-web-vm-2`             | Spoke 1                | Nginx web server                         |
| 15 | Internal Load Balancer       | `spoke1-internal-lb`          | Spoke 1                | Distributes traffic within spoke         |
| **Spoke 2 — Data Workload** | | | | |
| 16 | Virtual Network              | `spoke2-data-vnet`            | 10.2.0.0/16            | Data workload network                    |
| 17 | Data Subnet                  | `data-subnet`                 | 10.2.1.0/24            | For database                             |
| 18 | NSG — Data                   | `nsg-spoke2-data`             | —                      | Allow 3306 from Spoke 1 only             |
| 19 | Route Table                  | `rt-spoke2-to-firewall`       | —                      | Force all traffic through firewall       |
| 20 | Azure MySQL                  | `hubspoke-mysql`              | Spoke 2                | Managed database                         |
| **Shared Services** | | | | |
| 21 | Log Analytics Workspace      | `hubspoke-logs`               | —                      | Centralized logging                      |
| 22 | Azure Key Vault              | `hubspoke-kv`                 | —                      | Secret management                        |
| **Peering** | | | | |
| 23 | VNet Peering                 | `hub-to-spoke1`               | —                      | Connect Hub ↔ Spoke 1                    |
| 24 | VNet Peering                 | `hub-to-spoke2`               | —                      | Connect Hub ↔ Spoke 2                    |

**Total: ~24 resources**

---

## 📚 New Concepts You'll Learn

<details>
<summary><strong>🔹 What is VNet Peering?</strong></summary>

VNet Peering connects two VNets so resources inside them can talk to each other as if they're on the same network. Traffic stays on Azure's backbone — it doesn't go over the internet.

**Key rules:**
- Peering is **not transitive**: If Hub peers with Spoke1 and Hub peers with Spoke2, Spoke1 and Spoke2 **cannot** talk to each other automatically — traffic must go through a firewall/NVA in the Hub
- Address spaces must not overlap (that's why we use 10.0.x.x, 10.1.x.x, 10.2.x.x)
- You create the peering from **both sides** (Hub → Spoke AND Spoke → Hub)

</details>

<details>
<summary><strong>🔹 What is Azure Firewall?</strong></summary>

Azure Firewall is a **managed, cloud-based network security service**. Unlike NSGs (which filter by IP/port), Azure Firewall can:

- Filter by **FQDN** (fully qualified domain names): "Allow traffic to `*.ubuntu.com` but block everything else"
- Inspect traffic between spokes (east-west traffic)
- Act as a **central egress point**: All internet-bound traffic from all spokes goes through the firewall
- Provide **threat intelligence**: Automatically block known malicious IPs

**Think of it as:** A security guard at the building entrance who checks every person's ID and purpose before letting them in or out.

**Important:** The firewall subnet **must** be named exactly `AzureFirewallSubnet`. Azure enforces this.

</details>

<details>
<summary><strong>🔹 What is a Route Table (UDR)?</strong></summary>

A User-Defined Route (UDR) overrides Azure's default routing. By default, Spoke1 can reach the internet directly. We don't want that — we want all traffic to go through the firewall first.

We create a route table that says:
```
Destination: 0.0.0.0/0 (everything)
Next Hop: Azure Firewall private IP (e.g., 10.0.0.4)
```

Then we associate this route table with the spoke subnets. Now all outbound traffic is **forced** through the firewall.

**Think of it as:** A road sign that says "To reach the highway, you must go through the toll booth first."

</details>

<details>
<summary><strong>🔹 What is Azure Bastion?</strong></summary>

Azure Bastion provides **secure SSH/RDP access** to your VMs directly from the Azure Portal browser — no public IPs needed on VMs, no SSH client needed on your laptop.

**How it works:**
1. You click "Connect" on a VM in the portal
2. A browser tab opens with an SSH terminal
3. Traffic goes: Your Browser → Azure Bastion (over HTTPS/443) → VM (over private IP)

**Why it matters:** In this scenario, no VM has a public IP. Bastion is the **only** way to access them. This is enterprise-grade security.

**Important:** The bastion subnet **must** be named exactly `AzureBastionSubnet`. Azure enforces this.

</details>

<details>
<summary><strong>🔹 What is Azure Key Vault?</strong></summary>

Key Vault is a secure store for:
- **Secrets:** Database passwords, API keys, connection strings
- **Certificates:** SSL/TLS certificates
- **Keys:** Encryption keys

Instead of hardcoding `mysql_password = "P@ssw0rd"` in your app, you store it in Key Vault and your app retrieves it at runtime. If the password is compromised, you rotate it in one place.

</details>

<details>
<summary><strong>🔹 What is Log Analytics Workspace?</strong></summary>

A centralized place to collect, analyze, and query logs from **all** Azure resources. Think of it as a unified logging dashboard.

You'll configure:
- Firewall logs → Log Analytics (see what traffic is being blocked)
- VM metrics → Log Analytics (CPU, memory, disk)
- NSG flow logs → Log Analytics (who's connecting to what)

Use **KQL (Kusto Query Language)** to query logs:
```kql
AzureDiagnostics
| where Category == "AzureFirewallNetworkRule"
| where msg_s contains "Deny"
| project TimeGenerated, msg_s
| order by TimeGenerated desc
```

</details>

---

## 🚀 Step-by-Step Instructions

> [!CAUTION]
> **Azure Firewall costs ~₹1,000/day and Azure Bastion costs ~₹350/day.** Plan to complete this lab in one sitting and delete everything immediately after. **Do not leave resources running overnight.**

---

### Phase 1: Build the Networks (3 VNets)

#### Step 1: Create the Resource Group

1. Search **"Resource groups"** → **"+ Create"**

   | Field            | Value                |
   |------------------|----------------------|
   | Resource group   | `hubspoke-dev-rg`    |
   | Region           | `Central India`      |

#### Step 2: Create the Hub VNet

1. Search **"Virtual networks"** → **"+ Create"**
2. Fill in:

   | Field            | Value          |
   |------------------|----------------|
   | Resource group   | `hubspoke-dev-rg` |
   | Name             | `hub-vnet`     |
   | Region           | `Central India` |
   | Address space    | `10.0.0.0/16`  |

3. Add these subnets:

   | Subnet Name              | Address Range    | Notes                                    |
   |--------------------------|------------------|------------------------------------------|
   | `AzureFirewallSubnet`    | `10.0.0.0/24`    | ⚠️ **Exact name required** by Azure      |
   | `AzureBastionSubnet`     | `10.0.1.0/24`    | ⚠️ **Exact name required** by Azure      |

> [!WARNING]
> Azure Firewall and Azure Bastion both **require** their subnets to have these **exact names**. If you name them anything else, deployment will fail.

#### Step 3: Create Spoke 1 VNet (Web Workload)

1. Create another VNet:

   | Field            | Value               |
   |------------------|---------------------|
   | Name             | `spoke1-web-vnet`   |
   | Address space    | `10.1.0.0/16`       |

2. Add subnet:

   | Subnet Name   | Address Range  |
   |---------------|----------------|
   | `web-subnet`  | `10.1.1.0/24`  |

#### Step 4: Create Spoke 2 VNet (Data Workload)

1. Create another VNet:

   | Field            | Value               |
   |------------------|---------------------|
   | Name             | `spoke2-data-vnet`  |
   | Address space    | `10.2.0.0/16`       |

2. Add subnet:

   | Subnet Name    | Address Range  |
   |----------------|----------------|
   | `data-subnet`  | `10.2.1.0/24`  |

3. Delegate `data-subnet` to `Microsoft.DBforMySQL/flexibleServers` (same as Scenario 2 Step 3)

---

### Phase 2: Connect the Networks (VNet Peering)

#### Step 5: Peer Hub ↔ Spoke 1

1. Go to **`hub-vnet`** → Click **"Peerings"** in the left menu → **"+ Add"**
2. Fill in:

   | Field                                           | Value                      |
   |-------------------------------------------------|----------------------------|
   | This VNet — Peering link name                    | `hub-to-spoke1`            |
   | Allow traffic to remote VNet                     | `Enabled`                  |
   | Allow traffic forwarded from remote VNet         | `Enabled`                  |
   | Allow gateway transit                            | `Disabled` (no gateway yet)|
   | Remote VNet — Peering link name                  | `spoke1-to-hub`            |
   | Remote Virtual network                           | `spoke1-web-vnet`          |
   | Allow traffic to remote VNet                     | `Enabled`                  |
   | Allow traffic forwarded from remote VNet         | `Enabled`                  |
   | Use remote VNet gateway                          | `Disabled`                 |

3. Click **"Add"**

> [!NOTE]
> Azure creates **both sides** of the peering in one step when you do it from the portal. When you fill in the form, you're configuring the hub→spoke1 link AND the spoke1→hub link simultaneously.

#### Step 6: Peer Hub ↔ Spoke 2

Repeat Step 5 but:
- This VNet link name: `hub-to-spoke2`
- Remote VNet link name: `spoke2-to-hub`
- Remote Virtual network: `spoke2-data-vnet`

After this, verify all peerings show **"Connected"** status.

---

### Phase 3: Deploy the Azure Firewall (Central Security)

#### Step 7: Create the Firewall Public IP

1. Search **"Public IP addresses"** → **"+ Create"**

   | Field   | Value              |
   |---------|--------------------|
   | Name    | `hub-firewall-pip` |
   | SKU     | `Standard`         |
   | Assignment | `Static`        |

#### Step 8: Create the Azure Firewall

1. Search **"Firewalls"** → **"+ Create"**
2. Fill in:

   | Field                 | Value               |
   |-----------------------|---------------------|
   | Resource group        | `hubspoke-dev-rg`   |
   | Name                  | `hub-firewall`      |
   | Region                | `Central India`     |
   | Firewall SKU          | `Standard`          |
   | Firewall management   | `Use Firewall rules to manage this firewall` |
   | Virtual network       | `hub-vnet`          |
   | Public IP             | `hub-firewall-pip`  |

3. Click **"Review + create"** → **"Create"** *(Takes 5–10 minutes)*

4. **After creation**, go to the firewall → Note down the **Private IP address** (e.g., `10.0.0.4`). You'll need this for route tables.

#### Step 9: Configure Firewall Rules

Go to **`hub-firewall`** → **"Rules (classic)"** → Add rule collections:

**Network Rule Collection** (allow spoke-to-spoke and outbound traffic):

| Field                | Value                                |
|----------------------|--------------------------------------|
| Name                 | `net-rules`                          |
| Priority             | `100`                                |
| Action               | `Allow`                              |

Add rules inside this collection:

| Rule Name          | Source           | Destination      | Port       | Protocol |
|--------------------|------------------|-------------------|------------|----------|
| `spoke1-to-spoke2` | `10.1.0.0/16`    | `10.2.0.0/16`    | `3306`     | `TCP`    |
| `spoke2-to-spoke1` | `10.2.0.0/16`    | `10.1.0.0/16`    | `*`        | `Any`    |
| `allow-web-outbound`| `10.1.0.0/16`   | `*`               | `80,443`   | `TCP`    |

**Application Rule Collection** (allow VMs to download packages):

| Field                | Value                                |
|----------------------|--------------------------------------|
| Name                 | `app-rules`                          |
| Priority             | `200`                                |
| Action               | `Allow`                              |

| Rule Name          | Source           | Target FQDNs                            | Protocol    |
|--------------------|------------------|-----------------------------------------|-------------|
| `allow-ubuntu-repo`| `10.1.0.0/16`   | `*.ubuntu.com`, `*.archive.ubuntu.com`  | `HTTPS:443` |
| `allow-azure`      | `10.0.0.0/8`    | `*.azure.com`, `*.microsoft.com`        | `HTTPS:443` |

---

### Phase 4: Force Traffic Through the Firewall (Route Tables)

#### Step 10: Create Route Tables

**Route Table for Spoke 1:**

1. Search **"Route tables"** → **"+ Create"**

   | Field                     | Value                        |
   |---------------------------|------------------------------|
   | Name                      | `rt-spoke1-to-firewall`      |
   | Propagate gateway routes  | `No`                         |

2. After creation, go to the resource → **"Routes"** → **"+ Add"**

   | Field             | Value                                |
   |-------------------|--------------------------------------|
   | Route name        | `default-to-firewall`                |
   | Destination type  | `IP Addresses`                       |
   | Destination       | `0.0.0.0/0`                          |
   | Next hop type     | `Virtual appliance`                  |
   | Next hop address  | `10.0.0.4` *(your firewall private IP)* |

3. Go to **"Subnets"** → **"+ Associate"** → Select `spoke1-web-vnet` / `web-subnet`

**Route Table for Spoke 2:** Repeat with name `rt-spoke2-to-firewall`, same route, associate with `spoke2-data-vnet` / `data-subnet`.

> [!IMPORTANT]
> The **Next hop address** must match your Azure Firewall's **private IP**. Check this in the firewall's Overview page. It's typically `10.0.0.4` but verify.

---

### Phase 5: Deploy Workloads

#### Step 11: Create Web VMs in Spoke 1

Create **2 VMs** in `spoke1-web-vnet` / `web-subnet` (same process as Scenario 1 Steps 5–6):

| Field              | VM 1                   | VM 2                   |
|--------------------|------------------------|------------------------|
| Name               | `spoke1-web-vm-1`      | `spoke1-web-vm-2`      |
| VNet/Subnet        | `spoke1-web-vnet` / `web-subnet` | Same          |
| Public IP          | `None`                 | `None`                 |
| Image              | Ubuntu 22.04 LTS by Canonical (See all images) | Same |

Use this **Custom data** for cloud-init:
```yaml
#cloud-config
package_update: true
packages:
  - nginx
runcmd:
  - systemctl enable nginx
  - systemctl start nginx
  - echo '<html><body style="font-family:Arial;text-align:center;padding:50px;background:#1a1a2e;color:#e0e0e0"><h1>Hub-Spoke Web Server</h1><p>VM: '$(hostname)'</p><p>Traffic routed through Azure Firewall</p></body></html>' > /var/www/html/index.html
  - systemctl restart nginx
```

#### Step 12: Create Azure MySQL in Spoke 2

Same process as Scenario 2 Step 5, but:

| Field            | Value                  |
|------------------|------------------------|
| Server name      | `hubspoke-mysql`       |
| VNet              | `spoke2-data-vnet`    |
| Subnet            | `data-subnet`         |

#### Step 13: Create an Internal Load Balancer in Spoke 1

1. Search **"Load balancers"** → **"+ Create"**

   | Field            | Value                      |
   |------------------|----------------------------|
   | Name             | `spoke1-internal-lb`       |
   | SKU              | `Standard`                 |
   | Type             | **`Internal`** ← key difference from Scenario 1! |

2. **Frontend IP:**

   | Field            | Value                      |
   |------------------|----------------------------|
   | Name             | `internal-frontend`        |
   | Virtual network  | `spoke1-web-vnet`          |
   | Subnet           | `web-subnet`               |
   | Assignment       | `Dynamic`                  |

3. Add backend pool with both web VMs, health probe on port 80, and LB rule (port 80 → port 80).

> [!NOTE]
> This is an **Internal** Load Balancer — it has no public IP. Users reach it through the Azure Firewall via DNAT rules.

---

### Phase 6: Deploy Shared Services

#### Step 14: Create Azure Bastion

1. Search **"Bastions"** → **"+ Create"**

   | Field            | Value                |
   |------------------|----------------------|
   | Name             | `hub-bastion`        |
   | Region           | `Central India`      |
   | Virtual network  | `hub-vnet`           |
   | Subnet           | `AzureBastionSubnet` (auto-selected) |
   | Public IP        | **Create new** → `hub-bastion-pip` |

2. Click **"Review + create"** → **"Create"** *(Takes 5–10 minutes)*

#### Step 15: Create Log Analytics Workspace

1. Search **"Log Analytics workspaces"** → **"+ Create"**

   | Field            | Value                |
   |------------------|----------------------|
   | Name             | `hubspoke-logs`      |
   | Resource group   | `hubspoke-dev-rg`    |
   | Region           | `Central India`      |

#### Step 16: Create Azure Key Vault

1. Search **"Key vaults"** → **"+ Create"**

   | Field            | Value                             |
   |------------------|-----------------------------------|
   | Name             | `hubspoke-kv-XXXX` *(globally unique)* |
   | Resource group   | `hubspoke-dev-rg`                 |
   | Region           | `Central India`                   |
   | Pricing tier     | `Standard`                        |

2. After creation, add a secret:
   - Go to **"Secrets"** → **"+ Generate/Import"**
   - Name: `mysql-password`, Value: your MySQL password

---

### Phase 7: Test Everything

#### Step 17: Test Bastion SSH Access

1. Go to **`spoke1-web-vm-1`** → Click **"Connect"** → Select **"Bastion"**
2. Enter username (`azureadmin`) and password
3. A browser SSH terminal opens — you're connected via Bastion through the Hub VNet!

#### Step 18: Verify Firewall Routing

From the Bastion SSH session on `spoke1-web-vm-1`:

```bash
# Check your own web server
curl http://localhost

# Try to reach Spoke 2's MySQL (should connect if firewall rules are correct)
nc -zv <MYSQL_FQDN> 3306

# Try to reach a blocked site (should timeout — firewall blocks it)
curl http://example.com
```

#### Step 19: Check Firewall Logs

1. Go to **`hub-firewall`** → **"Diagnostic settings"** → **"+ Add diagnostic setting"**
2. Send **AzureFirewallNetworkRule** and **AzureFirewallApplicationRule** logs to `hubspoke-logs`
3. After a few minutes, go to **Log Analytics** → **"Logs"** and run:

```kql
AzureDiagnostics
| where Category == "AzureFirewallNetworkRule"
| project TimeGenerated, msg_s
| order by TimeGenerated desc
| take 20
```

---

## 🧹 Clean Up

> [!CAUTION]
> **Azure Firewall (~₹1,000/day) + Bastion (~₹350/day) + VPN Gateway (~₹250/day) = ~₹1,600/day.** Delete the resource group immediately!

```
Search "Resource groups" → click "hubspoke-dev-rg" → "Delete resource group" → confirm
```

---

## 🧠 What Did You Learn?

| Concept                  | What You Practiced                                              |
|--------------------------|-----------------------------------------------------------------|
| Hub-Spoke Architecture   | Enterprise network topology with centralized security          |
| VNet Peering             | Non-transitive peering between hub and spoke VNets             |
| Azure Firewall           | Centralized L3/L4/L7 filtering with FQDN-based rules          |
| Route Tables (UDRs)      | Forcing traffic through a virtual appliance (firewall)         |
| Azure Bastion            | Browser-based SSH without public IPs on VMs                    |
| Internal Load Balancer   | Private LB without public IP (accessed via firewall)           |
| Log Analytics + KQL      | Centralized logging and querying firewall/VM diagnostics       |
| Azure Key Vault          | Storing secrets securely instead of hardcoding                 |
| Network Segmentation     | Full isolation between workload VNets                          |

---

## 🏆 Congratulations!

You've now completed all three scenarios in this Azure learning path:

| Scenario | Level    | Key Skills                                     |
|----------|----------|-------------------------------------------------|
| 1        | Moderate | VNet, Subnet, NSG, LB, VMs, Cloud-Init         |
| 2        | Advanced | AppGW + WAF, VMSS Auto-Scale, Managed MySQL    |
| **3**    | **Expert** | **Hub-Spoke, Firewall, UDR, Peering, Bastion, Key Vault, Log Analytics** |

You now have a solid understanding of Azure networking and compute — from basic VM deployments to enterprise-grade hub-spoke architectures.

---

## 📂 Files

```
Lab03-HubSpoke-Firewall/
├── Lab03-HubSpoke-Firewall-Guide.md  ← You are here
├── generate_diagram.py               ← Regenerate the architecture diagram
└── Lab03-Architecture.png            ← Architecture diagram with Azure icons
```
