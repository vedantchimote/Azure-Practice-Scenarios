# 🧪 Lab 05: Multi-Region High Availability — Azure Front Door + Geo-Replicated SQL

> **Difficulty:** Expert+ &nbsp; | &nbsp; **Time:** 2–3 hours &nbsp; | &nbsp; **Estimated Cost:** ~₹500–1,000 (if destroyed within 3 hours)

This is the **capstone lab** — you'll build the same architecture used by production services that **cannot afford downtime**. Your application will survive an **entire Azure region going offline**, automatically failing over to a secondary region with zero user intervention.

---

## 🌍 Why Multi-Region?

| Scenario                          | Single Region (Labs 1–4)        | Multi-Region (This Lab)            |
|-----------------------------------|---------------------------------|------------------------------------|
| Azure Central India goes down     | **Your app is offline** ❌      | Front Door routes to South India ✅ |
| Data center fire                  | Data lost ❌                    | SQL Geo-Replica has your data ✅    |
| Latency for users far from India  | ~200ms from Europe              | <50ms via nearest Front Door POP ✅ |
| RTO (Recovery Time Objective)     | Hours (manual intervention)     | **~60 seconds** (automatic)        |

---

## 📐 Architecture Overview

![Lab 05 Architecture](./Lab05-Architecture.png)

### What You'll Build

| #  | Resource                     | Name                          | Region          | Purpose                              |
|----|------------------------------|-------------------------------|-----------------|----------------------------------------|
| **Global** | | | | |
| 1  | Resource Group               | `multiregion-dev-rg`          | —               | Container for all resources            |
| 2  | Azure Front Door             | `multiregion-fd`              | Global          | Global load balancer + WAF + SSL       |
| **Primary Region** | | | | |
| 3  | App Service Plan             | `primary-plan`                | Central India   | Hosting plan for primary app           |
| 4  | App Service                  | `multiregion-app-primary`     | Central India   | Primary web application                |
| 5  | Azure SQL Server             | `multiregion-sql-primary`     | Central India   | Primary database server                |
| 6  | Azure SQL Database           | `appdb`                       | Central India   | Application database (Read-Write)      |
| 7  | Application Insights         | `insights-primary`            | Central India   | Monitoring for primary                 |
| 8  | Key Vault                    | `multiregion-kv-primary`      | Central India   | Secrets for primary region             |
| **Secondary Region** | | | | |
| 9  | App Service Plan             | `secondary-plan`              | South India     | Hosting plan for secondary app         |
| 10 | App Service                  | `multiregion-app-secondary`   | South India     | Standby web application                |
| 11 | Azure SQL Server             | `multiregion-sql-secondary`   | South India     | Secondary database server              |
| 12 | Azure SQL Database           | `appdb` (Geo-Replica)         | South India     | Read-only replica (auto-synced)        |
| 13 | Application Insights         | `insights-secondary`          | South India     | Monitoring for secondary               |
| 14 | Key Vault                    | `multiregion-kv-secondary`    | South India     | Secrets for secondary region           |
| **Shared** | | | | |
| 15 | Azure Monitor                | `multiregion-monitor`         | —               | Alerts + Action Groups                 |
| 16 | Action Group                 | `critical-alerts`             | —               | Email/SMS notifications on failover    |

**Total: ~16 resources across 2 regions**

---

## 📚 New Concepts You'll Learn

<details>
<summary><strong>🔹 What is Azure Front Door?</strong></summary>

Azure Front Door is a **global Layer 7 load balancer** that operates from Microsoft's edge network (190+ POPs worldwide).

| Feature                    | Application Gateway (Lab 2) | Azure Front Door (This Lab)      |
|----------------------------|-----------------------------|----------------------------------|
| **Scope**                  | Regional (single VNet)      | **Global** (multi-region)        |
| **Edge locations**         | None                        | 190+ worldwide                   |
| **SSL termination**        | Yes (regional)              | Yes (at edge, closer to users)   |
| **WAF**                    | Yes                         | Yes (global WAF policies)        |
| **Health probing**         | Backend VMs                 | **Cross-region** backends        |
| **Failover**               | Within a region             | **Between regions** (auto)       |
| **Caching**                | No                          | Built-in CDN capabilities        |

**How failover works:**
1. Front Door probes both regions every 30 seconds
2. Primary (Central India) is healthy → all traffic goes there
3. Primary goes down → Front Door detects in ~30s
4. Traffic automatically routes to Secondary (South India)
5. Primary comes back → traffic returns to Primary

</details>

<details>
<summary><strong>🔹 What is Azure SQL Geo-Replication?</strong></summary>

