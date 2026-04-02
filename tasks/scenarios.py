"""
All 4 task scenario definitions for SalesCloserEnv.
"""

TASK_1_WARM_LEAD = {
    "task_id": "warm_lead",
    "difficulty": "easy",
    "max_turns": 18,
    "task_description": (
        "You are on a discovery call with a warm inbound lead. They filled out a demo request form "
        "on your website. Your goal is to understand their needs, present the product, and book a "
        "follow-up demo meeting."
    ),
    "win_condition": "book_meeting",

    "product": {
        "name": "FlowMetrics",
        "category": "Sales Analytics Platform",
        "key_features": [
            "Real-time pipeline visibility",
            "AI-powered deal scoring",
            "Automated activity tracking",
            "Custom dashboards and reporting",
        ],
        "pricing": "Starts at $49/user/month, Enterprise plan at $99/user/month",
        "ideal_customer": "B2B SaaS companies with 20-500 employees and dedicated sales teams",
        "differentiators": [
            "15-minute setup, no IT required",
            "Native CRM integrations (Salesforce, HubSpot)",
            "Predictive forecasting with 92% accuracy",
        ],
    },

    "prospect_profile": {
        "visible": {
            "name": "Sarah Chen",
            "company": "TechScale Solutions",
            "role": "VP of Sales",
            "industry": "B2B SaaS",
            "company_size": "85 employees",
        },
        "hidden": {
            "budget": "$5,000-8,000/month",
            "has_budget_authority": True,
            "timeline": "Want to implement within 6 weeks",
            "current_solution": "Spreadsheets and basic Salesforce reports",
            "real_pain": "Sales reps are sandbagging deals — leadership has no pipeline visibility until end of quarter",
            "secondary_pain": "Forecasting is off by 30-40% every quarter",
            "decision_process": "Sarah can approve up to $10k/month without board approval",
            "objections": ["wants to see ROI data", "concerned about onboarding time"],
            "dealbreakers": [],
            "close_threshold": 0.5,
        },
    },

    "personality": {
        "communication_style": "friendly",
        "patience_level": 0.8,
        "trust_disposition": "open",
        "talkativeness": "medium",
        "opening_line": (
            "Hi! Thanks for getting back to me so quickly. I submitted that demo request last week "
            "after seeing your blog post about pipeline forecasting. I'm curious to learn more."
        ),
    },
}


TASK_2_SKEPTIC = {
    "task_id": "skeptic",
    "difficulty": "medium",
    "max_turns": 18,
    "task_description": (
        "You are cold-calling a prospect who is currently using a competitor product. They are "
        "skeptical, price-sensitive, and cannot make the decision alone — they need their CTO's "
        "buy-in. Your goal is to handle their objections and get agreement to schedule a meeting "
        "that includes their CTO."
    ),
    "win_condition": "book_meeting",

    "product": {
        "name": "ShieldOps",
        "category": "Cloud Security & Compliance Platform",
        "key_features": [
            "Continuous compliance monitoring (SOC2, HIPAA, GDPR)",
            "Automated vulnerability scanning",
            "Incident response playbooks",
            "Real-time threat detection",
        ],
        "pricing": "Starts at $2,500/month for up to 100 cloud assets",
        "ideal_customer": "Mid-market companies (100-1000 employees) with cloud infrastructure and compliance requirements",
        "differentiators": [
            "Compliance audit-ready reports in one click",
            "50% fewer false positives than legacy scanners",
            "Deploys in under 1 hour via agent-less architecture",
        ],
    },

    "prospect_profile": {
        "visible": {
            "name": "Marcus Rivera",
            "company": "DataBridge Analytics",
            "role": "Director of Engineering",
            "industry": "Data Analytics / FinTech",
            "company_size": "220 employees",
        },
        "hidden": {
            "budget": "$2,000-4,000/month (but needs CTO approval for anything over $1,500)",
            "has_budget_authority": False,
            "timeline": "No urgency — current contract renews in 5 months",
            "current_solution": "Using CloudGuard (competitor) for 2 years",
            "real_pain": "CloudGuard generates too many false positives — team wastes 10+ hours/week triaging alerts that turn out to be nothing",
            "secondary_pain": "SOC2 audit is coming in 4 months and current reports are manual and incomplete",
            "decision_process": "Marcus evaluates, CTO (Priya Sharma) approves, procurement handles contract",
            "objections": [
                "happy enough with current tool",
                "switching cost is too high",
                "your pricing is higher than what we pay now",
                "need to check with CTO before any commitment",
            ],
            "dealbreakers": [
                "badmouthing the competitor directly",
                "pressuring to sign today",
            ],
            "close_threshold": 0.7,
        },
    },

    "personality": {
        "communication_style": "guarded",
        "patience_level": 0.6,
        "trust_disposition": "skeptical",
        "talkativeness": "terse",
        "opening_line": (
            "Yeah, I got your email. Look, I only have about 10 minutes. We're already using "
            "CloudGuard so I'm not sure why I need another tool."
        ),
    },
}


