# 07. Fleet, Engine, Insights, data export, and deployment control

Sources: docs pages `fleet__index`, `fleet__quickstart`, `fleet__schedules`, `fleet__webhooks`, `fleet__channels`, `fleet__slack-app`, `fleet__teams-app`, `fleet__access-and-oversight`, `fleet__agent-identity`, `fleet__skills`, `fleet__tools`, `fleet__remote-mcp-servers`, `fleet__computer-use`, `fleet__code`, `fleet__comparison`, `fleet__changelog`, `engine`, `engine-setup`, `engine-issues`, `engine-security`, `engine-self-hosted`, `engine-repositories`, `engine-fix-validation`, `engine-red-teaming`, `insights`, `data-export`, `data-export-destinations`, `data-export-monitor`, `big-query-bulk-export`, `deploy-with-control-plane`, `deploy-standalone-server`, `cloud-platform-features` (read in full for the points below; the rest headings). Read 2026-11-14.

## 1. Fleet (no-code agents)

- "Agent Builder is now LangSmith Fleet." A no-code platform: create an agent by describing it (Fleet builds it and pauses for input), or from a template; connect accounts; run routine work; approvals for important actions.
- **Where it runs:** in the LangSmith UI, in chat, and in Slack and Microsoft Teams through dedicated app pages (`fleet__slack-app`, `fleet__teams-app`).
- **Schedules** and **webhooks** trigger agents (`fleet__schedules`, `fleet__webhooks`); **channels** connect them to messaging.
- **Oversight:** access and oversight, agent identity, workspace administration, and manage agent settings pages.
- **Tools:** tool integrations, remote MCP servers, Salesforce, Arcade, and computer use (a desktop the agent can drive, with a custom image for document dependencies).
- **Code:** the page "Use Fleet agents in code" shows calling a Fleet agent from code.
- **Skills:** reusable capabilities an agent loads (`fleet__skills`).
- Fleet pages include a comparison with other agent platforms and a changelog.

## 2. Engine (issues, fixes, datasets from traces)

- "The LangSmith agent for agent engineering, turning production traces into tracked issues, fixes, and datasets."
- **Lifecycle** (from the page): for each issue Engine shows the contributing traces, proposes a fix, keeps the issue current by attaching new matching traces, and creates ground-truth dataset examples. Three stages: **Build** (open a pull request), **Test** (generate datasets for offline checks), **Monitor** (scan tracing projects on a schedule and track recurring issues).
- **Repositories:** connect GitHub or GitLab. Engine can propose changes to agents built with Deep Agents, LangChain or LangGraph.
- **Fix validation** (`engine-fix-validation`) and **red teaming** (`engine-red-teaming`) are separate pages.
- **Security** (`engine-security`): opt-in, advisory, does not train on customer data; runs under SOC 2 Type II and ISO 27001 controls. Engine works on trace data the customer already shared with LangChain and has GitHub and GitLab access controls and model subprocessor controls.
- **Self-hosted and BYOC:** Engine has its own deployment pages (GitHub configuration, model providers).
- **Notifications** page exists.

## 3. Insights

Automatic trace analysis with **hierarchical categorisation**, to surface usage patterns, common behaviours and failure modes. Plus and Enterprise plans. Requires a model configuration. Run per environment to analyse production traffic apart from local tests.

Difference from Engine (as the docs put it): Insights describes patterns across traces; Engine turns failures into issues with proposed fixes.

## 4. Data export

- **Bulk export** of trace data for a project and date range, in **Parquet**, to an **S3-compatible bucket**. Scheduled exports, field filtering, destination management, monitoring and troubleshooting pages.
- **BigQuery** bulk export (`big-query-bulk-export`) and an import page (`data-export-downstream`).
- **Plan rule:** for accounts that signed up after 2026-08-03, bulk export is Enterprise-only.

## 5. Dashboards, alerts, rules

Covered in file 04 §7 (rules and webhooks) and dashboards and alerts pages.

## 6. Deployment control and environments

- **Cloud** (managed, Plus plan and above): Serverless or Dedicated; regions; static NAT IPs for allowlisting (from `cloud-platform-features`: deployments created after 2025-01-06 use NAT gateways with static addresses per region); payload limits; managed databases.
- **Self-hosted:** the stack runs in your infrastructure; an optional **control plane** adds a data-plane listener and an operator to deploy Agent Servers through the LangSmith UI (`deploy-with-control-plane`). Standalone servers are documented separately (`deploy-standalone-server`).
- **Restricted-network builds:** a build machine can run in a restricted network (`self-host-restricted-network-build`).
- **Environment variables:** separate pages for Cloud and self-hosted.
- **Encryption:** AES at rest and custom encryption (file 02).

## 7. Usage and billing

The docs name Plus and Enterprise plan tiers (Insights, bulk export and Cloud deployments are gated by them). Cost and usage views exist; extended data retention auto-upgrades when an online evaluator runs. The usage-and-billing page was not read in full.
