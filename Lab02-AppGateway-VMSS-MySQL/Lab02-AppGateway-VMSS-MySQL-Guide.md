# 🧪 Scenario 2: Online Store — Application Gateway + VM Scale Set + Azure MySQL

> **Difficulty:** Advanced &nbsp; | &nbsp; **Time:** 90–120 minutes &nbsp; | &nbsp; **Estimated Cost:** ~₹200–400 (if destroyed within 3 hours)

Build a **3-tier online store** infrastructure that introduces **three major upgrades** over Scenario 1:

| What You Had (Scenario 1)         | What You'll Build Now (Scenario 2)                  |
|-----------------------------------|-----------------------------------------------------|
| Standard Load Balancer (Layer 4)  | **Application Gateway with WAF** (Layer 7)          |
| 2 manually created VMs            | **VM Scale Set** with auto-scaling (2–4 instances)  |
| No database                       | **Azure Database for MySQL** (Managed PaaS)         |

---

## 📐 Architecture Overview

![Scenario 2 Architecture](./Lab02-Architecture.png)

### What You'll Build

| #  | Resource                     | Name                          | Purpose                                            |
|----|------------------------------|-------------------------------|-----------------------------------------------------|
| 1  | Resource Group               | `onlinestore-dev-rg`          | Container for all resources                         |
| 2  | Virtual Network              | `onlinestore-vnet`            | Isolated network (10.2.0.0/16)                      |
| 3  | AppGW Subnet                 | `appgw-subnet`                | Dedicated subnet for Application Gateway            |
| 4  | Web Subnet                   | `web-subnet`                  | Where VMSS instances live                           |
| 5  | Database Subnet              | `db-subnet`                   | Isolated subnet for MySQL (delegated)               |
| 6  | NSG — Web                    | `nsg-web`                     | Allow HTTP from AppGW subnet only                   |
| 7  | NSG — Database               | `nsg-db`                      | Allow MySQL (3306) from web subnet only             |
| 8  | Public IP                    | `onlinestore-appgw-pip`       | Static IP for the Application Gateway               |
| 9  | Application Gateway          | `onlinestore-appgw`           | Layer 7 load balancer with WAF                      |
| 10 | VM Scale Set                 | `onlinestore-vmss`            | Auto-scaling group (2 min, 4 max instances)         |
| 11 | Azure Database for MySQL     | `onlinestore-mysql`           | Managed MySQL Flexible Server                       |
| 12 | Storage Account              | `onlinestorediagXXXX`         | Boot diagnostics                                    |

---

## 📚 New Concepts You'll Learn

<details>
<summary><strong>🔹 Application Gateway vs Load Balancer — What's the Difference?</strong></summary>

| Feature                | Load Balancer (Scenario 1)     | Application Gateway (This Scenario) |
|------------------------|--------------------------------|--------------------------------------|
| **OSI Layer**          | Layer 4 (TCP/UDP)              | Layer 7 (HTTP/HTTPS)                 |
| **Routing**            | By IP + Port only              | By URL path, hostname, headers       |
| **SSL Termination**    | ❌ No                          | ✅ Yes — handles HTTPS for you       |
| **WAF**                | ❌ No                          | ✅ Yes — blocks SQL injection, XSS   |
| **Cookie Affinity**    | ❌ No                          | ✅ Yes — sticky sessions             |
| **URL Rewriting**      | ❌ No                          | ✅ Yes                               |
| **Cost**               | ~₹1,500/mo                    | ~₹7,000/mo (WAF v2)                 |

**When to use which?**
- Need simple TCP load balancing? → **Load Balancer**
- Need URL-based routing, SSL offloading, or WAF? → **Application Gateway**

</details>

<details>
<summary><strong>🔹 What is a VM Scale Set (VMSS)?</strong></summary>

A VMSS is a group of **identical VMs** that can **automatically grow or shrink** based on demand.