Geo-Replication creates a **continuously synchronized read-only copy** of your database in another region.

```
Central India (Primary)          South India (Secondary)
┌─────────────────────┐         ┌─────────────────────┐
│   Azure SQL         │  Async  │   Azure SQL         │
│   Read + Write      │ ──────► │   Read-Only         │
│   appdb             │  Sync   │   appdb (replica)   │
└─────────────────────┘         └─────────────────────┘
```

**Key details:**
- **Async replication** — <5 second lag in typical conditions
- **Automatic failover groups** — Azure handles promotion of secondary to primary
- **Read-scale routing** — send read queries to the replica to reduce primary load
- **RPO (Recovery Point Objective)** — <5 seconds of data loss maximum
- **RTO (Recovery Time Objective)** — ~60 seconds for automatic failover

</details>

<details>
<summary><strong>🔹 What is an Azure App Service?</strong></summary>

App Service is a **fully managed PaaS** for hosting web applications. Unlike VMs (Labs 1–3), you don't manage the OS, patching, or scaling — you just deploy your code.

| Feature          | VMs (Labs 1–3)                    | App Service (This Lab)           |
|------------------|-----------------------------------|----------------------------------|
| **Deployment**   | SSH, install packages, configure  | `git push` or ZIP deploy         |
| **Scaling**      | Manual VMs or VMSS rules          | Slider in portal (1 → 10 instances) |
| **SSL**          | Configure Nginx/Apache manually   | One-click managed certificate    |
| **OS Updates**   | You patch the OS                  | Azure patches automatically      |
| **Custom domains** | Configure DNS + Nginx           | Add in portal + auto-certificate |

**Deployment slots** — a powerful feature you'll use:
- `production` slot: live traffic
- `staging` slot: deploy new code here, test it, then **swap** with production
- Zero-downtime deployments!

</details>

<details>
<summary><strong>🔹 What is an Action Group?</strong></summary>

An Action Group defines **who gets notified and how** when an Azure alert fires:

| Notification Type | Example                                      |
|-------------------|----------------------------------------------|
| Email             | Send to ops-team@company.com                 |
| SMS               | Text to +91-XXXXXXXXXX                       |
| Voice call        | Call the on-call engineer                    |
| Azure App push    | Push notification to Azure mobile app        |
| Webhook           | POST to Slack/Teams/PagerDuty                |
| Azure Function    | Trigger automated remediation                |
| Logic App         | Start an automated workflow                  |

In this lab, you'll set up email alerts for: failover events, high error rates, and slow response times.

</details>

<details>
<summary><strong>🔹 What are RTO and RPO?</strong></summary>

These are the two most important metrics in disaster recovery:

**RTO (Recovery Time Objective):** How quickly you can recover after a failure.
- "Our RTO is 60 seconds" = the app will be back online within 1 minute

**RPO (Recovery Point Objective):** How much data you can afford to lose.
- "Our RPO is 5 seconds" = you might lose the last 5 seconds of database writes

| DR Tier     | RTO        | RPO        | Cost         |
|-------------|------------|------------|--------------|
| Basic       | Hours      | Hours      | Low          |
| Standard    | Minutes    | Minutes    | Medium       |
| **Premium** | **<60s**   | **<5s**    | **High**     |

This lab implements **Premium tier DR** with automatic failover.

</details>

---

## 🚀 Step-by-Step Instructions

> [!CAUTION]
> This lab uses resources in **two regions**. Costs double! App Service S1 × 2 regions + Azure SQL S0 × 2 + Front Door = ~₹500–1,000 for 3 hours. **Plan to complete and delete in one sitting.**

---

### Phase 1: Create the Primary Region

#### Step 1: Create the Resource Group

1. Search **"Resource groups"** → **"+ Create"**

   | Field            | Value                  |
   |------------------|------------------------|
   | Resource group   | `multiregion-dev-rg`   |
   | Region           | `Central India`        |

#### Step 2: Create the Primary Azure SQL Server & Database

1. Search **"SQL databases"** → **"+ Create"**
2. Fill in:

   | Field                    | Value                           |
   |--------------------------|---------------------------------|
   | Resource group           | `multiregion-dev-rg`            |
   | Database name            | `appdb`                         |
   | Server                   | **Create new** ↓                |

   **New server settings:**
   | Field                    | Value                           |
   |--------------------------|---------------------------------|
   | Server name              | `multiregion-sql-primary` *(globally unique)* |
   | Location                 | `Central India`                 |
   | Authentication           | `SQL authentication`            |
   | Admin login              | `sqladmin`                      |
   | Password                 | *Choose a strong password*      |

