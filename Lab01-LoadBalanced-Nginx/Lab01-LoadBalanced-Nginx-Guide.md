# 🧪 Azure Portal Practice Lab — Deploy a High-Availability Nginx Website

> **Difficulty:** Moderate &nbsp; | &nbsp; **Time:** 60–90 minutes &nbsp; | &nbsp; **Cost:** ~₹50–100 (if destroyed within 2 hours)

This is a **hands-on practice scenario** designed for you to build entirely through the **Azure Portal** (web UI). You'll deploy a load-balanced Nginx website on two VMs — similar to the Terraform project you already have, but this time you'll click through every resource manually to deeply understand what each one does.

---

## 📐 Architecture Overview

![Architecture Diagram](./Lab01-Architecture.png)

### What You'll Build

| #  | Resource                    | Name                        | Purpose                                          |
|----|-----------------------------|-----------------------------|--------------------------------------------------|
| 1  | Resource Group              | `portfolio-dev-rg`          | Container that holds all your resources           |
| 2  | Virtual Network             | `portfolio-vnet`            | Your private network in Azure (10.1.0.0/16)       |
| 3  | Web Subnet                  | `web-subnet`                | Where your web VMs live (10.1.1.0/24)             |
| 4  | Management Subnet           | `mgmt-subnet`               | For secure management access (10.1.2.0/24)        |
| 5  | NSG — Web                   | `nsg-web`                   | Firewall allowing HTTP/HTTPS to web VMs           |
| 6  | NSG — Management            | `nsg-mgmt`                  | Firewall allowing SSH only                        |
| 7  | Availability Set            | `portfolio-avset`           | Spreads VMs across fault domains for HA           |
| 8  | VM 1                        | `web-vm-1`                  | Ubuntu 22.04 + Nginx                              |
| 9  | VM 2                        | `web-vm-2`                  | Ubuntu 22.04 + Nginx                              |
| 10 | Public IP                   | `portfolio-lb-pip`          | Static IP for the Load Balancer                   |
| 11 | Load Balancer               | `portfolio-lb`              | Distributes traffic across both VMs               |
| 12 | Health Probe                | `http-health-probe`         | Checks if VMs are alive (GET / every 5s)          |
| 13 | LB Rule                     | `http-lb-rule`              | Maps port 80 → backend pool                       |
| 14 | Storage Account             | `portfoliodiagXXXX`         | Stores boot diagnostic logs                       |

### Traffic Flow

```
End User (Browser)
      │
      ▼
  Public IP (Static)
      │
      ▼
  Load Balancer
      │
      ├── Health Probe checks each VM every 5 seconds
      │
      ▼
  ┌─────────┐    ┌─────────┐
  │ Web-VM-1 │    │ Web-VM-2 │
  │  Nginx   │    │  Nginx   │
  └─────────┘    └─────────┘
```

---

## 📚 Before You Start — Key Concepts

If any of these terms are new, read this section first. If you already understand them from the Terraform project, skip to the steps.

<details>
<summary><strong>🔹 What is a Resource Group?</strong></summary>

Think of it as a **folder** that contains all your Azure resources. When you delete the Resource Group, everything inside gets deleted too — perfect for learning since you can clean up easily.

**Real-world analogy:** A project folder on your laptop that contains all files for that project.
</details>

<details>
<summary><strong>🔹 What is a Virtual Network (VNet)?</strong></summary>

A VNet is your **private network** inside Azure. It's like having your own isolated data center network. Resources inside a VNet can talk to each other, but the outside world can't reach them unless you explicitly allow it.

- **Address Space:** `10.1.0.0/16` gives you 65,536 IP addresses to work with
- **Think of it as:** Your home Wi-Fi network, but in the cloud

</details>

<details>
<summary><strong>🔹 What is a Subnet?</strong></summary>

A Subnet is a **section** of your VNet. You divide your VNet into subnets to organize and secure traffic.

- **Web Subnet** (`10.1.1.0/24` = 256 IPs): Where your public-facing web servers live
- **Mgmt Subnet** (`10.1.2.0/24` = 256 IPs): Where management/admin tools live
- **Think of it as:** Different rooms in your house — the living room (public) vs. your office (private)

</details>

<details>
<summary><strong>🔹 What is a Network Security Group (NSG)?</strong></summary>

An NSG is a **virtual firewall** that controls what traffic can enter or leave a subnet (or a NIC). You define rules like:

