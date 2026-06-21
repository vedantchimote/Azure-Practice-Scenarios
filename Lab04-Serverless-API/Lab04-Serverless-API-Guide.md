# 🧪 Lab 04: Serverless Task Manager — Azure Functions + Cosmos DB + API Management

> **Difficulty:** Advanced-Expert &nbsp; | &nbsp; **Time:** 90–120 minutes &nbsp; | &nbsp; **Estimated Cost:** ~₹100–300 (if destroyed within 3 hours)

This lab marks a fundamental shift — from **IaaS** (managing VMs yourself) to **PaaS/Serverless** (Azure manages everything, you just write code). You'll build a serverless REST API backed by a NoSQL database, fronted by an API gateway, with a static website as the UI.

---

## 🔄 The IaaS → PaaS Shift

| What You Did Before (Labs 1–3)      | What You'll Do Now (Lab 4)                    |
|--------------------------------------|-----------------------------------------------|
| Created VMs, installed Nginx         | **Azure Functions** — no servers to manage    |
| Managed MySQL on a VM or PaaS       | **Cosmos DB** — serverless NoSQL, auto-scales |
| Load Balancer for traffic            | **API Management** — API gateway with policies|
| HTML files on VM disk                | **Static Web App** — hosted from blob storage |
| Paid per hour (VMs always running)   | **Pay per execution** (idle = ₹0)             |

---

## 📐 Architecture Overview

![Lab 04 Architecture](./Lab04-Architecture.png)

### What You'll Build

| #  | Resource                     | Name                          | Purpose                                            |
|----|------------------------------|-------------------------------|-----------------------------------------------------|
| 1  | Resource Group               | `serverless-dev-rg`           | Container for all resources                         |
| 2  | Storage Account              | `serverlesswebXXXX`          | Hosts the static frontend ($web container)          |
| 3  | Azure CDN Profile            | `serverless-cdn`              | Caches and accelerates the static site globally     |
| 4  | Function App                 | `serverless-api-func`         | CRUD API endpoints (Create, Read, Update, Delete)   |
| 5  | Function App (Events)        | `serverless-events-func`      | Cosmos DB change feed processor                     |
| 6  | App Service Plan              | `serverless-plan`            | Consumption plan (pay-per-execution)                |
| 7  | Storage Account (Functions)  | `serverlessfuncXXXX`         | Internal storage for Function App                   |
| 8  | Cosmos DB Account            | `serverless-cosmos`           | NoSQL database (serverless capacity mode)           |
| 9  | API Management               | `serverless-apim`             | API gateway with rate limiting and caching          |
| 10 | Application Insights         | `serverless-insights`         | Distributed tracing and performance monitoring      |
| 11 | Key Vault                    | `serverless-kv-XXXX`         | Stores Cosmos DB connection strings securely        |

---

## 📚 New Concepts You'll Learn

<details>
<summary><strong>🔹 What is Serverless Computing?</strong></summary>

"Serverless" doesn't mean no servers — it means **you don't manage them**. Azure provisions, scales, and patches the underlying infrastructure automatically.

| Aspect          | VMs (Labs 1–3)                      | Serverless (This Lab)                |
|-----------------|-------------------------------------|--------------------------------------|
| **You manage**  | OS, patches, scaling, disk, network | Just your code                       |
| **Scaling**     | Manual or VMSS rules                | Automatic (0 → thousands instantly)  |
| **Billing**     | Pay per hour (even when idle)       | Pay per execution (idle = ₹0)        |
| **Cold start**  | Always running                      | May take 1-2s on first request       |

**Think of it as:** Renting a kitchen vs. ordering from a cloud kitchen. You don't own the kitchen, you just place orders (function calls) and pay per dish.

</details>

<details>
<summary><strong>🔹 What is Azure Functions?</strong></summary>

Azure Functions lets you run small pieces of code ("functions") without provisioning VMs or servers.

**Triggers** — what starts a function:
- **HTTP Trigger:** Someone calls your API endpoint
- **Timer Trigger:** Runs on a schedule (like cron)
- **Cosmos DB Trigger:** Fires when data changes in the database
- **Blob Trigger:** Fires when a file is uploaded to storage

**Bindings** — automatic I/O connections:
```javascript
// This function automatically reads from Cosmos DB — no SDK code needed
module.exports = async function (context, req, inputDocument) {
    context.res = { body: inputDocument };
};
```

