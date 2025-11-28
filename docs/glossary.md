# Glossary of Scam-Related Terms 📖

This document defines key terms related to scams, fraud, and the technical implementation of this detection system.

---

## 🎯 Scam Types & Techniques

### Phishing
**Definition**: Fraudulent attempts to obtain sensitive information (passwords, credit cards, etc.) by disguising as a trustworthy entity.

**Common Forms**:
- **Email Phishing**: Fake emails impersonating banks, companies, or government agencies
- **Spear Phishing**: Targeted attacks against specific individuals or organizations
- **Smishing**: SMS/text message phishing
- **Vishing**: Voice call phishing (phone scams)

**Red Flags**:
- Urgent language ("Act now!", "Account suspended")
- Misspelled domains (paypa1.com instead of paypal.com)
- Generic greetings ("Dear Customer")
- Requests for personal information
- Suspicious links or attachments

---

### Social Engineering
**Definition**: Psychological manipulation to trick people into revealing confidential information or performing actions.

**Techniques**:
- **Urgency**: Creating time pressure ("Your account will be closed in 24 hours")
- **Authority**: Impersonating officials, bosses, or trusted entities
- **Fear**: Threatening legal action, arrest, or financial loss
- **Greed**: Promises of easy money, prizes, or rewards
- **Trust Exploitation**: Building fake relationships over time

---

### Business Email Compromise (BEC)
**Definition**: Sophisticated scam targeting businesses, often impersonating executives or vendors.

**Common Scenarios**:
- CEO fraud: Fake urgent payment requests from "executives"
- Invoice fraud: Fake invoices with altered payment details
- Vendor impersonation: Fake emails from suppliers

---

### Romance Scams
**Definition**: Fraudsters create fake romantic relationships to manipulate victims into sending money.

**Warning Signs**:
- Rapid professions of love
- Avoiding video calls or in-person meetings
- Financial emergencies requiring money transfers
- Requests to move conversation off dating platforms

---

### Investment & Cryptocurrency Scams
**Definition**: Fraudulent investment schemes promising unrealistic returns.

**Types**:
- **Ponzi Schemes**: Using new investors' money to pay earlier investors
- **Pump and Dump**: Artificially inflating asset prices then selling
- **Fake ICOs**: Fraudulent cryptocurrency offerings
- **Get-Rich-Quick**: Promises of guaranteed high returns

**Red Flags**:
- "Guaranteed" returns
- Pressure to invest quickly
- Unregistered investments
- Complex or secretive strategies

---

### Tech Support Scams
**Definition**: Fraudsters impersonate technical support to gain remote access or payment.

**Common Tactics**:
- Fake virus/malware warnings
- Unsolicited calls claiming computer issues
- Requests for remote access software
- Payment for unnecessary "fixes"

---

### Government Impersonation
**Definition**: Scammers pretend to be from government agencies (IRS, Social Security, immigration, etc.).

**Red Flags**:
- Demands for immediate payment (gift cards, wire transfers)
- Threats of arrest or deportation
- Requests for Social Security numbers
- Government agencies DON'T call demanding payment

---

## 🛠️ Technical Terms

### Malicious URL
**Definition**: Web addresses designed to distribute malware, steal information, or conduct phishing.

**Indicators**:
- Misspelled domains (g00gle.com)
- Unusual TLDs (.tk, .ml, .ga from free hosting)
- IP addresses instead of domains
- Excessive subdomains (legitimate-bank.malicious-site.com)
- URL shorteners hiding true destination

---

### Domain Age
**Definition**: How long a domain has been registered.

**Significance**: Scam sites are often newly registered (< 1 month old) and abandoned after short periods.

---

### SSL/TLS Certificate
**Definition**: Security certificate enabling HTTPS encryption.

**Note**: Having HTTPS doesn't guarantee legitimacy - scammers can obtain free certificates. Check the certificate details and domain ownership.

---

### Safe Browsing API
**Definition**: Google's service that identifies unsafe websites (phishing, malware, unwanted software).

**Used by**: Chrome, Firefox, Safari, and this scam detection tool.

---

