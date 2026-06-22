"""
SecureFlow AI — Memory Seed & Recall Service
Pre-loads 10 realistic APT incident memories and provides
keyword-similarity recall (no external vector DB required).
"""

from typing import List, Dict, Any
import re
from datetime import datetime, timedelta
import random

# ── Pre-seeded incident memory bank ─────────────────────────────────────────
# These 10 incidents are loaded into the DB on first run and used for
# similarity recall during demo. Each contains: summary, techniques,
# threat actor, mitigations that worked, and outcome.

SEED_MEMORIES: List[Dict[str, Any]] = [
    {
        "incident_id": "INC-104",
        "title": "APT29 VPN Brute Force → Akira Ransomware Deployment",
        "date": "2024-03-15",
        "summary": (
            "APT29 executed a credential stuffing campaign against the corporate VPN gateway "
            "using 47 automated login attempts from IP 185.220.101.34 (known Tor exit node). "
            "After obtaining valid credentials for john.miller, the attacker escalated privileges "
            "via CVE-2024-3094, moved laterally to API-GW-01 using WMI, deployed Akira ransomware, "
            "established C2 beacon to 91.121.87.18, exfiltrated 2.3GB of customer data, "
            "and encrypted 3,847 files before detection."
        ),
        "techniques": ["T1110", "T1078", "T1068", "T1021", "T1204", "T1071", "T1048", "T1486"],
        "threat_actor": "APT29",
        "assets_compromised": ["VPN-Gateway", "WKSTN-047", "API-GW-01", "DB-PROD-01"],
        "mitigations": [
            "VPN geographic IP block (EU → US blocked)",
            "Forced password reset for all compromised accounts",
            "Endpoint isolation of WKSTN-047 and API-GW-01",
            "CVE-2024-3094 emergency patch deployed",
            "DB access audit log review for 72 hours post-incident",
        ],
        "outcome": "resolved_in_6_hours",
        "financial_impact": "$180,000 (downtime + response costs)",
        "lessons_learned": [
            "Geographic IP blocking should be permanent policy for VPN",
            "CVE patch SLA must be < 24h for CVSS 9+",
            "WMI lateral movement can be blocked via firewall policy",
        ],
    },
    {
        "incident_id": "INC-089",
        "title": "FIN7 Spearphishing → LockBit 3.0 Ransomware",
        "date": "2024-01-08",
        "summary": (
            "FIN7 sent targeted spearphishing emails to the finance team impersonating a CFO. "
            "One employee (a.garcia) opened a malicious Word document that executed a PowerShell "
            "download cradle. Cobalt Strike beacon established C2. Attacker used pass-the-hash "
            "to move laterally to the finance server and deployed LockBit 3.0 ransomware. "
            "22 servers encrypted over 4 hours."
        ),
        "techniques": ["T1566", "T1059.001", "T1550.002", "T1021", "T1486"],
        "threat_actor": "FIN7",
        "assets_compromised": ["WKSTN-Finance-01", "WKSTN-Finance-02", "FS-FINANCE-01"],
        "mitigations": [
            "Email filtering rule: block macro-enabled Office docs from external",
            "Endpoint isolation of all finance workstations",
            "Pass-the-hash mitigation: disable NTLM where not required",
            "MFA enforced across all privileged accounts",
        ],
        "outcome": "resolved_in_18_hours",
        "financial_impact": "$2.1M (ransomware payment avoided via backup restoration)",
        "lessons_learned": [
            "Finance team requires quarterly social engineering training",
            "Macro execution must be disabled globally via Group Policy",
        ],
    },
    {
        "incident_id": "INC-076",
        "title": "Lazarus Group Supply Chain Attack via Build Server",
        "date": "2023-11-20",
        "summary": (
            "Lazarus Group compromised the software build server (BUILD-01) via an exposed "
            "Jenkins interface. Attacker injected malicious code into the CI/CD pipeline, "
            "which was then distributed to 14 internal systems via an automated software update. "
            "Backdoor installed on all affected endpoints. Data exfiltration detected after 3 days."
        ),
        "techniques": ["T1195", "T1072", "T1133", "T1059", "T1041"],
        "threat_actor": "Lazarus",
        "assets_compromised": ["BUILD-01", "14 downstream endpoints"],
        "mitigations": [
            "Build server taken offline and rebuilt from clean image",
            "All software distributed in last 30 days reviewed and re-signed",
            "Jenkins exposed interface moved behind VPN",
            "Code signing enforced for all internal software packages",
        ],
        "outcome": "resolved_in_5_days",
        "financial_impact": "$450,000 (incident response + rebuild costs)",
        "lessons_learned": [
            "Build servers must never be internet-facing",
            "Software signing validation must occur at installation, not just build",
        ],
    },
    {
        "incident_id": "INC-061",
        "title": "HAFNIUM Exchange Server Exploitation — Data Exfiltration",
        "date": "2023-08-14",
        "summary": (
            "HAFNIUM exploited CVE-2023-34362 (ProxyShell) to gain unauthenticated access to "
            "the on-premises Exchange server. Web shell planted in OWA directory. "
            "Attacker exfiltrated 14 months of executive email communications. "
            "Attack was stealthy — dwell time 31 days before detection."
        ),
        "techniques": ["T1190", "T1505.003", "T1114", "T1048"],
        "threat_actor": "HAFNIUM",
        "assets_compromised": ["EXCHANGE-01", "OWA directory"],
        "mitigations": [
            "Emergency patch CVE-2023-34362 applied",
            "Exchange server migrated to Exchange Online",
            "Web shell scanner deployed on all web servers",
            "Email DLP rules tightened to block large outbound transfers",
        ],
        "outcome": "resolved_in_3_days",
        "financial_impact": "$290,000 (legal + notification costs)",
        "lessons_learned": [
            "On-premises Exchange is high-risk — migrate to cloud",
            "Monthly CVE scanning must be automated with auto-alerting",
        ],
    },
    {
        "incident_id": "INC-053",
        "title": "Sandworm Destructive Wiper Attack — OT Network",
        "date": "2023-05-30",
        "summary": (
            "Sandworm gained access to the IT network via phishing then pivoted to the OT "
            "network through an unsegmented firewall. Deployed AcidRain wiper malware targeting "
            "industrial control systems. 3 manufacturing lines taken offline. "
            "Affected 8 PLCs and 2 HMI workstations."
        ),
        "techniques": ["T1566", "T1021", "T1561", "T1485"],
        "threat_actor": "Sandworm",
        "assets_compromised": ["OT-Network", "PLC-01 through PLC-08", "HMI-01", "HMI-02"],
        "mitigations": [
            "IT/OT network segmentation enforced with dedicated firewall",
            "OT systems restored from offline backups",
            "USB policy enforced on all OT workstations",
            "OT-specific EDR deployed on HMI workstations",
        ],
        "outcome": "resolved_in_72_hours",
        "financial_impact": "$3.8M (production downtime)",
        "lessons_learned": [
            "IT/OT segmentation is non-negotiable",
            "OT systems must have offline backups tested quarterly",
        ],
    },
    {
        "incident_id": "INC-047",
        "title": "Insider Threat — Privileged User Data Exfiltration",
        "date": "2023-03-12",
        "summary": (
            "A departing employee (k.wilson, senior DBA) exfiltrated 450GB of customer database "
            "records over 3 weeks before resignation. Used legitimate DB admin access to copy "
            "data to personal cloud storage (Google Drive) via HTTPS. "
            "Detected by DLP anomaly on large outbound HTTPS transfer."
        ),
        "techniques": ["T1078", "T1537", "T1048.002"],
        "threat_actor": "Insider",
        "assets_compromised": ["DB-PROD-01", "DB-ANALYTICS-01"],
        "mitigations": [
            "DLP rules created for large personal cloud storage transfers",
            "Privileged account access revoked immediately on resignation notice",
            "Database activity monitoring (DAM) deployed",
            "UEBA baseline established for all DBA accounts",
        ],
        "outcome": "resolved_in_2_days",
        "financial_impact": "$1.2M (regulatory fines + legal costs)",
        "lessons_learned": [
            "Access revocation policy must trigger at resignation, not last day",
            "DLP rules must cover personal cloud storage, not just email",
        ],
    },
    {
        "incident_id": "INC-039",
        "title": "SSH Brute Force → Crypto Mining Malware",
        "date": "2022-12-04",
        "summary": (
            "Automated brute force attack from IP 45.33.32.156 against SSH port (22) "
            "on a publicly exposed development server (DEV-SERVER-01). "
            "Attacker successfully logged in using default credentials root:root. "
            "XMRig cryptocurrency miner deployed, consuming 95% CPU for 4 days before detection."
        ),
        "techniques": ["T1110", "T1078.001", "T1496"],
        "threat_actor": "Unknown (opportunistic)",
        "assets_compromised": ["DEV-SERVER-01"],
        "mitigations": [
            "SSH key-only authentication enforced (password auth disabled)",
            "SSH moved from port 22 to non-standard port",
            "DEV-SERVER-01 firewall: SSH restricted to internal VPN only",
            "Default credentials audit run across all systems",
        ],
        "outcome": "resolved_in_4_hours",
        "financial_impact": "$12,000 (cloud compute overage)",
        "lessons_learned": [
            "No server should be internet-facing with password SSH enabled",
            "Default credentials must be changed before any server deployment",
        ],
    },
    {
        "incident_id": "INC-032",
        "title": "Phishing → Credential Harvest → BEC Fraud",
        "date": "2022-09-18",
        "summary": (
            "Adversary-in-the-Middle phishing site harvested credentials for the CFO's email. "
            "Attacker monitored email for 2 weeks (dwell time). Identified a pending $240,000 "
            "wire transfer and sent a lookalike email diverting the transfer. "
            "Detected after finance team noticed the wire didn't arrive."
        ),
        "techniques": ["T1566.002", "T1557.002", "T1534"],
        "threat_actor": "Unknown (BEC group)",
        "assets_compromised": ["CFO Email Account"],
        "mitigations": [
            "Hardware FIDO2 keys deployed for all C-suite accounts",
            "Anti-phishing training run company-wide",
            "Wire transfer confirmation policy: phone verification required",
            "DMARC/DKIM/SPF enforced on all email domains",
        ],
        "outcome": "resolved_in_1_day",
        "financial_impact": "$240,000 wire transfer reversed (partial recovery)",
        "lessons_learned": [
            "MFA alone does not stop AiTM phishing — FIDO2 required",
            "Finance transfer policy must require out-of-band verification",
        ],
    },
    {
        "incident_id": "INC-025",
        "title": "Port Scan → Service Exploitation → Reverse Shell",
        "date": "2022-06-22",
        "summary": (
            "Automated scanner from 103.224.182.250 identified exposed Apache Struts "
            "(CVE-2022-26377) on the web application server (WEB-APP-01). "
            "Attacker exploited the vulnerability to obtain a reverse shell. "
            "Attempted lateral movement blocked by host-based firewall. Contained quickly."
        ),
        "techniques": ["T1046", "T1190", "T1059.004"],
        "threat_actor": "Unknown (opportunistic)",
        "assets_compromised": ["WEB-APP-01"],
        "mitigations": [
            "Apache Struts emergency patch applied",
            "WAF rules updated to block Struts exploit patterns",
            "Host-based firewall rules hardened on all web servers",
            "Vulnerability scanner schedule changed from weekly to daily",
        ],
        "outcome": "resolved_in_2_hours",
        "financial_impact": "$8,000 (response costs only)",
        "lessons_learned": [
            "Public-facing apps must be patched within 24h of CVSS 9+ CVEs",
            "WAF is critical defense for web application layer",
        ],
    },
    {
        "incident_id": "INC-018",
        "title": "Malware C2 Beacon — APT41 Data Collection Campaign",
        "date": "2022-03-05",
        "summary": (
            "APT41 implanted PlugX malware via a watering hole attack on an industry news site. "
            "Malware established encrypted C2 channel to 198.51.100.99 using HTTPS. "
            "Keylogger active for 6 weeks collecting credentials. "
            "Detected by network anomaly: regular beaconing pattern to unknown external IP."
        ),
        "techniques": ["T1189", "T1543", "T1071.001", "T1056.001"],
        "threat_actor": "APT41",
        "assets_compromised": ["WKSTN-022", "WKSTN-031"],
        "mitigations": [
            "Web proxy configured to block uncategorized domains",
            "SSL inspection enabled for all outbound HTTPS",
            "Endpoint EDR telemetry: beaconing detection rule added",
            "Credential rotation for all accounts on affected endpoints",
        ],
        "outcome": "resolved_in_3_days",
        "financial_impact": "$95,000 (response + credential resets)",
        "lessons_learned": [
            "Beaconing detection must be a standard EDR alert",
            "Watering hole protection requires URL reputation filtering",
        ],
    },
]