**In Scenario 1**, you manually created 2 VMs. If traffic spikes, you'd have to manually create more.

**With VMSS:**
- Set minimum instances = 2, maximum = 4
- Define a rule: "If average CPU > 70% for 5 minutes → add 1 VM"
- Define another rule: "If average CPU < 30% for 10 minutes → remove 1 VM"
- Azure handles the rest automatically!

**Think of it as:** Instead of hiring employees manually, you have a staffing agency that adds or removes people based on workload.

</details>

<details>
<summary><strong>🔹 What is Azure Database for MySQL (Flexible Server)?</strong></summary>

Instead of installing MySQL on a VM yourself (and managing backups, updates, scaling, etc.), Azure gives you a **fully managed MySQL server**.

| You handle              | Azure handles                    |
|-------------------------|----------------------------------|
| Database schema         | OS patching                      |
| Queries                 | Automated backups (7–35 days)    |
| Connection strings      | High availability                |
| App code                | Scaling (compute + storage)      |

**Why use it?** Zero maintenance. You focus on your app, Azure keeps MySQL running.

</details>

<details>
<summary><strong>🔹 What is Subnet Delegation?</strong></summary>

Some Azure PaaS services (like MySQL Flexible Server) need to **own** a subnet — they inject their resources into it. This is called **delegation**.

When you delegate `db-subnet` to `Microsoft.DBforMySQL/flexibleServers`:
- Only MySQL resources can live in that subnet
- Azure automatically configures the networking
- No other VMs or services can be placed there

</details>

<details>
<summary><strong>🔹 What is a WAF (Web Application Firewall)?</strong></summary>

A WAF sits in front of your web application and inspects every HTTP request for attacks:
- **SQL Injection:** `' OR 1=1 --` in form fields
- **Cross-Site Scripting (XSS):** `<script>alert('hacked')</script>`
- **Path Traversal:** `../../etc/passwd`

The Application Gateway WAF v2 uses **OWASP Core Rule Set 3.2** — a battle-tested set of rules used by enterprises worldwide.

</details>

---

## 🚀 Step-by-Step Instructions

> **💡 Tip:** Delete your Scenario 1 resources first to keep costs down: delete the `portfolio-dev-rg` resource group if you haven't already.

---

### Step 1: Create the Resource Group

1. Search for **"Resource groups"** → Click **"+ Create"**
2. Fill in:

   | Field            | Value                    |
   |------------------|--------------------------|
   | Subscription     | *Your subscription*      |
   | Resource group   | `onlinestore-dev-rg`     |
   | Region           | `Central India`          |

3. Click **"Review + create"** → **"Create"**

---

### Step 2: Create the Virtual Network with 3 Subnets

1. Search for **"Virtual networks"** → Click **"+ Create"**
2. **Basics tab:**

   | Field            | Value                   |
   |------------------|-------------------------|
   | Resource group   | `onlinestore-dev-rg`    |
   | Name             | `onlinestore-vnet`      |
   | Region           | `Central India`         |

3. **IP Addresses tab:**
   - Set the IPv4 address space to: **`10.2.0.0/16`**
   - Delete the default subnet, then add these 3 subnets:

   | Subnet Name     | Address Range     | Notes                           |
   |-----------------|-------------------|---------------------------------|
   | `appgw-subnet`  | `10.2.0.0/24`     | Dedicated for Application Gateway |
   | `web-subnet`    | `10.2.1.0/24`     | For VM Scale Set instances       |
   | `db-subnet`     | `10.2.2.0/24`     | Will be delegated to MySQL later |

> [!IMPORTANT]
> **Application Gateway requires its own dedicated subnet.** No other resources can live in `appgw-subnet`. This is an Azure hard requirement.

4. Click **"Review + create"** → **"Create"**

---

### Step 3: Delegate the Database Subnet to MySQL

The MySQL Flexible Server needs subnet delegation configured before creation.