### URLhaus
**Definition**: Community-driven database of malicious URLs distributing malware.

**Maintained by**: abuse.ch (a non-profit organization)

---

## 🤖 System Architecture Terms

### Multi-Agent System
**Definition**: AI architecture using multiple specialized agents coordinated by a central orchestrator.

**This System's Agents**:
1. **Orchestrator**: Routes requests and coordinates specialists
2. **Receptionist**: Handles user interaction and context gathering
3. **Text Analyzer**: Analyzes text/images for scam patterns
4. **URL Analyzer**: Checks URLs against safety databases
5. **Report Generator**: Compiles findings into actionable reports
6. **Resource Assistant**: Finds location-specific reporting contacts

---

### LLM-Orchestrated Pattern
**Definition**: Architecture where a Large Language Model dynamically decides which agents to invoke based on request analysis.

**Advantage**: Flexible, intelligent routing without hardcoded logic.

---

### Agent Development Kit (ADK)
**Definition**: Google's framework for building AI agent systems with built-in session management, tool integration, and observability.

**Features**:
- Agent and tool abstractions
- Session persistence
- Multi-turn conversations
- Built-in logging and debugging

---

### Session Persistence
**Definition**: Maintaining conversation context and user state across server restarts.

**Implementation**: DatabaseSessionService stores sessions in SQLite (dev) or PostgreSQL (prod).

---

### Observability
**Definition**: System's ability to expose internal state for monitoring and debugging.

**This System's Approach**:
- Event tracking (agent calls, tool invocations, errors)
- Performance metrics (duration, success rates)
- Dashboard visualization
- DEBUG-level logging for LLM requests/responses

---

## 🚨 Risk Assessment Terms

### Risk Level
**Definition**: Categorization of scam likelihood.

**Levels in This System**:
- **HIGH**: Clear scam indicators, immediate action needed
- **MEDIUM**: Suspicious elements, caution advised
- **LOW**: Likely legitimate but verify before proceeding
- **UNCLEAR**: Insufficient information for assessment

---

### False Positive
**Definition**: System incorrectly flags legitimate content as a scam.

**Mitigation**: Multi-factor analysis, conservative thresholds, human review.

---

### False Negative
**Definition**: System fails to detect an actual scam.

**Mitigation**: Continuous model improvement, database updates, user feedback.

---

## 📞 Reporting Terms

### Local Reporting Contact
**Definition**: Region-specific organizations to report scams.

**Examples**:
- **Australia**: Scamwatch (ACCC)
- **United States**: IC3 (FBI), FTC
- **United Kingdom**: Action Fraud
- **Canada**: Canadian Anti-Fraud Centre

---

### Law Enforcement Liaison
**Definition**: Drafting formal reports for police or regulatory agencies.

**System Feature**: Generates professional email drafts with evidence compilation for submission to authorities.

---

## 🔍 Detection Techniques

### Pattern Recognition
**Definition**: Identifying common scam characteristics through LLM analysis.

**Patterns Detected**:
- Urgency language
- Grammatical errors (non-native speakers)
- Generic greetings
- Suspicious payment requests
- Authority impersonation
- Too-good-to-be-true offers

---

### Multimodal Analysis
**Definition**: Analyzing multiple input types (text, images, audio) simultaneously.

**Advantage**: Scammers often use screenshots or images to evade text-based detection.

---

### Database Cross-Reference
**Definition**: Checking URLs against known malicious databases (Safe Browsing, URLhaus).

**Benefit**: Immediate identification of known threats.

---

## 📚 Additional Resources

### Learn More About Scams
- **FTC Consumer Alerts**: https://consumer.ftc.gov/scams
- **ACCC Scamwatch**: https://www.scamwatch.gov.au/
- **UK Action Fraud**: https://www.actionfraud.police.uk/

### Technical Documentation
- **Google ADK**: https://google.github.io/adk-docs/
- **Safe Browsing API**: https://developers.google.com/safe-browsing
- **URLhaus**: https://urlhaus.abuse.ch/

---

**Last Updated**: November 29, 2025  
**Maintained by**: Scam Detection Tool Team