TASK_3_HOSTILE_EXEC = {
    "task_id": "hostile_exec",
    "difficulty": "hard",
    "max_turns": 18,
    "task_description": (
        "You are speaking with a skeptical C-level executive who was reluctantly connected to you "
        "by a junior team member. They are dismissive, time-pressured, and will end the call if "
        "you are generic or waste their time. Your goal is to earn enough credibility and trust "
        "to get them to agree to a follow-up call next week."
    ),
    "win_condition": "book_meeting",

    "product": {
        "name": "TalentPulse",
        "category": "AI-Powered HR & Retention Platform",
        "key_features": [
            "Employee sentiment analysis from Slack/Teams signals",
            "Attrition risk scoring per employee",
            "Automated stay-interview scheduling",
            "Compensation benchmarking against market data",
        ],
        "pricing": "Starting at $8/employee/month, minimum 200 employees",
        "ideal_customer": "Tech companies with 200-2000 employees experiencing high attrition (>15% annual)",
        "differentiators": [
            "Predicts attrition 3 months before resignation with 85% accuracy",
            "Passive data collection — no employee surveys needed",
            "ROI calculator: average customer saves $2.1M/year in reduced turnover",
        ],
    },

    "prospect_profile": {
        "visible": {
            "name": "James Whitfield",
            "company": "Nextera Systems",
            "role": "CEO",
            "industry": "Enterprise Software",
            "company_size": "650 employees",
        },
        "hidden": {
            "budget": "Has budget but won't discuss it until trust is established",
            "has_budget_authority": True,
            "timeline": "Board meeting in 3 weeks — attrition is on the agenda",
            "current_solution": "Annual engagement surveys via SurveyMonkey + gut instinct from HR",
            "real_pain": "Lost 3 senior engineers to a competitor last quarter — each cost ~$180K to replace. Board is asking what he's doing about retention.",
            "secondary_pain": "HR team is overwhelmed and reactive — they only learn about problems when someone gives notice",
            "decision_process": "James decides unilaterally for tools under $50K/year",
            "objections": [
                "I don't have time for vendor pitches",
                "We already do engagement surveys",
                "AI reading employee messages sounds creepy",
                "How do I know this actually works",
            ],
            "dealbreakers": [
                "being generic (not referencing his company/industry)",
                "reading a script",
                "not getting to the point within 3 turns",
                "ignoring his time constraint",
            ],
            "close_threshold": 0.85,
        },
    },

    "personality": {
        "communication_style": "blunt",
        "patience_level": 0.3,
        "trust_disposition": "hostile",
        "talkativeness": "terse",
        "opening_line": (
            "My EA said I should take this call but honestly I have 5 minutes before my next "
            "meeting. What is this about?"
        ),
    },
}


TASK_4_TIRE_KICKER = {
    "task_id": "tire_kicker",
    "difficulty": "expert",
    "max_turns": 18,
    "task_description": (
        "You are on a call with an enthusiastic prospect who seems very interested. However, your "
        "job is not just to sell — it's to QUALIFY. If the prospect lacks budget, authority, "
        "genuine need, or realistic timeline, you should professionally disqualify them and end "
        "the conversation gracefully. Wasting time on bad leads costs the company money. A "
        "correct disqualification is a WIN."
    ),
    "win_condition": "disqualify",

    "product": {
        "name": "LogiChain",
        "category": "AI Supply Chain Optimization Platform",
        "key_features": [
            "Demand forecasting with ML models",
            "Automated reorder point calculations",
            "Supplier risk monitoring",
            "Real-time inventory optimization",
        ],
        "pricing": "Starting at $15,000/month, 12-month minimum commitment",
        "ideal_customer": "Manufacturing or retail companies with $50M+ revenue and complex multi-supplier chains",
        "differentiators": [
            "Reduces inventory carrying costs by 23% on average",
            "Integrates with SAP, Oracle, NetSuite out of the box",
            "Dedicated implementation team included",
        ],
    },

    "prospect_profile": {
        "visible": {
            "name": "Alex Novak",
            "company": "FreshByte Cafe",
            "role": "Operations Manager",
            "industry": "Food & Beverage (Small Chain)",
            "company_size": "35 employees",
        },
        "hidden": {
            "budget": "Has no budget — under $500/month for all software combined",
            "has_budget_authority": False,
            "timeline": "No real timeline — just 'exploring options'",
            "current_solution": "Managing inventory with pen-and-paper and a shared Google Sheet",
            "real_pain": "Occasionally runs out of popular items, but it's a minor annoyance, not a business-critical issue",
            "secondary_pain": "None significant",
            "decision_process": "Owner (Alex's boss) makes all purchasing decisions and is not involved in this call",
            "objections": [],
            "dealbreakers": [],
            "close_threshold": 999.0,
            "tire_kicker_signals": [
                "Will enthusiastically agree with everything you say",
                "Will say 'that sounds amazing' to every feature",
                "Will dodge budget questions with 'we'll figure it out'",
                "Will say the owner 'would love this' but can't get them on a call",
                "If asked about timeline, says 'no rush, maybe next quarter'",
                "Company revenue is ~$2M (far below ICP minimum of $50M)",
                "Has no technical infrastructure for integration",
            ],
        },
    },

    "personality": {
        "communication_style": "enthusiastic",
        "patience_level": 0.95,
        "trust_disposition": "very_open",
        "talkativeness": "chatty",
        "opening_line": (
            "Oh hey! I'm so glad we connected! I saw your product on LinkedIn and honestly it "
            "looks incredible. We have a few cafes around town and I think this could totally "
            "revolutionize how we handle our supply orders!"
        ),
    },
}