def keyword_similarity(text1: str, text2: str) -> float:
    """
    TF-IDF-inspired keyword similarity for security incident matching.
    No external dependencies — pure Python.
    """
    # Security-domain stop words (too common to be meaningful)
    STOP = {
        "the", "a", "an", "is", "was", "were", "has", "have", "had",
        "to", "of", "in", "on", "at", "for", "and", "or", "but", "with",
        "from", "by", "via", "this", "that", "be", "been", "being",
        "are", "it", "its", "into", "as", "after", "before", "during",
    }

    def tokenize(text: str) -> set:
        words = re.findall(r"[a-zA-Z0-9\.\-]+", text.lower())
        return {w for w in words if w not in STOP and len(w) > 2}

    t1 = tokenize(text1)
    t2 = tokenize(text2)

    if not t1 or not t2:
        return 0.0

    intersection = t1 & t2
    union = t1 | t2

    # Jaccard + bonus for MITRE technique matches (T-codes)
    jaccard = len(intersection) / len(union)
    technique_bonus = len(
        {w for w in intersection if re.match(r"t\d{4}", w)}
    ) * 0.05

    return min(1.0, jaccard + technique_bonus)


def recall_similar_incidents(
    query: str,
    techniques: List[str] = None,
    threat_actor: str = None,
    top_k: int = 3,
    threshold: float = 0.08,
) -> List[Dict[str, Any]]:
    """
    Retrieve similar past incidents using keyword similarity + technique overlap.
    Returns top-k matches above threshold with similarity score.
    """
    results = []

    query_full = query
    if techniques:
        query_full += " " + " ".join(techniques)
    if threat_actor:
        query_full += " " + threat_actor

    for mem in SEED_MEMORIES:
        mem_text = (
            mem["summary"] + " " +
            " ".join(mem["techniques"]) + " " +
            mem["threat_actor"] + " " +
            " ".join(mem.get("assets_compromised", []))
        )

        score = keyword_similarity(query_full, mem_text)

        # Extra boost for matching threat actor
        if threat_actor and threat_actor.upper() in mem["threat_actor"].upper():
            score = min(1.0, score + 0.20)

        # Extra boost for shared MITRE techniques
        if techniques:
            shared = set(techniques) & set(mem["techniques"])
            score = min(1.0, score + len(shared) * 0.08)

        if score >= threshold:
            results.append({
                "incident_id": mem["incident_id"],
                "title": mem["title"],
                "date": mem["date"],
                "similarity_score": round(score, 3),
                "similarity_pct": f"{round(score * 100)}%",
                "threat_actor": mem["threat_actor"],
                "techniques": mem["techniques"],
                "mitigations": mem["mitigations"],
                "outcome": mem["outcome"],
                "lessons_learned": mem.get("lessons_learned", []),
                "summary_brief": mem["summary"][:200] + "...",
            })

    results.sort(key=lambda x: x["similarity_score"], reverse=True)
    return results[:top_k]


def get_all_memories() -> List[Dict[str, Any]]:
    """Return all seeded memories for the Memory Center page."""
    return [
        {
            "incident_id": m["incident_id"],
            "title": m["title"],
            "date": m["date"],
            "threat_actor": m["threat_actor"],
            "techniques": m["techniques"],
            "assets_compromised": m.get("assets_compromised", []),
            "mitigations": m["mitigations"],
            "outcome": m["outcome"],
            "financial_impact": m.get("financial_impact", "N/A"),
            "lessons_learned": m.get("lessons_learned", []),
        }
        for m in SEED_MEMORIES
    ]