- "Allow HTTP (port 80) from anywhere" → Priority 100
- "Allow SSH (port 22) from my IP only" → Priority 110
- "Deny everything else" → Priority 4096

**Lower priority number = higher precedence.** Azure evaluates rules from lowest number to highest.

</details>

<details>
<summary><strong>🔹 What is an Availability Set?</strong></summary>

An Availability Set ensures your VMs are distributed across:
- **Fault Domains (FD):** Different physical server racks → protects against hardware failure
- **Update Domains (UD):** Different maintenance groups → protects during Azure updates

With FD=2 and UD=5, if one rack fails, only one VM goes down — the other stays up.

**Think of it as:** Don't put all your eggs in one basket.

</details>

<details>
<summary><strong>🔹 What is a Load Balancer?</strong></summary>

A Load Balancer distributes incoming traffic across multiple VMs. Key components:

| Component        | Purpose                                                |
|------------------|--------------------------------------------------------|
| **Frontend IP**  | The public IP that users connect to                    |
| **Backend Pool** | The group of VMs that receive traffic                  |
| **Health Probe** | Periodically checks if each VM is alive                |
| **LB Rule**      | Maps frontend port → backend port                      |
| **Outbound Rule**| Allows VMs to reach the internet (for apt-get, etc.)   |

If a VM fails the health check, the LB stops sending traffic to it automatically.

</details>

---

## 🚀 Step-by-Step Instructions