</details>

<details>
<summary><strong>🔹 What is Cosmos DB?</strong></summary>

Cosmos DB is Azure's globally distributed, multi-model NoSQL database. It's designed for:
- **Single-digit millisecond** reads/writes anywhere in the world
- **Automatic scaling** — serverless mode charges per RU (Request Unit) consumed
- **Multiple APIs** — SQL (document), MongoDB, Cassandra, Gremlin (graph), Table

**Key concept — Request Units (RUs):**
- A simple read of a 1KB document = 1 RU
- A write = ~5 RUs
- Serverless mode: up to 5000 RU/s, pay only for what you use

**Partition Key** — the most important design decision:
- Determines how data is distributed across physical partitions
- For a task manager: `/userId` is a good partition key (each user's tasks are grouped)
- Bad partition key: `/status` (only 3 values → hot partition)

</details>

<details>
<summary><strong>🔹 What is API Management (APIM)?</strong></summary>

APIM sits between your users and your backend APIs. It provides:

| Feature            | What It Does                                              |
|--------------------|-----------------------------------------------------------|
| **Rate Limiting**  | "Max 100 requests per minute per user"                    |
| **Authentication** | Validate API keys, OAuth tokens, JWT                      |
| **Caching**        | Cache GET responses to reduce backend calls               |
| **Transformation** | Rewrite headers, change response format                   |
| **Analytics**      | Track who calls your API, response times, error rates     |
| **Developer Portal**| Auto-generated API documentation for consumers           |

**Think of it as:** A bouncer at a club who checks IDs (authentication), manages the queue (rate limiting), and keeps a guest list (analytics).

</details>

<details>
<summary><strong>🔹 What is a Static Web App?</strong></summary>

A Static Web App hosts your frontend (HTML, CSS, JS) directly from Azure Blob Storage's `$web` container — no web server needed. Combined with Azure CDN, your site is served from edge locations worldwide.

**How it works:**
1. You upload HTML/CSS/JS files to the `$web` blob container
2. Enable "Static website" on the storage account
3. Azure gives you a URL: `https://serverlesswebxxxx.z29.web.core.windows.net`
4. Add Azure CDN in front for custom domain + global caching

</details>

<details>
<summary><strong>🔹 What is Application Insights?</strong></summary>

Application Insights is an APM (Application Performance Management) service that:
- **Traces** every request end-to-end (frontend → APIM → Function → Cosmos DB)
- **Detects anomalies** in response times and failure rates
- **Live metrics** — see requests flowing in real-time
- **Application Map** — visual diagram showing how components communicate

You'll query telemetry with KQL:
```kql
requests
| where resultCode >= 400
| summarize count() by bin(timestamp, 1h), resultCode
| render timechart
```

</details>

---

## 🚀 Step-by-Step Instructions

> [!TIP]
> This lab uses mostly PaaS services which are cheaper than VMs. The biggest cost is API Management (~₹150/day for Developer tier). Use the Consumption tier if available to reduce costs.

---

### Step 1: Create the Resource Group

1. Search **"Resource groups"** → **"+ Create"**

   | Field            | Value                  |
   |------------------|------------------------|
   | Resource group   | `serverless-dev-rg`    |
   | Region           | `Central India`        |

---

### Step 2: Create the Cosmos DB Account

1. Search **"Azure Cosmos DB"** → **"+ Create"** → Select **"Azure Cosmos DB for NoSQL"**
2. Fill in:

   | Field                   | Value                           |
   |-------------------------|---------------------------------|
   | Resource group          | `serverless-dev-rg`             |
   | Account name            | `serverless-cosmos` *(must be globally unique — add digits if taken)* |
   | Region                  | `Central India`                 |
   | Capacity mode           | **`Serverless`** ← important!  |

> [!IMPORTANT]
> Choose **Serverless** capacity mode — NOT Provisioned Throughput. Serverless charges per-request and is dramatically cheaper for learning (~₹0 for light usage vs. ₹4,000/mo minimum for provisioned).

3. **Backup Policy tab:** Keep defaults (Periodic, 4-hour interval)
4. Click **"Review + create"** → **"Create"** *(Takes 3–5 minutes)*

**After creation, create a database and container:**
1. Go to the Cosmos DB account → **"Data Explorer"**
2. Click **"New Container"**

   | Field              | Value             |
   |--------------------|-------------------|
   | Database id        | `taskdb` (Create new) |
   | Container id       | `tasks`           |
   | Partition key      | `/userId`         |

> [!NOTE]
> The partition key `/userId` means all tasks for a single user are stored together on the same physical partition — this gives excellent query performance for "get all tasks for user X" queries.

---

### Step 3: Create the Function App (CRUD API)

1. Search **"Function App"** → **"+ Create"**
2. **Basics tab:**

   | Field                   | Value                                     |
   |-------------------------|-------------------------------------------|
   | Resource group          | `serverless-dev-rg`                       |
   | Function App name       | `serverless-api-func` *(globally unique)* |
   | Runtime stack           | `Node.js` (or `Python` if you prefer)     |
   | Version                 | `20 LTS` (Node) or `3.11` (Python)        |
   | Region                  | `Central India`                           |
   | Operating System        | `Linux`                                   |
   | Plan type               | **`Consumption (Serverless)`**            |

3. **Storage tab:**
   - Create new storage account: `serverlessfuncXXXX`

4. **Monitoring tab:**

   | Field                   | Value              |
   |-------------------------|--------------------|
   | Enable App Insights     | `Yes`              |
   | Application Insights    | **Create new** → `serverless-insights` |

5. Click **"Review + create"** → **"Create"**

---

### Step 4: Create Your First Function (HTTP Trigger)

1. Go to your Function App → **"Functions"** in the left menu → **"+ Create"**
2. Select **"HTTP trigger"**

   | Field              | Value                |
   |--------------------|----------------------|
   | New Function       | `GetTasks`           |
   | Authorization level| `Function`           |

3. After creation, click on the function → **"Code + Test"**
4. Replace the code with:

   **Node.js:**
   ```javascript
   module.exports = async function (context, req) {
       // In production, this would query Cosmos DB
       const tasks = [
           { id: "1", title: "Learn Azure Functions", status: "done", userId: "user1" },
           { id: "2", title: "Build Cosmos DB API", status: "in-progress", userId: "user1" },
           { id: "3", title: "Set up API Management", status: "todo", userId: "user1" }
       ];

       context.res = {
           status: 200,
           headers: { "Content-Type": "application/json" },
           body: { tasks: tasks, servedBy: "Azure Functions", timestamp: new Date().toISOString() }
       };
   };
   ```

5. Click **"Save"** → Click **"Test/Run"** → Verify you get the JSON response
6. Click **"Get function URL"** → Copy it — you'll need this for APIM

> [!TIP]
> The `Authorization level: Function` means callers need a function key in the URL. APIM will handle passing this key automatically.

---

### Step 5: Create a Second Function (Cosmos DB Input Binding)

1. Create another function: **"+ Create"** → **"HTTP trigger"** → Name: `GetTaskById`
2. Go to **"Integration"** → Under **Inputs**, click **"+ Add input"**

   | Field              | Value                               |
   |--------------------|-------------------------------------|
   | Binding type       | `Azure Cosmos DB`                   |
   | Connection         | **New** → select your Cosmos account |
   | Database name      | `taskdb`                            |
   | Container name     | `tasks`                             |
   | Document ID        | `{id}` (from route parameter)       |
   | Partition key      | `{userId}` (from query parameter)   |

3. This automatically reads from Cosmos DB without you writing any SDK code!

---

### Step 6: Create the Static Web App (Frontend)

1. Search **"Storage accounts"** → **"+ Create"**

   | Field            | Value                               |
   |------------------|-------------------------------------|
   | Resource group   | `serverless-dev-rg`                 |
   | Name             | `serverlesswebXXXX` *(globally unique)* |
   | Region           | `Central India`                     |
   | Performance      | `Standard`                          |
   | Redundancy       | `LRS` (cheapest for dev)            |

2. After creation, go to the storage account
3. In the left menu, scroll to **"Data management"** → **"Static website"**
4. Toggle **"Enabled"**

   | Field               | Value          |
   |---------------------|----------------|
   | Index document name | `index.html`   |
   | Error document      | `404.html`     |

5. Click **"Save"** — Azure creates a `$web` blob container and gives you a **Primary endpoint** URL

6. Go to **"Containers"** → Click **`$web`** → Click **"Upload"**
7. Create and upload this `index.html`:

   ```html
   <!DOCTYPE html>
   <html lang="en">
   <head>
       <meta charset="UTF-8">
       <title>Serverless Task Manager</title>
       <style>
           * { margin: 0; padding: 0; box-sizing: border-box; }
           body { font-family: 'Segoe UI', Arial, sans-serif; background: #0f0c29;
                  color: #e0e0e0; min-height: 100vh; display: flex; justify-content: center;
                  align-items: center; }
           .container { background: rgba(255,255,255,0.05); border-radius: 16px;
                        padding: 40px; max-width: 600px; width: 90%;
                        border: 1px solid rgba(255,255,255,0.1); }
           h1 { color: #00d4ff; margin-bottom: 20px; }
           .task { background: rgba(255,255,255,0.08); padding: 15px; margin: 10px 0;
                   border-radius: 8px; display: flex; justify-content: space-between; }
           .badge { padding: 4px 12px; border-radius: 12px; font-size: 12px; }
           .done { background: #2e7d32; } .in-progress { background: #e65100; }
           .todo { background: #1565c0; }
           button { background: #00d4ff; color: #000; border: none; padding: 12px 24px;
                    border-radius: 8px; cursor: pointer; font-size: 14px; margin-top: 20px; }
           #output { margin-top: 20px; font-family: monospace; font-size: 12px;
                     color: #888; white-space: pre-wrap; }
       </style>
   </head>
   <body>
       <div class="container">
           <h1>⚡ Serverless Task Manager</h1>
           <p style="color:#888; margin-bottom:20px;">Powered by Azure Functions + Cosmos DB</p>
           <div id="tasks">Loading tasks...</div>
           <button onclick="fetchTasks()">🔄 Refresh Tasks</button>
           <div id="output"></div>
       </div>
       <script>
           async function fetchTasks() {
               document.getElementById('output').textContent = 'Fetching from Azure Functions API...';
               try {
                   // Replace with your actual Function App URL or APIM URL
                   const API_URL = 'YOUR_FUNCTION_URL_HERE';
                   const res = await fetch(API_URL);
                   const data = await res.json();
                   let html = '';
                   data.tasks.forEach(t => {
                       html += `<div class="task"><span>${t.title}</span>
                                <span class="badge ${t.status}">${t.status}</span></div>`;
                   });
                   document.getElementById('tasks').innerHTML = html;
                   document.getElementById('output').textContent =
                       `✅ Response from: ${data.servedBy}\n⏱ Timestamp: ${data.timestamp}`;
               } catch(e) {
                   document.getElementById('output').textContent = '❌ Error: ' + e.message;
               }
           }
           fetchTasks();
       </script>
   </body>
   </html>
   ```

8. Access your site at the **Primary endpoint** URL from step 5

---

### Step 7: Create API Management

1. Search **"API Management services"** → **"+ Create"**
2. Fill in:

   | Field                | Value                               |
   |----------------------|-------------------------------------|
   | Resource group       | `serverless-dev-rg`                 |
   | Name                 | `serverless-apim` *(globally unique)* |
   | Region               | `Central India`                     |
   | Organization name    | `Learning Lab`                      |
   | Admin email          | *Your email*                        |
   | Pricing tier         | `Consumption` (cheapest, if available) or `Developer` |

> [!WARNING]
> APIM takes **30–60 minutes** to provision (especially Developer tier). Start this step early and work on other things while it deploys.

3. **After creation**, import your Function App as an API:
   - Go to APIM → **"APIs"** → **"+ Add API"** → **"Function App"**
   - Select your `serverless-api-func`
   - API URL suffix: `tasks`
   - This auto-imports all your functions as API endpoints

4. **Add a Rate Limiting Policy:**
   - Go to **"APIs"** → Select your API → **"All operations"** → **"Inbound processing"** → **"+ Add policy"**
   - Select **"Limit call rate"**

   | Field              | Value          |
   |--------------------|----------------|
   | Number of calls    | `100`          |
   | Renewal period (s) | `60`           |

---

### Step 8: Create Azure Key Vault

1. Search **"Key vaults"** → **"+ Create"**

   | Field            | Value                              |
   |------------------|------------------------------------|
   | Name             | `serverless-kv-XXXX` *(globally unique)* |
   | Resource group   | `serverless-dev-rg`                |
   | Pricing tier     | `Standard`                         |

2. After creation, store your Cosmos DB connection string:
   - Go to your **Cosmos DB account** → **"Keys"** → Copy the **Primary Connection String**
   - Go to Key Vault → **"Secrets"** → **"+ Generate/Import"**
   - Name: `cosmos-connection-string`, Value: *paste the connection string*

3. **Grant Function App access to Key Vault:**
   - Go to Function App → **"Identity"** → Enable **System assigned** managed identity → Save
   - Go to Key Vault → **"Access policies"** → **"+ Add Access Policy"**
   - Secret permissions: `Get`, `List`
   - Select principal: your Function App name
   - Click **"Save"**

> [!NOTE]
> This is the **Managed Identity** pattern — instead of hardcoding connection strings in your code, the Function App uses its Azure identity to retrieve secrets from Key Vault at runtime. If a secret is compromised, you rotate it in one place.

---

### Step 9: Test the Full Flow 🎉

1. **Test the frontend:** Open the Static Web App URL in your browser
2. **Test the API directly:** Open the APIM → **"Test"** tab → Run your `GetTasks` endpoint
3. **Test via PowerShell:**

   ```powershell
   # Direct Function call
   Invoke-WebRequest -Uri "https://serverless-api-func.azurewebsites.net/api/GetTasks?code=YOUR_KEY" | Select-Object -ExpandProperty Content

   # Via APIM (if configured)
   Invoke-WebRequest -Uri "https://serverless-apim.azure-api.net/tasks/GetTasks" -Headers @{"Ocp-Apim-Subscription-Key"="YOUR_APIM_KEY"} | Select-Object -ExpandProperty Content
   ```

4. **Check Application Insights:**
   - Go to `serverless-insights` → **"Application Map"** — see the visual flow
   - Click **"Live Metrics"** — watch requests in real-time
   - Run a KQL query:
   ```kql
   requests
   | where name contains "GetTasks"
   | project timestamp, duration, resultCode, name
   | order by timestamp desc
   | take 20
   ```

---

### Step 10: Create a Cosmos DB Trigger Function (Event-Driven)

1. Go to Function App → **"Functions"** → **"+ Create"**
2. Select **"Azure Cosmos DB trigger"**

   | Field              | Value                               |
   |--------------------|-------------------------------------|
   | New Function       | `OnTaskChange`                      |
   | Connection         | *Select your Cosmos account*        |
   | Database name      | `taskdb`                            |
   | Container name     | `tasks`                             |
   | Lease container    | `leases` (create automatically)     |

3. This function fires **automatically** whenever a document is created or modified in Cosmos DB — no polling needed!

```javascript
module.exports = async function (context, documents) {
    if (documents && documents.length > 0) {
        context.log(`Processing ${documents.length} changed document(s)`);
        documents.forEach(doc => {
            context.log(`Task changed: ${doc.title} → Status: ${doc.status}`);
            // In production: send notification, update cache, trigger workflow, etc.
        });
    }
};
```

---

## 🧹 Clean Up

> [!CAUTION]
> APIM Developer tier costs ~₹150/day. Delete immediately!

```
Search "Resource groups" → click "serverless-dev-rg" → "Delete resource group" → confirm
```

---

## 🧠 What Did You Learn?

| Concept                   | What You Practiced                                              |
|---------------------------|-----------------------------------------------------------------|
| Serverless Computing      | Functions that scale to zero and cost nothing when idle         |
| Azure Functions           | HTTP triggers, Cosmos DB triggers, input/output bindings        |
| Cosmos DB (NoSQL)         | Serverless document database with partition keys                |
| API Management            | API gateway with rate limiting, caching, and policies           |
| Static Web App            | Frontend hosted from blob storage's $web container              |
| Application Insights      | Distributed tracing, Application Map, Live Metrics              |
| Key Vault + Managed Identity | Zero-secret-in-code pattern using Azure AD identity          |
| Event-Driven Architecture | Cosmos DB Change Feed triggering downstream processing          |

---

## 📂 Files

```
Lab04-Serverless-API/
├── Lab04-Serverless-API-Guide.md     ← You are here
├── generate_diagram.py               ← Regenerate the architecture diagram
└── Lab04-Architecture.png            ← Architecture diagram with Azure icons
```
