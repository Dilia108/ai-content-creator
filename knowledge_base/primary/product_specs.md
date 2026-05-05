# IronVeil Security — Product Portfolio & Specifications

## Product Overview

IronVeil offers three core products sold modularly or as a bundled platform. All products share a unified agent and a single management console (IronVeil Command).

---

## Product 1: VeilGuard EDR

### What It Is
Cloud-native endpoint detection and response (EDR) for Windows, macOS, and Linux. VeilGuard deploys a lightweight agent (<1% CPU, <80MB RAM footprint) and streams telemetry to IronVeil's cloud detection engine in real time.

### Core Capabilities
- Behavioral detection across process, file, network, and registry telemetry
- MITRE ATT&CK-mapped alerts with tactic/technique tagging out of the box
- Automated containment: network isolation, process kill, file quarantine — all reversible with one click
- 365-day telemetry retention with full process tree replay
- Offline protection mode (no cloud dependency for core detections)

### Key Differentiators vs. Competition
- **vs. CrowdStrike Falcon Go**: VeilGuard includes full EDR (not just EPP) at the Falcon Go price point. Falcon Go lacks process tree replay and has 90-day retention limits.
- **vs. SentinelOne Singularity Core**: VeilGuard includes MITRE tagging and automated containment at the Core tier; SentinelOne gates these behind higher tiers.
- **vs. Huntress**: IronVeil covers macOS and Linux natively. Huntress is Windows-first.

### Pricing
- $8/endpoint/month (1–500 endpoints)
- $6.50/endpoint/month (501–2,000 endpoints)
- Custom pricing above 2,000 endpoints
- Minimum commitment: 100 endpoints, 12-month term

### Deployment
- Agent deployment: GPO, Intune, JAMF, manual installer, or API-driven via IronVeil Command
- Detection updates: pushed silently, no reboot required
- Time to first detection: typically under 4 hours post-deployment

---

## Product 2: VeilID (ITDR)

### What It Is
Identity threat detection and response (ITDR) platform covering Entra ID (Azure AD), Okta, and Active Directory on-prem. VeilID monitors identity layer activity — authentication, privilege changes, directory modifications — and surfaces identity-specific threats that EDR tools miss.

### Core Capabilities
- Continuous monitoring of Entra ID sign-in logs, audit logs, and Conditional Access events
- Okta System Log ingestion with behavioral baselining per user/role
- On-prem Active Directory monitoring via lightweight DC-side log collector
- Identity threat scenarios detected: MFA fatigue attacks, impossible travel, legacy auth abuse, privilege escalation, service account anomalies, OAuth app abuse
- Automated response: account suspension, MFA reset forcing, session revocation (requires admin pre-authorization)
- Weekly identity risk digest report (PDF, auto-generated)

### Why This Exists
In 2024, credential-based attacks overtook vulnerability exploitation as the #1 initial access method (Verizon DBIR 2024). EDR tools don't see identity layer activity — they see what happens *after* the attacker is already in. VeilID closes that gap.

### Key Differentiators
- **vs. Microsoft Entra ID Protection**: VeilID correlates across Okta AND Entra AND on-prem AD. Microsoft's native tooling only covers its own stack.
- **vs. CrowdStrike Falcon Identity Protection**: Same capability set at roughly 40% lower cost for mid-market seat counts.
- **vs. Vectra AI**: Vectra is network-first. VeilID is identity-first. They are complementary, not competitive.

### Pricing
- $5/identity/month (1–1,000 identities)
- $4/identity/month (1,001–5,000 identities)
- Minimum commitment: 250 identities, 12-month term

---

## Product 3: IronVeil MDR

### What It Is
Managed detection & response service where IronVeil's analyst team monitors VeilGuard + VeilID telemetry 24/7, triages alerts, and takes pre-authorized response actions on the customer's behalf.

### What Makes It Different: The Open Playbook Model
Every MDR engagement at IronVeil operates on a shared playbook. Customers receive:
- Full access to IronVeil's detection rules (read-only)
- A written runbook for every automated response action taken on their behalf
- Real-time incident timeline in IronVeil Command — no waiting for email summaries
- Post-incident report within 24 hours of any escalation, including what the analyst saw and why they made each decision

This is the opposite of the black-box MSSP model where customers receive a PDF at the end of the month and have no idea what happened.

### SLA Commitments
- Mean time to triage (P1 alerts): 15 minutes or less
- Mean time to escalate (confirmed incident): 30 minutes or less
- Analyst coverage: 24/7/365, US + EU analyst teams
- Customer onboarding: full integration and tuning within 30 days

### Response Actions Included (Pre-Authorized Options)
- Network isolation of endpoint
- Account suspension (Entra ID / Okta)
- Process termination
- File quarantine
- MFA enforcement reset

### Pricing
- Requires active VeilGuard license (minimum)
- MDR add-on: $4/endpoint/month (VeilGuard customers)
- MDR + ITDR bundle: $7/identity/month (replaces VeilID base price)
- Minimum: 100 endpoints or 250 identities; 12-month term

---

## IronVeil Command (Management Console)

Unified console for all IronVeil products. Key capabilities:
- Single-pane view across all endpoints and identities
- Role-based access control (RBAC) with MFA enforcement
- API-first: full REST API for SIEM/SOAR integration (Splunk, Sentinel, Chronicle, Elastic)
- Pre-built integrations: ServiceNow, Jira, PagerDuty, Slack, Microsoft Teams
- Executive dashboards: risk score, MTTR trends, detection coverage heatmap
- Available as SaaS (default) or private cloud deployment (MDR customers only, additional cost)

---

## Certifications & Compliance Support

- SOC 2 Type II certified (IronVeil as a data processor)
- HIPAA Business Associate Agreement available
- Supports compliance evidence collection for: NIST CSF, CIS Controls v8, ISO 27001, PCI DSS 4.0
- FedRAMP In-Process (expected authorization: Q3 2025)

---

## Typical Customer Profile

| Attribute | Typical Range |
|---|---|
| Employee count | 300–2,500 |
| Endpoint count | 200–1,800 |
| Security team size | 1–8 FTEs |
| IT setup | Microsoft 365 + Entra ID (85% of customers), Okta (40%), hybrid AD (55%) |
| Verticals | Financial services (34%), healthcare (28%), professional services (22%), other (16%) |
| Primary buyer | Security Director or IT Director; CISO sign-off for deals >$50K ARR |