1. Go to your **`onlinestore-vnet`** → Click **"Subnets"** in the left menu
2. Click on **`db-subnet`**
3. Under **"Subnet delegation"**, select: **`Microsoft.DBforMySQL/flexibleServers`**
4. Click **"Save"**

---

### Step 4: Create the Network Security Groups

#### NSG 1: Web NSG

1. Search for **"Network security groups"** → Click **"+ Create"**
2. Name: **`nsg-web`**, Resource Group: `onlinestore-dev-rg`, Region: `Central India`
3. After creation, add inbound rules:

   | Rule Name             | Priority | Port | Source               | Action |
   |-----------------------|----------|------|----------------------|--------|
   | `Allow-HTTP-from-AppGW` | 100    | 80   | `10.2.0.0/24`        | Allow  |
   | `Allow-HTTPS-from-AppGW`| 110    | 443  | `10.2.0.0/24`        | Allow  |
   | `Allow-AppGW-Health`  | 120      | 65200-65535 | `GatewayManager` | Allow  |

> [!WARNING]
> The **`Allow-AppGW-Health`** rule on ports 65200–65535 is **mandatory** for Application Gateway to function. Without it, the AppGW will show as unhealthy and won't route traffic!

4. Associate **`nsg-web`** with `web-subnet`

#### NSG 2: Database NSG

1. Create **`nsg-db`** in the same resource group
2. Add one inbound rule:

   | Rule Name                | Priority | Port  | Source          | Action |
   |--------------------------|----------|-------|-----------------|--------|
   | `Allow-MySQL-from-Web`   | 100      | 3306  | `10.2.1.0/24`   | Allow  |

3. Associate **`nsg-db`** with `db-subnet`

> [!NOTE]
> Notice how `nsg-db` only allows port 3306 from the web subnet CIDR (`10.2.1.0/24`). This means no one on the internet — and nothing outside the web subnet — can reach your database. This is called **network segmentation** and it's a critical security practice.

---

### Step 5: Create the Azure Database for MySQL

1. Search for **"Azure Database for MySQL flexible servers"** → Click **"+ Create"**
2. Fill in:

   | Field                 | Value                           |
   |-----------------------|---------------------------------|
   | Resource group        | `onlinestore-dev-rg`            |
   | Server name           | `onlinestore-mysql` *(must be globally unique — add random digits if taken)* |
   | Region                | `Central India`                 |
   | MySQL version         | `8.0`                           |
   | Workload type         | `For development or hobby projects` (cheapest) |
   | Compute + storage     | `Burstable, Standard_B1s`       |
   | Admin username        | `mysqladmin`                    |
   | Password              | *Choose a strong password*      |

3. **Networking tab:**

   | Field                 | Value                           |
   |-----------------------|---------------------------------|
   | Connectivity method   | `Private access (VNet Integration)` |
   | Virtual network       | `onlinestore-vnet`              |
   | Subnet                | `db-subnet` *(delegated)*       |
   | Private DNS zone      | `Create new` → accept default   |

> [!IMPORTANT]
> Choose **Private access** — NOT public access. This ensures MySQL is only reachable from within the VNet, never from the internet.

4. Click **"Review + create"** → **"Create"** *(This takes 5–10 minutes)*

---

### Step 6: Create the VM Scale Set

1. Search for **"Virtual machine scale sets"** → Click **"+ Create"**
2. **Basics tab:**

   | Field                    | Value                                     |
   |--------------------------|-------------------------------------------|
   | Resource group           | `onlinestore-dev-rg`                      |
   | Scale set name           | `onlinestore-vmss`                        |
   | Region                   | `Central India`                           |
   | Availability zone        | `None`                                    |
   | Orchestration mode       | `Uniform`                                 |
   | Image                    | **"See all images"** → search `Ubuntu Server 22.04 LTS` by **Canonical** → select **x64 Gen2** |
   | Size                     | `Standard_B1s`                            |
   | Authentication           | `Password`                                |
   | Username                 | `azureadmin`                              |
   | Password                 | *Choose a strong password*                |