> **💡 Tip:** Open the [Azure Portal](https://portal.azure.com) in your browser before starting.

---

### Step 1: Create the Resource Group

The Resource Group is the container for everything. **Always create this first.**

1. In the Azure Portal, search for **"Resource groups"** in the top search bar
2. Click **"+ Create"**
3. Fill in:

   | Field            | Value                 |
   |------------------|-----------------------|
   | Subscription     | *Your subscription*   |
   | Resource group   | `portfolio-dev-rg`    |
   | Region           | `Central India`       |

4. Click **"Review + create"** → **"Create"**

> [!TIP]
> Always use the **same region** for all resources in a lab. Cross-region traffic costs money and adds latency.

---

### Step 2: Create the Virtual Network with Subnets

This creates your isolated network and both subnets in one go.

1. Search for **"Virtual networks"** → Click **"+ Create"**
2. **Basics tab:**

   | Field            | Value              |
   |------------------|--------------------|
   | Resource group   | `portfolio-dev-rg` |
   | Name             | `portfolio-vnet`   |
   | Region           | `Central India`    |

3. **IP Addresses tab:**
   - Set the IPv4 address space to: **`10.1.0.0/16`**
   - Delete the `default` subnet if one exists
   - Click **"+ Add a subnet"** and create:

   | Subnet Name   | Address Range     |
   |---------------|-------------------|
   | `web-subnet`  | `10.1.1.0/24`     |
   | `mgmt-subnet` | `10.1.2.0/24`     |

4. Click **"Review + create"** → **"Create"**

> [!NOTE]
> The `/16` VNet gives you 65,536 addresses. Each `/24` subnet uses 256 of those. Azure reserves 5 IPs per subnet for internal use, so you actually get 251 usable IPs per subnet.

---

### Step 3: Create the Network Security Groups

You'll create two NSGs — one for each subnet.

#### NSG 1: Web NSG (allows web traffic)

1. Search for **"Network security groups"** → Click **"+ Create"**
2. Fill in:

   | Field            | Value              |
   |------------------|--------------------|
   | Resource group   | `portfolio-dev-rg` |
   | Name             | `nsg-web`          |
   | Region           | `Central India`    |

3. Click **"Review + create"** → **"Create"**
4. Once created, go to the resource → Click **"Inbound security rules"** in the left menu
5. Add these rules by clicking **"+ Add"** for each:

   | Rule Name         | Priority | Port | Protocol | Source | Action |
   |-------------------|----------|------|----------|--------|--------|
   | `Allow-HTTP`      | 100      | 80   | TCP      | Any    | Allow  |
   | `Allow-HTTPS`     | 110      | 443  | TCP      | Any    | Allow  |
   | `Allow-SSH`       | 120      | 22   | TCP      | Any    | Allow  |

> [!WARNING]
> In production, **never** set SSH source to "Any". Restrict it to your IP address. For this lab, "Any" is fine since we'll delete everything after.

#### NSG 2: Management NSG (SSH only)

1. Create another NSG named **`nsg-mgmt`** in the same Resource Group
2. Add one inbound rule:

   | Rule Name    | Priority | Port | Protocol | Source | Action |
   |--------------|----------|------|----------|--------|--------|
   | `Allow-SSH`  | 100      | 22   | TCP      | Any    | Allow  |

#### Associate NSGs with Subnets

1. Go to your **`nsg-web`** resource → Click **"Subnets"** in the left menu
2. Click **"+ Associate"** → Select `portfolio-vnet` → Select `web-subnet` → Click **"OK"**
3. Repeat for **`nsg-mgmt`**: Associate it with `mgmt-subnet`

---

### Step 4: Create the Availability Set

1. Search for **"Availability sets"** → Click **"+ Create"**
2. Fill in:

   | Field                   | Value                |
   |-------------------------|----------------------|
   | Resource group          | `portfolio-dev-rg`   |
   | Name                    | `portfolio-avset`    |
   | Region                  | `Central India`      |
   | Fault domains           | `2`                  |
   | Update domains          | `5`                  |
   | Use managed disks       | `Yes`                |

3. Click **"Review + create"** → **"Create"**

> [!IMPORTANT]
> You **must** create the Availability Set **before** creating the VMs. You cannot add a VM to an Availability Set after creation.

---

### Step 5: Create VM 1 — Web Server

1. Search for **"Virtual machines"** → Click **"+ Create"** → **"Azure Virtual Machine"**
2. **Basics tab:**

   | Field                   | Value                                  |
   |-------------------------|----------------------------------------|
   | Resource group          | `portfolio-dev-rg`                     |
   | Virtual machine name    | `web-vm-1`                             |
   | Region                  | `Central India`                        |
   | Availability options    | `Availability set`                     |
   | Availability set        | `portfolio-avset`                      |
   | Image                   | *(See image selection steps below)*    |
   | Size                    | `Standard_B1s` (1 vCPU, 1 GB RAM)     |
   | Authentication type     | `Password`                             |
   | Username                | `azureadmin`                           |
   | Password                | *Choose a strong password*             |

   **⚠️ Selecting the correct Image (important!):**
   1. In the **Image** dropdown, click **"See all images"**
   2. In the Marketplace search bar, type **`Ubuntu Server`**
   3. Find **"Ubuntu Server 22.04 LTS"** published by **Canonical** (look for the Canonical logo)
   4. Click the **"Select"** dropdown on that card → Choose **"Ubuntu Server 22.04 LTS - x64 Gen2"**
   5. If 22.04 is unavailable in your region, select **"Ubuntu Server 24.04 LTS"** by Canonical instead

   > [!CAUTION]
   > **Do NOT** type the image name manually in the dropdown — always use **"See all images"** to browse the Marketplace. Typing can select community/shared images with invalid publishers, causing a `imageReference.publisher is invalid` deployment error.

3. **Disks tab:**

   | Field              | Value           |
   |--------------------|-----------------|
   | OS disk type       | `Standard SSD`  |
   | OS disk size       | `30 GiB`        |

4. **Networking tab:**

   | Field                      | Value              |
   |----------------------------|--------------------|
   | Virtual network            | `portfolio-vnet`   |
   | Subnet                     | `web-subnet`       |
   | Public IP                  | `None`             |
   | NIC NSG                    | `None` (subnet NSG handles this) |

> [!NOTE]
> We set Public IP to **None** because all traffic will come through the Load Balancer. The VMs don't need their own public IPs.

5. **Management tab:**

   | Field                      | Value    |
   |----------------------------|----------|
   | Boot diagnostics           | `Enable with managed storage account` |

6. **Advanced tab:**
   - Scroll down to **"Custom data"** (cloud-init)
   - Paste this script:

   ```yaml
   #cloud-config
   package_update: true
   packages:
     - nginx
   runcmd:
     - systemctl enable nginx
     - systemctl start nginx
     - echo '<html><head><title>Portfolio</title></head><body style="font-family:Arial;text-align:center;padding:50px;background:#1a1a2e;color:#e0e0e0"><h1>Hello from Web-VM-1!</h1><p>Nginx on Azure</p></body></html>' > /var/www/html/index.html
     - systemctl restart nginx
   ```

7. Click **"Review + create"** → **"Create"**

---

### Step 6: Create VM 2 — Web Server

Repeat **Step 5** with these changes:

| Field                | Value        |
|----------------------|--------------|
| Virtual machine name | `web-vm-2`   |
| Custom data hostname | Change `Web-VM-1` to `Web-VM-2` in the HTML |

> [!TIP]
> Having different text on each VM's page lets you verify the Load Balancer is actually distributing traffic. Refresh the page multiple times — you should see it alternate between VM-1 and VM-2.

---

### Step 7: Create the Public IP for the Load Balancer

1. Search for **"Public IP addresses"** → Click **"+ Create"**
2. Fill in:

   | Field            | Value                |
   |------------------|----------------------|
   | Resource group   | `portfolio-dev-rg`   |
   | Name             | `portfolio-lb-pip`   |
   | Region           | `Central India`      |
   | SKU              | `Standard`           |
   | Tier             | `Regional`           |
   | Assignment       | `Static`             |

3. Click **"Create"**

> [!IMPORTANT]
> The Public IP **must** be **Standard** SKU to work with a Standard Load Balancer. Basic and Standard SKUs cannot be mixed.

---

### Step 8: Create the Load Balancer

1. Search for **"Load balancers"** → Click **"+ Create"**
2. **Basics tab:**

   | Field            | Value                |
   |------------------|----------------------|
   | Resource group   | `portfolio-dev-rg`   |
   | Name             | `portfolio-lb`       |
   | Region           | `Central India`      |
   | SKU              | `Standard`           |
   | Type             | `Public`             |
   | Tier             | `Regional`           |

3. **Frontend IP configuration tab:**
   - Click **"+ Add a frontend IP configuration"**

   | Field       | Value                          |
   |-------------|--------------------------------|
   | Name        | `web-frontend`                 |
   | Public IP   | Select `portfolio-lb-pip`      |

4. **Backend pools tab:**
   - Click **"+ Add a backend pool"**

   | Field                | Value                          |
   |----------------------|--------------------------------|
   | Name                 | `web-backend-pool`             |
   | Virtual network      | `portfolio-vnet`               |
   | Backend Pool Config  | `NIC`                          |
   | IP Configurations    | Add `web-vm-1` and `web-vm-2`  |

5. **Inbound rules tab:**
   - Click **"+ Add a load balancing rule"**

   | Field                    | Value                      |
   |--------------------------|----------------------------|
   | Name                     | `http-lb-rule`             |
   | Frontend IP              | `web-frontend`             |
   | Backend pool             | `web-backend-pool`         |
   | Protocol                 | `TCP`                      |
   | Frontend port            | `80`                       |
   | Backend port             | `80`                       |
   | Health probe             | *Create new (see below)*   |
   | Session persistence      | `None`                     |
   | Idle timeout             | `4 minutes`                |

   For the **Health Probe**, click "Create new":

   | Field               | Value                |
   |---------------------|----------------------|
   | Name                | `http-health-probe`  |
   | Protocol            | `HTTP`               |
   | Port                | `80`                 |
   | Path                | `/`                  |
   | Interval            | `5` seconds          |
   | Unhealthy threshold | `2`                  |

6. **Outbound rules tab:**
   - Click **"+ Add an outbound rule"**

   | Field                    | Value                      |
   |--------------------------|----------------------------|
   | Name                     | `allow-outbound`           |
   | Frontend IP              | `web-frontend`             |
   | Backend pool             | `web-backend-pool`         |
   | Protocol                 | `All`                      |

> [!NOTE]
> The **Outbound Rule** is essential! Without it, your VMs behind a Standard LB cannot reach the internet (needed for `apt-get` during cloud-init).

7. Click **"Review + create"** → **"Create"**

---

### Step 9: Test Your Deployment! 🎉

1. Go to your **`portfolio-lb-pip`** Public IP resource
2. Copy the **IP address** shown
3. Open your browser and navigate to: `http://<YOUR_IP_ADDRESS>`
4. You should see **"Hello from Web-VM-1!"** or **"Hello from Web-VM-2!"**
5. **Refresh several times** — the page should alternate between the two VMs

```
✅ If you see the page → Congratulations! Your load-balanced setup is working!
❌ If it doesn't load → Wait 2-3 minutes for cloud-init to finish installing Nginx
```

---

### Step 10: Verify Load Balancing

To confirm the LB is actually distributing traffic, open PowerShell and run:

```powershell
# Hit the endpoint 10 times and see which VM responds
1..10 | ForEach-Object { (Invoke-WebRequest -Uri "http://<YOUR_IP>" -UseBasicParsing).Content }
```

You should see responses from both `Web-VM-1` and `Web-VM-2`.

---

### Step 11: SSH into Your VMs (Optional)

Since the VMs don't have public IPs, you need to create **Inbound NAT Rules** on the LB:

1. Go to your **`portfolio-lb`** → Click **"Inbound NAT rules"**
2. Click **"+ Add"** and create:

   | Rule       | Frontend Port | Target VM  | Backend Port |
   |------------|---------------|------------|--------------|
   | `ssh-vm1`  | `50001`       | `web-vm-1` | `22`         |
   | `ssh-vm2`  | `50002`       | `web-vm-2` | `22`         |

3. Now SSH using:

```bash
# Connect to VM-1
ssh -p 50001 azureadmin@<LB_PUBLIC_IP>

# Connect to VM-2
ssh -p 50002 azureadmin@<LB_PUBLIC_IP>
```

---

## 🧹 Step 12: CLEAN UP — Delete Everything

> [!CAUTION]
> **This is the most important step!** Azure charges for running resources. If you forget to delete, you'll be billed ~₹3,000/month.

1. Search for **"Resource groups"** in the portal
2. Click on **`portfolio-dev-rg`**
3. Click **"Delete resource group"** at the top
4. Type the resource group name to confirm → Click **"Delete"**

This deletes **everything** inside — VMs, VNet, LB, Public IP, all of it. Clean slate.

---

## 🧠 What Did You Learn?

After completing this lab, you should be able to explain:

| Concept              | What You Practiced                                      |
|----------------------|---------------------------------------------------------|
| Resource Groups      | Organizing all resources in a single container          |
| Virtual Networks     | Creating an isolated network with custom address space  |
| Subnets              | Segmenting a VNet into web and management tiers         |
| NSGs                 | Writing firewall rules (allow HTTP, deny the rest)      |
| Availability Sets    | Distributing VMs across fault/update domains            |
| VMs + Cloud-Init     | Deploying Ubuntu VMs with automatic Nginx installation  |
| Load Balancer        | Distributing traffic + health probing + outbound rules  |
| NAT Rules            | Accessing VMs without public IPs via port forwarding    |

---

## 💡 Bonus Challenges

Once you've completed the basic lab, try these extensions:

### Challenge 1: Add Azure Monitor
1. Go to **"Monitor"** → **"Alerts"** → Create an alert rule
2. Target your VMs, set condition to "CPU > 80% for 5 minutes"
3. Create an Action Group that sends you an email

### Challenge 2: Add a Storage Account for Static Content
1. Create a Storage Account with blob access
2. Upload images to a blob container
3. Modify the Nginx config on VMs to proxy to the blob storage URL

### Challenge 3: Simulate a Failure
1. Stop `web-vm-1` from the portal (click "Stop")
2. Refresh your website — it should still work (served by VM-2 only)
3. Check the Load Balancer metrics to see the health probe marked VM-1 as unhealthy
4. Start VM-1 again — the LB should automatically add it back

---

## 🆚 Portal vs Terraform — What Did You Notice?

| Aspect              | Portal (This Lab)                        | Terraform (Your Other Project)             |
|---------------------|------------------------------------------|--------------------------------------------|
| **Speed**           | Slower — lots of clicking                | Faster — one `terraform apply`             |
| **Repeatability**   | Hard to reproduce exactly                | 100% reproducible from code                |
| **Learning**        | ✅ Great for understanding each resource | Less visual, more abstract                 |
| **Error-prone**     | Easy to miss a setting                   | Validated before deployment                |
| **Documentation**   | Screenshots + notes                      | Code IS the documentation                  |
| **Cleanup**         | Delete resource group                    | `terraform destroy`                        |

> [!TIP]
> **Best practice:** Learn via the Portal first (like this lab), then automate with Terraform. This way you understand what Terraform is doing under the hood.

---

## 📂 Files in This Directory

```
Lab01-LoadBalanced-Nginx/
├── Lab01-LoadBalanced-Nginx-Guide.md    ← You are here
├── generate_diagram.py                  ← Python script to regenerate the architecture diagram
└── Lab01-Architecture.png               ← Architecture diagram with Azure icons
```