3. **Compute + storage:** Click **"Configure database"**

   | Field            | Value                   |
   |------------------|-------------------------|
   | Service tier     | `Basic` (5 DTUs) — cheapest for learning |

4. **Networking tab:**

   | Field                    | Value              |
   |--------------------------|--------------------|
   | Connectivity method      | `Public endpoint`  |
   | Allow Azure services     | `Yes`              |
   | Add current client IP    | `Yes`              |

5. Click **"Review + create"** → **"Create"**

**After creation, add sample data:**
1. Go to the database → **"Query editor"** → Login with SQL admin credentials
2. Run:
   ```sql
   CREATE TABLE Tasks (
       Id INT PRIMARY KEY IDENTITY(1,1),
       Title NVARCHAR(200) NOT NULL,
       Status NVARCHAR(50) DEFAULT 'todo',
       CreatedAt DATETIME DEFAULT GETDATE(),
       Region NVARCHAR(50) DEFAULT 'Central India'
   );

   INSERT INTO Tasks (Title, Status) VALUES
   ('Deploy to Azure', 'done'),
   ('Configure Front Door', 'in-progress'),
   ('Set up Geo-Replication', 'todo'),
   ('Test Failover', 'todo');
   ```

#### Step 3: Create the Primary App Service

1. Search **"App services"** → **"+ Create"** → **"Web App"**
2. Fill in:

   | Field                    | Value                                     |
   |--------------------------|-------------------------------------------|
   | Resource group           | `multiregion-dev-rg`                      |
   | Name                     | `multiregion-app-primary` *(globally unique)* |
   | Runtime stack            | `Node.js 20 LTS` (or `.NET 8` / `Python 3.11`) |
   | Region                   | `Central India`                           |
   | App Service Plan         | **Create new** → `primary-plan`           |
   | Pricing plan             | `S1 Standard` (supports slots + scaling)  |

3. **Monitoring tab:**

   | Field                    | Value                |
   |--------------------------|----------------------|
   | Enable App Insights      | `Yes`                |
   | Application Insights     | **Create new** → `insights-primary` |

4. Click **"Review + create"** → **"Create"**

**After creation, deploy a simple health-check app:**
1. Go to your App Service → **"Advanced Tools"** → **"Go"** (opens Kudu)
2. Go to **Debug console** → **CMD** → Navigate to `site/wwwroot`
3. Create `index.html`:

   ```html
   <!DOCTYPE html>
   <html>
   <head><title>Multi-Region App</title></head>
   <body style="font-family:Arial;text-align:center;padding:50px;background:#1a1a2e;color:#e0e0e0">
       <h1>🌍 Multi-Region App</h1>
       <h2 style="color:#4caf50;">Region: Central India (Primary)</h2>
       <p>Served by: multiregion-app-primary</p>
       <p>Status: ✅ Active</p>
       <p id="time"></p>
       <script>document.getElementById('time').textContent = 'Timestamp: ' + new Date().toISOString();</script>
   </body>
   </html>
   ```

4. Verify: Open `https://multiregion-app-primary.azurewebsites.net` in your browser

---

### Phase 2: Create the Secondary Region

#### Step 4: Create the Secondary App Service

Repeat Step 3 but in **South India**:

| Field            | Primary                      | Secondary                      |
|------------------|------------------------------|--------------------------------|
| Name             | `multiregion-app-primary`    | `multiregion-app-secondary`    |
| Region           | Central India                | **South India**                |
| Plan             | `primary-plan`               | `secondary-plan`               |
| App Insights     | `insights-primary`           | `insights-secondary`           |
| HTML heading     | "Central India (Primary)"    | **"South India (Secondary)"**  |
| Status text      | "✅ Active"                  | **"⏳ Standby"**               |

#### Step 5: Set Up SQL Geo-Replication

1. Go to your **`appdb`** database in the primary SQL server
2. In the left menu, under **"Data management"**, click **"Geo-Replication"**
3. Click on the **South India** region on the map (or in the list)
4. Fill in:

   | Field                    | Value                           |
   |--------------------------|---------------------------------|
   | Target server            | **Create new**                  |
   | Server name              | `multiregion-sql-secondary`     |
   | Location                 | `South India`                   |
   | Admin login              | `sqladmin` *(same as primary)*  |
   | Password                 | *Same password as primary*      |

5. Click **"OK"** → Replication begins immediately

> [!NOTE]
> The secondary database is **read-only**. Your secondary App Service can read from it, but all writes must go to the primary. During failover, the secondary is promoted to read-write.