3. **Networking tab:**

   | Field                    | Value                                     |
   |--------------------------|-------------------------------------------|
   | Virtual network          | `onlinestore-vnet`                        |
   | Subnet                   | `web-subnet`                              |
   | Network interface NIC NSG| `None` (subnet NSG handles this)          |
   | Public IP per instance   | `Disabled`                                |

4. **Scaling tab:**

   | Field                    | Value         |
   |--------------------------|---------------|
   | Initial instance count   | `2`           |
   | Scaling policy           | `Custom`      |
   | Minimum instances        | `2`           |
   | Maximum instances        | `4`           |

   Add a **Scale-Out rule** (add instances):
   | Field                 | Value                      |
   |-----------------------|----------------------------|
   | Metric source         | `Current scale set`        |
   | Metric name           | `Percentage CPU`           |
   | Operator              | `Greater than`             |
   | Threshold             | `70`                       |
   | Duration (minutes)    | `5`                        |
   | Operation             | `Increase count by`        |
   | Instance count        | `1`                        |
   | Cool down (minutes)   | `5`                        |

   Add a **Scale-In rule** (remove instances):
   | Field                 | Value                      |
   |-----------------------|----------------------------|
   | Metric name           | `Percentage CPU`           |
   | Operator              | `Less than`                |
   | Threshold             | `30`                       |
   | Duration (minutes)    | `10`                       |
   | Operation             | `Decrease count by`        |
   | Instance count        | `1`                        |
   | Cool down (minutes)   | `5`                        |

5. **Advanced tab → Custom data:**

   ```yaml
   #cloud-config
   package_update: true
   packages:
     - nginx
     - mysql-client-core-8.0
   runcmd:
     - systemctl enable nginx
     - systemctl start nginx
     - |
       cat > /var/www/html/index.html << 'EOF'
       <!DOCTYPE html>
       <html>
       <head><title>Online Store</title></head>
       <body style="font-family:Arial;text-align:center;padding:50px;background:#0f0c29;color:#e0e0e0">
         <h1>🛒 Online Store</h1>
         <p>Served by VMSS instance: <strong>$(hostname)</strong></p>
         <p>AppGW + VMSS + Azure MySQL</p>
       </body>
       </html>
       EOF
     - systemctl restart nginx
   ```

6. Click **"Review + create"** → **"Create"**

---

### Step 7: Create the Public IP for Application Gateway

1. Search for **"Public IP addresses"** → Click **"+ Create"**
2. Fill in:

   | Field            | Value                        |
   |------------------|------------------------------|
   | Resource group   | `onlinestore-dev-rg`         |
   | Name             | `onlinestore-appgw-pip`      |
   | SKU              | `Standard`                   |
   | Assignment       | `Static`                     |

3. Click **"Create"**

---

### Step 8: Create the Application Gateway

This is the most complex resource in this scenario. Take it step by step.

1. Search for **"Application gateways"** → Click **"+ Create"**
2. **Basics tab:**

   | Field            | Value                        |
   |------------------|------------------------------|
   | Resource group   | `onlinestore-dev-rg`         |
   | Name             | `onlinestore-appgw`          |
   | Region           | `Central India`              |
   | Tier             | `WAF V2`                     |
   | Enable autoscaling | `No` (for cost control)    |
   | Instance count   | `1`                          |
   | WAF Policy       | `Create new` → name it `onlinestore-waf-policy`, set Mode to **Detection** |
   | Virtual network  | `onlinestore-vnet`           |
   | Subnet           | `appgw-subnet`               |

3. **Frontends tab:**

   | Field            | Value                        |
   |------------------|------------------------------|
   | Frontend IP type | `Public`                     |
   | Public IP        | `onlinestore-appgw-pip`      |

4. **Backends tab:**
   - Click **"Add a backend pool"**

   | Field            | Value                        |
   |------------------|------------------------------|
   | Name             | `vmss-backend-pool`          |
   | Target type      | `Virtual machine scale set`  |
   | Target           | `onlinestore-vmss`           |

5. **Configuration tab:**
   - Click **"+ Add a routing rule"**

   **Listener settings:**
   | Field            | Value              |
   |------------------|--------------------|
   | Rule name        | `http-routing-rule` |
   | Priority         | `100`              |
   | Listener name    | `http-listener`    |
   | Frontend IP      | `Public`           |
   | Protocol         | `HTTP`             |
   | Port             | `80`               |

   **Backend targets:**
   | Field                | Value                  |
   |----------------------|------------------------|
   | Target type          | `Backend pool`         |
   | Backend target       | `vmss-backend-pool`    |
   | Backend settings     | `Add new`              |

   **HTTP Settings (click "Add new"):**
   | Field                    | Value          |
   |--------------------------|----------------|
   | Settings name            | `http-settings` |
   | Backend protocol         | `HTTP`         |
   | Backend port             | `80`           |
   | Request time-out         | `30`           |
   | Override with new host name | `No`        |

6. Click **"Review + create"** → **"Create"** *(Takes 5–10 minutes)*

---

### Step 9: Test Your Deployment 🎉

1. Go to the **`onlinestore-appgw-pip`** Public IP resource → copy the IP address
2. Open your browser: `http://<YOUR_APPGW_IP>`
3. You should see the **"🛒 Online Store"** page with the VMSS hostname

```powershell
# Test from PowerShell
1..10 | ForEach-Object { (Invoke-WebRequest -Uri "http://<YOUR_IP>" -UseBasicParsing -DisableKeepAlive).Content }
```

---

### Step 10: Test Auto-Scaling (Bonus Challenge) 🔥

SSH into a VMSS instance (via Run Command in portal) and stress the CPU:

1. Go to **Virtual machine scale sets** → `onlinestore-vmss` → **Instances**
2. Click on an instance → **Run command** → **RunShellScript**
3. Run:
   ```bash
   sudo apt-get install stress -y
   stress --cpu 4 --timeout 300
   ```
4. Go to **Monitor** → **Metrics** → Select your VMSS → Chart `Percentage CPU`
5. Watch the CPU spike above 70% and wait ~5 minutes
6. Go back to **Instances** — you should see a 3rd (and maybe 4th) instance spinning up!

---

## 🧹 Clean Up

> [!CAUTION]
> **Application Gateway WAF v2 costs ~₹500/day.** Delete immediately after practicing!

1. Search for **"Resource groups"** → Click **`onlinestore-dev-rg`**
2. Click **"Delete resource group"** → Type the name → Click **"Delete"**

---

## 🧠 What Did You Learn?

| Concept                   | What You Practiced                                              |
|---------------------------|-----------------------------------------------------------------|
| Application Gateway       | Layer 7 load balancing with URL routing and WAF                |
| WAF (Web Application FW)  | Protecting web apps from OWASP Top 10 attacks                  |
| VM Scale Set (VMSS)        | Auto-scaling compute based on CPU metrics                      |
| Auto-Scale Rules           | Scale-out and scale-in policies with cooldown periods          |
| Azure Database for MySQL   | Managed PaaS database with private VNet integration            |
| Subnet Delegation          | Reserving a subnet for a specific Azure PaaS service           |
| Network Segmentation       | Using NSGs to restrict DB access to the web tier only          |
| AppGW Health Probes         | Port 65200–65535 requirement for Gateway Manager               |

---

## 📂 Files

```
Lab02-AppGateway-VMSS-MySQL/
├── Lab02-AppGateway-VMSS-MySQL-Guide.md  ← You are here
├── generate_diagram.py                   ← Regenerate the architecture diagram
└── Lab02-Architecture.png                ← Architecture diagram with Azure icons
```