#### Step 6: Create a Failover Group (Automatic Failover)

1. Go to your **primary SQL server** (`multiregion-sql-primary`)
2. In the left menu, click **"Failover groups"** → **"+ Add group"**

   | Field                    | Value                           |
   |--------------------------|---------------------------------|
   | Failover group name      | `multiregion-failover`          |
   | Secondary server         | `multiregion-sql-secondary`     |
   | Read/Write failover policy | `Automatic`                   |
   | Grace period (minutes)   | `1` (minimum)                   |
   | Database                 | Select `appdb`                  |

3. Click **"Create"**

After creation, you get two **listener endpoints**:
- **Read-Write:** `multiregion-failover.database.windows.net` → always points to current primary
- **Read-Only:** `multiregion-failover.secondary.database.windows.net` → always points to replica

> [!IMPORTANT]
> **Use the failover group endpoints in your app — NOT the individual server names.** During failover, Azure automatically updates where these endpoints point. Your app doesn't need to change anything.

---

### Phase 3: Set Up Azure Front Door (Global Load Balancer)

#### Step 7: Create Azure Front Door

1. Search **"Front Doors and CDN profiles"** → **"+ Create"** → Select **"Azure Front Door"** → **"Custom create"**
2. **Basics tab:**

   | Field            | Value                  |
   |------------------|------------------------|
   | Resource group   | `multiregion-dev-rg`   |
   | Name             | `multiregion-fd`       |
   | Tier             | `Standard`             |

3. **Endpoint tab:**
   - Click **"+ Add an endpoint"**
   - Name: `multiregion-endpoint`

4. **Route tab:**
   - Click **"+ Add a route"**

   | Field              | Value                       |
   |--------------------|-----------------------------|
   | Name               | `default-route`             |
   | Endpoint           | `multiregion-endpoint`      |
   | Patterns to match  | `/*`                        |
   | Origin group       | **Add new** ↓               |

   **Origin Group settings:**
   | Field                           | Value          |
   |---------------------------------|----------------|
   | Origin group name               | `app-origins`  |
   | Health probe — Protocol         | `HTTPS`        |
   | Health probe — Path             | `/`            |
   | Health probe — Interval (sec)   | `30`           |

   **Add Origin 1 (Primary):**
   | Field              | Value                                    |
   |--------------------|------------------------------------------|
   | Name               | `primary-origin`                         |
   | Origin type        | `App services`                           |
   | Host name          | `multiregion-app-primary.azurewebsites.net` |
   | Priority           | `1` ← Active                            |
   | Weight             | `1000`                                   |

   **Add Origin 2 (Secondary):**
   | Field              | Value                                    |
   |--------------------|------------------------------------------|
   | Name               | `secondary-origin`                       |
   | Origin type        | `App services`                           |
   | Host name          | `multiregion-app-secondary.azurewebsites.net` |
   | Priority           | `2` ← Standby (only used if primary fails) |
   | Weight             | `1000`                                   |

5. Click **"Review + create"** → **"Create"** *(Takes 5–10 minutes)*

> [!NOTE]
> **Priority 1 vs Priority 2:** Front Door sends all traffic to Priority 1 origins. Priority 2 origins only receive traffic when ALL Priority 1 origins are unhealthy. This is the **Active-Standby** pattern.

---

### Phase 4: Set Up Monitoring & Alerts

#### Step 8: Create an Action Group

1. Search **"Monitor"** → **"Alerts"** → **"Action groups"** → **"+ Create"**

   | Field            | Value                  |
   |------------------|------------------------|
   | Resource group   | `multiregion-dev-rg`   |
   | Action group name| `critical-alerts`      |
   | Display name     | `CriticalAlerts`       |

2. **Notifications tab:**

   | Notification type | Name             | Detail              |
   |-------------------|------------------|----------------------|
   | Email             | `email-alert`    | *Your email address* |

#### Step 9: Create Alert Rules

**Alert 1: Primary App Down**
1. Go to **Monitor** → **"Alerts"** → **"+ Create"** → **"Alert rule"**

   | Field                | Value                              |
   |----------------------|------------------------------------|
   | Scope                | `multiregion-app-primary`          |
   | Condition            | `Metric: Http Server Errors (5xx)` |
   | Operator             | `Greater than`                     |
   | Threshold            | `5`                                |
   | Evaluation period    | `5 minutes`                        |
   | Action group         | `critical-alerts`                  |
   | Alert rule name      | `Primary-App-5xx-Alert`            |
   | Severity             | `Sev 1 - Error`                    |

**Alert 2: SQL Failover Occurred**
1. Create another alert:

   | Field                | Value                              |
   |----------------------|------------------------------------|
   | Scope                | `multiregion-sql-primary`          |
   | Condition            | `Metric: DTU percentage`           |
   | Operator             | `Greater than`                     |
   | Threshold            | `90`                               |
   | Action group         | `critical-alerts`                  |
   | Alert rule name      | `SQL-High-DTU-Alert`               |

---

### Phase 5: Test the Disaster Recovery 🔥

#### Step 10: Verify Normal Operation

1. Get your Front Door URL: Go to `multiregion-fd` → Copy the **Endpoint hostname** (e.g., `multiregion-endpoint-xxxxx.z01.azurefd.net`)
2. Open it in your browser — you should see **"Central India (Primary)"**
3. Test from PowerShell:

   ```powershell
   1..5 | ForEach-Object {
       $response = Invoke-WebRequest -Uri "https://multiregion-endpoint-xxxxx.z01.azurefd.net" -UseBasicParsing
       $response.Content | Select-String -Pattern "Region:.*" | ForEach-Object { $_.Matches.Value }
   }
   ```
   All 5 should say **"Central India (Primary)"**.

#### Step 11: Simulate a Regional Failure

1. Go to **`multiregion-app-primary`** App Service
2. Click **"Stop"** at the top ← this simulates Central India going offline
3. Wait **60–90 seconds** for Front Door's health probe to detect the failure
4. Refresh your browser → You should now see **"South India (Secondary)"** 🎉

```powershell
# Verify failover happened
1..5 | ForEach-Object {
    $response = Invoke-WebRequest -Uri "https://multiregion-endpoint-xxxxx.z01.azurefd.net" -UseBasicParsing
    $response.Content | Select-String -Pattern "Region:.*" | ForEach-Object { $_.Matches.Value }
}
# Should now say "South India (Secondary)"
```

5. Check your email — you should have received an alert from the Action Group!

#### Step 12: Recover (Failback)

1. Go to **`multiregion-app-primary`** → Click **"Start"**
2. Wait 60 seconds for Front Door to detect it's healthy again
3. Refresh → Traffic returns to **"Central India (Primary)"**

> [!TIP]
> This is exactly how Netflix, Spotify, and Azure itself handle regional failures. The user never even knows an outage happened.

---

## 🧹 Clean Up

> [!CAUTION]
> **Two App Service S1 plans + Azure SQL + Front Door = ~₹800–1,000/day.** Delete the resource group immediately!

```
Search "Resource groups" → click "multiregion-dev-rg" → "Delete resource group" → confirm
```

> [!WARNING]
> SQL Geo-Replication and Failover Groups can sometimes block resource group deletion. If deletion hangs, manually delete the failover group first (SQL Server → Failover groups → Delete), then retry resource group deletion.

---

## 🧠 What Did You Learn?

| Concept                      | What You Practiced                                              |
|------------------------------|-----------------------------------------------------------------|
| Azure Front Door             | Global Layer 7 load balancer with priority-based routing       |
| Active-Standby Pattern       | Primary (priority 1) and standby (priority 2) origins          |
| App Service                  | PaaS web hosting with deployment slots and auto-SSL            |
| SQL Geo-Replication          | Async read-only replica in a secondary region                  |
| Failover Groups              | Automatic database failover with listener endpoints            |
| RTO / RPO                    | ~60s recovery time, <5s data loss                              |
| Azure Monitor + Action Groups| Email/SMS alerts on service health changes                     |
| Cross-Region Architecture    | Designing for regional failure tolerance                       |
| Health Probes                | Automatic detection of unhealthy backends                      |

---

## 🏆 Complete Learning Path

| Lab | Level    | Architecture Pattern                          |
|-----|----------|------------------------------------------------|
| 01  | Moderate | Single-region VM load balancing                |
| 02  | Advanced | Application Gateway + Auto-scaling + Managed DB |
| 03  | Expert   | Hub-Spoke enterprise networking                |
| 04  | Expert   | Serverless event-driven APIs (IaaS → PaaS)    |
| **05** | **Expert+** | **Multi-region disaster recovery (Capstone)** |

You now have hands-on experience across the full Azure spectrum — from Linux VMs to serverless functions to multi-region high availability. 🚀

---

## 📂 Files

```
Lab05-MultiRegion-FrontDoor/
├── Lab05-MultiRegion-FrontDoor-Guide.md  ← You are here
├── generate_diagram.py                   ← Regenerate the architecture diagram
└── Lab05-Architecture.png                ← Architecture diagram with Azure icons
```
