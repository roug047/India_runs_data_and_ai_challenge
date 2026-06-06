# candidate_schema.json

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Redrob Candidate Profile Schema",
  "description": "Schema for a single candidate profile in the Intelligent Candidate Discovery & Ranking Challenge dataset.",
  "type": "object",
  "required": [
    "candidate_id",
    "profile",
    "career_history",
    "education",
    "skills",
    "redrob_signals"
  ],
  "properties": {
    "candidate_id": {
      "type": "string",
      "pattern": "^CAND_[0-9]{7}$",
      "description": "Unique identifier for the candidate. Format: CAND_XXXXXXX (7 digits)."
    },
    "profile": {
      "type": "object",
      "required": [
        "anonymized_name",
        "headline",
        "summary",
        "location",
        "country",
        "years_of_experience",
        "current_title",
        "current_company",
        "current_company_size",
        "current_industry"
      ],
      "properties": {
        "anonymized_name": { "type": "string", "description": "Anonymized full name." },
        "headline": { "type": "string", "description": "One-line professional headline." },
        "summary": { "type": "string", "description": "Multi-sentence professional summary." },
        "location": { "type": "string", "description": "City, region/state." },
        "country": { "type": "string" },
        "years_of_experience": { "type": "number", "minimum": 0, "maximum": 50 },
        "current_title": { "type": "string" },
        "current_company": { "type": "string" },
        "current_company_size": {
          "type": "string",
          "enum": ["1-10", "11-50", "51-200", "201-500", "501-1000", "1001-5000", "5001-10000", "10001+"]
        },
        "current_industry": { "type": "string" }
      }
    },
    "career_history": {
      "type": "array",
      "minItems": 1,
      "maxItems": 10,
      "items": {
        "type": "object",
        "required": ["company", "title", "start_date", "end_date", "duration_months", "is_current", "industry", "company_size", "description"],
        "properties": {
          "company": { "type": "string" },
          "title": { "type": "string" },
          "start_date": { "type": "string", "format": "date" },
          "end_date": { "type": ["string", "null"], "format": "date" },
          "duration_months": { "type": "integer", "minimum": 0 },
          "is_current": { "type": "boolean" },
          "industry": { "type": "string" },
          "company_size": {
            "type": "string",
            "enum": ["1-10", "11-50", "51-200", "201-500", "501-1000", "1001-5000", "5001-10000", "10001+"]
          },
          "description": { "type": "string", "description": "Role responsibilities and achievements." }
        }
      }
    },
    "education": {
      "type": "array",
      "minItems": 0,
      "maxItems": 5,
      "items": {
        "type": "object",
        "required": ["institution", "degree", "field_of_study", "start_year", "end_year"],
        "properties": {
          "institution": { "type": "string" },
          "degree": { "type": "string" },
          "field_of_study": { "type": "string" },
          "start_year": { "type": "integer", "minimum": 1970, "maximum": 2030 },
          "end_year": { "type": "integer", "minimum": 1970, "maximum": 2035 },
          "grade": { "type": ["string", "null"], "description": "GPA / percentage / class." },
          "tier": {
            "type": "string",
            "enum": ["tier_1", "tier_2", "tier_3", "tier_4", "unknown"],
            "description": "Internal tiering for institution prestige."
          }
        }
      }
    },
    "skills": {
      "type": "array",
      "minItems": 0,
      "items": {
        "type": "object",
        "required": ["name", "proficiency", "endorsements"],
        "properties": {
          "name": { "type": "string" },
          "proficiency": {
            "type": "string",
            "enum": ["beginner", "intermediate", "advanced", "expert"]
          },
          "endorsements": { "type": "integer", "minimum": 0 },
          "duration_months": { "type": "integer", "minimum": 0, "description": "Months the candidate has used this skill" }
        }
      }
    },
    "certifications": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "issuer", "year"],
        "properties": {
          "name": { "type": "string" },
          "issuer": { "type": "string" },
          "year": { "type": "integer" }
        }
      }
    },
    "languages": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["language", "proficiency"],
        "properties": {
          "language": { "type": "string" },
          "proficiency": {
            "type": "string",
            "enum": ["basic", "conversational", "professional", "native"]
          }
        }
      }
    },
    "redrob_signals": {
      "type": "object",
      "description": "Simulated platform activity and engagement signals from the Redrob ecosystem.",
      "required": [
        "profile_completeness_score",
        "signup_date",
        "last_active_date",
        "open_to_work_flag",
        "profile_views_received_30d",
        "applications_submitted_30d",
        "recruiter_response_rate",
        "avg_response_time_hours",
        "skill_assessment_scores",
        "connection_count",
        "endorsements_received",
        "notice_period_days",
        "expected_salary_range_inr_lpa",
        "preferred_work_mode",
        "willing_to_relocate",
        "github_activity_score",
        "search_appearance_30d",
        "saved_by_recruiters_30d",
        "interview_completion_rate",
        "offer_acceptance_rate",
        "verified_email",
        "verified_phone",
        "linkedin_connected"
      ],
      "properties": {
        "profile_completeness_score": {
          "type": "number",
          "minimum": 0,
          "maximum": 100,
          "description": "Percentage of profile completeness."
        },
        "signup_date": { "type": "string", "format": "date" },
        "last_active_date": { "type": "string", "format": "date" },
        "open_to_work_flag": { "type": "boolean" },
        "profile_views_received_30d": { "type": "integer", "minimum": 0 },
        "applications_submitted_30d": { "type": "integer", "minimum": 0 },
        "recruiter_response_rate": {
          "type": "number",
          "minimum": 0,
          "maximum": 1,
          "description": "Fraction of recruiter messages the candidate has responded to."
        },
        "avg_response_time_hours": { "type": "number", "minimum": 0 },
        "skill_assessment_scores": {
          "type": "object",
          "description": "Dict of skill_name -> score 0-100. Assessments completed on Redrob platform.",
          "additionalProperties": { "type": "number", "minimum": 0, "maximum": 100 }
        },
        "connection_count": { "type": "integer", "minimum": 0 },
        "endorsements_received": { "type": "integer", "minimum": 0 },
        "notice_period_days": { "type": "integer", "minimum": 0, "maximum": 180 },
        "expected_salary_range_inr_lpa": {
          "type": "object",
          "required": ["min", "max"],
          "properties": {
            "min": { "type": "number", "minimum": 0 },
            "max": { "type": "number", "minimum": 0 }
          },
          "description": "Expected salary in INR Lakhs Per Annum."
        },
        "preferred_work_mode": {
          "type": "string",
          "enum": ["remote", "hybrid", "onsite", "flexible"]
        },
        "willing_to_relocate": { "type": "boolean" },
        "github_activity_score": {
          "type": "number",
          "minimum": -1,
          "maximum": 100,
          "description": "0-100 score based on commits, PRs, stars in last 12 months. -1 if no GitHub linked."
        },
        "search_appearance_30d": {
          "type": "integer",
          "minimum": 0,
          "description": "Number of times profile appeared in recruiter searches in last 30 days."
        },
        "saved_by_recruiters_30d": {
          "type": "integer",
          "minimum": 0,
          "description": "Number of recruiters who saved this profile in last 30 days."
        },
        "interview_completion_rate": {
          "type": "number",
          "minimum": 0,
          "maximum": 1,
          "description": "Fraction of scheduled interviews actually attended."
        },
        "offer_acceptance_rate": {
          "type": "number",
          "minimum": -1,
          "maximum": 1,
          "description": "Historical offer acceptance rate. -1 if no offer history."
        },
        "verified_email": { "type": "boolean" },
        "verified_phone": { "type": "boolean" },
        "linkedin_connected": { "type": "boolean" }
      }
    }
  }
}

```


# sample_candidates.json

```json
[
  {
    "candidate_id": "CAND_0000001",
    "profile": {
      "anonymized_name": "Ira Vora",
      "headline": "Backend Engineer | SQL, Spark, Cloud",
      "summary": "Software / data professional with 6.9 years of experience building data pipelines, backend systems, and analytics infrastructure. I'm a backend/data hybrid \u2014 Spark, Airflow, SQL warehouses are home territory; I'm building competence on the ML side. My toolkit is solid on the data engineering side \u2014 Python, SQL, Spark, Airflow, warehouse design \u2014 and I've completed a couple of self-directed ML projects (Kaggle competitions, side projects fine-tuning small models). Interested in transitioning toward more AI/ML-focused work, ideally at a company where I can leverage my existing data-infra skills while learning modern ML practice.",
      "location": "Toronto",
      "country": "Canada",
      "years_of_experience": 6.9,
      "current_title": "Backend Engineer",
      "current_company": "Mindtree",
      "current_company_size": "10001+",
      "current_industry": "IT Services"
    },
    "career_history": [
      {
        "company": "Mindtree",
        "title": "Backend Engineer",
        "start_date": "2024-03-08",
        "end_date": null,
        "duration_months": 27,
        "is_current": true,
        "industry": "IT Services",
        "company_size": "10001+",
        "description": "Implemented streaming data pipelines on Kafka and Spark Streaming for a real-time user-activity processing platform. Designed the schema-registry integration, the watermark/state management approach, and the deduplication logic for late-arriving events. Worked closely with the data science team to make sure feature pipelines aligned with what their models needed. Most of my career has been data engineering, with some adjacent ML exposure."
      },
      {
        "company": "Dunder Mifflin",
        "title": "Analytics Engineer",
        "start_date": "2019-07-03",
        "end_date": "2024-01-08",
        "duration_months": 55,
        "is_current": false,
        "industry": "Paper Products",
        "company_size": "201-500",
        "description": "Built and maintained data pipelines on Apache Airflow processing ~500GB of daily transactional data across 12 source systems. Worked extensively with Spark (PySpark) for batch processing and dbt for the transformation/modeling layer in our Snowflake warehouse. Owned the on-call rotation for data quality issues \u2014 wrote most of the data quality checks that detect schema drift and unusual volume changes. The pipeline supports the analytics team and a few internal ML models."
      }
    ],
    "education": [
      {
        "institution": "Lovely Professional University",
        "degree": "B.E.",
        "field_of_study": "Computer Science",
        "start_year": 2017,
        "end_year": 2020,
        "grade": "8.24 CGPA",
        "tier": "tier_3"
      }
    ],
    "skills": [
      {
        "name": "Tailwind",
        "proficiency": "intermediate",
        "endorsements": 3,
        "duration_months": 13
      },
      {
        "name": "NLP",
        "proficiency": "advanced",
        "endorsements": 37,
        "duration_months": 26
      },
      {
        "name": "Image Classification",
        "proficiency": "advanced",
        "endorsements": 7,
        "duration_months": 40
      },
      {
        "name": "Fine-tuning LLMs",
        "proficiency": "advanced",
        "endorsements": 21,
        "duration_months": 36
      },
      {
        "name": "Weights & Biases",
        "proficiency": "intermediate",
        "endorsements": 13,
        "duration_months": 30
      },
      {
        "name": "Speech Recognition",
        "proficiency": "advanced",
        "endorsements": 52,
        "duration_months": 33
      },
      {
        "name": "Photoshop",
        "proficiency": "intermediate",
        "endorsements": 8,
        "duration_months": 24
      },
      {
        "name": "TTS",
        "proficiency": "advanced",
        "endorsements": 56,
        "duration_months": 60
      },
      {
        "name": "LoRA",
        "proficiency": "intermediate",
        "endorsements": 0,
        "duration_months": 28
      },
      {
        "name": "Apache Beam",
        "proficiency": "intermediate",
        "endorsements": 4,
        "duration_months": 9
      },
      {
        "name": "AWS",
        "proficiency": "beginner",
        "endorsements": 5,
        "duration_months": 8
      },
      {
        "name": "Flask",
        "proficiency": "beginner",
        "endorsements": 15,
        "duration_months": 15
      },
      {
        "name": "BentoML",
        "proficiency": "intermediate",
        "endorsements": 3,
        "duration_months": 36
      },
      {
        "name": "Milvus",
        "proficiency": "advanced",
        "endorsements": 40,
        "duration_months": 35
      },
      {
        "name": "GANs",
        "proficiency": "advanced",
        "endorsements": 12,
        "duration_months": 19
      },
      {
        "name": "Statistical Modeling",
        "proficiency": "intermediate",
        "endorsements": 9,
        "duration_months": 8
      },
      {
        "name": "GCP",
        "proficiency": "beginner",
        "endorsements": 7,
        "duration_months": 2
      }
    ],
    "certifications": [],
    "languages": [
      {
        "language": "English",
        "proficiency": "professional"
      },
      {
        "language": "Hindi",
        "proficiency": "conversational"
      }
    ],
    "redrob_signals": {
      "profile_completeness_score": 86.9,
      "signup_date": "2025-10-16",
      "last_active_date": "2026-05-20",
      "open_to_work_flag": true,
      "profile_views_received_30d": 23,
      "applications_submitted_30d": 2,
      "recruiter_response_rate": 0.34,
      "avg_response_time_hours": 177.8,
      "skill_assessment_scores": {
        "NLP": 38.8,
        "Image Classification": 64.8,
        "Fine-tuning LLMs": 41.6,
        "Speech Recognition": 53.7
      },
      "connection_count": 356,
      "endorsements_received": 35,
      "notice_period_days": 60,
      "expected_salary_range_inr_lpa": {
        "min": 18.7,
        "max": 36.1
      },
      "preferred_work_mode": "onsite",
      "willing_to_relocate": false,
      "github_activity_score": 9.2,
      "search_appearance_30d": 249,
      "saved_by_recruiters_30d": 4,
      "interview_completion_rate": 0.71,
      "offer_acceptance_rate": 0.58,
      "verified_email": true,
      "verified_phone": true,
      "linkedin_connected": false
    }
  },
  {
    "candidate_id": "CAND_0000002",
    "profile": {
      "anonymized_name": "Saanvi Sethi",
      "headline": "Operations Manager | 12.5+ yrs experience",
      "summary": "Professional with 12.5+ years of experience. My professional background is in marketing manager \u2014 I've built and led teams, owned KPIs, and driven business outcomes in this domain. Lately I've been curious about how AI tools could augment my work \u2014 I've experimented with ChatGPT and a few other tools for productivity and content creation, and I think the space is exciting. Open to roles where I can apply my domain expertise alongside emerging AI capabilities.",
      "location": "Chennai, Tamil Nadu",
      "country": "India",
      "years_of_experience": 12.5,
      "current_title": "Operations Manager",
      "current_company": "Wipro",
      "current_company_size": "10001+",
      "current_industry": "IT Services"
    },
    "career_history": [
      {
        "company": "Wipro",
        "title": "Operations Manager",
        "start_date": "2022-11-14",
        "end_date": null,
        "duration_months": 43,
        "is_current": true,
        "industry": "IT Services",
        "company_size": "10001+",
        "description": "Customer support team lead at a SaaS product. Managed a team of 8 support agents handling tier-1 and tier-2 tickets; owned the escalation process to engineering and the customer-feedback loop to product. Built out the support knowledge base and the agent training program. Strong on the people-management side and the process side; lighter on technical depth beyond product expertise."
      },
      {
        "company": "Wipro",
        "title": "Operations Manager",
        "start_date": "2021-09-13",
        "end_date": "2022-11-07",
        "duration_months": 14,
        "is_current": false,
        "industry": "IT Services",
        "company_size": "10001+",
        "description": "Mechanical engineering design role at a hardware-product company. Led the design of two product subsystems through full lifecycle: concept, DFM/DFMA review, prototype, production tooling. Comfortable with CAD (SolidWorks, Creo), FEA (ANSYS), and the typical hardware-development cadence. Worked closely with manufacturing partners on production scale-up."
      },
      {
        "company": "Acme Corp",
        "title": "Marketing Manager",
        "start_date": "2017-03-08",
        "end_date": "2021-08-14",
        "duration_months": 54,
        "is_current": false,
        "industry": "Manufacturing",
        "company_size": "201-500",
        "description": "Content writing and SEO strategy for a tech-focused publication. Wrote longform articles on developer tools, cloud platforms, and AI/ML topics \u2014 including some that ranked on the first page of search for high-competition keywords. Managed a freelance writer pool and the editorial calendar. Recent work has been on AI-assisted content production, using LLM tools for research, drafting, and editing while maintaining editorial quality."
      },
      {
        "company": "Dunder Mifflin",
        "title": "Marketing Manager",
        "start_date": "2014-01-23",
        "end_date": "2017-03-08",
        "duration_months": 38,
        "is_current": false,
        "industry": "Paper Products",
        "company_size": "201-500",
        "description": "Brand design and creative direction at a consumer-products company. Owned brand identity (logo, visual system, typography), packaging design, and digital creative across web and social. Led the recent rebrand and managed a small external agency for production work. Comfortable across the Adobe suite, Figma, and the production side of brand and packaging design."
      }
    ],
    "education": [
      {
        "institution": "Local Engineering College",
        "degree": "B.Sc",
        "field_of_study": "Mathematics",
        "start_year": 2007,
        "end_year": 2011,
        "grade": "77%",
        "tier": "tier_4"
      }
    ],
    "skills": [
      {
        "name": "Project Management",
        "proficiency": "intermediate",
        "endorsements": 14,
        "duration_months": 23
      },
      {
        "name": "React",
        "proficiency": "intermediate",
        "endorsements": 6,
        "duration_months": 35
      },
      {
        "name": "Photoshop",
        "proficiency": "intermediate",
        "endorsements": 9,
        "duration_months": 35
      },
      {
        "name": "TypeScript",
        "proficiency": "beginner",
        "endorsements": 2,
        "duration_months": 3
      },
      {
        "name": "Marketing",
        "proficiency": "beginner",
        "endorsements": 9,
        "duration_months": 11
      },
      {
        "name": "Kafka",
        "proficiency": "intermediate",
        "endorsements": 3,
        "duration_months": 16
      },
      {
        "name": "JavaScript",
        "proficiency": "beginner",
        "endorsements": 9,
        "duration_months": 3
      },
      {
        "name": "Feature Engineering",
        "proficiency": "intermediate",
        "endorsements": 11,
        "duration_months": 27
      },
      {
        "name": "GCP",
        "proficiency": "intermediate",
        "endorsements": 7,
        "duration_months": 30
      }
    ],
    "certifications": [],
    "languages": [
      {
        "language": "English",
        "proficiency": "professional"
      },
      {
        "language": "Hindi",
        "proficiency": "conversational"
      }
    ],
    "redrob_signals": {
      "profile_completeness_score": 78.7,
      "signup_date": "2025-07-28",
      "last_active_date": "2025-11-12",
      "open_to_work_flag": true,
      "profile_views_received_30d": 7,
      "applications_submitted_30d": 1,
      "recruiter_response_rate": 0.29,
      "avg_response_time_hours": 171.6,
      "skill_assessment_scores": {},
      "connection_count": 179,
      "endorsements_received": 3,
      "notice_period_days": 60,
      "expected_salary_range_inr_lpa": {
        "min": 8.8,
        "max": 9.0
      },
      "preferred_work_mode": "flexible",
      "willing_to_relocate": false,
      "github_activity_score": -1,
      "search_appearance_30d": 107,
      "saved_by_recruiters_30d": 10,
      "interview_completion_rate": 0.62,
      "offer_acceptance_rate": -1,
      "verified_email": false,
      "verified_phone": false,
      "linkedin_connected": false
    }
  },
  {
    "candidate_id": "CAND_0000003",
    "profile": {
      "anonymized_name": "Yash Agarwal",
      "headline": "Customer Support | 1.1+ yrs experience",
      "summary": "Professional with 1.1+ years of experience. I've spent my career in marketing manager roles, mostly focused on driving outcomes through process, people, and customer relationships. Lately I've been curious about how AI tools could augment my work \u2014 I've experimented with ChatGPT and a few other tools for productivity and content creation, and I think the space is exciting. Open to roles where I can apply my domain expertise alongside emerging AI capabilities.",
      "location": "Austin",
      "country": "USA",
      "years_of_experience": 1.1,
      "current_title": "Customer Support",
      "current_company": "TCS",
      "current_company_size": "10001+",
      "current_industry": "IT Services"
    },
    "career_history": [
      {
        "company": "TCS",
        "title": "Customer Support",
        "start_date": "2025-05-02",
        "end_date": null,
        "duration_months": 13,
        "is_current": true,
        "industry": "IT Services",
        "company_size": "10001+",
        "description": "Business analyst at a consulting firm, working primarily with retail and CPG clients. Conducted business diagnostics, process re-engineering work, and digital transformation strategy projects. Strong on stakeholder management, structured problem-solving, and the typical consulting toolkit (slide-craft, Excel modeling, executive communication). Recent project work involved AI-strategy advisory but my own technical depth in AI is limited."
      }
    ],
    "education": [
      {
        "institution": "Local Engineering College",
        "degree": "M.E.",
        "field_of_study": "Chemical Engineering",
        "start_year": 2005,
        "end_year": 2010,
        "grade": "6.82 CGPA",
        "tier": "tier_4"
      },
      {
        "institution": "Chandigarh University",
        "degree": "M.Sc",
        "field_of_study": "Information Technology",
        "start_year": 2017,
        "end_year": 2021,
        "grade": "87%",
        "tier": "tier_3"
      }
    ],
    "skills": [
      {
        "name": "Angular",
        "proficiency": "intermediate",
        "endorsements": 13,
        "duration_months": 10
      },
      {
        "name": "SEO",
        "proficiency": "beginner",
        "endorsements": 11,
        "duration_months": 11
      },
      {
        "name": "Excel",
        "proficiency": "intermediate",
        "endorsements": 2,
        "duration_months": 15
      },
      {
        "name": "Accounting",
        "proficiency": "beginner",
        "endorsements": 7,
        "duration_months": 18
      },
      {
        "name": "Kubernetes",
        "proficiency": "intermediate",
        "endorsements": 0,
        "duration_months": 34
      },
      {
        "name": "Databricks",
        "proficiency": "beginner",
        "endorsements": 14,
        "duration_months": 18
      }
    ],
    "certifications": [],
    "languages": [
      {
        "language": "English",
        "proficiency": "professional"
      },
      {
        "language": "Hindi",
        "proficiency": "professional"
      }
    ],
    "redrob_signals": {
      "profile_completeness_score": 31.9,
      "signup_date": "2024-08-02",
      "last_active_date": "2026-03-21",
      "open_to_work_flag": false,
      "profile_views_received_30d": 1,
      "applications_submitted_30d": 9,
      "recruiter_response_rate": 0.46,
      "avg_response_time_hours": 119.4,
      "skill_assessment_scores": {},
      "connection_count": 19,
      "endorsements_received": 46,
      "notice_period_days": 150,
      "expected_salary_range_inr_lpa": {
        "min": 11.2,
        "max": 18.1
      },
      "preferred_work_mode": "hybrid",
      "willing_to_relocate": false,
      "github_activity_score": -1,
      "search_appearance_30d": 28,
      "saved_by_recruiters_30d": 4,
      "interview_completion_rate": 0.86,
      "offer_acceptance_rate": -1,
      "verified_email": true,
      "verified_phone": false,
      "linkedin_connected": false
    }
  },
  {
    "candidate_id": "CAND_0000004",
    "profile": {
      "anonymized_name": "Anil Bose",
      "headline": "Marketing Manager | Driving business outcomes",
      "summary": "Professional with 3.8+ years of experience. My professional background is in marketing manager \u2014 I've built and led teams, owned KPIs, and driven business outcomes in this domain. Lately I've been curious about how AI tools could augment my work \u2014 I've experimented with ChatGPT and a few other tools for productivity and content creation, and I think the space is exciting. Open to roles where I can apply my domain expertise alongside emerging AI capabilities.",
      "location": "Sydney",
      "country": "Australia",
      "years_of_experience": 3.8,
      "current_title": "Marketing Manager",
      "current_company": "Dunder Mifflin",
      "current_company_size": "201-500",
      "current_industry": "Paper Products"
    },
    "career_history": [
      {
        "company": "Dunder Mifflin",
        "title": "Marketing Manager",
        "start_date": "2025-04-02",
        "end_date": null,
        "duration_months": 14,
        "is_current": true,
        "industry": "Paper Products",
        "company_size": "201-500",
        "description": "Mechanical engineering design role at a hardware-product company. Led the design of two product subsystems through full lifecycle: concept, DFM/DFMA review, prototype, production tooling. Comfortable with CAD (SolidWorks, Creo), FEA (ANSYS), and the typical hardware-development cadence. Worked closely with manufacturing partners on production scale-up."
      },
      {
        "company": "Infosys",
        "title": "Operations Manager",
        "start_date": "2023-07-28",
        "end_date": "2025-03-19",
        "duration_months": 20,
        "is_current": false,
        "industry": "IT Services",
        "company_size": "10001+",
        "description": "Content writing and SEO strategy for a tech-focused publication. Wrote longform articles on developer tools, cloud platforms, and AI/ML topics \u2014 including some that ranked on the first page of search for high-competition keywords. Managed a freelance writer pool and the editorial calendar. Recent work has been on AI-assisted content production, using LLM tools for research, drafting, and editing while maintaining editorial quality."
      },
      {
        "company": "Globex Inc",
        "title": "Business Analyst",
        "start_date": "2022-08-02",
        "end_date": "2023-05-29",
        "duration_months": 10,
        "is_current": false,
        "industry": "Manufacturing",
        "company_size": "501-1000",
        "description": "Operations management role at a logistics company. Owned daily fulfillment operations across 3 warehouses, managing a team of 80 across receiving, picking, packing, and outbound. Built and tracked the operational KPIs (on-time fulfillment, accuracy, cost per order) and led the continuous improvement initiatives that drove a 22% productivity gain over 18 months."
      }
    ],
    "education": [
      {
        "institution": "Local Engineering College",
        "degree": "B.Tech",
        "field_of_study": "Machine Learning",
        "start_year": 2015,
        "end_year": 2019,
        "grade": "7.72 CGPA",
        "tier": "tier_4"
      },
      {
        "institution": "Lovely Professional University",
        "degree": "Ph.D",
        "field_of_study": "Electronics",
        "start_year": 2013,
        "end_year": 2016,
        "grade": "7.61 CGPA",
        "tier": "tier_3"
      }
    ],
    "skills": [
      {
        "name": "Node.js",
        "proficiency": "intermediate",
        "endorsements": 1,
        "duration_months": 20
      },
      {
        "name": "Content Writing",
        "proficiency": "beginner",
        "endorsements": 7,
        "duration_months": 3
      },
      {
        "name": "Redux",
        "proficiency": "beginner",
        "endorsements": 14,
        "duration_months": 8
      },
      {
        "name": "Airflow",
        "proficiency": "intermediate",
        "endorsements": 11,
        "duration_months": 27
      },
      {
        "name": "GraphQL",
        "proficiency": "beginner",
        "endorsements": 13,
        "duration_months": 2
      },
      {
        "name": "Object Detection",
        "proficiency": "intermediate",
        "endorsements": 3,
        "duration_months": 17
      },
      {
        "name": "Webpack",
        "proficiency": "beginner",
        "endorsements": 10,
        "duration_months": 7
      },
      {
        "name": "Six Sigma",
        "proficiency": "beginner",
        "endorsements": 1,
        "duration_months": 12
      },
      {
        "name": "SAP",
        "proficiency": "intermediate",
        "endorsements": 6,
        "duration_months": 9
      },
      {
        "name": "JavaScript",
        "proficiency": "intermediate",
        "endorsements": 14,
        "duration_months": 29
      }
    ],
    "certifications": [
      {
        "name": "AWS Certified Cloud Practitioner",
        "issuer": "AWS",
        "year": 2025
      },
      {
        "name": "Scrum Master Certified",
        "issuer": "Scrum Alliance",
        "year": 2025
      }
    ],
    "languages": [
      {
        "language": "English",
        "proficiency": "professional"
      },
      {
        "language": "Hindi",
        "proficiency": "professional"
      }
    ],
    "redrob_signals": {
      "profile_completeness_score": 28.5,
      "signup_date": "2025-07-21",
      "last_active_date": "2026-03-25",
      "open_to_work_flag": false,
      "profile_views_received_30d": 3,
      "applications_submitted_30d": 9,
      "recruiter_response_rate": 0.26,
      "avg_response_time_hours": 104.1,
      "skill_assessment_scores": {},
      "connection_count": 485,
      "endorsements_received": 22,
      "notice_period_days": 120,
      "expected_salary_range_inr_lpa": {
        "min": 4.6,
        "max": 6.7
      },
      "preferred_work_mode": "onsite",
      "willing_to_relocate": true,
      "github_activity_score": -1,
      "search_appearance_30d": 5,
      "saved_by_recruiters_30d": 8,
      "interview_completion_rate": 0.35,
      "offer_acceptance_rate": -1,
      "verified_email": true,
      "verified_phone": true,
      "linkedin_connected": true
    }
  },
  {
    "candidate_id": "CAND_0000005",
    "profile": {
      "anonymized_name": "Aisha Sethi",
      "headline": "Accountant | Helping teams scale",
      "summary": "Professional with 11.0+ years of experience. I've spent my career in marketing manager roles, mostly focused on driving outcomes through process, people, and customer relationships. Lately I've been curious about how AI tools could augment my work \u2014 I've experimented with ChatGPT and a few other tools for productivity and content creation, and I think the space is exciting. Open to roles where I can apply my domain expertise alongside emerging AI capabilities.",
      "location": "Gurgaon, Haryana",
      "country": "India",
      "years_of_experience": 11.0,
      "current_title": "Accountant",
      "current_company": "Stark Industries",
      "current_company_size": "1001-5000",
      "current_industry": "Manufacturing"
    },
    "career_history": [
      {
        "company": "Stark Industries",
        "title": "Accountant",
        "start_date": "2022-02-17",
        "end_date": null,
        "duration_months": 52,
        "is_current": true,
        "industry": "Manufacturing",
        "company_size": "1001-5000",
        "description": "Business analyst at a consulting firm, working primarily with retail and CPG clients. Conducted business diagnostics, process re-engineering work, and digital transformation strategy projects. Strong on stakeholder management, structured problem-solving, and the typical consulting toolkit (slide-craft, Excel modeling, executive communication). Recent project work involved AI-strategy advisory but my own technical depth in AI is limited."
      },
      {
        "company": "Wipro",
        "title": "HR Manager",
        "start_date": "2018-05-25",
        "end_date": "2022-02-03",
        "duration_months": 45,
        "is_current": false,
        "industry": "IT Services",
        "company_size": "10001+",
        "description": "Senior accounting role at a mid-sized company \u2014 month-end close, financial reporting, statutory compliance (GAAP / Ind-AS), and tax filings. Owned the GL, fixed-asset register, and the audit-readiness function. Managed a team of 3 staff accountants. Built strong process discipline around the close cycle, reducing close time from 12 days to 7 over the last two years."
      },
      {
        "company": "Initech",
        "title": "HR Manager",
        "start_date": "2016-06-04",
        "end_date": "2018-05-25",
        "duration_months": 24,
        "is_current": false,
        "industry": "Software",
        "company_size": "51-200",
        "description": "Business analyst at a consulting firm, working primarily with retail and CPG clients. Conducted business diagnostics, process re-engineering work, and digital transformation strategy projects. Strong on stakeholder management, structured problem-solving, and the typical consulting toolkit (slide-craft, Excel modeling, executive communication). Recent project work involved AI-strategy advisory but my own technical depth in AI is limited."
      },
      {
        "company": "TCS",
        "title": "Accountant",
        "start_date": "2015-09-08",
        "end_date": "2016-06-04",
        "duration_months": 9,
        "is_current": false,
        "industry": "IT Services",
        "company_size": "10001+",
        "description": "Customer support team lead at a SaaS product. Managed a team of 8 support agents handling tier-1 and tier-2 tickets; owned the escalation process to engineering and the customer-feedback loop to product. Built out the support knowledge base and the agent training program. Strong on the people-management side and the process side; lighter on technical depth beyond product expertise."
      }
    ],
    "education": [
      {
        "institution": "Chandigarh University",
        "degree": "M.Sc",
        "field_of_study": "Information Technology",
        "start_year": 2007,
        "end_year": 2012,
        "grade": "87%",
        "tier": "tier_3"
      }
    ],
    "skills": [
      {
        "name": "SQL",
        "proficiency": "beginner",
        "endorsements": 12,
        "duration_months": 12
      },
      {
        "name": "PowerPoint",
        "proficiency": "beginner",
        "endorsements": 6,
        "duration_months": 14
      },
      {
        "name": "Photoshop",
        "proficiency": "beginner",
        "endorsements": 4,
        "duration_months": 18
      },
      {
        "name": "Tailwind",
        "proficiency": "intermediate",
        "endorsements": 15,
        "duration_months": 35
      },
      {
        "name": "Apache Flink",
        "proficiency": "intermediate",
        "endorsements": 1,
        "duration_months": 30
      },
      {
        "name": "Image Classification",
        "proficiency": "advanced",
        "endorsements": 50,
        "duration_months": 38
      }
    ],
    "certifications": [],
    "languages": [
      {
        "language": "English",
        "proficiency": "professional"
      },
      {
        "language": "Hindi",
        "proficiency": "conversational"
      }
    ],
    "redrob_signals": {
      "profile_completeness_score": 84.6,
      "signup_date": "2023-10-07",
      "last_active_date": "2025-10-01",
      "open_to_work_flag": true,
      "profile_views_received_30d": 12,
      "applications_submitted_30d": 2,
      "recruiter_response_rate": 0.37,
      "avg_response_time_hours": 116.7,
      "skill_assessment_scores": {},
      "connection_count": 300,
      "endorsements_received": 14,
      "notice_period_days": 30,
      "expected_salary_range_inr_lpa": {
        "min": 12.4,
        "max": 19.7
      },
      "preferred_work_mode": "hybrid",
      "willing_to_relocate": true,
      "github_activity_score": -1,
      "search_appearance_30d": 67,
      "saved_by_recruiters_30d": 1,
      "interview_completion_rate": 0.74,
      "offer_acceptance_rate": -1,
      "verified_email": false,
      "verified_phone": true,
      "linkedin_connected": true
    }
  },
  {
    "candidate_id": "CAND_0000006",
    "profile": {
      "anonymized_name": "Rajesh Desai",
      "headline": "Business Analyst | 6.0+ yrs experience",
      "summary": "Professional with 6.0+ years of experience. I've spent my career in marketing manager roles, mostly focused on driving outcomes through process, people, and customer relationships. Lately I've been curious about how AI tools could augment my work \u2014 I've experimented with ChatGPT and a few other tools for productivity and content creation, and I think the space is exciting. Open to roles where I can apply my domain expertise alongside emerging AI capabilities.",
      "location": "Austin",
      "country": "USA",
      "years_of_experience": 6.0,
      "current_title": "Business Analyst",
      "current_company": "Wayne Enterprises",
      "current_company_size": "10001+",
      "current_industry": "Conglomerate"
    },
    "career_history": [
      {
        "company": "Wayne Enterprises",
        "title": "Business Analyst",
        "start_date": "2023-09-10",
        "end_date": null,
        "duration_months": 33,
        "is_current": true,
        "industry": "Conglomerate",
        "company_size": "10001+",
        "description": "Senior accounting role at a mid-sized company \u2014 month-end close, financial reporting, statutory compliance (GAAP / Ind-AS), and tax filings. Owned the GL, fixed-asset register, and the audit-readiness function. Managed a team of 3 staff accountants. Built strong process discipline around the close cycle, reducing close time from 12 days to 7 over the last two years."
      },
      {
        "company": "Pied Piper",
        "title": "Mechanical Engineer",
        "start_date": "2020-07-27",
        "end_date": "2023-09-10",
        "duration_months": 38,
        "is_current": false,
        "industry": "Software",
        "company_size": "11-50",
        "description": "Business analyst at a consulting firm, working primarily with retail and CPG clients. Conducted business diagnostics, process re-engineering work, and digital transformation strategy projects. Strong on stakeholder management, structured problem-solving, and the typical consulting toolkit (slide-craft, Excel modeling, executive communication). Recent project work involved AI-strategy advisory but my own technical depth in AI is limited."
      }
    ],
    "education": [
      {
        "institution": "Lovely Professional University",
        "degree": "B.Sc",
        "field_of_study": "Artificial Intelligence",
        "start_year": 2005,
        "end_year": 2008,
        "grade": "9.26 CGPA",
        "tier": "tier_3"
      }
    ],
    "skills": [
      {
        "name": "Content Writing",
        "proficiency": "intermediate",
        "endorsements": 0,
        "duration_months": 33
      },
      {
        "name": "SEO",
        "proficiency": "intermediate",
        "endorsements": 13,
        "duration_months": 31
      },
      {
        "name": "Redux",
        "proficiency": "beginner",
        "endorsements": 15,
        "duration_months": 12
      },
      {
        "name": "SQL",
        "proficiency": "beginner",
        "endorsements": 9,
        "duration_months": 11
      },
      {
        "name": "Sales",
        "proficiency": "intermediate",
        "endorsements": 5,
        "duration_months": 27
      },
      {
        "name": "gRPC",
        "proficiency": "beginner",
        "endorsements": 8,
        "duration_months": 3
      },
      {
        "name": "Django",
        "proficiency": "intermediate",
        "endorsements": 3,
        "duration_months": 11
      },
      {
        "name": "Terraform",
        "proficiency": "beginner",
        "endorsements": 4,
        "duration_months": 13
      }
    ],
    "certifications": [],
    "languages": [
      {
        "language": "English",
        "proficiency": "professional"
      },
      {
        "language": "Hindi",
        "proficiency": "conversational"
      }
    ],
    "redrob_signals": {
      "profile_completeness_score": 29.7,
      "signup_date": "2026-04-26",
      "last_active_date": "2026-02-28",
      "open_to_work_flag": false,
      "profile_views_received_30d": 53,
      "applications_submitted_30d": 8,
      "recruiter_response_rate": 0.12,
      "avg_response_time_hours": 172.1,
      "skill_assessment_scores": {},
      "connection_count": 389,
      "endorsements_received": 29,
      "notice_period_days": 150,
      "expected_salary_range_inr_lpa": {
        "min": 7.7,
        "max": 11.7
      },
      "preferred_work_mode": "remote",
      "willing_to_relocate": true,
      "github_activity_score": -1,
      "search_appearance_30d": 131,
      "saved_by_recruiters_30d": 9,
      "interview_completion_rate": 0.57,
      "offer_acceptance_rate": -1,
      "verified_email": true,
      "verified_phone": true,
      "linkedin_connected": false
    }
  },
  {
    "candidate_id": "CAND_0000007",
    "profile": {
      "anonymized_name": "Vihaan Bose",
      "headline": "Civil Engineer | 5.5+ yrs experience",
      "summary": "Professional with 5.5+ years of experience. My professional background is in marketing manager \u2014 I've built and led teams, owned KPIs, and driven business outcomes in this domain. Lately I've been curious about how AI tools could augment my work \u2014 I've experimented with ChatGPT and a few other tools for productivity and content creation, and I think the space is exciting. Open to roles where I can apply my domain expertise alongside emerging AI capabilities.",
      "location": "Gurgaon, Haryana",
      "country": "India",
      "years_of_experience": 5.5,
      "current_title": "Civil Engineer",
      "current_company": "Wipro",
      "current_company_size": "10001+",
      "current_industry": "IT Services"
    },
    "career_history": [
      {
        "company": "Wipro",
        "title": "Civil Engineer",
        "start_date": "2023-04-13",
        "end_date": null,
        "duration_months": 38,
        "is_current": true,
        "industry": "IT Services",
        "company_size": "10001+",
        "description": "Brand design and creative direction at a consumer-products company. Owned brand identity (logo, visual system, typography), packaging design, and digital creative across web and social. Led the recent rebrand and managed a small external agency for production work. Comfortable across the Adobe suite, Figma, and the production side of brand and packaging design."
      },
      {
        "company": "Initech",
        "title": "Mechanical Engineer",
        "start_date": "2021-01-16",
        "end_date": "2023-04-06",
        "duration_months": 27,
        "is_current": false,
        "industry": "Software",
        "company_size": "51-200",
        "description": "Customer support team lead at a SaaS product. Managed a team of 8 support agents handling tier-1 and tier-2 tickets; owned the escalation process to engineering and the customer-feedback loop to product. Built out the support knowledge base and the agent training program. Strong on the people-management side and the process side; lighter on technical depth beyond product expertise."
      }
    ],
    "education": [
      {
        "institution": "SRM University",
        "degree": "M.E.",
        "field_of_study": "Data Science",
        "start_year": 2009,
        "end_year": 2013,
        "grade": "8.28 CGPA",
        "tier": "tier_2"
      }
    ],
    "skills": [
      {
        "name": "Content Writing",
        "proficiency": "beginner",
        "endorsements": 12,
        "duration_months": 14
      },
      {
        "name": "MongoDB",
        "proficiency": "intermediate",
        "endorsements": 13,
        "duration_months": 9
      },
      {
        "name": "Sales",
        "proficiency": "intermediate",
        "endorsements": 0,
        "duration_months": 27
      },
      {
        "name": "Spark",
        "proficiency": "beginner",
        "endorsements": 14,
        "duration_months": 14
      },
      {
        "name": "Scrum",
        "proficiency": "beginner",
        "endorsements": 4,
        "duration_months": 18
      },
      {
        "name": "Apache Beam",
        "proficiency": "beginner",
        "endorsements": 4,
        "duration_months": 3
      },
      {
        "name": "Illustrator",
        "proficiency": "beginner",
        "endorsements": 14,
        "duration_months": 2
      }
    ],
    "certifications": [],
    "languages": [
      {
        "language": "English",
        "proficiency": "professional"
      },
      {
        "language": "Hindi",
        "proficiency": "professional"
      }
    ],
    "redrob_signals": {
      "profile_completeness_score": 74.6,
      "signup_date": "2025-09-29",
      "last_active_date": "2026-05-25",
      "open_to_work_flag": false,
      "profile_views_received_30d": 2,
      "applications_submitted_30d": 1,
      "recruiter_response_rate": 0.62,
      "avg_response_time_hours": 61.3,
      "skill_assessment_scores": {},
      "connection_count": 122,
      "endorsements_received": 50,
      "notice_period_days": 30,
      "expected_salary_range_inr_lpa": {
        "min": 6.7,
        "max": 14.6
      },
      "preferred_work_mode": "onsite",
      "willing_to_relocate": true,
      "github_activity_score": -1,
      "search_appearance_30d": 104,
      "saved_by_recruiters_30d": 8,
      "interview_completion_rate": 0.47,
      "offer_acceptance_rate": -1,
      "verified_email": true,
      "verified_phone": true,
      "linkedin_connected": true
    }
  },
  {
    "candidate_id": "CAND_0000008",
    "profile": {
      "anonymized_name": "Shaurya Chatterjee",
      "headline": "Operations Manager | 3.6+ yrs experience",
      "summary": "Professional with 3.6+ years of experience. I've spent my career in marketing manager roles, mostly focused on driving outcomes through process, people, and customer relationships. Lately I've been curious about how AI tools could augment my work \u2014 I've experimented with ChatGPT and a few other tools for productivity and content creation, and I think the space is exciting. Open to roles where I can apply my domain expertise alongside emerging AI capabilities.",
      "location": "Noida, Uttar Pradesh",
      "country": "India",
      "years_of_experience": 3.6,
      "current_title": "Operations Manager",
      "current_company": "Wipro",
      "current_company_size": "10001+",
      "current_industry": "IT Services"
    },
    "career_history": [
      {
        "company": "Wipro",
        "title": "Operations Manager",
        "start_date": "2022-11-14",
        "end_date": null,
        "duration_months": 43,
        "is_current": true,
        "industry": "IT Services",
        "company_size": "10001+",
        "description": "Marketing leadership role at a B2B SaaS company. Owned the demand-generation function \u2014 content marketing, paid acquisition, SEO, email nurture. Built and managed a team of 5 across content, performance marketing, and marketing operations. Worked closely with sales on lead-quality definitions and the SDR-handoff process. Recent focus has been on account-based marketing for our enterprise segment."
      }
    ],
    "education": [
      {
        "institution": "Anna University",
        "degree": "B.Tech",
        "field_of_study": "Data Science",
        "start_year": 2008,
        "end_year": 2012,
        "grade": "8.60 CGPA",
        "tier": "tier_2"
      },
      {
        "institution": "SRM University",
        "degree": "M.Sc",
        "field_of_study": "Computer Engineering",
        "start_year": 2009,
        "end_year": 2013,
        "grade": "67%",
        "tier": "tier_2"
      }
    ],
    "skills": [
      {
        "name": "Java",
        "proficiency": "intermediate",
        "endorsements": 2,
        "duration_months": 32
      },
      {
        "name": "BigQuery",
        "proficiency": "beginner",
        "endorsements": 5,
        "duration_months": 9
      },
      {
        "name": "Spark",
        "proficiency": "beginner",
        "endorsements": 4,
        "duration_months": 6
      },
      {
        "name": "Accounting",
        "proficiency": "beginner",
        "endorsements": 8,
        "duration_months": 3
      },
      {
        "name": "Kubernetes",
        "proficiency": "intermediate",
        "endorsements": 2,
        "duration_months": 9
      },
      {
        "name": "TypeScript",
        "proficiency": "intermediate",
        "endorsements": 14,
        "duration_months": 11
      },
      {
        "name": "Rust",
        "proficiency": "intermediate",
        "endorsements": 12,
        "duration_months": 16
      },
      {
        "name": "HTML",
        "proficiency": "beginner",
        "endorsements": 8,
        "duration_months": 11
      }
    ],
    "certifications": [
      {
        "name": "Six Sigma Green Belt",
        "issuer": "ASQ",
        "year": 2018
      }
    ],
    "languages": [
      {
        "language": "English",
        "proficiency": "professional"
      },
      {
        "language": "Hindi",
        "proficiency": "professional"
      }
    ],
    "redrob_signals": {
      "profile_completeness_score": 63.0,
      "signup_date": "2022-06-26",
      "last_active_date": "2025-12-13",
      "open_to_work_flag": false,
      "profile_views_received_30d": 28,
      "applications_submitted_30d": 5,
      "recruiter_response_rate": 0.42,
      "avg_response_time_hours": 98.4,
      "skill_assessment_scores": {},
      "connection_count": 285,
      "endorsements_received": 7,
      "notice_period_days": 90,
      "expected_salary_range_inr_lpa": {
        "min": 6.6,
        "max": 17.2
      },
      "preferred_work_mode": "onsite",
      "willing_to_relocate": false,
      "github_activity_score": -1,
      "search_appearance_30d": 91,
      "saved_by_recruiters_30d": 0,
      "interview_completion_rate": 0.74,
      "offer_acceptance_rate": -1,
      "verified_email": true,
      "verified_phone": false,
      "linkedin_connected": false
    }
  },
  {
    "candidate_id": "CAND_0000009",
    "profile": {
      "anonymized_name": "Amit Shah",
      "headline": "Mechanical Engineer | Driving business outcomes",
      "summary": "Professional with 11.0+ years of experience. My professional background is in marketing manager \u2014 I've built and led teams, owned KPIs, and driven business outcomes in this domain. Lately I've been curious about how AI tools could augment my work \u2014 I've experimented with ChatGPT and a few other tools for productivity and content creation, and I think the space is exciting. Open to roles where I can apply my domain expertise alongside emerging AI capabilities.",
      "location": "New York",
      "country": "USA",
      "years_of_experience": 11.0,
      "current_title": "Mechanical Engineer",
      "current_company": "Dunder Mifflin",
      "current_company_size": "201-500",
      "current_industry": "Paper Products"
    },
    "career_history": [
      {
        "company": "Dunder Mifflin",
        "title": "Mechanical Engineer",
        "start_date": "2022-10-15",
        "end_date": null,
        "duration_months": 44,
        "is_current": true,
        "industry": "Paper Products",
        "company_size": "201-500",
        "description": "Business analyst at a consulting firm, working primarily with retail and CPG clients. Conducted business diagnostics, process re-engineering work, and digital transformation strategy projects. Strong on stakeholder management, structured problem-solving, and the typical consulting toolkit (slide-craft, Excel modeling, executive communication). Recent project work involved AI-strategy advisory but my own technical depth in AI is limited."
      },
      {
        "company": "Wipro",
        "title": "Content Writer",
        "start_date": "2021-02-22",
        "end_date": "2022-10-15",
        "duration_months": 20,
        "is_current": false,
        "industry": "IT Services",
        "company_size": "10001+",
        "description": "Marketing leadership role at a B2B SaaS company. Owned the demand-generation function \u2014 content marketing, paid acquisition, SEO, email nurture. Built and managed a team of 5 across content, performance marketing, and marketing operations. Worked closely with sales on lead-quality definitions and the SDR-handoff process. Recent focus has been on account-based marketing for our enterprise segment."
      },
      {
        "company": "Stark Industries",
        "title": "Customer Support",
        "start_date": "2017-02-13",
        "end_date": "2021-02-22",
        "duration_months": 49,
        "is_current": false,
        "industry": "Manufacturing",
        "company_size": "1001-5000",
        "description": "Mechanical engineering design role at a hardware-product company. Led the design of two product subsystems through full lifecycle: concept, DFM/DFMA review, prototype, production tooling. Comfortable with CAD (SolidWorks, Creo), FEA (ANSYS), and the typical hardware-development cadence. Worked closely with manufacturing partners on production scale-up."
      },
      {
        "company": "Acme Corp",
        "title": "Project Manager",
        "start_date": "2015-08-23",
        "end_date": "2017-02-13",
        "duration_months": 18,
        "is_current": false,
        "industry": "Manufacturing",
        "company_size": "201-500",
        "description": "Enterprise sales of cloud software solutions into the mid-market segment. Carried a $1.8M ARR quota and consistently delivered against it across the last three years. Owned the full sales cycle: prospecting, discovery, technical evaluation (with SE support), commercial negotiation, and close. Strong on consultative selling for technical buyers; comfortable engaging with both engineering and finance stakeholders."
      }
    ],
    "education": [
      {
        "institution": "KIIT University",
        "degree": "B.Tech",
        "field_of_study": "Electronics",
        "start_year": 2009,
        "end_year": 2014,
        "grade": "7.89 CGPA",
        "tier": "tier_3"
      }
    ],
    "skills": [
      {
        "name": "Snowflake",
        "proficiency": "intermediate",
        "endorsements": 5,
        "duration_months": 8
      },
      {
        "name": "gRPC",
        "proficiency": "beginner",
        "endorsements": 6,
        "duration_months": 12
      },
      {
        "name": "JavaScript",
        "proficiency": "intermediate",
        "endorsements": 0,
        "duration_months": 23
      },
      {
        "name": "OpenCV",
        "proficiency": "intermediate",
        "endorsements": 12,
        "duration_months": 36
      },
      {
        "name": "Go",
        "proficiency": "intermediate",
        "endorsements": 12,
        "duration_months": 20
      },
      {
        "name": "PowerPoint",
        "proficiency": "intermediate",
        "endorsements": 1,
        "duration_months": 10
      }
    ],
    "certifications": [],
    "languages": [
      {
        "language": "English",
        "proficiency": "native"
      },
      {
        "language": "Hindi",
        "proficiency": "professional"
      }
    ],
    "redrob_signals": {
      "profile_completeness_score": 39.6,
      "signup_date": "2025-10-19",
      "last_active_date": "2026-01-27",
      "open_to_work_flag": false,
      "profile_views_received_30d": 50,
      "applications_submitted_30d": 8,
      "recruiter_response_rate": 0.53,
      "avg_response_time_hours": 202.0,
      "skill_assessment_scores": {},
      "connection_count": 516,
      "endorsements_received": 34,
      "notice_period_days": 150,
      "expected_salary_range_inr_lpa": {
        "min": 16.0,
        "max": 7.3
      },
      "preferred_work_mode": "remote",
      "willing_to_relocate": false,
      "github_activity_score": -1,
      "search_appearance_30d": 74,
      "saved_by_recruiters_30d": 1,
      "interview_completion_rate": 0.54,
      "offer_acceptance_rate": 0.48,
      "verified_email": true,
      "verified_phone": true,
      "linkedin_connected": false
    }
  },
  {
    "candidate_id": "CAND_0000010",
    "profile": {
      "anonymized_name": "Aarav Kapoor",
      "headline": "Data Engineer | Data pipelines & analytics",
      "summary": "Software / data professional with 4.6 years of experience building data pipelines, backend systems, and analytics infrastructure. Most of my work has been data pipelines and analytics infrastructure; I've shipped a couple of small ML features but it's not the core of my day. My toolkit is solid on the data engineering side \u2014 Python, SQL, Spark, Airflow, warehouse design \u2014 and I've completed a couple of self-directed ML projects (Kaggle competitions, side projects fine-tuning small models). Interested in transitioning toward more AI/ML-focused work, ideally at a company where I can leverage my existing data-infra skills while learning modern ML practice.",
      "location": "London",
      "country": "UK",
      "years_of_experience": 4.6,
      "current_title": "Data Engineer",
      "current_company": "Ola",
      "current_company_size": "5001-10000",
      "current_industry": "Transportation"
    },
    "career_history": [
      {
        "company": "Ola",
        "title": "Data Engineer",
        "start_date": "2021-11-19",
        "end_date": null,
        "duration_months": 55,
        "is_current": true,
        "industry": "Transportation",
        "company_size": "5001-10000",
        "description": "Mixed data science and analytics-engineering role at a marketing-analytics startup. Spent maybe 30% of my time on lightweight ML (clustering, classification, churn prediction in sklearn/XGBoost) and 70% on data infrastructure and dashboards. Comfortable with the modeling work but I wouldn't call myself an ML specialist. Built our experimentation framework that supports the product team's A/B tests."
      }
    ],
    "education": [
      {
        "institution": "Generic State University",
        "degree": "B.E.",
        "field_of_study": "Mathematics",
        "start_year": 2007,
        "end_year": 2011,
        "grade": "85%",
        "tier": "tier_4"
      },
      {
        "institution": "Local Engineering College",
        "degree": "M.S.",
        "field_of_study": "Computer Engineering",
        "start_year": 2013,
        "end_year": 2018,
        "grade": "7.73 CGPA",
        "tier": "tier_4"
      }
    ],
    "skills": [
      {
        "name": "GCP",
        "proficiency": "beginner",
        "endorsements": 7,
        "duration_months": 8
      },
      {
        "name": "Spring Boot",
        "proficiency": "beginner",
        "endorsements": 3,
        "duration_months": 2
      },
      {
        "name": "Kubeflow",
        "proficiency": "intermediate",
        "endorsements": 11,
        "duration_months": 19
      },
      {
        "name": "Java",
        "proficiency": "intermediate",
        "endorsements": 12,
        "duration_months": 19
      },
      {
        "name": "GANs",
        "proficiency": "advanced",
        "endorsements": 58,
        "duration_months": 57
      },
      {
        "name": "Figma",
        "proficiency": "beginner",
        "endorsements": 4,
        "duration_months": 3
      },
      {
        "name": "Elasticsearch",
        "proficiency": "intermediate",
        "endorsements": 15,
        "duration_months": 17
      },
      {
        "name": "OpenCV",
        "proficiency": "advanced",
        "endorsements": 0,
        "duration_months": 24
      },
      {
        "name": "CNN",
        "proficiency": "intermediate",
        "endorsements": 15,
        "duration_months": 8
      },
      {
        "name": "Azure",
        "proficiency": "beginner",
        "endorsements": 7,
        "duration_months": 11
      },
      {
        "name": "Prompt Engineering",
        "proficiency": "advanced",
        "endorsements": 42,
        "duration_months": 35
      },
      {
        "name": "Object Detection",
        "proficiency": "advanced",
        "endorsements": 55,
        "duration_months": 58
      },
      {
        "name": "MLOps",
        "proficiency": "intermediate",
        "endorsements": 3,
        "duration_months": 10
      },
      {
        "name": "Python",
        "proficiency": "intermediate",
        "endorsements": 7,
        "duration_months": 14
      },
      {
        "name": "BM25",
        "proficiency": "advanced",
        "endorsements": 55,
        "duration_months": 55
      },
      {
        "name": "Weights & Biases",
        "proficiency": "advanced",
        "endorsements": 4,
        "duration_months": 21
      },
      {
        "name": "Sales",
        "proficiency": "beginner",
        "endorsements": 5,
        "duration_months": 18
      }
    ],
    "certifications": [],
    "languages": [
      {
        "language": "English",
        "proficiency": "native"
      },
      {
        "language": "Hindi",
        "proficiency": "professional"
      }
    ],
    "redrob_signals": {
      "profile_completeness_score": 81.6,
      "signup_date": "2026-01-09",
      "last_active_date": "2026-04-29",
      "open_to_work_flag": false,
      "profile_views_received_30d": 60,
      "applications_submitted_30d": 13,
      "recruiter_response_rate": 0.4,
      "avg_response_time_hours": 19.0,
      "skill_assessment_scores": {
        "GANs": 53.3,
        "OpenCV": 65.5,
        "Prompt Engineering": 73.8,
        "Object Detection": 81.3
      },
      "connection_count": 712,
      "endorsements_received": 38,
      "notice_period_days": 120,
      "expected_salary_range_inr_lpa": {
        "min": 13.0,
        "max": 32.0
      },
      "preferred_work_mode": "hybrid",
      "willing_to_relocate": false,
      "github_activity_score": 33.7,
      "search_appearance_30d": 256,
      "saved_by_recruiters_30d": 2,
      "interview_completion_rate": 0.53,
      "offer_acceptance_rate": -1,
      "verified_email": true,
      "verified_phone": true,
      "linkedin_connected": false
    }
  },
  {
    "candidate_id": "CAND_0000011",
    "profile": {
      "anonymized_name": "Deepak Desai",
      "headline": "QA Engineer | Cloud & DevOps",
      "summary": "Software engineer with 2.0 years of experience across web, backend, and cloud systems. Strong fundamentals in software development and system design. Most of my work is conventional backend engineering \u2014 APIs, databases, queues, deployments. I've been keeping up with AI/ML at a self-learner level \u2014 taken some online courses, played with the OpenAI and Anthropic APIs, built a small RAG side project \u2014 but I haven't done it in a professional capacity yet. Open to roles where I can either deepen my software engineering work or, if the team is open to it, start contributing to ML-adjacent systems.",
      "location": "Hyderabad, Telangana",
      "country": "India",
      "years_of_experience": 2.0,
      "current_title": "QA Engineer",
      "current_company": "Pied Piper",
      "current_company_size": "11-50",
      "current_industry": "Software"
    },
    "career_history": [
      {
        "company": "Pied Piper",
        "title": "QA Engineer",
        "start_date": "2025-05-02",
        "end_date": null,
        "duration_months": 13,
        "is_current": true,
        "industry": "Software",
        "company_size": "11-50",
        "description": "Android mobile development using Java and (more recently) Kotlin at a consumer-app company. Built and maintained multiple production features including the main shopping flow, push notification system, and the offline-first sync layer. Comfortable with the Android framework, Jetpack components, and the typical patterns (MVVM, Hilt, Coroutines). My career has been entirely on mobile so far; interested in expanding into broader backend or platform engineering."
      },
      {
        "company": "Hooli",
        "title": "QA Engineer",
        "start_date": "2024-06-06",
        "end_date": "2025-04-02",
        "duration_months": 10,
        "is_current": false,
        "industry": "Software",
        "company_size": "1001-5000",
        "description": "Test automation and QA engineering for a fintech product. Built and maintained the end-to-end test suite using Selenium and pytest, plus the load-testing setup using Locust. Worked closely with developers on testability patterns and with product on acceptance criteria. Recent work has been on shifting test responsibility into the dev team \u2014 moving from QA-as-gate to QA-as-coach. Career has been entirely in QA/test engineering."
      }
    ],
    "education": [
      {
        "institution": "Chandigarh University",
        "degree": "B.Tech",
        "field_of_study": "Data Science",
        "start_year": 2014,
        "end_year": 2019,
        "grade": "6.96 CGPA",
        "tier": "tier_3"
      },
      {
        "institution": "Anna University",
        "degree": "B.Sc",
        "field_of_study": "Information Technology",
        "start_year": 2015,
        "end_year": 2020,
        "grade": "9.16 CGPA",
        "tier": "tier_2"
      }
    ],
    "skills": [
      {
        "name": "Recommendation Systems",
        "proficiency": "advanced",
        "endorsements": 5,
        "duration_months": 40
      },
      {
        "name": "Scrum",
        "proficiency": "beginner",
        "endorsements": 13,
        "duration_months": 7
      },
      {
        "name": "FastAPI",
        "proficiency": "beginner",
        "endorsements": 4,
        "duration_months": 12
      },
      {
        "name": "Hugging Face Transformers",
        "proficiency": "intermediate",
        "endorsements": 1,
        "duration_months": 30
      },
      {
        "name": "AWS",
        "proficiency": "beginner",
        "endorsements": 4,
        "duration_months": 18
      },
      {
        "name": "Snowflake",
        "proficiency": "beginner",
        "endorsements": 4,
        "duration_months": 11
      },
      {
        "name": "Spring Boot",
        "proficiency": "intermediate",
        "endorsements": 12,
        "duration_months": 31
      },
      {
        "name": "PostgreSQL",
        "proficiency": "intermediate",
        "endorsements": 7,
        "duration_months": 24
      },
      {
        "name": "Kubeflow",
        "proficiency": "advanced",
        "endorsements": 6,
        "duration_months": 59
      },
      {
        "name": "Azure",
        "proficiency": "beginner",
        "endorsements": 12,
        "duration_months": 8
      }
    ],
    "certifications": [
      {
        "name": "AWS Certified Cloud Practitioner",
        "issuer": "AWS",
        "year": 2019
      },
      {
        "name": "Six Sigma Green Belt",
        "issuer": "ASQ",
        "year": 2021
      }
    ],
    "languages": [
      {
        "language": "English",
        "proficiency": "native"
      },
      {
        "language": "Hindi",
        "proficiency": "professional"
      }
    ],
    "redrob_signals": {
      "profile_completeness_score": 59.2,
      "signup_date": "2023-07-22",
      "last_active_date": "2026-01-19",
      "open_to_work_flag": false,
      "profile_views_received_30d": 112,
      "applications_submitted_30d": 0,
      "recruiter_response_rate": 0.56,
      "avg_response_time_hours": 184.4,
      "skill_assessment_scores": {
        "Recommendation Systems": 29.8
      },
      "connection_count": 496,
      "endorsements_received": 9,
      "notice_period_days": 90,
      "expected_salary_range_inr_lpa": {
        "min": 15.5,
        "max": 13.9
      },
      "preferred_work_mode": "flexible",
      "willing_to_relocate": false,
      "github_activity_score": 32.3,
      "search_appearance_30d": 200,
      "saved_by_recruiters_30d": 13,
      "interview_completion_rate": 0.45,
      "offer_acceptance_rate": -1,
      "verified_email": true,
      "verified_phone": true,
      "linkedin_connected": true
    }
  },
  {
    "candidate_id": "CAND_0000012",
    "profile": {
      "anonymized_name": "Anjali Krishnan",
      "headline": "Operations Manager | Driving business outcomes",
      "summary": "Professional with 1.1+ years of experience. My professional background is in marketing manager \u2014 I've built and led teams, owned KPIs, and driven business outcomes in this domain. Lately I've been curious about how AI tools could augment my work \u2014 I've experimented with ChatGPT and a few other tools for productivity and content creation, and I think the space is exciting. Open to roles where I can apply my domain expertise alongside emerging AI capabilities.",
      "location": "Chandigarh, Chandigarh",
      "country": "India",
      "years_of_experience": 1.1,
      "current_title": "Operations Manager",
      "current_company": "Stark Industries",
      "current_company_size": "1001-5000",
      "current_industry": "Manufacturing"
    },
    "career_history": [
      {
        "company": "Stark Industries",
        "title": "Operations Manager",
        "start_date": "2025-05-02",
        "end_date": null,
        "duration_months": 13,
        "is_current": true,
        "industry": "Manufacturing",
        "company_size": "1001-5000",
        "description": "Senior accounting role at a mid-sized company \u2014 month-end close, financial reporting, statutory compliance (GAAP / Ind-AS), and tax filings. Owned the GL, fixed-asset register, and the audit-readiness function. Managed a team of 3 staff accountants. Built strong process discipline around the close cycle, reducing close time from 12 days to 7 over the last two years."
      }
    ],
    "education": [
      {
        "institution": "Symbiosis International",
        "degree": "B.Sc",
        "field_of_study": "Physics",
        "start_year": 2018,
        "end_year": 2022,
        "grade": "68%",
        "tier": "tier_3"
      },
      {
        "institution": "Christ University",
        "degree": "B.Sc",
        "field_of_study": "Mechanical Engineering",
        "start_year": 2011,
        "end_year": 2015,
        "grade": "7.28 CGPA",
        "tier": "tier_3"
      }
    ],
    "skills": [
      {
        "name": "Azure",
        "proficiency": "beginner",
        "endorsements": 7,
        "duration_months": 10
      },
      {
        "name": "Airflow",
        "proficiency": "intermediate",
        "endorsements": 2,
        "duration_months": 15
      },
      {
        "name": "AWS",
        "proficiency": "intermediate",
        "endorsements": 15,
        "duration_months": 30
      },
      {
        "name": "gRPC",
        "proficiency": "beginner",
        "endorsements": 9,
        "duration_months": 2
      },
      {
        "name": "Vue.js",
        "proficiency": "intermediate",
        "endorsements": 2,
        "duration_months": 15
      },
      {
        "name": "dbt",
        "proficiency": "intermediate",
        "endorsements": 11,
        "duration_months": 22
      },
      {
        "name": "Agile",
        "proficiency": "intermediate",
        "endorsements": 4,
        "duration_months": 14
      },
      {
        "name": "PowerPoint",
        "proficiency": "intermediate",
        "endorsements": 1,
        "duration_months": 27
      },
      {
        "name": "Content Writing",
        "proficiency": "intermediate",
        "endorsements": 3,
        "duration_months": 36
      },
      {
        "name": "Project Management",
        "proficiency": "beginner",
        "endorsements": 5,
        "duration_months": 3
      }
    ],
    "certifications": [],
    "languages": [
      {
        "language": "English",
        "proficiency": "professional"
      },
      {
        "language": "Hindi",
        "proficiency": "conversational"
      }
    ],
    "redrob_signals": {
      "profile_completeness_score": 53.4,
      "signup_date": "2024-01-28",
      "last_active_date": "2025-10-28",
      "open_to_work_flag": false,
      "profile_views_received_30d": 60,
      "applications_submitted_30d": 1,
      "recruiter_response_rate": 0.16,
      "avg_response_time_hours": 38.4,
      "skill_assessment_scores": {},
      "connection_count": 165,
      "endorsements_received": 31,
      "notice_period_days": 60,
      "expected_salary_range_inr_lpa": {
        "min": 14.8,
        "max": 7.9
      },
      "preferred_work_mode": "flexible",
      "willing_to_relocate": false,
      "github_activity_score": -1,
      "search_appearance_30d": 61,
      "saved_by_recruiters_30d": 3,
      "interview_completion_rate": 0.42,
      "offer_acceptance_rate": -1,
      "verified_email": true,
      "verified_phone": false,
      "linkedin_connected": false
    }
  },
  {
    "candidate_id": "CAND_0000013",
    "profile": {
      "anonymized_name": "Pari Nair",
      "headline": "Civil Engineer | Driving business outcomes",
      "summary": "Professional with 1.1+ years of experience. I'm a marketing manager with substantial experience in cross-functional collaboration, stakeholder management, and execution. Lately I've been curious about how AI tools could augment my work \u2014 I've experimented with ChatGPT and a few other tools for productivity and content creation, and I think the space is exciting. Open to roles where I can apply my domain expertise alongside emerging AI capabilities.",
      "location": "Dubai",
      "country": "UAE",
      "years_of_experience": 1.1,
      "current_title": "Civil Engineer",
      "current_company": "Globex Inc",
      "current_company_size": "501-1000",
      "current_industry": "Manufacturing"
    },
    "career_history": [
      {
        "company": "Globex Inc",
        "title": "Civil Engineer",
        "start_date": "2025-05-02",
        "end_date": null,
        "duration_months": 13,
        "is_current": true,
        "industry": "Manufacturing",
        "company_size": "501-1000",
        "description": "Customer support team lead at a SaaS product. Managed a team of 8 support agents handling tier-1 and tier-2 tickets; owned the escalation process to engineering and the customer-feedback loop to product. Built out the support knowledge base and the agent training program. Strong on the people-management side and the process side; lighter on technical depth beyond product expertise."
      }
    ],
    "education": [
      {
        "institution": "Delhi College of Engineering",
        "degree": "B.E.",
        "field_of_study": "Information Technology",
        "start_year": 2019,
        "end_year": 2022,
        "grade": "8.84 CGPA",
        "tier": "tier_2"
      },
      {
        "institution": "Amity University",
        "degree": "Ph.D",
        "field_of_study": "Information Technology",
        "start_year": 2008,
        "end_year": 2013,
        "grade": "8.29 CGPA",
        "tier": "tier_3"
      }
    ],
    "skills": [
      {
        "name": "React",
        "proficiency": "intermediate",
        "endorsements": 5,
        "duration_months": 23
      },
      {
        "name": "Redux",
        "proficiency": "intermediate",
        "endorsements": 11,
        "duration_months": 9
      },
      {
        "name": "Vue.js",
        "proficiency": "beginner",
        "endorsements": 12,
        "duration_months": 12
      },
      {
        "name": "Six Sigma",
        "proficiency": "beginner",
        "endorsements": 1,
        "duration_months": 2
      },
      {
        "name": "Spring Boot",
        "proficiency": "beginner",
        "endorsements": 12,
        "duration_months": 12
      },
      {
        "name": "Spark",
        "proficiency": "intermediate",
        "endorsements": 7,
        "duration_months": 30
      },
      {
        "name": "Data Pipelines",
        "proficiency": "intermediate",
        "endorsements": 6,
        "duration_months": 36
      },
      {
        "name": "GCP",
        "proficiency": "intermediate",
        "endorsements": 0,
        "duration_months": 18
      },
      {
        "name": "Flask",
        "proficiency": "intermediate",
        "endorsements": 12,
        "duration_months": 8
      },
      {
        "name": "Snowflake",
        "proficiency": "intermediate",
        "endorsements": 2,
        "duration_months": 8
      }
    ],
    "certifications": [],
    "languages": [
      {
        "language": "English",
        "proficiency": "native"
      },
      {
        "language": "Hindi",
        "proficiency": "conversational"
      }
    ],
    "redrob_signals": {
      "profile_completeness_score": 44.2,
      "signup_date": "2024-06-14",
      "last_active_date": "2026-03-26",
      "open_to_work_flag": true,
      "profile_views_received_30d": 16,
      "applications_submitted_30d": 3,
      "recruiter_response_rate": 0.28,
      "avg_response_time_hours": 80.3,
      "skill_assessment_scores": {},
      "connection_count": 281,
      "endorsements_received": 9,
      "notice_period_days": 30,
      "expected_salary_range_inr_lpa": {
        "min": 11.6,
        "max": 8.1
      },
      "preferred_work_mode": "remote",
      "willing_to_relocate": false,
      "github_activity_score": 35.6,
      "search_appearance_30d": 40,
      "saved_by_recruiters_30d": 12,
      "interview_completion_rate": 0.33,
      "offer_acceptance_rate": 0.26,
      "verified_email": true,
      "verified_phone": false,
      "linkedin_connected": false
    }
  },
  {
    "candidate_id": "CAND_0000014",
    "profile": {
      "anonymized_name": "Atharv Joshi",
      "headline": "Frontend Engineer | Full-stack development",
      "summary": "Software engineer with 8.4 years of experience across web, backend, and cloud systems. Strong fundamentals in software development and system design. My background is full-stack, but my comfort zone is the backend and the database. I've been keeping up with AI/ML at a self-learner level \u2014 taken some online courses, played with the OpenAI and Anthropic APIs, built a small RAG side project \u2014 but I haven't done it in a professional capacity yet. Open to roles where I can either deepen my software engineering work or, if the team is open to it, start contributing to ML-adjacent systems.",
      "location": "Hyderabad, Telangana",
      "country": "India",
      "years_of_experience": 8.4,
      "current_title": "Frontend Engineer",
      "current_company": "Zomato",
      "current_company_size": "5001-10000",
      "current_industry": "Food Delivery"
    },
    "career_history": [
      {
        "company": "Zomato",
        "title": "Frontend Engineer",
        "start_date": "2023-09-10",
        "end_date": null,
        "duration_months": 33,
        "is_current": true,
        "industry": "Food Delivery",
        "company_size": "5001-10000",
        "description": "Frontend engineering at a media company. React, TypeScript, and the typical surrounding tooling (Webpack, Jest, Cypress). Built the company's design system from scratch and led the migration from a legacy AngularJS app. Strong on the frontend craft \u2014 accessibility, performance, animations \u2014 but limited backend exposure."
      },
      {
        "company": "Dunder Mifflin",
        "title": "Software Engineer",
        "start_date": "2019-10-01",
        "end_date": "2023-09-10",
        "duration_months": 48,
        "is_current": false,
        "industry": "Paper Products",
        "company_size": "201-500",
        "description": "Test automation and QA engineering for a fintech product. Built and maintained the end-to-end test suite using Selenium and pytest, plus the load-testing setup using Locust. Worked closely with developers on testability patterns and with product on acceptance criteria. Recent work has been on shifting test responsibility into the dev team \u2014 moving from QA-as-gate to QA-as-coach. Career has been entirely in QA/test engineering."
      },
      {
        "company": "Acme Corp",
        "title": "Java Developer",
        "start_date": "2018-03-03",
        "end_date": "2019-09-24",
        "duration_months": 19,
        "is_current": false,
        "industry": "Manufacturing",
        "company_size": "201-500",
        "description": "Android mobile development using Java and (more recently) Kotlin at a consumer-app company. Built and maintained multiple production features including the main shopping flow, push notification system, and the offline-first sync layer. Comfortable with the Android framework, Jetpack components, and the typical patterns (MVVM, Hilt, Coroutines). My career has been entirely on mobile so far; interested in expanding into broader backend or platform engineering."
      }
    ],
    "education": [
      {
        "institution": "Lovely Professional University",
        "degree": "B.E.",
        "field_of_study": "Statistics",
        "start_year": 2012,
        "end_year": 2015,
        "grade": "7.45 CGPA",
        "tier": "tier_3"
      }
    ],
    "skills": [
      {
        "name": "FAISS",
        "proficiency": "advanced",
        "endorsements": 40,
        "duration_months": 44
      },
      {
        "name": "BigQuery",
        "proficiency": "intermediate",
        "endorsements": 6,
        "duration_months": 24
      },
      {
        "name": "React",
        "proficiency": "beginner",
        "endorsements": 11,
        "duration_months": 10
      },
      {
        "name": "OpenSearch",
        "proficiency": "advanced",
        "endorsements": 47,
        "duration_months": 59
      },
      {
        "name": "OpenCV",
        "proficiency": "advanced",
        "endorsements": 30,
        "duration_months": 60
      },
      {
        "name": "YOLO",
        "proficiency": "advanced",
        "endorsements": 1,
        "duration_months": 44
      },
      {
        "name": "SAP",
        "proficiency": "intermediate",
        "endorsements": 5,
        "duration_months": 30
      },
      {
        "name": "SEO",
        "proficiency": "beginner",
        "endorsements": 0,
        "duration_months": 12
      },
      {
        "name": "REST APIs",
        "proficiency": "beginner",
        "endorsements": 3,
        "duration_months": 4
      },
      {
        "name": "GANs",
        "proficiency": "advanced",
        "endorsements": 9,
        "duration_months": 33
      },
      {
        "name": "dbt",
        "proficiency": "beginner",
        "endorsements": 0,
        "duration_months": 13
      },
      {
        "name": "Photoshop",
        "proficiency": "intermediate",
        "endorsements": 1,
        "duration_months": 32
      },
      {
        "name": "Tailwind",
        "proficiency": "intermediate",
        "endorsements": 2,
        "duration_months": 32
      }
    ],
    "certifications": [],
    "languages": [
      {
        "language": "English",
        "proficiency": "professional"
      },
      {
        "language": "Hindi",
        "proficiency": "native"
      }
    ],
    "redrob_signals": {
      "profile_completeness_score": 61.9,
      "signup_date": "2025-04-29",
      "last_active_date": "2026-04-12",
      "open_to_work_flag": false,
      "profile_views_received_30d": 21,
      "applications_submitted_30d": 1,
      "recruiter_response_rate": 0.8,
      "avg_response_time_hours": 7.7,
      "skill_assessment_scores": {
        "FAISS": 77.6
      },
      "connection_count": 708,
      "endorsements_received": 63,
      "notice_period_days": 90,
      "expected_salary_range_inr_lpa": {
        "min": 9.0,
        "max": 30.0
      },
      "preferred_work_mode": "remote",
      "willing_to_relocate": false,
      "github_activity_score": -1,
      "search_appearance_30d": 12,
      "saved_by_recruiters_30d": 0,
      "interview_completion_rate": 0.55,
      "offer_acceptance_rate": -1,
      "verified_email": true,
      "verified_phone": true,
      "linkedin_connected": false
    }
  },
  {
    "candidate_id": "CAND_0000015",
    "profile": {
      "anonymized_name": "Rahul Agarwal",
      "headline": "Software Engineer | Cloud & DevOps",
      "summary": "Software engineer with 5.4 years of experience across web, backend, and cloud systems. Strong fundamentals in software development and system design. I've worked across web frontends, REST APIs, and cloud deployments; comfortable in most parts of a typical SaaS stack. I've been keeping up with AI/ML at a self-learner level \u2014 taken some online courses, played with the OpenAI and Anthropic APIs, built a small RAG side project \u2014 but I haven't done it in a professional capacity yet. Open to roles where I can either deepen my software engineering work or, if the team is open to it, start contributing to ML-adjacent systems.",
      "location": "Trivandrum, Kerala",
      "country": "India",
      "years_of_experience": 5.4,
      "current_title": "Software Engineer",
      "current_company": "Razorpay",
      "current_company_size": "1001-5000",
      "current_industry": "Fintech"
    },
    "career_history": [
      {
        "company": "Razorpay",
        "title": "Software Engineer",
        "start_date": "2023-11-09",
        "end_date": null,
        "duration_months": 31,
        "is_current": true,
        "industry": "Fintech",
        "company_size": "1001-5000",
        "description": "Cloud infrastructure and DevOps work at an enterprise SaaS company. Owned the AWS account architecture (VPC, IAM, networking), the Terraform modules for our service deployments, and the Kubernetes cluster operations. Designed the CI/CD pipelines (GitLab CI + ArgoCD) and the monitoring stack (Prometheus, Grafana, Loki). Strong on the infra and ops side; haven't done much application development."
      },
      {
        "company": "Hooli",
        "title": "Mobile Developer",
        "start_date": "2021-11-12",
        "end_date": "2023-11-02",
        "duration_months": 24,
        "is_current": false,
        "industry": "Software",
        "company_size": "1001-5000",
        "description": "Android mobile development using Java and (more recently) Kotlin at a consumer-app company. Built and maintained multiple production features including the main shopping flow, push notification system, and the offline-first sync layer. Comfortable with the Android framework, Jetpack components, and the typical patterns (MVVM, Hilt, Coroutines). My career has been entirely on mobile so far; interested in expanding into broader backend or platform engineering."
      },
      {
        "company": "Globex Inc",
        "title": "DevOps Engineer",
        "start_date": "2021-02-15",
        "end_date": "2021-11-12",
        "duration_months": 9,
        "is_current": false,
        "industry": "Manufacturing",
        "company_size": "501-1000",
        "description": "Java backend development at a large enterprise \u2014 Spring Boot microservices, Kafka for inter-service messaging, Postgres + Redis for storage. Worked on the customer onboarding flow which involved orchestrating multiple downstream services. Solid on the Spring ecosystem, transaction handling, and the operational side of Java services. Looking to either go deeper on distributed systems or expand into modern application stacks."
      }
    ],
    "education": [
      {
        "institution": "Local Engineering College",
        "degree": "Ph.D",
        "field_of_study": "Mathematics",
        "start_year": 2013,
        "end_year": 2017,
        "grade": "8.15 CGPA",
        "tier": "tier_4"
      }
    ],
    "skills": [
      {
        "name": "PyTorch",
        "proficiency": "intermediate",
        "endorsements": 10,
        "duration_months": 15
      },
      {
        "name": "Content Writing",
        "proficiency": "intermediate",
        "endorsements": 8,
        "duration_months": 31
      },
      {
        "name": "Weights & Biases",
        "proficiency": "intermediate",
        "endorsements": 5,
        "duration_months": 24
      },
      {
        "name": "Qdrant",
        "proficiency": "intermediate",
        "endorsements": 13,
        "duration_months": 9
      },
      {
        "name": "Sales",
        "proficiency": "intermediate",
        "endorsements": 13,
        "duration_months": 30
      },
      {
        "name": "Figma",
        "proficiency": "intermediate",
        "endorsements": 9,
        "duration_months": 29
      },
      {
        "name": "BigQuery",
        "proficiency": "beginner",
        "endorsements": 0,
        "duration_months": 7
      },
      {
        "name": "Computer Vision",
        "proficiency": "intermediate",
        "endorsements": 6,
        "duration_months": 20
      },
      {
        "name": "Next.js",
        "proficiency": "intermediate",
        "endorsements": 12,
        "duration_months": 35
      },
      {
        "name": "SEO",
        "proficiency": "intermediate",
        "endorsements": 10,
        "duration_months": 29
      }
    ],
    "certifications": [],
    "languages": [
      {
        "language": "English",
        "proficiency": "native"
      },
      {
        "language": "Hindi",
        "proficiency": "conversational"
      }
    ],
    "redrob_signals": {
      "profile_completeness_score": 79.4,
      "signup_date": "2023-02-16",
      "last_active_date": "2026-02-12",
      "open_to_work_flag": true,
      "profile_views_received_30d": 93,
      "applications_submitted_30d": 3,
      "recruiter_response_rate": 0.32,
      "avg_response_time_hours": 117.7,
      "skill_assessment_scores": {},
      "connection_count": 361,
      "endorsements_received": 61,
      "notice_period_days": 90,
      "expected_salary_range_inr_lpa": {
        "min": 21.8,
        "max": 18.9
      },
      "preferred_work_mode": "remote",
      "willing_to_relocate": false,
      "github_activity_score": -1,
      "search_appearance_30d": 164,
      "saved_by_recruiters_30d": 8,
      "interview_completion_rate": 0.72,
      "offer_acceptance_rate": -1,
      "verified_email": true,
      "verified_phone": true,
      "linkedin_connected": false
    }
  },
  {
    "candidate_id": "CAND_0000016",
    "profile": {
      "anonymized_name": "Aanya Malhotra",
      "headline": "Accountant | Helping teams scale",
      "summary": "Professional with 5.3+ years of experience. I'm a marketing manager with substantial experience in cross-functional collaboration, stakeholder management, and execution. Lately I've been curious about how AI tools could augment my work \u2014 I've experimented with ChatGPT and a few other tools for productivity and content creation, and I think the space is exciting. Open to roles where I can apply my domain expertise alongside emerging AI capabilities.",
      "location": "Gurgaon, Haryana",
      "country": "India",
      "years_of_experience": 5.3,
      "current_title": "Accountant",
      "current_company": "Infosys",
      "current_company_size": "10001+",
      "current_industry": "IT Services"
    },
    "career_history": [
      {
        "company": "Infosys",
        "title": "Accountant",
        "start_date": "2024-12-03",
        "end_date": null,
        "duration_months": 18,
        "is_current": true,
        "industry": "IT Services",
        "company_size": "10001+",
        "description": "Enterprise sales of cloud software solutions into the mid-market segment. Carried a $1.8M ARR quota and consistently delivered against it across the last three years. Owned the full sales cycle: prospecting, discovery, technical evaluation (with SE support), commercial negotiation, and close. Strong on consultative selling for technical buyers; comfortable engaging with both engineering and finance stakeholders."
      },
      {
        "company": "TCS",
        "title": "Mechanical Engineer",
        "start_date": "2021-09-06",
        "end_date": "2024-11-19",
        "duration_months": 39,
        "is_current": false,
        "industry": "IT Services",
        "company_size": "10001+",
        "description": "Customer support team lead at a SaaS product. Managed a team of 8 support agents handling tier-1 and tier-2 tickets; owned the escalation process to engineering and the customer-feedback loop to product. Built out the support knowledge base and the agent training program. Strong on the people-management side and the process side; lighter on technical depth beyond product expertise."
      },
      {
        "company": "Globex Inc",
        "title": "Operations Manager",
        "start_date": "2021-02-08",
        "end_date": "2021-08-07",
        "duration_months": 6,
        "is_current": false,
        "industry": "Manufacturing",
        "company_size": "501-1000",
        "description": "Mechanical engineering design role at a hardware-product company. Led the design of two product subsystems through full lifecycle: concept, DFM/DFMA review, prototype, production tooling. Comfortable with CAD (SolidWorks, Creo), FEA (ANSYS), and the typical hardware-development cadence. Worked closely with manufacturing partners on production scale-up."
      }
    ],
    "education": [
      {
        "institution": "Christ University",
        "degree": "B.E.",
        "field_of_study": "Electronics",
        "start_year": 2001,
        "end_year": 2006,
        "grade": "8.32 CGPA",
        "tier": "tier_3"
      }
    ],
    "skills": [
      {
        "name": "Node.js",
        "proficiency": "beginner",
        "endorsements": 4,
        "duration_months": 11
      },
      {
        "name": "Figma",
        "proficiency": "beginner",
        "endorsements": 12,
        "duration_months": 6
      },
      {
        "name": "Data Pipelines",
        "proficiency": "beginner",
        "endorsements": 2,
        "duration_months": 7
      },
      {
        "name": "Go",
        "proficiency": "beginner",
        "endorsements": 0,
        "duration_months": 10
      },
      {
        "name": "Photoshop",
        "proficiency": "intermediate",
        "endorsements": 10,
        "duration_months": 22
      },
      {
        "name": "Kubeflow",
        "proficiency": "advanced",
        "endorsements": 2,
        "duration_months": 54
      },
      {
        "name": "Accounting",
        "proficiency": "intermediate",
        "endorsements": 4,
        "duration_months": 31
      },
      {
        "name": "SQL",
        "proficiency": "intermediate",
        "endorsements": 14,
        "duration_months": 16
      }
    ],
    "certifications": [],
    "languages": [
      {
        "language": "English",
        "proficiency": "native"
      },
      {
        "language": "Hindi",
        "proficiency": "professional"
      }
    ],
    "redrob_signals": {
      "profile_completeness_score": 69.4,
      "signup_date": "2022-12-12",
      "last_active_date": "2025-12-21",
      "open_to_work_flag": true,
      "profile_views_received_30d": 76,
      "applications_submitted_30d": 5,
      "recruiter_response_rate": 0.64,
      "avg_response_time_hours": 205.6,
      "skill_assessment_scores": {},
      "connection_count": 148,
      "endorsements_received": 2,
      "notice_period_days": 60,
      "expected_salary_range_inr_lpa": {
        "min": 6.1,
        "max": 8.1
      },
      "preferred_work_mode": "hybrid",
      "willing_to_relocate": false,
      "github_activity_score": 42.9,
      "search_appearance_30d": 126,
      "saved_by_recruiters_30d": 5,
      "interview_completion_rate": 0.66,
      "offer_acceptance_rate": -1,
      "verified_email": false,
      "verified_phone": false,
      "linkedin_connected": true
    }
  },
  {
    "candidate_id": "CAND_0000017",
    "profile": {
      "anonymized_name": "Anil Pandey",
      "headline": "Accountant | 12.3+ yrs experience",
      "summary": "Professional with 12.3+ years of experience. My professional background is in marketing manager \u2014 I've built and led teams, owned KPIs, and driven business outcomes in this domain. Lately I've been curious about how AI tools could augment my work \u2014 I've experimented with ChatGPT and a few other tools for productivity and content creation, and I think the space is exciting. Open to roles where I can apply my domain expertise alongside emerging AI capabilities.",
      "location": "Bangalore, Karnataka",
      "country": "India",
      "years_of_experience": 12.3,
      "current_title": "Accountant",
      "current_company": "Wipro",
      "current_company_size": "10001+",
      "current_industry": "IT Services"
    },
    "career_history": [
      {
        "company": "Wipro",
        "title": "Accountant",
        "start_date": "2024-03-08",
        "end_date": null,
        "duration_months": 27,
        "is_current": true,
        "industry": "IT Services",
        "company_size": "10001+",
        "description": "Customer support team lead at a SaaS product. Managed a team of 8 support agents handling tier-1 and tier-2 tickets; owned the escalation process to engineering and the customer-feedback loop to product. Built out the support knowledge base and the agent training program. Strong on the people-management side and the process side; lighter on technical depth beyond product expertise."
      },
      {
        "company": "Infosys",
        "title": "Customer Support",
        "start_date": "2021-02-08",
        "end_date": "2024-02-23",
        "duration_months": 37,
        "is_current": false,
        "industry": "IT Services",
        "company_size": "10001+",
        "description": "Mechanical engineering design role at a hardware-product company. Led the design of two product subsystems through full lifecycle: concept, DFM/DFMA review, prototype, production tooling. Comfortable with CAD (SolidWorks, Creo), FEA (ANSYS), and the typical hardware-development cadence. Worked closely with manufacturing partners on production scale-up."
      },
      {
        "company": "Initech",
        "title": "Mechanical Engineer",
        "start_date": "2017-07-29",
        "end_date": "2021-02-08",
        "duration_months": 43,
        "is_current": false,
        "industry": "Software",
        "company_size": "51-200",
        "description": "Enterprise sales of cloud software solutions into the mid-market segment. Carried a $1.8M ARR quota and consistently delivered against it across the last three years. Owned the full sales cycle: prospecting, discovery, technical evaluation (with SE support), commercial negotiation, and close. Strong on consultative selling for technical buyers; comfortable engaging with both engineering and finance stakeholders."
      },
      {
        "company": "Acme Corp",
        "title": "Accountant",
        "start_date": "2014-05-16",
        "end_date": "2017-07-29",
        "duration_months": 39,
        "is_current": false,
        "industry": "Manufacturing",
        "company_size": "201-500",
        "description": "Senior accounting role at a mid-sized company \u2014 month-end close, financial reporting, statutory compliance (GAAP / Ind-AS), and tax filings. Owned the GL, fixed-asset register, and the audit-readiness function. Managed a team of 3 staff accountants. Built strong process discipline around the close cycle, reducing close time from 12 days to 7 over the last two years."
      }
    ],
    "education": [
      {
        "institution": "Tier-3 Engineering College",
        "degree": "M.Tech",
        "field_of_study": "Data Science",
        "start_year": 2017,
        "end_year": 2022,
        "grade": "7.58 CGPA",
        "tier": "tier_4"
      }
    ],
    "skills": [
      {
        "name": "Next.js",
        "proficiency": "beginner",
        "endorsements": 9,
        "duration_months": 18
      },
      {
        "name": "Java",
        "proficiency": "intermediate",
        "endorsements": 13,
        "duration_months": 15
      },
      {
        "name": "Apache Flink",
        "proficiency": "intermediate",
        "endorsements": 4,
        "duration_months": 16
      },
      {
        "name": "Sales",
        "proficiency": "intermediate",
        "endorsements": 4,
        "duration_months": 8
      },
      {
        "name": "Tally",
        "proficiency": "intermediate",
        "endorsements": 14,
        "duration_months": 12
      },
      {
        "name": "PostgreSQL",
        "proficiency": "intermediate",
        "endorsements": 11,
        "duration_months": 25
      },
      {
        "name": "REST APIs",
        "proficiency": "beginner",
        "endorsements": 15,
        "duration_months": 4
      },
      {
        "name": "Hadoop",
        "proficiency": "intermediate",
        "endorsements": 4,
        "duration_months": 35
      }
    ],
    "certifications": [
      {
        "name": "Six Sigma Green Belt",
        "issuer": "ASQ",
        "year": 2018
      },
      {
        "name": "Scrum Master Certified",
        "issuer": "Scrum Alliance",
        "year": 2022
      }
    ],
    "languages": [
      {
        "language": "English",
        "proficiency": "native"
      },
      {
        "language": "Hindi",
        "proficiency": "conversational"
      }
    ],
    "redrob_signals": {
      "profile_completeness_score": 38.7,
      "signup_date": "2025-08-11",
      "last_active_date": "2025-11-04",
      "open_to_work_flag": false,
      "profile_views_received_30d": 3,
      "applications_submitted_30d": 4,
      "recruiter_response_rate": 0.27,
      "avg_response_time_hours": 197.4,
      "skill_assessment_scores": {},
      "connection_count": 35,
      "endorsements_received": 23,
      "notice_period_days": 90,
      "expected_salary_range_inr_lpa": {
        "min": 13.8,
        "max": 8.4
      },
      "preferred_work_mode": "hybrid",
      "willing_to_relocate": false,
      "github_activity_score": -1,
      "search_appearance_30d": 110,
      "saved_by_recruiters_30d": 2,
      "interview_completion_rate": 0.32,
      "offer_acceptance_rate": 0.17,
      "verified_email": true,
      "verified_phone": false,
      "linkedin_connected": false
    }
  },
  {
    "candidate_id": "CAND_0000018",
    "profile": {
      "anonymized_name": "Vivaan Reddy",
      "headline": "Frontend Engineer | Full-stack development",
      "summary": "Software engineer with 6.6 years of experience across web, backend, and cloud systems. Strong fundamentals in software development and system design. My background is full-stack, but my comfort zone is the backend and the database. I've been keeping up with AI/ML at a self-learner level \u2014 taken some online courses, played with the OpenAI and Anthropic APIs, built a small RAG side project \u2014 but I haven't done it in a professional capacity yet. Open to roles where I can either deepen my software engineering work or, if the team is open to it, start contributing to ML-adjacent systems.",
      "location": "Bhubaneswar, Odisha",
      "country": "India",
      "years_of_experience": 6.6,
      "current_title": "Frontend Engineer",
      "current_company": "Acme Corp",
      "current_company_size": "201-500",
      "current_industry": "Manufacturing"
    },
    "career_history": [
      {
        "company": "Acme Corp",
        "title": "Frontend Engineer",
        "start_date": "2023-09-10",
        "end_date": null,
        "duration_months": 33,
        "is_current": true,
        "industry": "Manufacturing",
        "company_size": "201-500",
        "description": "Test automation and QA engineering for a fintech product. Built and maintained the end-to-end test suite using Selenium and pytest, plus the load-testing setup using Locust. Worked closely with developers on testability patterns and with product on acceptance criteria. Recent work has been on shifting test responsibility into the dev team \u2014 moving from QA-as-gate to QA-as-coach. Career has been entirely in QA/test engineering."
      },
      {
        "company": "Pied Piper",
        "title": "Frontend Engineer",
        "start_date": "2021-01-23",
        "end_date": "2023-09-10",
        "duration_months": 32,
        "is_current": false,
        "industry": "Software",
        "company_size": "11-50",
        "description": "Test automation and QA engineering for a fintech product. Built and maintained the end-to-end test suite using Selenium and pytest, plus the load-testing setup using Locust. Worked closely with developers on testability patterns and with product on acceptance criteria. Recent work has been on shifting test responsibility into the dev team \u2014 moving from QA-as-gate to QA-as-coach. Career has been entirely in QA/test engineering."
      },
      {
        "company": "Initech",
        "title": "Full Stack Developer",
        "start_date": "2019-12-30",
        "end_date": "2021-01-23",
        "duration_months": 13,
        "is_current": false,
        "industry": "Software",
        "company_size": "51-200",
        "description": "Android mobile development using Java and (more recently) Kotlin at a consumer-app company. Built and maintained multiple production features including the main shopping flow, push notification system, and the offline-first sync layer. Comfortable with the Android framework, Jetpack components, and the typical patterns (MVVM, Hilt, Coroutines). My career has been entirely on mobile so far; interested in expanding into broader backend or platform engineering."
      }
    ],
    "education": [
      {
        "institution": "Lovely Professional University",
        "degree": "Ph.D",
        "field_of_study": "Computer Engineering",
        "start_year": 2016,
        "end_year": 2020,
        "grade": "7.25 CGPA",
        "tier": "tier_3"
      }
    ],
    "skills": [
      {
        "name": "CNN",
        "proficiency": "advanced",
        "endorsements": 53,
        "duration_months": 55
      },
      {
        "name": "Java",
        "proficiency": "intermediate",
        "endorsements": 10,
        "duration_months": 12
      },
      {
        "name": "Accounting",
        "proficiency": "intermediate",
        "endorsements": 9,
        "duration_months": 20
      },
      {
        "name": "Data Pipelines",
        "proficiency": "beginner",
        "endorsements": 3,
        "duration_months": 13
      },
      {
        "name": "Node.js",
        "proficiency": "intermediate",
        "endorsements": 0,
        "duration_months": 9
      },
      {
        "name": "Tailwind",
        "proficiency": "beginner",
        "endorsements": 10,
        "duration_months": 10
      }
    ],
    "certifications": [],
    "languages": [
      {
        "language": "English",
        "proficiency": "native"
      },
      {
        "language": "Hindi",
        "proficiency": "native"
      }
    ],
    "redrob_signals": {
      "profile_completeness_score": 34.8,
      "signup_date": "2025-07-09",
      "last_active_date": "2026-02-18",
      "open_to_work_flag": false,
      "profile_views_received_30d": 88,
      "applications_submitted_30d": 11,
      "recruiter_response_rate": 0.16,
      "avg_response_time_hours": 154.6,
      "skill_assessment_scores": {},
      "connection_count": 284,
      "endorsements_received": 49,
      "notice_period_days": 120,
      "expected_salary_range_inr_lpa": {
        "min": 12.3,
        "max": 26.4
      },
      "preferred_work_mode": "onsite",
      "willing_to_relocate": false,
      "github_activity_score": -1,
      "search_appearance_30d": 41,
      "saved_by_recruiters_30d": 16,
      "interview_completion_rate": 0.7,
      "offer_acceptance_rate": 0.46,
      "verified_email": false,
      "verified_phone": false,
      "linkedin_connected": false
    }
  },
  {
    "candidate_id": "CAND_0000019",
    "profile": {
      "anonymized_name": "Myra Mishra",
      "headline": "Project Manager | 6.5+ yrs experience",
      "summary": "Professional with 6.5+ years of experience. I've spent my career in marketing manager roles, mostly focused on driving outcomes through process, people, and customer relationships. Lately I've been curious about how AI tools could augment my work \u2014 I've experimented with ChatGPT and a few other tools for productivity and content creation, and I think the space is exciting. Open to roles where I can apply my domain expertise alongside emerging AI capabilities.",
      "location": "Trivandrum, Kerala",
      "country": "India",
      "years_of_experience": 6.5,
      "current_title": "Project Manager",
      "current_company": "Wayne Enterprises",
      "current_company_size": "10001+",
      "current_industry": "Conglomerate"
    },
    "career_history": [
      {
        "company": "Wayne Enterprises",
        "title": "Project Manager",
        "start_date": "2022-10-15",
        "end_date": null,
        "duration_months": 44,
        "is_current": true,
        "industry": "Conglomerate",
        "company_size": "10001+",
        "description": "Business analyst at a consulting firm, working primarily with retail and CPG clients. Conducted business diagnostics, process re-engineering work, and digital transformation strategy projects. Strong on stakeholder management, structured problem-solving, and the typical consulting toolkit (slide-craft, Excel modeling, executive communication). Recent project work involved AI-strategy advisory but my own technical depth in AI is limited."
      },
      {
        "company": "Wayne Enterprises",
        "title": "Marketing Manager",
        "start_date": "2020-08-19",
        "end_date": "2022-10-08",
        "duration_months": 26,
        "is_current": false,
        "industry": "Conglomerate",
        "company_size": "10001+",
        "description": "Mechanical engineering design role at a hardware-product company. Led the design of two product subsystems through full lifecycle: concept, DFM/DFMA review, prototype, production tooling. Comfortable with CAD (SolidWorks, Creo), FEA (ANSYS), and the typical hardware-development cadence. Worked closely with manufacturing partners on production scale-up."
      },
      {
        "company": "Pied Piper",
        "title": "Business Analyst",
        "start_date": "2020-01-15",
        "end_date": "2020-08-12",
        "duration_months": 7,
        "is_current": false,
        "industry": "Software",
        "company_size": "11-50",
        "description": "Brand design and creative direction at a consumer-products company. Owned brand identity (logo, visual system, typography), packaging design, and digital creative across web and social. Led the recent rebrand and managed a small external agency for production work. Comfortable across the Adobe suite, Figma, and the production side of brand and packaging design."
      }
    ],
    "education": [
      {
        "institution": "IISc Bangalore",
        "degree": "M.Tech",
        "field_of_study": "Computer Science",
        "start_year": 2010,
        "end_year": 2014,
        "grade": "72%",
        "tier": "tier_1"
      },
      {
        "institution": "IIT Guwahati",
        "degree": "M.Tech",
        "field_of_study": "Machine Learning",
        "start_year": 2002,
        "end_year": 2006,
        "grade": "7.34 CGPA",
        "tier": "tier_1"
      }
    ],
    "skills": [
      {
        "name": "Figma",
        "proficiency": "intermediate",
        "endorsements": 13,
        "duration_months": 34
      },
      {
        "name": "GraphQL",
        "proficiency": "beginner",
        "endorsements": 4,
        "duration_months": 12
      },
      {
        "name": "Six Sigma",
        "proficiency": "beginner",
        "endorsements": 4,
        "duration_months": 10
      },
      {
        "name": "Scrum",
        "proficiency": "beginner",
        "endorsements": 15,
        "duration_months": 2
      },
      {
        "name": "YOLO",
        "proficiency": "intermediate",
        "endorsements": 10,
        "duration_months": 34
      },
      {
        "name": "gRPC",
        "proficiency": "beginner",
        "endorsements": 12,
        "duration_months": 9
      },
      {
        "name": "AWS",
        "proficiency": "intermediate",
        "endorsements": 11,
        "duration_months": 28
      },
      {
        "name": "Azure",
        "proficiency": "intermediate",
        "endorsements": 6,
        "duration_months": 21
      }
    ],
    "certifications": [],
    "languages": [
      {
        "language": "English",
        "proficiency": "professional"
      },
      {
        "language": "Hindi",
        "proficiency": "conversational"
      }
    ],
    "redrob_signals": {
      "profile_completeness_score": 38.6,
      "signup_date": "2025-07-20",
      "last_active_date": "2026-05-21",
      "open_to_work_flag": false,
      "profile_views_received_30d": 61,
      "applications_submitted_30d": 9,
      "recruiter_response_rate": 0.34,
      "avg_response_time_hours": 100.0,
      "skill_assessment_scores": {},
      "connection_count": 593,
      "endorsements_received": 25,
      "notice_period_days": 60,
      "expected_salary_range_inr_lpa": {
        "min": 12.5,
        "max": 7.7
      },
      "preferred_work_mode": "hybrid",
      "willing_to_relocate": false,
      "github_activity_score": -1,
      "search_appearance_30d": 141,
      "saved_by_recruiters_30d": 0,
      "interview_completion_rate": 0.31,
      "offer_acceptance_rate": -1,
      "verified_email": false,
      "verified_phone": true,
      "linkedin_connected": false
    }
  },
  {
    "candidate_id": "CAND_0000020",
    "profile": {
      "anonymized_name": "Aditya Iyengar",
      "headline": "Mechanical Engineer | 6.3+ yrs experience",
      "summary": "Professional with 6.3+ years of experience. I'm a marketing manager with substantial experience in cross-functional collaboration, stakeholder management, and execution. Lately I've been curious about how AI tools could augment my work \u2014 I've experimented with ChatGPT and a few other tools for productivity and content creation, and I think the space is exciting. Open to roles where I can apply my domain expertise alongside emerging AI capabilities.",
      "location": "Ahmedabad, Gujarat",
      "country": "India",
      "years_of_experience": 6.3,
      "current_title": "Mechanical Engineer",
      "current_company": "Wipro",
      "current_company_size": "10001+",
      "current_industry": "IT Services"
    },
    "career_history": [
      {
        "company": "Wipro",
        "title": "Mechanical Engineer",
        "start_date": "2023-06-12",
        "end_date": null,
        "duration_months": 36,
        "is_current": true,
        "industry": "IT Services",
        "company_size": "10001+",
        "description": "Marketing leadership role at a B2B SaaS company. Owned the demand-generation function \u2014 content marketing, paid acquisition, SEO, email nurture. Built and managed a team of 5 across content, performance marketing, and marketing operations. Worked closely with sales on lead-quality definitions and the SDR-handoff process. Recent focus has been on account-based marketing for our enterprise segment."
      },
      {
        "company": "Stark Industries",
        "title": "Graphic Designer",
        "start_date": "2020-07-27",
        "end_date": "2023-04-13",
        "duration_months": 33,
        "is_current": false,
        "industry": "Manufacturing",
        "company_size": "1001-5000",
        "description": "Marketing leadership role at a B2B SaaS company. Owned the demand-generation function \u2014 content marketing, paid acquisition, SEO, email nurture. Built and managed a team of 5 across content, performance marketing, and marketing operations. Worked closely with sales on lead-quality definitions and the SDR-handoff process. Recent focus has been on account-based marketing for our enterprise segment."
      },
      {
        "company": "Dunder Mifflin",
        "title": "Civil Engineer",
        "start_date": "2020-01-29",
        "end_date": "2020-07-27",
        "duration_months": 6,
        "is_current": false,
        "industry": "Paper Products",
        "company_size": "201-500",
        "description": "Content writing and SEO strategy for a tech-focused publication. Wrote longform articles on developer tools, cloud platforms, and AI/ML topics \u2014 including some that ranked on the first page of search for high-competition keywords. Managed a freelance writer pool and the editorial calendar. Recent work has been on AI-assisted content production, using LLM tools for research, drafting, and editing while maintaining editorial quality."
      }
    ],
    "education": [
      {
        "institution": "IIT Kharagpur",
        "degree": "B.E.",
        "field_of_study": "Computer Science",
        "start_year": 2018,
        "end_year": 2022,
        "grade": "6.67 CGPA",
        "tier": "tier_1"
      }
    ],
    "skills": [
      {
        "name": "GraphQL",
        "proficiency": "beginner",
        "endorsements": 15,
        "duration_months": 18
      },
      {
        "name": "TypeScript",
        "proficiency": "beginner",
        "endorsements": 7,
        "duration_months": 8
      },
      {
        "name": "Flask",
        "proficiency": "beginner",
        "endorsements": 11,
        "duration_months": 16
      },
      {
        "name": "Weights & Biases",
        "proficiency": "advanced",
        "endorsements": 50,
        "duration_months": 30
      },
      {
        "name": "GCP",
        "proficiency": "intermediate",
        "endorsements": 2,
        "duration_months": 34
      },
      {
        "name": "Salesforce CRM",
        "proficiency": "beginner",
        "endorsements": 8,
        "duration_months": 16
      },
      {
        "name": "HTML",
        "proficiency": "intermediate",
        "endorsements": 2,
        "duration_months": 35
      }
    ],
    "certifications": [
      {
        "name": "Scrum Master Certified",
        "issuer": "Scrum Alliance",
        "year": 2021
      }
    ],
    "languages": [
      {
        "language": "English",
        "proficiency": "professional"
      },
      {
        "language": "Hindi",
        "proficiency": "conversational"
      }
    ],
    "redrob_signals": {
      "profile_completeness_score": 73.0,
      "signup_date": "2023-01-26",
      "last_active_date": "2025-10-05",
      "open_to_work_flag": false,
      "profile_views_received_30d": 38,
      "applications_submitted_30d": 9,
      "recruiter_response_rate": 0.55,
      "avg_response_time_hours": 207.8,
      "skill_assessment_scores": {
        "Weights & Biases": 53.7
      },
      "connection_count": 479,
      "endorsements_received": 35,
      "notice_period_days": 30,
      "expected_salary_range_inr_lpa": {
        "min": 17.2,
        "max": 18.2
      },
      "preferred_work_mode": "remote",
      "willing_to_relocate": false,
      "github_activity_score": -1,
      "search_appearance_30d": 31,
      "saved_by_recruiters_30d": 11,
      "interview_completion_rate": 0.71,
      "offer_acceptance_rate": -1,
      "verified_email": true,
      "verified_phone": false,
      "linkedin_connected": true
    }
  },
  {
    "candidate_id": "CAND_0000021",
    "profile": {
      "anonymized_name": "Rahul Joshi",
      "headline": "Project Manager | AI enthusiast | Building with LLMs",
      "summary": "Project Manager with 14.5+ years of experience driving outcomes in my domain. I have built strong functional expertise in the typical responsibilities of the role, including team management, stakeholder communication, and project delivery. Recently I've been excited about how AI and GenAI tools can augment my work. I've been taking online courses on RAG and vector databases, experimenting with LangChain and the OpenAI API for side projects, and exploring how LLMs can streamline workflows in my current function. Open to roles that combine my existing domain experience with emerging AI technologies \u2014 I think the most interesting opportunities are at this intersection. Looking for positions where I can contribute both my functional expertise and grow my AI capabilities.",
      "location": "Bhubaneswar, Odisha",
      "country": "India",
      "years_of_experience": 14.5,
      "current_title": "Project Manager",
      "current_company": "Wipro",
      "current_company_size": "10001+",
      "current_industry": "IT Services"
    },
    "career_history": [
      {
        "company": "Wipro",
        "title": "Project Manager",
        "start_date": "2023-12-09",
        "end_date": null,
        "duration_months": 30,
        "is_current": true,
        "industry": "IT Services",
        "company_size": "10001+",
        "description": "Brand design and creative direction at a consumer-products company. Owned brand identity (logo, visual system, typography), packaging design, and digital creative across web and social. Led the recent rebrand and managed a small external agency for production work. Comfortable across the Adobe suite, Figma, and the production side of brand and packaging design."
      },
      {
        "company": "Infosys",
        "title": "Marketing Manager",
        "start_date": "2021-02-22",
        "end_date": "2023-10-10",
        "duration_months": 32,
        "is_current": false,
        "industry": "IT Services",
        "company_size": "10001+",
        "description": "Mechanical engineering design role at a hardware-product company. Led the design of two product subsystems through full lifecycle: concept, DFM/DFMA review, prototype, production tooling. Comfortable with CAD (SolidWorks, Creo), FEA (ANSYS), and the typical hardware-development cadence. Worked closely with manufacturing partners on production scale-up."
      },
      {
        "company": "Stark Industries",
        "title": "Sales Executive",
        "start_date": "2019-08-25",
        "end_date": "2021-02-15",
        "duration_months": 18,
        "is_current": false,
        "industry": "Manufacturing",
        "company_size": "1001-5000",
        "description": "Customer support team lead at a SaaS product. Managed a team of 8 support agents handling tier-1 and tier-2 tickets; owned the escalation process to engineering and the customer-feedback loop to product. Built out the support knowledge base and the agent training program. Strong on the people-management side and the process side; lighter on technical depth beyond product expertise."
      },
      {
        "company": "Dunder Mifflin",
        "title": "Customer Support",
        "start_date": "2015-06-17",
        "end_date": "2019-08-25",
        "duration_months": 51,
        "is_current": false,
        "industry": "Paper Products",
        "company_size": "201-500",
        "description": "Customer support team lead at a SaaS product. Managed a team of 8 support agents handling tier-1 and tier-2 tickets; owned the escalation process to engineering and the customer-feedback loop to product. Built out the support knowledge base and the agent training program. Strong on the people-management side and the process side; lighter on technical depth beyond product expertise."
      },
      {
        "company": "Wipro",
        "title": "Project Manager",
        "start_date": "2014-03-24",
        "end_date": "2015-06-17",
        "duration_months": 15,
        "is_current": false,
        "industry": "IT Services",
        "company_size": "10001+",
        "description": "Customer support team lead at a SaaS product. Managed a team of 8 support agents handling tier-1 and tier-2 tickets; owned the escalation process to engineering and the customer-feedback loop to product. Built out the support knowledge base and the agent training program. Strong on the people-management side and the process side; lighter on technical depth beyond product expertise."
      },
      {
        "company": "TCS",
        "title": "Customer Support",
        "start_date": "2011-12-05",
        "end_date": "2014-01-23",
        "duration_months": 26,
        "is_current": false,
        "industry": "IT Services",
        "company_size": "10001+",
        "description": "Business analyst at a consulting firm, working primarily with retail and CPG clients. Conducted business diagnostics, process re-engineering work, and digital transformation strategy projects. Strong on stakeholder management, structured problem-solving, and the typical consulting toolkit (slide-craft, Excel modeling, executive communication). Recent project work involved AI-strategy advisory but my own technical depth in AI is limited."
      }
    ],
    "education": [
      {
        "institution": "Tier-3 Engineering College",
        "degree": "B.Tech",
        "field_of_study": "Artificial Intelligence",
        "start_year": 2008,
        "end_year": 2011,
        "grade": "9.30 CGPA",
        "tier": "tier_4"
      }
    ],
    "skills": [
      {
        "name": "Hadoop",
        "proficiency": "beginner",
        "endorsements": 10,
        "duration_months": 5
      },
      {
        "name": "PostgreSQL",
        "proficiency": "beginner",
        "endorsements": 10,
        "duration_months": 4
      },
      {
        "name": "Kafka",
        "proficiency": "beginner",
        "endorsements": 6,
        "duration_months": 6
      },
      {
        "name": "Microservices",
        "proficiency": "intermediate",
        "endorsements": 0,
        "duration_months": 14
      },
      {
        "name": "AWS",
        "proficiency": "intermediate",
        "endorsements": 11,
        "duration_months": 26
      },
      {
        "name": "TypeScript",
        "proficiency": "beginner",
        "endorsements": 6,
        "duration_months": 6
      },
      {
        "name": "ETL",
        "proficiency": "beginner",
        "endorsements": 11,
        "duration_months": 3
      },
      {
        "name": "Spring Boot",
        "proficiency": "beginner",
        "endorsements": 1,
        "duration_months": 12
      },
      {
        "name": "Recommendation Systems",
        "proficiency": "advanced",
        "endorsements": 3,
        "duration_months": 13
      },
      {
        "name": "Fine-tuning LLMs",
        "proficiency": "advanced",
        "endorsements": 4,
        "duration_months": 4
      },
      {
        "name": "Prompt Engineering",
        "proficiency": "advanced",
        "endorsements": 4,
        "duration_months": 5
      },
      {
        "name": "LangChain",
        "proficiency": "intermediate",
        "endorsements": 1,
        "duration_months": 7
      },
      {
        "name": "Pinecone",
        "proficiency": "intermediate",
        "endorsements": 4,
        "duration_months": 16
      },
      {
        "name": "Vector Search",
        "proficiency": "intermediate",
        "endorsements": 3,
        "duration_months": 13
      },
      {
        "name": "Embeddings",
        "proficiency": "advanced",
        "endorsements": 4,
        "duration_months": 18
      },
      {
        "name": "FAISS",
        "proficiency": "intermediate",
        "endorsements": 2,
        "duration_months": 8
      }
    ],
    "certifications": [],
    "languages": [
      {
        "language": "English",
        "proficiency": "professional"
      },
      {
        "language": "Hindi",
        "proficiency": "professional"
      }
    ],
    "redrob_signals": {
      "profile_completeness_score": 58.5,
      "signup_date": "2026-02-10",
      "last_active_date": "2025-11-21",
      "open_to_work_flag": false,
      "profile_views_received_30d": 1,
      "applications_submitted_30d": 8,
      "recruiter_response_rate": 0.49,
      "avg_response_time_hours": 98.7,
      "skill_assessment_scores": {},
      "connection_count": 52,
      "endorsements_received": 3,
      "notice_period_days": 60,
      "expected_salary_range_inr_lpa": {
        "min": 10.9,
        "max": 24.4
      },
      "preferred_work_mode": "hybrid",
      "willing_to_relocate": true,
      "github_activity_score": 6.4,
      "search_appearance_30d": 8,
      "saved_by_recruiters_30d": 3,
      "interview_completion_rate": 0.53,
      "offer_acceptance_rate": -1,
      "verified_email": true,
      "verified_phone": true,
      "linkedin_connected": true
    }
  },
  {
    "candidate_id": "CAND_0000022",
    "profile": {
      "anonymized_name": "Shaurya Chatterjee",
      "headline": "Mechanical Engineer | Driving business outcomes",
      "summary": "Professional with 1.1+ years of experience. I'm a marketing manager with substantial experience in cross-functional collaboration, stakeholder management, and execution. Lately I've been curious about how AI tools could augment my work \u2014 I've experimented with ChatGPT and a few other tools for productivity and content creation, and I think the space is exciting. Open to roles where I can apply my domain expertise alongside emerging AI capabilities.",
      "location": "Sydney",
      "country": "Australia",
      "years_of_experience": 1.1,
      "current_title": "Mechanical Engineer",
      "current_company": "Hooli",
      "current_company_size": "1001-5000",
      "current_industry": "Software"
    },
    "career_history": [
      {
        "company": "Hooli",
        "title": "Mechanical Engineer",
        "start_date": "2025-05-02",
        "end_date": null,
        "duration_months": 13,
        "is_current": true,
        "industry": "Software",
        "company_size": "1001-5000",
        "description": "Content writing and SEO strategy for a tech-focused publication. Wrote longform articles on developer tools, cloud platforms, and AI/ML topics \u2014 including some that ranked on the first page of search for high-competition keywords. Managed a freelance writer pool and the editorial calendar. Recent work has been on AI-assisted content production, using LLM tools for research, drafting, and editing while maintaining editorial quality."
      }
    ],
    "education": [
      {
        "institution": "VJTI Mumbai",
        "degree": "M.E.",
        "field_of_study": "Information Technology",
        "start_year": 2002,
        "end_year": 2006,
        "grade": "8.23 CGPA",
        "tier": "tier_2"
      }
    ],
    "skills": [
      {
        "name": "OpenCV",
        "proficiency": "intermediate",
        "endorsements": 2,
        "duration_months": 11
      },
      {
        "name": "Django",
        "proficiency": "intermediate",
        "endorsements": 0,
        "duration_months": 23
      },
      {
        "name": "Terraform",
        "proficiency": "intermediate",
        "endorsements": 11,
        "duration_months": 14
      },
      {
        "name": "Scrum",
        "proficiency": "intermediate",
        "endorsements": 7,
        "duration_months": 18
      },
      {
        "name": "SQL",
        "proficiency": "intermediate",
        "endorsements": 3,
        "duration_months": 36
      },
      {
        "name": "Java",
        "proficiency": "beginner",
        "endorsements": 11,
        "duration_months": 15
      },
      {
        "name": "AWS",
        "proficiency": "intermediate",
        "endorsements": 5,
        "duration_months": 29
      },
      {
        "name": "Six Sigma",
        "proficiency": "beginner",
        "endorsements": 1,
        "duration_months": 4
      }
    ],
    "certifications": [
      {
        "name": "AWS Certified Cloud Practitioner",
        "issuer": "AWS",
        "year": 2024
      }
    ],
    "languages": [
      {
        "language": "English",
        "proficiency": "professional"
      },
      {
        "language": "Hindi",
        "proficiency": "conversational"
      }
    ],
    "redrob_signals": {
      "profile_completeness_score": 63.1,
      "signup_date": "2022-12-26",
      "last_active_date": "2026-05-03",
      "open_to_work_flag": true,
      "profile_views_received_30d": 39,
      "applications_submitted_30d": 2,
      "recruiter_response_rate": 0.27,
      "avg_response_time_hours": 30.2,
      "skill_assessment_scores": {},
      "connection_count": 538,
      "endorsements_received": 21,
      "notice_period_days": 150,
      "expected_salary_range_inr_lpa": {
        "min": 12.3,
        "max": 8.5
      },
      "preferred_work_mode": "remote",
      "willing_to_relocate": false,
      "github_activity_score": -1,
      "search_appearance_30d": 136,
      "saved_by_recruiters_30d": 5,
      "interview_completion_rate": 0.45,
      "offer_acceptance_rate": -1,
      "verified_email": true,
      "verified_phone": false,
      "linkedin_connected": false
    }
  },
  {
    "candidate_id": "CAND_0000023",
    "profile": {
      "anonymized_name": "Kavya Nair",
      "headline": "Software Engineer | Cloud & DevOps",
      "summary": "Software engineer with 3.7 years of experience across web, backend, and cloud systems. Strong fundamentals in software development and system design. Most of my work is conventional backend engineering \u2014 APIs, databases, queues, deployments. I've been keeping up with AI/ML at a self-learner level \u2014 taken some online courses, played with the OpenAI and Anthropic APIs, built a small RAG side project \u2014 but I haven't done it in a professional capacity yet. Open to roles where I can either deepen my software engineering work or, if the team is open to it, start contributing to ML-adjacent systems.",
      "location": "New York",
      "country": "USA",
      "years_of_experience": 3.7,
      "current_title": "Software Engineer",
      "current_company": "Acme Corp",
      "current_company_size": "201-500",
      "current_industry": "Manufacturing"
    },
    "career_history": [
      {
        "company": "Acme Corp",
        "title": "Software Engineer",
        "start_date": "2025-04-02",
        "end_date": null,
        "duration_months": 14,
        "is_current": true,
        "industry": "Manufacturing",
        "company_size": "201-500",
        "description": "Test automation and QA engineering for a fintech product. Built and maintained the end-to-end test suite using Selenium and pytest, plus the load-testing setup using Locust. Worked closely with developers on testability patterns and with product on acceptance criteria. Recent work has been on shifting test responsibility into the dev team \u2014 moving from QA-as-gate to QA-as-coach. Career has been entirely in QA/test engineering."
      },
      {
        "company": "Flipkart",
        "title": "Frontend Engineer",
        "start_date": "2022-10-15",
        "end_date": "2025-04-02",
        "duration_months": 30,
        "is_current": false,
        "industry": "E-commerce",
        "company_size": "10001+",
        "description": "Android mobile development using Java and (more recently) Kotlin at a consumer-app company. Built and maintained multiple production features including the main shopping flow, push notification system, and the offline-first sync layer. Comfortable with the Android framework, Jetpack components, and the typical patterns (MVVM, Hilt, Coroutines). My career has been entirely on mobile so far; interested in expanding into broader backend or platform engineering."
      }
    ],
    "education": [
      {
        "institution": "VJTI Mumbai",
        "degree": "B.E.",
        "field_of_study": "Data Science",
        "start_year": 2009,
        "end_year": 2013,
        "grade": "9.43 CGPA",
        "tier": "tier_2"
      }
    ],
    "skills": [
      {
        "name": "BigQuery",
        "proficiency": "beginner",
        "endorsements": 8,
        "duration_months": 6
      },
      {
        "name": "Marketing",
        "proficiency": "intermediate",
        "endorsements": 0,
        "duration_months": 15
      },
      {
        "name": "Node.js",
        "proficiency": "intermediate",
        "endorsements": 3,
        "duration_months": 28
      },
      {
        "name": "Django",
        "proficiency": "beginner",
        "endorsements": 13,
        "duration_months": 16
      },
      {
        "name": "Salesforce CRM",
        "proficiency": "beginner",
        "endorsements": 9,
        "duration_months": 18
      },
      {
        "name": "MongoDB",
        "proficiency": "beginner",
        "endorsements": 8,
        "duration_months": 10
      },
      {
        "name": "ETL",
        "proficiency": "beginner",
        "endorsements": 12,
        "duration_months": 16
      },
      {
        "name": "Redis",
        "proficiency": "beginner",
        "endorsements": 4,
        "duration_months": 10
      },
      {
        "name": "Illustrator",
        "proficiency": "beginner",
        "endorsements": 1,
        "duration_months": 2
      },
      {
        "name": "Rust",
        "proficiency": "intermediate",
        "endorsements": 2,
        "duration_months": 16
      }
    ],
    "certifications": [],
    "languages": [
      {
        "language": "English",
        "proficiency": "native"
      },
      {
        "language": "Hindi",
        "proficiency": "native"
      }
    ],
    "redrob_signals": {
      "profile_completeness_score": 50.7,
      "signup_date": "2025-09-13",
      "last_active_date": "2026-04-06",
      "open_to_work_flag": false,
      "profile_views_received_30d": 10,
      "applications_submitted_30d": 2,
      "recruiter_response_rate": 0.57,
      "avg_response_time_hours": 64.8,
      "skill_assessment_scores": {},
      "connection_count": 763,
      "endorsements_received": 39,
      "notice_period_days": 30,
      "expected_salary_range_inr_lpa": {
        "min": 17.4,
        "max": 20.5
      },
      "preferred_work_mode": "flexible",
      "willing_to_relocate": false,
      "github_activity_score": 48.5,
      "search_appearance_30d": 239,
      "saved_by_recruiters_30d": 14,
      "interview_completion_rate": 0.9,
      "offer_acceptance_rate": -1,
      "verified_email": true,
      "verified_phone": true,
      "linkedin_connected": false
    }
  },
  {
    "candidate_id": "CAND_0000024",
    "profile": {
      "anonymized_name": "Rajesh Arora",
      "headline": "HR Manager | 7.5+ yrs experience",
      "summary": "Professional with 7.5+ years of experience. I've spent my career in marketing manager roles, mostly focused on driving outcomes through process, people, and customer relationships. Lately I've been curious about how AI tools could augment my work \u2014 I've experimented with ChatGPT and a few other tools for productivity and content creation, and I think the space is exciting. Open to roles where I can apply my domain expertise alongside emerging AI capabilities.",
      "location": "Trivandrum, Kerala",
      "country": "India",
      "years_of_experience": 7.5,
      "current_title": "HR Manager",
      "current_company": "TCS",
      "current_company_size": "10001+",
      "current_industry": "IT Services"
    },
    "career_history": [
      {
        "company": "TCS",
        "title": "HR Manager",
        "start_date": "2023-04-13",
        "end_date": null,
        "duration_months": 38,
        "is_current": true,
        "industry": "IT Services",
        "company_size": "10001+",
        "description": "Marketing leadership role at a B2B SaaS company. Owned the demand-generation function \u2014 content marketing, paid acquisition, SEO, email nurture. Built and managed a team of 5 across content, performance marketing, and marketing operations. Worked closely with sales on lead-quality definitions and the SDR-handoff process. Recent focus has been on account-based marketing for our enterprise segment."
      },
      {
        "company": "Infosys",
        "title": "Accountant",
        "start_date": "2018-12-05",
        "end_date": "2023-02-12",
        "duration_months": 51,
        "is_current": false,
        "industry": "IT Services",
        "company_size": "10001+",
        "description": "Content writing and SEO strategy for a tech-focused publication. Wrote longform articles on developer tools, cloud platforms, and AI/ML topics \u2014 including some that ranked on the first page of search for high-competition keywords. Managed a freelance writer pool and the editorial calendar. Recent work has been on AI-assisted content production, using LLM tools for research, drafting, and editing while maintaining editorial quality."
      }
    ],
    "education": [
      {
        "institution": "Symbiosis International",
        "degree": "Ph.D",
        "field_of_study": "Computer Science",
        "start_year": 2008,
        "end_year": 2013,
        "grade": "7.65 CGPA",
        "tier": "tier_3"
      }
    ],
    "skills": [
      {
        "name": "Figma",
        "proficiency": "beginner",
        "endorsements": 14,
        "duration_months": 15
      },
      {
        "name": "Kubernetes",
        "proficiency": "beginner",
        "endorsements": 8,
        "duration_months": 17
      },
      {
        "name": "Forecasting",
        "proficiency": "advanced",
        "endorsements": 43,
        "duration_months": 30
      },
      {
        "name": "ETL",
        "proficiency": "intermediate",
        "endorsements": 11,
        "duration_months": 12
      },
      {
        "name": "Node.js",
        "proficiency": "intermediate",
        "endorsements": 3,
        "duration_months": 15
      },
      {
        "name": "Docker",
        "proficiency": "beginner",
        "endorsements": 5,
        "duration_months": 5
      }
    ],
    "certifications": [],
    "languages": [
      {
        "language": "English",
        "proficiency": "professional"
      },
      {
        "language": "Hindi",
        "proficiency": "native"
      }
    ],
    "redrob_signals": {
      "profile_completeness_score": 63.7,
      "signup_date": "2022-08-30",
      "last_active_date": "2026-01-20",
      "open_to_work_flag": false,
      "profile_views_received_30d": 71,
      "applications_submitted_30d": 4,
      "recruiter_response_rate": 0.78,
      "avg_response_time_hours": 238.2,
      "skill_assessment_scores": {
        "Forecasting": 65.1
      },
      "connection_count": 445,
      "endorsements_received": 41,
      "notice_period_days": 60,
      "expected_salary_range_inr_lpa": {
        "min": 9.9,
        "max": 22.1
      },
      "preferred_work_mode": "flexible",
      "willing_to_relocate": true,
      "github_activity_score": 46.3,
      "search_appearance_30d": 84,
      "saved_by_recruiters_30d": 7,
      "interview_completion_rate": 0.72,
      "offer_acceptance_rate": -1,
      "verified_email": false,
      "verified_phone": true,
      "linkedin_connected": false
    }
  },
  {
    "candidate_id": "CAND_0000025",
    "profile": {
      "anonymized_name": "Anika Kumar",
      "headline": "Frontend Engineer | Cloud & DevOps",
      "summary": "Software engineer with 7.3 years of experience across web, backend, and cloud systems. Strong fundamentals in software development and system design. I've worked across web frontends, REST APIs, and cloud deployments; comfortable in most parts of a typical SaaS stack. I've been keeping up with AI/ML at a self-learner level \u2014 taken some online courses, played with the OpenAI and Anthropic APIs, built a small RAG side project \u2014 but I haven't done it in a professional capacity yet. Open to roles where I can either deepen my software engineering work or, if the team is open to it, start contributing to ML-adjacent systems.",
      "location": "Vizag, Andhra Pradesh",
      "country": "India",
      "years_of_experience": 7.3,
      "current_title": "Frontend Engineer",
      "current_company": "Tech Mahindra",
      "current_company_size": "10001+",
      "current_industry": "IT Services"
    },
    "career_history": [
      {
        "company": "Tech Mahindra",
        "title": "Frontend Engineer",
        "start_date": "2023-09-10",
        "end_date": null,
        "duration_months": 33,
        "is_current": true,
        "industry": "IT Services",
        "company_size": "10001+",
        "description": "Android mobile development using Java and (more recently) Kotlin at a consumer-app company. Built and maintained multiple production features including the main shopping flow, push notification system, and the offline-first sync layer. Comfortable with the Android framework, Jetpack components, and the typical patterns (MVVM, Hilt, Coroutines). My career has been entirely on mobile so far; interested in expanding into broader backend or platform engineering."
      },
      {
        "company": "Mindtree",
        "title": "Frontend Engineer",
        "start_date": "2019-09-17",
        "end_date": "2023-08-27",
        "duration_months": 48,
        "is_current": false,
        "industry": "IT Services",
        "company_size": "10001+",
        "description": "Android mobile development using Java and (more recently) Kotlin at a consumer-app company. Built and maintained multiple production features including the main shopping flow, push notification system, and the offline-first sync layer. Comfortable with the Android framework, Jetpack components, and the typical patterns (MVVM, Hilt, Coroutines). My career has been entirely on mobile so far; interested in expanding into broader backend or platform engineering."
      },
      {
        "company": "Zomato",
        "title": "Frontend Engineer",
        "start_date": "2019-03-21",
        "end_date": "2019-09-17",
        "duration_months": 6,
        "is_current": false,
        "industry": "Food Delivery",
        "company_size": "5001-10000",
        "description": "Frontend engineering at a media company. React, TypeScript, and the typical surrounding tooling (Webpack, Jest, Cypress). Built the company's design system from scratch and led the migration from a legacy AngularJS app. Strong on the frontend craft \u2014 accessibility, performance, animations \u2014 but limited backend exposure."
      }
    ],
    "education": [
      {
        "institution": "Regional Technical Institute",
        "degree": "Ph.D",
        "field_of_study": "Mechanical Engineering",
        "start_year": 2006,
        "end_year": 2010,
        "grade": "8.18 CGPA",
        "tier": "tier_4"
      }
    ],
    "skills": [
      {
        "name": "JavaScript",
        "proficiency": "intermediate",
        "endorsements": 10,
        "duration_months": 26
      },
      {
        "name": "Spark",
        "proficiency": "intermediate",
        "endorsements": 0,
        "duration_months": 22
      },
      {
        "name": "GCP",
        "proficiency": "beginner",
        "endorsements": 7,
        "duration_months": 13
      },
      {
        "name": "TypeScript",
        "proficiency": "beginner",
        "endorsements": 2,
        "duration_months": 17
      },
      {
        "name": "LangChain",
        "proficiency": "advanced",
        "endorsements": 15,
        "duration_months": 34
      },
      {
        "name": "Apache Flink",
        "proficiency": "intermediate",
        "endorsements": 2,
        "duration_months": 19
      },
      {
        "name": "ETL",
        "proficiency": "beginner",
        "endorsements": 1,
        "duration_months": 18
      },
      {
        "name": "Redis",
        "proficiency": "beginner",
        "endorsements": 0,
        "duration_months": 10
      },
      {
        "name": "Data Pipelines",
        "proficiency": "intermediate",
        "endorsements": 9,
        "duration_months": 32
      }
    ],
    "certifications": [
      {
        "name": "Six Sigma Green Belt",
        "issuer": "ASQ",
        "year": 2018
      },
      {
        "name": "AWS Certified Cloud Practitioner",
        "issuer": "AWS",
        "year": 2025
      }
    ],
    "languages": [
      {
        "language": "English",
        "proficiency": "professional"
      },
      {
        "language": "Hindi",
        "proficiency": "conversational"
      }
    ],
    "redrob_signals": {
      "profile_completeness_score": 70.7,
      "signup_date": "2023-12-18",
      "last_active_date": "2026-03-30",
      "open_to_work_flag": true,
      "profile_views_received_30d": 107,
      "applications_submitted_30d": 11,
      "recruiter_response_rate": 0.74,
      "avg_response_time_hours": 128.0,
      "skill_assessment_scores": {
        "LangChain": 40.0
      },
      "connection_count": 276,
      "endorsements_received": 52,
      "notice_period_days": 120,
      "expected_salary_range_inr_lpa": {
        "min": 18.8,
        "max": 30.7
      },
      "preferred_work_mode": "hybrid",
      "willing_to_relocate": false,
      "github_activity_score": -1,
      "search_appearance_30d": 74,
      "saved_by_recruiters_30d": 9,
      "interview_completion_rate": 0.7,
      "offer_acceptance_rate": -1,
      "verified_email": true,
      "verified_phone": true,
      "linkedin_connected": true
    }
  },
  {
    "candidate_id": "CAND_0000026",
    "profile": {
      "anonymized_name": "Neha Rao",
      "headline": "Graphic Designer | 6.8+ yrs experience",
      "summary": "Professional with 6.8+ years of experience. My professional background is in marketing manager \u2014 I've built and led teams, owned KPIs, and driven business outcomes in this domain. Lately I've been curious about how AI tools could augment my work \u2014 I've experimented with ChatGPT and a few other tools for productivity and content creation, and I think the space is exciting. Open to roles where I can apply my domain expertise alongside emerging AI capabilities.",
      "location": "Kochi, Kerala",
      "country": "India",
      "years_of_experience": 6.8,
      "current_title": "Graphic Designer",
      "current_company": "Initech",
      "current_company_size": "51-200",
      "current_industry": "Software"
    },
    "career_history": [
      {
        "company": "Initech",
        "title": "Graphic Designer",
        "start_date": "2022-11-14",
        "end_date": null,
        "duration_months": 43,
        "is_current": true,
        "industry": "Software",
        "company_size": "51-200",
        "description": "Customer support team lead at a SaaS product. Managed a team of 8 support agents handling tier-1 and tier-2 tickets; owned the escalation process to engineering and the customer-feedback loop to product. Built out the support knowledge base and the agent training program. Strong on the people-management side and the process side; lighter on technical depth beyond product expertise."
      },
      {
        "company": "Acme Corp",
        "title": "Accountant",
        "start_date": "2021-03-24",
        "end_date": "2022-11-14",
        "duration_months": 20,
        "is_current": false,
        "industry": "Manufacturing",
        "company_size": "201-500",
        "description": "Content writing and SEO strategy for a tech-focused publication. Wrote longform articles on developer tools, cloud platforms, and AI/ML topics \u2014 including some that ranked on the first page of search for high-competition keywords. Managed a freelance writer pool and the editorial calendar. Recent work has been on AI-assisted content production, using LLM tools for research, drafting, and editing while maintaining editorial quality."
      },
      {
        "company": "Acme Corp",
        "title": "Project Manager",
        "start_date": "2019-10-31",
        "end_date": "2021-03-24",
        "duration_months": 17,
        "is_current": false,
        "industry": "Manufacturing",
        "company_size": "201-500",
        "description": "Enterprise sales of cloud software solutions into the mid-market segment. Carried a $1.8M ARR quota and consistently delivered against it across the last three years. Owned the full sales cycle: prospecting, discovery, technical evaluation (with SE support), commercial negotiation, and close. Strong on consultative selling for technical buyers; comfortable engaging with both engineering and finance stakeholders."
      }
    ],
    "education": [
      {
        "institution": "Generic State University",
        "degree": "M.Sc",
        "field_of_study": "Statistics",
        "start_year": 2008,
        "end_year": 2012,
        "grade": "81%",
        "tier": "tier_4"
      },
      {
        "institution": "Lovely Professional University",
        "degree": "B.E.",
        "field_of_study": "Machine Learning",
        "start_year": 2008,
        "end_year": 2013,
        "grade": "83%",
        "tier": "tier_3"
      }
    ],
    "skills": [
      {
        "name": "Apache Beam",
        "proficiency": "intermediate",
        "endorsements": 4,
        "duration_months": 18
      },
      {
        "name": "Kubeflow",
        "proficiency": "intermediate",
        "endorsements": 14,
        "duration_months": 27
      },
      {
        "name": "Scrum",
        "proficiency": "beginner",
        "endorsements": 12,
        "duration_months": 8
      },
      {
        "name": "ETL",
        "proficiency": "beginner",
        "endorsements": 15,
        "duration_months": 17
      },
      {
        "name": "Django",
        "proficiency": "beginner",
        "endorsements": 6,
        "duration_months": 11
      },
      {
        "name": "Docker",
        "proficiency": "beginner",
        "endorsements": 4,
        "duration_months": 9
      },
      {
        "name": "Airflow",
        "proficiency": "intermediate",
        "endorsements": 7,
        "duration_months": 21
      },
      {
        "name": "Kubernetes",
        "proficiency": "intermediate",
        "endorsements": 13,
        "duration_months": 22
      }
    ],
    "certifications": [],
    "languages": [
      {
        "language": "English",
        "proficiency": "native"
      },
      {
        "language": "Hindi",
        "proficiency": "native"
      }
    ],
    "redrob_signals": {
      "profile_completeness_score": 80.3,
      "signup_date": "2023-12-08",
      "last_active_date": "2025-10-03",
      "open_to_work_flag": false,
      "profile_views_received_30d": 75,
      "applications_submitted_30d": 7,
      "recruiter_response_rate": 0.59,
      "avg_response_time_hours": 45.4,
      "skill_assessment_scores": {},
      "connection_count": 321,
      "endorsements_received": 8,
      "notice_period_days": 30,
      "expected_salary_range_inr_lpa": {
        "min": 17.1,
        "max": 8.0
      },
      "preferred_work_mode": "hybrid",
      "willing_to_relocate": false,
      "github_activity_score": -1,
      "search_appearance_30d": 154,
      "saved_by_recruiters_30d": 11,
      "interview_completion_rate": 0.49,
      "offer_acceptance_rate": -1,
      "verified_email": true,
      "verified_phone": false,
      "linkedin_connected": true
    }
  },
  {
    "candidate_id": "CAND_0000027",
    "profile": {
      "anonymized_name": "Avni Pandey",
      "headline": "DevOps Engineer | Cloud & DevOps",
      "summary": "Software engineer with 3.9 years of experience across web, backend, and cloud systems. Strong fundamentals in software development and system design. I've worked across web frontends, REST APIs, and cloud deployments; comfortable in most parts of a typical SaaS stack. I've been keeping up with AI/ML at a self-learner level \u2014 taken some online courses, played with the OpenAI and Anthropic APIs, built a small RAG side project \u2014 but I haven't done it in a professional capacity yet. Open to roles where I can either deepen my software engineering work or, if the team is open to it, start contributing to ML-adjacent systems.",
      "location": "Kolkata, West Bengal",
      "country": "India",
      "years_of_experience": 3.9,
      "current_title": "DevOps Engineer",
      "current_company": "Infosys",
      "current_company_size": "10001+",
      "current_industry": "IT Services"
    },
    "career_history": [
      {
        "company": "Infosys",
        "title": "DevOps Engineer",
        "start_date": "2023-06-12",
        "end_date": null,
        "duration_months": 36,
        "is_current": true,
        "industry": "IT Services",
        "company_size": "10001+",
        "description": "Java backend development at a large enterprise \u2014 Spring Boot microservices, Kafka for inter-service messaging, Postgres + Redis for storage. Worked on the customer onboarding flow which involved orchestrating multiple downstream services. Solid on the Spring ecosystem, transaction handling, and the operational side of Java services. Looking to either go deeper on distributed systems or expand into modern application stacks."
      },
      {
        "company": "Wipro",
        "title": "DevOps Engineer",
        "start_date": "2022-08-02",
        "end_date": "2023-05-29",
        "duration_months": 10,
        "is_current": false,
        "industry": "IT Services",
        "company_size": "10001+",
        "description": "Full-stack web application development at a SaaS company. Built React-based admin interfaces and the Node.js REST API backing them. Worked across the stack: frontend components, REST endpoint design, PostgreSQL schema, deployment via Docker/Kubernetes. Comfortable in most parts of a typical web stack though my comfort zone is the backend and database side. Recent learning has been on the testing and CI/CD discipline."
      }
    ],
    "education": [
      {
        "institution": "IIT Bombay",
        "degree": "Ph.D",
        "field_of_study": "Information Technology",
        "start_year": 2006,
        "end_year": 2010,
        "grade": "6.55 CGPA",
        "tier": "tier_1"
      },
      {
        "institution": "VJTI Mumbai",
        "degree": "B.E.",
        "field_of_study": "Artificial Intelligence",
        "start_year": 2017,
        "end_year": 2020,
        "grade": "9.11 CGPA",
        "tier": "tier_2"
      }
    ],
    "skills": [
      {
        "name": "Docker",
        "proficiency": "intermediate",
        "endorsements": 1,
        "duration_months": 9
      },
      {
        "name": "YOLO",
        "proficiency": "advanced",
        "endorsements": 31,
        "duration_months": 20
      },
      {
        "name": "PEFT",
        "proficiency": "advanced",
        "endorsements": 39,
        "duration_months": 35
      },
      {
        "name": "Webpack",
        "proficiency": "intermediate",
        "endorsements": 0,
        "duration_months": 33
      },
      {
        "name": "Data Science",
        "proficiency": "advanced",
        "endorsements": 18,
        "duration_months": 24
      },
      {
        "name": "AWS",
        "proficiency": "beginner",
        "endorsements": 4,
        "duration_months": 16
      },
      {
        "name": "Java",
        "proficiency": "intermediate",
        "endorsements": 2,
        "duration_months": 15
      },
      {
        "name": "Angular",
        "proficiency": "intermediate",
        "endorsements": 4,
        "duration_months": 25
      },
      {
        "name": "Databricks",
        "proficiency": "intermediate",
        "endorsements": 3,
        "duration_months": 31
      },
      {
        "name": "ETL",
        "proficiency": "intermediate",
        "endorsements": 5,
        "duration_months": 11
      },
      {
        "name": "Marketing",
        "proficiency": "beginner",
        "endorsements": 15,
        "duration_months": 14
      },
      {
        "name": "Information Retrieval",
        "proficiency": "intermediate",
        "endorsements": 5,
        "duration_months": 32
      },
      {
        "name": "Weights & Biases",
        "proficiency": "advanced",
        "endorsements": 31,
        "duration_months": 44
      },
      {
        "name": "Terraform",
        "proficiency": "intermediate",
        "endorsements": 12,
        "duration_months": 19
      },
      {
        "name": "SAP",
        "proficiency": "intermediate",
        "endorsements": 8,
        "duration_months": 9
      },
      {
        "name": "Illustrator",
        "proficiency": "beginner",
        "endorsements": 1,
        "duration_months": 11
      }
    ],
    "certifications": [],
    "languages": [
      {
        "language": "English",
        "proficiency": "professional"
      },
      {
        "language": "Hindi",
        "proficiency": "conversational"
      }
    ],
    "redrob_signals": {
      "profile_completeness_score": 31.0,
      "signup_date": "2023-03-07",
      "last_active_date": "2026-05-07",
      "open_to_work_flag": true,
      "profile_views_received_30d": 89,
      "applications_submitted_30d": 5,
      "recruiter_response_rate": 0.58,
      "avg_response_time_hours": 112.3,
      "skill_assessment_scores": {
        "YOLO": 60.2,
        "PEFT": 50.5,
        "Data Science": 35.1
      },
      "connection_count": 282,
      "endorsements_received": 24,
      "notice_period_days": 90,
      "expected_salary_range_inr_lpa": {
        "min": 17.9,
        "max": 20.2
      },
      "preferred_work_mode": "hybrid",
      "willing_to_relocate": false,
      "github_activity_score": 38.6,
      "search_appearance_30d": 136,
      "saved_by_recruiters_30d": 6,
      "interview_completion_rate": 0.61,
      "offer_acceptance_rate": 0.65,
      "verified_email": false,
      "verified_phone": true,
      "linkedin_connected": true
    }
  },
  {
    "candidate_id": "CAND_0000028",
    "profile": {
      "anonymized_name": "Rohan Krishnan",
      "headline": "Operations Manager | Driving business outcomes",
      "summary": "Professional with 1.1+ years of experience. My professional background is in marketing manager \u2014 I've built and led teams, owned KPIs, and driven business outcomes in this domain. Lately I've been curious about how AI tools could augment my work \u2014 I've experimented with ChatGPT and a few other tools for productivity and content creation, and I think the space is exciting. Open to roles where I can apply my domain expertise alongside emerging AI capabilities.",
      "location": "Dubai",
      "country": "UAE",
      "years_of_experience": 1.1,
      "current_title": "Operations Manager",
      "current_company": "Wipro",
      "current_company_size": "10001+",
      "current_industry": "IT Services"
    },
    "career_history": [
      {
        "company": "Wipro",
        "title": "Operations Manager",
        "start_date": "2025-05-02",
        "end_date": null,
        "duration_months": 13,
        "is_current": true,
        "industry": "IT Services",
        "company_size": "10001+",
        "description": "Brand design and creative direction at a consumer-products company. Owned brand identity (logo, visual system, typography), packaging design, and digital creative across web and social. Led the recent rebrand and managed a small external agency for production work. Comfortable across the Adobe suite, Figma, and the production side of brand and packaging design."
      }
    ],
    "education": [
      {
        "institution": "Symbiosis International",
        "degree": "M.Tech",
        "field_of_study": "Mathematics",
        "start_year": 2014,
        "end_year": 2017,
        "grade": "7.85 CGPA",
        "tier": "tier_3"
      }
    ],
    "skills": [
      {
        "name": "Snowflake",
        "proficiency": "beginner",
        "endorsements": 6,
        "duration_months": 3
      },
      {
        "name": "React",
        "proficiency": "beginner",
        "endorsements": 11,
        "duration_months": 7
      },
      {
        "name": "JavaScript",
        "proficiency": "beginner",
        "endorsements": 6,
        "duration_months": 10
      },
      {
        "name": "Tailwind",
        "proficiency": "beginner",
        "endorsements": 13,
        "duration_months": 15
      },
      {
        "name": "REST APIs",
        "proficiency": "intermediate",
        "endorsements": 6,
        "duration_months": 21
      },
      {
        "name": "Photoshop",
        "proficiency": "intermediate",
        "endorsements": 9,
        "duration_months": 30
      },
      {
        "name": "Data Pipelines",
        "proficiency": "intermediate",
        "endorsements": 4,
        "duration_months": 23
      },
      {
        "name": "Terraform",
        "proficiency": "intermediate",
        "endorsements": 9,
        "duration_months": 18
      },
      {
        "name": "CNN",
        "proficiency": "intermediate",
        "endorsements": 8,
        "duration_months": 29
      },
      {
        "name": "Content Writing",
        "proficiency": "beginner",
        "endorsements": 9,
        "duration_months": 18
      }
    ],
    "certifications": [
      {
        "name": "AWS Certified Cloud Practitioner",
        "issuer": "AWS",
        "year": 2020
      }
    ],
    "languages": [
      {
        "language": "English",
        "proficiency": "professional"
      },
      {
        "language": "Hindi",
        "proficiency": "conversational"
      }
    ],
    "redrob_signals": {
      "profile_completeness_score": 51.2,
      "signup_date": "2025-09-23",
      "last_active_date": "2026-03-31",
      "open_to_work_flag": false,
      "profile_views_received_30d": 6,
      "applications_submitted_30d": 7,
      "recruiter_response_rate": 0.14,
      "avg_response_time_hours": 13.2,
      "skill_assessment_scores": {},
      "connection_count": 524,
      "endorsements_received": 1,
      "notice_period_days": 60,
      "expected_salary_range_inr_lpa": {
        "min": 12.9,
        "max": 17.2
      },
      "preferred_work_mode": "remote",
      "willing_to_relocate": true,
      "github_activity_score": -1,
      "search_appearance_30d": 68,
      "saved_by_recruiters_30d": 4,
      "interview_completion_rate": 0.86,
      "offer_acceptance_rate": 0.49,
      "verified_email": true,
      "verified_phone": true,
      "linkedin_connected": false
    }
  },
  {
    "candidate_id": "CAND_0000029",
    "profile": {
      "anonymized_name": "Priya Sethi",
      "headline": "Business Analyst | Driving business outcomes",
      "summary": "Professional with 7.2+ years of experience. I'm a marketing manager with substantial experience in cross-functional collaboration, stakeholder management, and execution. Lately I've been curious about how AI tools could augment my work \u2014 I've experimented with ChatGPT and a few other tools for productivity and content creation, and I think the space is exciting. Open to roles where I can apply my domain expertise alongside emerging AI capabilities.",
      "location": "Noida, Uttar Pradesh",
      "country": "India",
      "years_of_experience": 7.2,
      "current_title": "Business Analyst",
      "current_company": "Wipro",
      "current_company_size": "10001+",
      "current_industry": "IT Services"
    },
    "career_history": [
      {
        "company": "Wipro",
        "title": "Business Analyst",
        "start_date": "2025-02-01",
        "end_date": null,
        "duration_months": 16,
        "is_current": true,
        "industry": "IT Services",
        "company_size": "10001+",
        "description": "Marketing leadership role at a B2B SaaS company. Owned the demand-generation function \u2014 content marketing, paid acquisition, SEO, email nurture. Built and managed a team of 5 across content, performance marketing, and marketing operations. Worked closely with sales on lead-quality definitions and the SDR-handoff process. Recent focus has been on account-based marketing for our enterprise segment."
      },
      {
        "company": "Globex Inc",
        "title": "Mechanical Engineer",
        "start_date": "2023-12-09",
        "end_date": "2025-02-01",
        "duration_months": 14,
        "is_current": false,
        "industry": "Manufacturing",
        "company_size": "501-1000",
        "description": "Mechanical engineering design role at a hardware-product company. Led the design of two product subsystems through full lifecycle: concept, DFM/DFMA review, prototype, production tooling. Comfortable with CAD (SolidWorks, Creo), FEA (ANSYS), and the typical hardware-development cadence. Worked closely with manufacturing partners on production scale-up."
      },
      {
        "company": "TCS",
        "title": "Civil Engineer",
        "start_date": "2019-05-27",
        "end_date": "2023-12-02",
        "duration_months": 55,
        "is_current": false,
        "industry": "IT Services",
        "company_size": "10001+",
        "description": "Customer support team lead at a SaaS product. Managed a team of 8 support agents handling tier-1 and tier-2 tickets; owned the escalation process to engineering and the customer-feedback loop to product. Built out the support knowledge base and the agent training program. Strong on the people-management side and the process side; lighter on technical depth beyond product expertise."
      }
    ],
    "education": [
      {
        "institution": "Symbiosis International",
        "degree": "B.Tech",
        "field_of_study": "Artificial Intelligence",
        "start_year": 2007,
        "end_year": 2011,
        "grade": "6.59 CGPA",
        "tier": "tier_3"
      }
    ],
    "skills": [
      {
        "name": "Node.js",
        "proficiency": "beginner",
        "endorsements": 9,
        "duration_months": 18
      },
      {
        "name": "Scrum",
        "proficiency": "beginner",
        "endorsements": 2,
        "duration_months": 5
      },
      {
        "name": "Tailwind",
        "proficiency": "intermediate",
        "endorsements": 5,
        "duration_months": 21
      },
      {
        "name": "Hadoop",
        "proficiency": "beginner",
        "endorsements": 10,
        "duration_months": 4
      },
      {
        "name": "Spring Boot",
        "proficiency": "intermediate",
        "endorsements": 1,
        "duration_months": 10
      },
      {
        "name": "CI/CD",
        "proficiency": "beginner",
        "endorsements": 4,
        "duration_months": 18
      },
      {
        "name": "gRPC",
        "proficiency": "beginner",
        "endorsements": 15,
        "duration_months": 17
      },
      {
        "name": "Terraform",
        "proficiency": "beginner",
        "endorsements": 9,
        "duration_months": 10
      }
    ],
    "certifications": [],
    "languages": [
      {
        "language": "English",
        "proficiency": "native"
      },
      {
        "language": "Hindi",
        "proficiency": "native"
      }
    ],
    "redrob_signals": {
      "profile_completeness_score": 40.5,
      "signup_date": "2025-06-17",
      "last_active_date": "2025-09-29",
      "open_to_work_flag": false,
      "profile_views_received_30d": 51,
      "applications_submitted_30d": 8,
      "recruiter_response_rate": 0.12,
      "avg_response_time_hours": 48.4,
      "skill_assessment_scores": {},
      "connection_count": 297,
      "endorsements_received": 4,
      "notice_period_days": 60,
      "expected_salary_range_inr_lpa": {
        "min": 17.5,
        "max": 19.1
      },
      "preferred_work_mode": "onsite",
      "willing_to_relocate": false,
      "github_activity_score": 42.5,
      "search_appearance_30d": 150,
      "saved_by_recruiters_30d": 8,
      "interview_completion_rate": 0.67,
      "offer_acceptance_rate": -1,
      "verified_email": true,
      "verified_phone": false,
      "linkedin_connected": true
    }
  },
  {
    "candidate_id": "CAND_0000030",
    "profile": {
      "anonymized_name": "Ritu Pillai",
      "headline": "Marketing Manager | Driving business outcomes",
      "summary": "Professional with 10.0+ years of experience. I've spent my career in marketing manager roles, mostly focused on driving outcomes through process, people, and customer relationships. Lately I've been curious about how AI tools could augment my work \u2014 I've experimented with ChatGPT and a few other tools for productivity and content creation, and I think the space is exciting. Open to roles where I can apply my domain expertise alongside emerging AI capabilities.",
      "location": "Kochi, Kerala",
      "country": "India",
      "years_of_experience": 10.0,
      "current_title": "Marketing Manager",
      "current_company": "Dunder Mifflin",
      "current_company_size": "201-500",
      "current_industry": "Paper Products"
    },
    "career_history": [
      {
        "company": "Dunder Mifflin",
        "title": "Marketing Manager",
        "start_date": "2022-03-19",
        "end_date": null,
        "duration_months": 51,
        "is_current": true,
        "industry": "Paper Products",
        "company_size": "201-500",
        "description": "Senior accounting role at a mid-sized company \u2014 month-end close, financial reporting, statutory compliance (GAAP / Ind-AS), and tax filings. Owned the GL, fixed-asset register, and the audit-readiness function. Managed a team of 3 staff accountants. Built strong process discipline around the close cycle, reducing close time from 12 days to 7 over the last two years."
      },
      {
        "company": "Hooli",
        "title": "Sales Executive",
        "start_date": "2018-07-08",
        "end_date": "2022-03-19",
        "duration_months": 45,
        "is_current": false,
        "industry": "Software",
        "company_size": "1001-5000",
        "description": "Operations management role at a logistics company. Owned daily fulfillment operations across 3 warehouses, managing a team of 80 across receiving, picking, packing, and outbound. Built and tracked the operational KPIs (on-time fulfillment, accuracy, cost per order) and led the continuous improvement initiatives that drove a 22% productivity gain over 18 months."
      },
      {
        "company": "Hooli",
        "title": "Content Writer",
        "start_date": "2016-08-17",
        "end_date": "2018-06-08",
        "duration_months": 22,
        "is_current": false,
        "industry": "Software",
        "company_size": "1001-5000",
        "description": "Content writing and SEO strategy for a tech-focused publication. Wrote longform articles on developer tools, cloud platforms, and AI/ML topics \u2014 including some that ranked on the first page of search for high-competition keywords. Managed a freelance writer pool and the editorial calendar. Recent work has been on AI-assisted content production, using LLM tools for research, drafting, and editing while maintaining editorial quality."
      }
    ],
    "education": [
      {
        "institution": "Generic State University",
        "degree": "B.E.",
        "field_of_study": "Computer Engineering",
        "start_year": 2010,
        "end_year": 2014,
        "grade": "81%",
        "tier": "tier_4"
      },
      {
        "institution": "Generic State University",
        "degree": "Ph.D",
        "field_of_study": "Artificial Intelligence",
        "start_year": 2017,
        "end_year": 2020,
        "grade": "7.98 CGPA",
        "tier": "tier_4"
      }
    ],
    "skills": [
      {
        "name": "gRPC",
        "proficiency": "intermediate",
        "endorsements": 3,
        "duration_months": 36
      },
      {
        "name": "Apache Beam",
        "proficiency": "beginner",
        "endorsements": 5,
        "duration_months": 6
      },
      {
        "name": "GraphQL",
        "proficiency": "intermediate",
        "endorsements": 2,
        "duration_months": 22
      },
      {
        "name": "Java",
        "proficiency": "intermediate",
        "endorsements": 14,
        "duration_months": 11
      },
      {
        "name": "Spring Boot",
        "proficiency": "intermediate",
        "endorsements": 2,
        "duration_months": 22
      },
      {
        "name": "Microservices",
        "proficiency": "beginner",
        "endorsements": 11,
        "duration_months": 5
      },
      {
        "name": "Six Sigma",
        "proficiency": "beginner",
        "endorsements": 8,
        "duration_months": 8
      },
      {
        "name": "Accounting",
        "proficiency": "intermediate",
        "endorsements": 3,
        "duration_months": 30
      },
      {
        "name": "HTML",
        "proficiency": "intermediate",
        "endorsements": 12,
        "duration_months": 9
      }
    ],
    "certifications": [],
    "languages": [
      {
        "language": "English",
        "proficiency": "professional"
      },
      {
        "language": "Hindi",
        "proficiency": "conversational"
      }
    ],
    "redrob_signals": {
      "profile_completeness_score": 59.7,
      "signup_date": "2025-09-25",
      "last_active_date": "2025-10-27",
      "open_to_work_flag": false,
      "profile_views_received_30d": 58,
      "applications_submitted_30d": 0,
      "recruiter_response_rate": 0.66,
      "avg_response_time_hours": 131.1,
      "skill_assessment_scores": {},
      "connection_count": 552,
      "endorsements_received": 45,
      "notice_period_days": 60,
      "expected_salary_range_inr_lpa": {
        "min": 14.7,
        "max": 14.2
      },
      "preferred_work_mode": "flexible",
      "willing_to_relocate": false,
      "github_activity_score": 21.7,
      "search_appearance_30d": 54,
      "saved_by_recruiters_30d": 1,
      "interview_completion_rate": 0.73,
      "offer_acceptance_rate": -1,
      "verified_email": true,
      "verified_phone": true,
      "linkedin_connected": false
    }
  },
  {
    "candidate_id": "CAND_0000031",
    "profile": {
      "anonymized_name": "Ela Singh",
      "headline": "Recommendation Systems Engineer | Search, Ranking & Retrieval",
      "summary": "Machine learning engineer with 6.0 years of experience building ML-powered features in production. Strong background in NLP, recommendation systems, and applied AI; comfortable across the ML stack from feature engineering through deployment. Recently, I led the team that migrated our keyword-search-based product to embedding-based retrieval. I've learned that most retrieval problems are actually evaluation problems in disguise. My academic background is in CS/ML but my main learning has come from shipping real systems and seeing what holds up under production load. Open to senior IC roles in applied ML or AI engineering, ideally at product companies where I'd own a meaningful piece of the ML stack.",
      "location": "Hyderabad, Telangana",
      "country": "India",
      "years_of_experience": 6.0,
      "current_title": "Recommendation Systems Engineer",
      "current_company": "Swiggy",
      "current_company_size": "5001-10000",
      "current_industry": "Food Delivery"
    },
    "career_history": [
      {
        "company": "Swiggy",
        "title": "Recommendation Systems Engineer",
        "start_date": "2025-04-02",
        "end_date": null,
        "duration_months": 14,
        "is_current": true,
        "industry": "Food Delivery",
        "company_size": "5001-10000",
        "description": "Trained and shipped multiple ranking models for our product's discovery feed using XGBoost and LightGBM. Designed features across three families: content metadata, user behavior signals, and item engagement history. Owned the offline-online correlation analysis that determined which offline metrics actually predicted A/B test outcomes. Worked closely with PMs to define the optimization target (click-through vs. dwell time vs. downstream conversion) \u2014 that work was as important as the modeling itself."
      },
      {
        "company": "Mad Street Den",
        "title": "Search Engineer",
        "start_date": "2023-10-10",
        "end_date": "2025-02-01",
        "duration_months": 16,
        "is_current": false,
        "industry": "AI/ML",
        "company_size": "201-500",
        "description": "Trained and shipped multiple ranking models for our product's discovery feed using XGBoost and LightGBM. Designed features across three families: content metadata, user behavior signals, and item engagement history. Owned the offline-online correlation analysis that determined which offline metrics actually predicted A/B test outcomes. Worked closely with PMs to define the optimization target (click-through vs. dwell time vs. downstream conversion) \u2014 that work was as important as the modeling itself."
      },
      {
        "company": "Uber",
        "title": "NLP Engineer",
        "start_date": "2021-07-22",
        "end_date": "2023-10-10",
        "duration_months": 27,
        "is_current": false,
        "industry": "Transportation",
        "company_size": "10001+",
        "description": "Trained and shipped multiple ranking models for our product's discovery feed using XGBoost and LightGBM. Designed features across three families: content metadata, user behavior signals, and item engagement history. Owned the offline-online correlation analysis that determined which offline metrics actually predicted A/B test outcomes. Worked closely with PMs to define the optimization target (click-through vs. dwell time vs. downstream conversion) \u2014 that work was as important as the modeling itself."
      },
      {
        "company": "Zomato",
        "title": "Applied ML Engineer",
        "start_date": "2020-06-27",
        "end_date": "2021-07-22",
        "duration_months": 13,
        "is_current": false,
        "industry": "Food Delivery",
        "company_size": "5001-10000",
        "description": "Owned the ranking layer for an e-commerce search product, evolving it from a hand-tuned scoring function to a learning-to-rank model over 9 months. Designed the relevance labeling pipeline (mix of click-through data and explicit human judgments), the feature pipeline, and the training/eval workflow. Most of the work was infrastructure and data quality \u2014 the modeling part was almost the easy bit. Final model improved revenue-per-search by 12%."
      }
    ],
    "education": [
      {
        "institution": "SRM University",
        "degree": "M.Tech",
        "field_of_study": "Computer Engineering",
        "start_year": 2002,
        "end_year": 2006,
        "grade": "9.16 CGPA",
        "tier": "tier_2"
      }
    ],
    "skills": [
      {
        "name": "Go",
        "proficiency": "intermediate",
        "endorsements": 7,
        "duration_months": 19
      },
      {
        "name": "MLflow",
        "proficiency": "advanced",
        "endorsements": 59,
        "duration_months": 21
      },
      {
        "name": "FAISS",
        "proficiency": "advanced",
        "endorsements": 19,
        "duration_months": 35
      },
      {
        "name": "Pinecone",
        "proficiency": "expert",
        "endorsements": 34,
        "duration_months": 88
      },
      {
        "name": "Angular",
        "proficiency": "beginner",
        "endorsements": 4,
        "duration_months": 18
      },
      {
        "name": "Image Classification",
        "proficiency": "advanced",
        "endorsements": 56,
        "duration_months": 28
      },
      {
        "name": "Machine Learning",
        "proficiency": "advanced",
        "endorsements": 43,
        "duration_months": 23
      },
      {
        "name": "Speech Recognition",
        "proficiency": "intermediate",
        "endorsements": 14,
        "duration_months": 24
      },
      {
        "name": "BentoML",
        "proficiency": "intermediate",
        "endorsements": 6,
        "duration_months": 14
      },
      {
        "name": "MLOps",
        "proficiency": "intermediate",
        "endorsements": 15,
        "duration_months": 36
      },
      {
        "name": "Embeddings",
        "proficiency": "expert",
        "endorsements": 48,
        "duration_months": 60
      },
      {
        "name": "Information Retrieval",
        "proficiency": "expert",
        "endorsements": 2,
        "duration_months": 84
      },
      {
        "name": "Hugging Face Transformers",
        "proficiency": "expert",
        "endorsements": 18,
        "duration_months": 36
      },
      {
        "name": "Feature Engineering",
        "proficiency": "advanced",
        "endorsements": 38,
        "duration_months": 26
      },
      {
        "name": "Sentence Transformers",
        "proficiency": "expert",
        "endorsements": 16,
        "duration_months": 69
      },
      {
        "name": "scikit-learn",
        "proficiency": "advanced",
        "endorsements": 41,
        "duration_months": 60
      },
      {
        "name": "Marketing",
        "proficiency": "intermediate",
        "endorsements": 11,
        "duration_months": 36
      }
    ],
    "certifications": [],
    "languages": [
      {
        "language": "English",
        "proficiency": "native"
      },
      {
        "language": "Hindi",
        "proficiency": "native"
      }
    ],
    "redrob_signals": {
      "profile_completeness_score": 83.4,
      "signup_date": "2026-01-28",
      "last_active_date": "2026-05-24",
      "open_to_work_flag": true,
      "profile_views_received_30d": 194,
      "applications_submitted_30d": 2,
      "recruiter_response_rate": 0.91,
      "avg_response_time_hours": 76.1,
      "skill_assessment_scores": {
        "MLflow": 75.1,
        "FAISS": 68.4,
        "Pinecone": 53.6,
        "Image Classification": 57.1
      },
      "connection_count": 832,
      "endorsements_received": 177,
      "notice_period_days": 60,
      "expected_salary_range_inr_lpa": {
        "min": 27.3,
        "max": 60.2
      },
      "preferred_work_mode": "flexible",
      "willing_to_relocate": true,
      "github_activity_score": 32.6,
      "search_appearance_30d": 778,
      "saved_by_recruiters_30d": 13,
      "interview_completion_rate": 0.6,
      "offer_acceptance_rate": 0.38,
      "verified_email": false,
      "verified_phone": true,
      "linkedin_connected": false
    }
  },
  {
    "candidate_id": "CAND_0000032",
    "profile": {
      "anonymized_name": "Pranav Agarwal",
      "headline": ".NET Developer | Full-stack development",
      "summary": "Software engineer with 8.1 years of experience across web, backend, and cloud systems. Strong fundamentals in software development and system design. Most of my work is conventional backend engineering \u2014 APIs, databases, queues, deployments. I've been keeping up with AI/ML at a self-learner level \u2014 taken some online courses, played with the OpenAI and Anthropic APIs, built a small RAG side project \u2014 but I haven't done it in a professional capacity yet. Open to roles where I can either deepen my software engineering work or, if the team is open to it, start contributing to ML-adjacent systems.",
      "location": "Gurgaon, Haryana",
      "country": "India",
      "years_of_experience": 8.1,
      "current_title": ".NET Developer",
      "current_company": "Cognizant",
      "current_company_size": "10001+",
      "current_industry": "IT Services"
    },
    "career_history": [
      {
        "company": "Cognizant",
        "title": ".NET Developer",
        "start_date": "2024-02-07",
        "end_date": null,
        "duration_months": 28,
        "is_current": true,
        "industry": "IT Services",
        "company_size": "10001+",
        "description": "Java backend development at a large enterprise \u2014 Spring Boot microservices, Kafka for inter-service messaging, Postgres + Redis for storage. Worked on the customer onboarding flow which involved orchestrating multiple downstream services. Solid on the Spring ecosystem, transaction handling, and the operational side of Java services. Looking to either go deeper on distributed systems or expand into modern application stacks."
      },
      {
        "company": "HCL",
        "title": "Cloud Engineer",
        "start_date": "2021-11-19",
        "end_date": "2024-02-07",
        "duration_months": 27,
        "is_current": false,
        "industry": "IT Services",
        "company_size": "10001+",
        "description": "Test automation and QA engineering for a fintech product. Built and maintained the end-to-end test suite using Selenium and pytest, plus the load-testing setup using Locust. Worked closely with developers on testability patterns and with product on acceptance criteria. Recent work has been on shifting test responsibility into the dev team \u2014 moving from QA-as-gate to QA-as-coach. Career has been entirely in QA/test engineering."
      },
      {
        "company": "Globex Inc",
        "title": "Mobile Developer",
        "start_date": "2018-07-24",
        "end_date": "2021-11-05",
        "duration_months": 40,
        "is_current": false,
        "industry": "Manufacturing",
        "company_size": "501-1000",
        "description": "Full-stack web application development at a SaaS company. Built React-based admin interfaces and the Node.js REST API backing them. Worked across the stack: frontend components, REST endpoint design, PostgreSQL schema, deployment via Docker/Kubernetes. Comfortable in most parts of a typical web stack though my comfort zone is the backend and database side. Recent learning has been on the testing and CI/CD discipline."
      }
    ],
    "education": [
      {
        "institution": "VIT Chennai",
        "degree": "M.Sc",
        "field_of_study": "Machine Learning",
        "start_year": 2017,
        "end_year": 2020,
        "grade": "8.37 CGPA",
        "tier": "tier_3"
      },
      {
        "institution": "Amity University",
        "degree": "Ph.D",
        "field_of_study": "Physics",
        "start_year": 2011,
        "end_year": 2015,
        "grade": "7.95 CGPA",
        "tier": "tier_3"
      }
    ],
    "skills": [
      {
        "name": "Speech Recognition",
        "proficiency": "advanced",
        "endorsements": 36,
        "duration_months": 19
      },
      {
        "name": "Project Management",
        "proficiency": "beginner",
        "endorsements": 6,
        "duration_months": 17
      },
      {
        "name": "REST APIs",
        "proficiency": "beginner",
        "endorsements": 13,
        "duration_months": 6
      },
      {
        "name": "CSS",
        "proficiency": "intermediate",
        "endorsements": 15,
        "duration_months": 27
      },
      {
        "name": "Embeddings",
        "proficiency": "advanced",
        "endorsements": 30,
        "duration_months": 30
      },
      {
        "name": "Hadoop",
        "proficiency": "beginner",
        "endorsements": 0,
        "duration_months": 8
      },
      {
        "name": "Spark",
        "proficiency": "intermediate",
        "endorsements": 14,
        "duration_months": 30
      },
      {
        "name": "Python",
        "proficiency": "intermediate",
        "endorsements": 2,
        "duration_months": 13
      },
      {
        "name": "Data Pipelines",
        "proficiency": "beginner",
        "endorsements": 6,
        "duration_months": 8
      },
      {
        "name": "OpenCV",
        "proficiency": "advanced",
        "endorsements": 45,
        "duration_months": 54
      }
    ],
    "certifications": [],
    "languages": [
      {
        "language": "English",
        "proficiency": "native"
      },
      {
        "language": "Hindi",
        "proficiency": "native"
      }
    ],
    "redrob_signals": {
      "profile_completeness_score": 35.4,
      "signup_date": "2023-12-20",
      "last_active_date": "2025-12-29",
      "open_to_work_flag": false,
      "profile_views_received_30d": 80,
      "applications_submitted_30d": 3,
      "recruiter_response_rate": 0.69,
      "avg_response_time_hours": 58.6,
      "skill_assessment_scores": {},
      "connection_count": 404,
      "endorsements_received": 22,
      "notice_period_days": 150,
      "expected_salary_range_inr_lpa": {
        "min": 18.3,
        "max": 15.7
      },
      "preferred_work_mode": "flexible",
      "willing_to_relocate": true,
      "github_activity_score": -1,
      "search_appearance_30d": 56,
      "saved_by_recruiters_30d": 4,
      "interview_completion_rate": 0.78,
      "offer_acceptance_rate": 0.25,
      "verified_email": true,
      "verified_phone": false,
      "linkedin_connected": false
    }
  },
  {
    "candidate_id": "CAND_0000033",
    "profile": {
      "anonymized_name": "Shreya Nair",
      "headline": "Graphic Designer | Helping teams scale",
      "summary": "Professional with 8.6+ years of experience. I'm a marketing manager with substantial experience in cross-functional collaboration, stakeholder management, and execution. Lately I've been curious about how AI tools could augment my work \u2014 I've experimented with ChatGPT and a few other tools for productivity and content creation, and I think the space is exciting. Open to roles where I can apply my domain expertise alongside emerging AI capabilities.",
      "location": "Pune, Maharashtra",
      "country": "India",
      "years_of_experience": 8.6,
      "current_title": "Graphic Designer",
      "current_company": "Wipro",
      "current_company_size": "10001+",
      "current_industry": "IT Services"
    },
    "career_history": [
      {
        "company": "Wipro",
        "title": "Graphic Designer",
        "start_date": "2023-11-09",
        "end_date": null,
        "duration_months": 31,
        "is_current": true,
        "industry": "IT Services",
        "company_size": "10001+",
        "description": "Business analyst at a consulting firm, working primarily with retail and CPG clients. Conducted business diagnostics, process re-engineering work, and digital transformation strategy projects. Strong on stakeholder management, structured problem-solving, and the typical consulting toolkit (slide-craft, Excel modeling, executive communication). Recent project work involved AI-strategy advisory but my own technical depth in AI is limited."
      },
      {
        "company": "Dunder Mifflin",
        "title": "Project Manager",
        "start_date": "2020-07-20",
        "end_date": "2023-11-02",
        "duration_months": 40,
        "is_current": false,
        "industry": "Paper Products",
        "company_size": "201-500",
        "description": "Senior accounting role at a mid-sized company \u2014 month-end close, financial reporting, statutory compliance (GAAP / Ind-AS), and tax filings. Owned the GL, fixed-asset register, and the audit-readiness function. Managed a team of 3 staff accountants. Built strong process discipline around the close cycle, reducing close time from 12 days to 7 over the last two years."
      },
      {
        "company": "Acme Corp",
        "title": "Content Writer",
        "start_date": "2018-01-02",
        "end_date": "2020-07-20",
        "duration_months": 31,
        "is_current": false,
        "industry": "Manufacturing",
        "company_size": "201-500",
        "description": "Enterprise sales of cloud software solutions into the mid-market segment. Carried a $1.8M ARR quota and consistently delivered against it across the last three years. Owned the full sales cycle: prospecting, discovery, technical evaluation (with SE support), commercial negotiation, and close. Strong on consultative selling for technical buyers; comfortable engaging with both engineering and finance stakeholders."
      }
    ],
    "education": [
      {
        "institution": "Tier-3 Engineering College",
        "degree": "M.S.",
        "field_of_study": "Computer Science",
        "start_year": 2014,
        "end_year": 2017,
        "grade": "9.32 CGPA",
        "tier": "tier_4"
      }
    ],
    "skills": [
      {
        "name": "Kubernetes",
        "proficiency": "beginner",
        "endorsements": 0,
        "duration_months": 9
      },
      {
        "name": "Data Pipelines",
        "proficiency": "beginner",
        "endorsements": 4,
        "duration_months": 8
      },
      {
        "name": "Snowflake",
        "proficiency": "intermediate",
        "endorsements": 11,
        "duration_months": 12
      },
      {
        "name": "CI/CD",
        "proficiency": "intermediate",
        "endorsements": 11,
        "duration_months": 29
      },
      {
        "name": "SEO",
        "proficiency": "intermediate",
        "endorsements": 9,
        "duration_months": 36
      },
      {
        "name": "ETL",
        "proficiency": "intermediate",
        "endorsements": 0,
        "duration_months": 20
      },
      {
        "name": "Airflow",
        "proficiency": "intermediate",
        "endorsements": 11,
        "duration_months": 16
      },
      {
        "name": "TypeScript",
        "proficiency": "intermediate",
        "endorsements": 13,
        "duration_months": 15
      },
      {
        "name": "Content Writing",
        "proficiency": "intermediate",
        "endorsements": 13,
        "duration_months": 11
      },
      {
        "name": "Spring Boot",
        "proficiency": "intermediate",
        "endorsements": 5,
        "duration_months": 26
      }
    ],
    "certifications": [
      {
        "name": "Six Sigma Green Belt",
        "issuer": "ASQ",
        "year": 2019
      }
    ],
    "languages": [
      {
        "language": "English",
        "proficiency": "professional"
      },
      {
        "language": "Hindi",
        "proficiency": "conversational"
      }
    ],
    "redrob_signals": {
      "profile_completeness_score": 74.0,
      "signup_date": "2026-03-13",
      "last_active_date": "2026-03-27",
      "open_to_work_flag": true,
      "profile_views_received_30d": 42,
      "applications_submitted_30d": 9,
      "recruiter_response_rate": 0.08,
      "avg_response_time_hours": 210.9,
      "skill_assessment_scores": {},
      "connection_count": 410,
      "endorsements_received": 29,
      "notice_period_days": 30,
      "expected_salary_range_inr_lpa": {
        "min": 8.3,
        "max": 13.0
      },
      "preferred_work_mode": "remote",
      "willing_to_relocate": false,
      "github_activity_score": 38.3,
      "search_appearance_30d": 98,
      "saved_by_recruiters_30d": 2,
      "interview_completion_rate": 0.37,
      "offer_acceptance_rate": -1,
      "verified_email": false,
      "verified_phone": true,
      "linkedin_connected": false
    }
  },
  {
    "candidate_id": "CAND_0000034",
    "profile": {
      "anonymized_name": "Yash Chatterjee",
      "headline": "Business Analyst | Driving business outcomes",
      "summary": "Professional with 14.5+ years of experience. I'm a marketing manager with substantial experience in cross-functional collaboration, stakeholder management, and execution. Lately I've been curious about how AI tools could augment my work \u2014 I've experimented with ChatGPT and a few other tools for productivity and content creation, and I think the space is exciting. Open to roles where I can apply my domain expertise alongside emerging AI capabilities.",
      "location": "Ahmedabad, Gujarat",
      "country": "India",
      "years_of_experience": 14.5,
      "current_title": "Business Analyst",
      "current_company": "Wipro",
      "current_company_size": "10001+",
      "current_industry": "IT Services"
    },
    "career_history": [
      {
        "company": "Wipro",
        "title": "Business Analyst",
        "start_date": "2025-04-02",
        "end_date": null,
        "duration_months": 14,
        "is_current": true,
        "industry": "IT Services",
        "company_size": "10001+",
        "description": "Content writing and SEO strategy for a tech-focused publication. Wrote longform articles on developer tools, cloud platforms, and AI/ML topics \u2014 including some that ranked on the first page of search for high-competition keywords. Managed a freelance writer pool and the editorial calendar. Recent work has been on AI-assisted content production, using LLM tools for research, drafting, and editing while maintaining editorial quality."
      },
      {
        "company": "Hooli",
        "title": "Mechanical Engineer",
        "start_date": "2023-05-13",
        "end_date": "2025-02-01",
        "duration_months": 21,
        "is_current": false,
        "industry": "Software",
        "company_size": "1001-5000",
        "description": "Business analyst at a consulting firm, working primarily with retail and CPG clients. Conducted business diagnostics, process re-engineering work, and digital transformation strategy projects. Strong on stakeholder management, structured problem-solving, and the typical consulting toolkit (slide-craft, Excel modeling, executive communication). Recent project work involved AI-strategy advisory but my own technical depth in AI is limited."
      },
      {
        "company": "Infosys",
        "title": "Business Analyst",
        "start_date": "2021-02-22",
        "end_date": "2023-04-13",
        "duration_months": 26,
        "is_current": false,
        "industry": "IT Services",
        "company_size": "10001+",
        "description": "Business analyst at a consulting firm, working primarily with retail and CPG clients. Conducted business diagnostics, process re-engineering work, and digital transformation strategy projects. Strong on stakeholder management, structured problem-solving, and the typical consulting toolkit (slide-craft, Excel modeling, executive communication). Recent project work involved AI-strategy advisory but my own technical depth in AI is limited."
      },
      {
        "company": "TCS",
        "title": "Accountant",
        "start_date": "2017-11-10",
        "end_date": "2021-02-22",
        "duration_months": 40,
        "is_current": false,
        "industry": "IT Services",
        "company_size": "10001+",
        "description": "Business analyst at a consulting firm, working primarily with retail and CPG clients. Conducted business diagnostics, process re-engineering work, and digital transformation strategy projects. Strong on stakeholder management, structured problem-solving, and the typical consulting toolkit (slide-craft, Excel modeling, executive communication). Recent project work involved AI-strategy advisory but my own technical depth in AI is limited."
      },
      {
        "company": "Hooli",
        "title": "Accountant",
        "start_date": "2016-01-20",
        "end_date": "2017-11-10",
        "duration_months": 22,
        "is_current": false,
        "industry": "Software",
        "company_size": "1001-5000",
        "description": "Marketing leadership role at a B2B SaaS company. Owned the demand-generation function \u2014 content marketing, paid acquisition, SEO, email nurture. Built and managed a team of 5 across content, performance marketing, and marketing operations. Worked closely with sales on lead-quality definitions and the SDR-handoff process. Recent focus has been on account-based marketing for our enterprise segment."
      },
      {
        "company": "Pied Piper",
        "title": "Content Writer",
        "start_date": "2012-12-06",
        "end_date": "2016-01-20",
        "duration_months": 38,
        "is_current": false,
        "industry": "Software",
        "company_size": "11-50",
        "description": "Marketing leadership role at a B2B SaaS company. Owned the demand-generation function \u2014 content marketing, paid acquisition, SEO, email nurture. Built and managed a team of 5 across content, performance marketing, and marketing operations. Worked closely with sales on lead-quality definitions and the SDR-handoff process. Recent focus has been on account-based marketing for our enterprise segment."
      },
      {
        "company": "Stark Industries",
        "title": "Content Writer",
        "start_date": "2012-01-11",
        "end_date": "2012-10-07",
        "duration_months": 9,
        "is_current": false,
        "industry": "Manufacturing",
        "company_size": "1001-5000",
        "description": "Mechanical engineering design role at a hardware-product company. Led the design of two product subsystems through full lifecycle: concept, DFM/DFMA review, prototype, production tooling. Comfortable with CAD (SolidWorks, Creo), FEA (ANSYS), and the typical hardware-development cadence. Worked closely with manufacturing partners on production scale-up."
      }
    ],
    "education": [
      {
        "institution": "Tier-3 Engineering College",
        "degree": "B.E.",
        "field_of_study": "Computer Engineering",
        "start_year": 2005,
        "end_year": 2010,
        "grade": "8.97 CGPA",
        "tier": "tier_4"
      }
    ],
    "skills": [
      {
        "name": "GraphQL",
        "proficiency": "beginner",
        "endorsements": 2,
        "duration_months": 3
      },
      {
        "name": "Excel",
        "proficiency": "intermediate",
        "endorsements": 15,
        "duration_months": 19
      },
      {
        "name": "Node.js",
        "proficiency": "beginner",
        "endorsements": 6,
        "duration_months": 6
      },
      {
        "name": "Terraform",
        "proficiency": "intermediate",
        "endorsements": 6,
        "duration_months": 13
      },
      {
        "name": "Salesforce CRM",
        "proficiency": "intermediate",
        "endorsements": 6,
        "duration_months": 27
      },
      {
        "name": "Flask",
        "proficiency": "intermediate",
        "endorsements": 8,
        "duration_months": 28
      },
      {
        "name": "React",
        "proficiency": "beginner",
        "endorsements": 14,
        "duration_months": 2
      },
      {
        "name": "Azure",
        "proficiency": "beginner",
        "endorsements": 1,
        "duration_months": 5
      },
      {
        "name": "Redux",
        "proficiency": "beginner",
        "endorsements": 15,
        "duration_months": 3
      },
      {
        "name": "Next.js",
        "proficiency": "intermediate",
        "endorsements": 7,
        "duration_months": 21
      }
    ],
    "certifications": [],
    "languages": [
      {
        "language": "English",
        "proficiency": "native"
      },
      {
        "language": "Hindi",
        "proficiency": "native"
      }
    ],
    "redrob_signals": {
      "profile_completeness_score": 41.2,
      "signup_date": "2024-01-15",
      "last_active_date": "2026-01-03",
      "open_to_work_flag": false,
      "profile_views_received_30d": 25,
      "applications_submitted_30d": 7,
      "recruiter_response_rate": 0.15,
      "avg_response_time_hours": 253.5,
      "skill_assessment_scores": {},
      "connection_count": 226,
      "endorsements_received": 27,
      "notice_period_days": 90,
      "expected_salary_range_inr_lpa": {
        "min": 14.4,
        "max": 28.0
      },
      "preferred_work_mode": "hybrid",
      "willing_to_relocate": false,
      "github_activity_score": -1,
      "search_appearance_30d": 143,
      "saved_by_recruiters_30d": 2,
      "interview_completion_rate": 0.41,
      "offer_acceptance_rate": -1,
      "verified_email": true,
      "verified_phone": true,
      "linkedin_connected": false
    }
  },
  {
    "candidate_id": "CAND_0000035",
    "profile": {
      "anonymized_name": "Vikram Verma",
      "headline": "Full Stack Developer | Backend systems & APIs",
      "summary": "Software engineer with 4.3 years of experience across web, backend, and cloud systems. Strong fundamentals in software development and system design. My background is full-stack, but my comfort zone is the backend and the database. I've been keeping up with AI/ML at a self-learner level \u2014 taken some online courses, played with the OpenAI and Anthropic APIs, built a small RAG side project \u2014 but I haven't done it in a professional capacity yet. Open to roles where I can either deepen my software engineering work or, if the team is open to it, start contributing to ML-adjacent systems.",
      "location": "Hyderabad, Telangana",
      "country": "India",
      "years_of_experience": 4.3,
      "current_title": "Full Stack Developer",
      "current_company": "Globex Inc",
      "current_company_size": "501-1000",
      "current_industry": "Manufacturing"
    },
    "career_history": [
      {
        "company": "Globex Inc",
        "title": "Full Stack Developer",
        "start_date": "2023-09-10",
        "end_date": null,
        "duration_months": 33,
        "is_current": true,
        "industry": "Manufacturing",
        "company_size": "501-1000",
        "description": "Full-stack web application development at a SaaS company. Built React-based admin interfaces and the Node.js REST API backing them. Worked across the stack: frontend components, REST endpoint design, PostgreSQL schema, deployment via Docker/Kubernetes. Comfortable in most parts of a typical web stack though my comfort zone is the backend and database side. Recent learning has been on the testing and CI/CD discipline."
      },
      {
        "company": "Wipro",
        "title": "Software Engineer",
        "start_date": "2022-03-19",
        "end_date": "2023-09-10",
        "duration_months": 18,
        "is_current": false,
        "industry": "IT Services",
        "company_size": "10001+",
        "description": "Frontend engineering at a media company. React, TypeScript, and the typical surrounding tooling (Webpack, Jest, Cypress). Built the company's design system from scratch and led the migration from a legacy AngularJS app. Strong on the frontend craft \u2014 accessibility, performance, animations \u2014 but limited backend exposure."
      }
    ],
    "education": [
      {
        "institution": "Generic State University",
        "degree": "B.E.",
        "field_of_study": "Civil Engineering",
        "start_year": 2010,
        "end_year": 2013,
        "grade": "90%",
        "tier": "tier_4"
      },
      {
        "institution": "Bharati Vidyapeeth",
        "degree": "M.S.",
        "field_of_study": "Data Science",
        "start_year": 2010,
        "end_year": 2015,
        "grade": "7.08 CGPA",
        "tier": "tier_3"
      }
    ],
    "skills": [
      {
        "name": "Snowflake",
        "proficiency": "intermediate",
        "endorsements": 11,
        "duration_months": 27
      },
      {
        "name": "BigQuery",
        "proficiency": "beginner",
        "endorsements": 15,
        "duration_months": 6
      },
      {
        "name": "Recommendation Systems",
        "proficiency": "intermediate",
        "endorsements": 2,
        "duration_months": 34
      },
      {
        "name": "Data Pipelines",
        "proficiency": "beginner",
        "endorsements": 14,
        "duration_months": 18
      },
      {
        "name": "Docker",
        "proficiency": "beginner",
        "endorsements": 3,
        "duration_months": 11
      },
      {
        "name": "MongoDB",
        "proficiency": "intermediate",
        "endorsements": 11,
        "duration_months": 16
      },
      {
        "name": "PostgreSQL",
        "proficiency": "intermediate",
        "endorsements": 14,
        "duration_months": 13
      },
      {
        "name": "Sales",
        "proficiency": "intermediate",
        "endorsements": 0,
        "duration_months": 19
      },
      {
        "name": "Kafka",
        "proficiency": "intermediate",
        "endorsements": 14,
        "duration_months": 29
      },
      {
        "name": "Speech Recognition",
        "proficiency": "intermediate",
        "endorsements": 5,
        "duration_months": 33
      },
      {
        "name": "BentoML",
        "proficiency": "advanced",
        "endorsements": 40,
        "duration_months": 59
      },
      {
        "name": "Go",
        "proficiency": "beginner",
        "endorsements": 1,
        "duration_months": 11
      },
      {
        "name": "Next.js",
        "proficiency": "intermediate",
        "endorsements": 15,
        "duration_months": 22
      },
      {
        "name": "dbt",
        "proficiency": "beginner",
        "endorsements": 2,
        "duration_months": 9
      }
    ],
    "certifications": [
      {
        "name": "AWS Certified Cloud Practitioner",
        "issuer": "AWS",
        "year": 2022
      },
      {
        "name": "Six Sigma Green Belt",
        "issuer": "ASQ",
        "year": 2020
      }
    ],
    "languages": [
      {
        "language": "English",
        "proficiency": "professional"
      },
      {
        "language": "Hindi",
        "proficiency": "conversational"
      }
    ],
    "redrob_signals": {
      "profile_completeness_score": 56.2,
      "signup_date": "2024-08-13",
      "last_active_date": "2026-02-06",
      "open_to_work_flag": false,
      "profile_views_received_30d": 7,
      "applications_submitted_30d": 4,
      "recruiter_response_rate": 0.34,
      "avg_response_time_hours": 178.0,
      "skill_assessment_scores": {},
      "connection_count": 398,
      "endorsements_received": 45,
      "notice_period_days": 60,
      "expected_salary_range_inr_lpa": {
        "min": 11.2,
        "max": 22.8
      },
      "preferred_work_mode": "onsite",
      "willing_to_relocate": false,
      "github_activity_score": -1,
      "search_appearance_30d": 173,
      "saved_by_recruiters_30d": 1,
      "interview_completion_rate": 0.5,
      "offer_acceptance_rate": -1,
      "verified_email": true,
      "verified_phone": true,
      "linkedin_connected": false
    }
  },
  {
    "candidate_id": "CAND_0000036",
    "profile": {
      "anonymized_name": "Ananya Bose",
      "headline": "Project Manager | 11.3+ yrs experience",
      "summary": "Professional with 11.3+ years of experience. I'm a marketing manager with substantial experience in cross-functional collaboration, stakeholder management, and execution. Lately I've been curious about how AI tools could augment my work \u2014 I've experimented with ChatGPT and a few other tools for productivity and content creation, and I think the space is exciting. Open to roles where I can apply my domain expertise alongside emerging AI capabilities.",
      "location": "Trivandrum, Kerala",
      "country": "India",
      "years_of_experience": 11.3,
      "current_title": "Project Manager",
      "current_company": "Initech",
      "current_company_size": "51-200",
      "current_industry": "Software"
    },
    "career_history": [
      {
        "company": "Initech",
        "title": "Project Manager",
        "start_date": "2025-02-01",
        "end_date": null,
        "duration_months": 16,
        "is_current": true,
        "industry": "Software",
        "company_size": "51-200",
        "description": "Brand design and creative direction at a consumer-products company. Owned brand identity (logo, visual system, typography), packaging design, and digital creative across web and social. Led the recent rebrand and managed a small external agency for production work. Comfortable across the Adobe suite, Figma, and the production side of brand and packaging design."
      },
      {
        "company": "Hooli",
        "title": "Content Writer",
        "start_date": "2023-08-11",
        "end_date": "2025-02-01",
        "duration_months": 18,
        "is_current": false,
        "industry": "Software",
        "company_size": "1001-5000",
        "description": "Marketing leadership role at a B2B SaaS company. Owned the demand-generation function \u2014 content marketing, paid acquisition, SEO, email nurture. Built and managed a team of 5 across content, performance marketing, and marketing operations. Worked closely with sales on lead-quality definitions and the SDR-handoff process. Recent focus has been on account-based marketing for our enterprise segment."
      },
      {
        "company": "Dunder Mifflin",
        "title": "HR Manager",
        "start_date": "2019-11-30",
        "end_date": "2023-08-11",
        "duration_months": 45,
        "is_current": false,
        "industry": "Paper Products",
        "company_size": "201-500",
        "description": "Brand design and creative direction at a consumer-products company. Owned brand identity (logo, visual system, typography), packaging design, and digital creative across web and social. Led the recent rebrand and managed a small external agency for production work. Comfortable across the Adobe suite, Figma, and the production side of brand and packaging design."
      },
      {
        "company": "TCS",
        "title": "Civil Engineer",
        "start_date": "2017-12-10",
        "end_date": "2019-11-30",
        "duration_months": 24,
        "is_current": false,
        "industry": "IT Services",
        "company_size": "10001+",
        "description": "Senior accounting role at a mid-sized company \u2014 month-end close, financial reporting, statutory compliance (GAAP / Ind-AS), and tax filings. Owned the GL, fixed-asset register, and the audit-readiness function. Managed a team of 3 staff accountants. Built strong process discipline around the close cycle, reducing close time from 12 days to 7 over the last two years."
      },
      {
        "company": "Wayne Enterprises",
        "title": "Marketing Manager",
        "start_date": "2015-05-18",
        "end_date": "2017-12-03",
        "duration_months": 31,
        "is_current": false,
        "industry": "Conglomerate",
        "company_size": "10001+",
        "description": "Mechanical engineering design role at a hardware-product company. Led the design of two product subsystems through full lifecycle: concept, DFM/DFMA review, prototype, production tooling. Comfortable with CAD (SolidWorks, Creo), FEA (ANSYS), and the typical hardware-development cadence. Worked closely with manufacturing partners on production scale-up."
      }
    ],
    "education": [
      {
        "institution": "KIIT University",
        "degree": "M.S.",
        "field_of_study": "Commerce",
        "start_year": 2002,
        "end_year": 2006,
        "grade": "8.89 CGPA",
        "tier": "tier_3"
      }
    ],
    "skills": [
      {
        "name": "Figma",
        "proficiency": "beginner",
        "endorsements": 6,
        "duration_months": 13
      },
      {
        "name": "MongoDB",
        "proficiency": "beginner",
        "endorsements": 4,
        "duration_months": 8
      },
      {
        "name": "PowerPoint",
        "proficiency": "beginner",
        "endorsements": 5,
        "duration_months": 3
      },
      {
        "name": "CSS",
        "proficiency": "beginner",
        "endorsements": 5,
        "duration_months": 14
      },
      {
        "name": "Excel",
        "proficiency": "intermediate",
        "endorsements": 9,
        "duration_months": 28
      },
      {
        "name": "GraphQL",
        "proficiency": "beginner",
        "endorsements": 5,
        "duration_months": 18
      },
      {
        "name": "Object Detection",
        "proficiency": "advanced",
        "endorsements": 39,
        "duration_months": 37
      },
      {
        "name": "Vue.js",
        "proficiency": "beginner",
        "endorsements": 13,
        "duration_months": 4
      },
      {
        "name": "Sales",
        "proficiency": "beginner",
        "endorsements": 4,
        "duration_months": 9
      }
    ],
    "certifications": [],
    "languages": [
      {
        "language": "English",
        "proficiency": "native"
      },
      {
        "language": "Hindi",
        "proficiency": "conversational"
      }
    ],
    "redrob_signals": {
      "profile_completeness_score": 81.8,
      "signup_date": "2025-09-05",
      "last_active_date": "2025-12-12",
      "open_to_work_flag": true,
      "profile_views_received_30d": 70,
      "applications_submitted_30d": 4,
      "recruiter_response_rate": 0.4,
      "avg_response_time_hours": 236.6,
      "skill_assessment_scores": {},
      "connection_count": 324,
      "endorsements_received": 3,
      "notice_period_days": 60,
      "expected_salary_range_inr_lpa": {
        "min": 15.3,
        "max": 9.7
      },
      "preferred_work_mode": "remote",
      "willing_to_relocate": false,
      "github_activity_score": -1,
      "search_appearance_30d": 175,
      "saved_by_recruiters_30d": 0,
      "interview_completion_rate": 0.78,
      "offer_acceptance_rate": 0.46,
      "verified_email": true,
      "verified_phone": false,
      "linkedin_connected": false
    }
  },
  {
    "candidate_id": "CAND_0000037",
    "profile": {
      "anonymized_name": "Ved Sen",
      "headline": "Business Analyst | 14.3+ yrs experience",
      "summary": "Professional with 14.3+ years of experience. I've spent my career in marketing manager roles, mostly focused on driving outcomes through process, people, and customer relationships. Lately I've been curious about how AI tools could augment my work \u2014 I've experimented with ChatGPT and a few other tools for productivity and content creation, and I think the space is exciting. Open to roles where I can apply my domain expertise alongside emerging AI capabilities.",
      "location": "Dubai",
      "country": "UAE",
      "years_of_experience": 14.3,
      "current_title": "Business Analyst",
      "current_company": "Stark Industries",
      "current_company_size": "1001-5000",
      "current_industry": "Manufacturing"
    },
    "career_history": [
      {
        "company": "Stark Industries",
        "title": "Business Analyst",
        "start_date": "2022-03-19",
        "end_date": null,
        "duration_months": 51,
        "is_current": true,
        "industry": "Manufacturing",
        "company_size": "1001-5000",
        "description": "Business analyst at a consulting firm, working primarily with retail and CPG clients. Conducted business diagnostics, process re-engineering work, and digital transformation strategy projects. Strong on stakeholder management, structured problem-solving, and the typical consulting toolkit (slide-craft, Excel modeling, executive communication). Recent project work involved AI-strategy advisory but my own technical depth in AI is limited."
      },
      {
        "company": "Initech",
        "title": "Civil Engineer",
        "start_date": "2019-08-18",
        "end_date": "2022-03-05",
        "duration_months": 31,
        "is_current": false,
        "industry": "Software",
        "company_size": "51-200",
        "description": "Operations management role at a logistics company. Owned daily fulfillment operations across 3 warehouses, managing a team of 80 across receiving, picking, packing, and outbound. Built and tracked the operational KPIs (on-time fulfillment, accuracy, cost per order) and led the continuous improvement initiatives that drove a 22% productivity gain over 18 months."
      },
      {
        "company": "Stark Industries",
        "title": "Content Writer",
        "start_date": "2016-01-06",
        "end_date": "2019-08-18",
        "duration_months": 44,
        "is_current": false,
        "industry": "Manufacturing",
        "company_size": "1001-5000",
        "description": "Operations management role at a logistics company. Owned daily fulfillment operations across 3 warehouses, managing a team of 80 across receiving, picking, packing, and outbound. Built and tracked the operational KPIs (on-time fulfillment, accuracy, cost per order) and led the continuous improvement initiatives that drove a 22% productivity gain over 18 months."
      },
      {
        "company": "Hooli",
        "title": "Mechanical Engineer",
        "start_date": "2013-07-20",
        "end_date": "2016-01-06",
        "duration_months": 30,
        "is_current": false,
        "industry": "Software",
        "company_size": "1001-5000",
        "description": "Marketing leadership role at a B2B SaaS company. Owned the demand-generation function \u2014 content marketing, paid acquisition, SEO, email nurture. Built and managed a team of 5 across content, performance marketing, and marketing operations. Worked closely with sales on lead-quality definitions and the SDR-handoff process. Recent focus has been on account-based marketing for our enterprise segment."
      },
      {
        "company": "Acme Corp",
        "title": "HR Manager",
        "start_date": "2012-04-26",
        "end_date": "2013-06-20",
        "duration_months": 14,
        "is_current": false,
        "industry": "Manufacturing",
        "company_size": "201-500",
        "description": "Brand design and creative direction at a consumer-products company. Owned brand identity (logo, visual system, typography), packaging design, and digital creative across web and social. Led the recent rebrand and managed a small external agency for production work. Comfortable across the Adobe suite, Figma, and the production side of brand and packaging design."
      }
    ],
    "education": [
      {
        "institution": "Tier-3 Engineering College",
        "degree": "B.Tech",
        "field_of_study": "Machine Learning",
        "start_year": 2001,
        "end_year": 2005,
        "grade": "69%",
        "tier": "tier_4"
      },
      {
        "institution": "Lovely Professional University",
        "degree": "M.Tech",
        "field_of_study": "Statistics",
        "start_year": 2013,
        "end_year": 2016,
        "grade": "6.81 CGPA",
        "tier": "tier_3"
      }
    ],
    "skills": [
      {
        "name": "Databricks",
        "proficiency": "intermediate",
        "endorsements": 12,
        "duration_months": 32
      },
      {
        "name": "Docker",
        "proficiency": "intermediate",
        "endorsements": 6,
        "duration_months": 35
      },
      {
        "name": "Flask",
        "proficiency": "beginner",
        "endorsements": 5,
        "duration_months": 14
      },
      {
        "name": "AWS",
        "proficiency": "intermediate",
        "endorsements": 2,
        "duration_months": 33
      },
      {
        "name": "Terraform",
        "proficiency": "beginner",
        "endorsements": 3,
        "duration_months": 18
      },
      {
        "name": "Tally",
        "proficiency": "intermediate",
        "endorsements": 14,
        "duration_months": 24
      },
      {
        "name": "TTS",
        "proficiency": "intermediate",
        "endorsements": 3,
        "duration_months": 13
      },
      {
        "name": "Apache Beam",
        "proficiency": "intermediate",
        "endorsements": 15,
        "duration_months": 23
      }
    ],
    "certifications": [
      {
        "name": "AWS Certified Cloud Practitioner",
        "issuer": "AWS",
        "year": 2024
      }
    ],
    "languages": [
      {
        "language": "English",
        "proficiency": "native"
      },
      {
        "language": "Hindi",
        "proficiency": "professional"
      }
    ],
    "redrob_signals": {
      "profile_completeness_score": 25.6,
      "signup_date": "2025-04-11",
      "last_active_date": "2025-12-11",
      "open_to_work_flag": false,
      "profile_views_received_30d": 80,
      "applications_submitted_30d": 6,
      "recruiter_response_rate": 0.78,
      "avg_response_time_hours": 107.1,
      "skill_assessment_scores": {},
      "connection_count": 503,
      "endorsements_received": 13,
      "notice_period_days": 30,
      "expected_salary_range_inr_lpa": {
        "min": 8.8,
        "max": 14.2
      },
      "preferred_work_mode": "onsite",
      "willing_to_relocate": false,
      "github_activity_score": -1,
      "search_appearance_30d": 178,
      "saved_by_recruiters_30d": 1,
      "interview_completion_rate": 0.82,
      "offer_acceptance_rate": 0.19,
      "verified_email": true,
      "verified_phone": true,
      "linkedin_connected": true
    }
  },
  {
    "candidate_id": "CAND_0000038",
    "profile": {
      "anonymized_name": "Myra Trivedi",
      "headline": "Java Developer | Cloud & DevOps",
      "summary": "Software engineer with 6.7 years of experience across web, backend, and cloud systems. Strong fundamentals in software development and system design. My background is full-stack, but my comfort zone is the backend and the database. I've been keeping up with AI/ML at a self-learner level \u2014 taken some online courses, played with the OpenAI and Anthropic APIs, built a small RAG side project \u2014 but I haven't done it in a professional capacity yet. Open to roles where I can either deepen my software engineering work or, if the team is open to it, start contributing to ML-adjacent systems.",
      "location": "Coimbatore, Tamil Nadu",
      "country": "India",
      "years_of_experience": 6.7,
      "current_title": "Java Developer",
      "current_company": "Swiggy",
      "current_company_size": "5001-10000",
      "current_industry": "Food Delivery"
    },
    "career_history": [
      {
        "company": "Swiggy",
        "title": "Java Developer",
        "start_date": "2023-11-09",
        "end_date": null,
        "duration_months": 31,
        "is_current": true,
        "industry": "Food Delivery",
        "company_size": "5001-10000",
        "description": "Frontend engineering at a media company. React, TypeScript, and the typical surrounding tooling (Webpack, Jest, Cypress). Built the company's design system from scratch and led the migration from a legacy AngularJS app. Strong on the frontend craft \u2014 accessibility, performance, animations \u2014 but limited backend exposure."
      },
      {
        "company": "Globex Inc",
        "title": ".NET Developer",
        "start_date": "2022-09-15",
        "end_date": "2023-11-09",
        "duration_months": 14,
        "is_current": false,
        "industry": "Manufacturing",
        "company_size": "501-1000",
        "description": "Java backend development at a large enterprise \u2014 Spring Boot microservices, Kafka for inter-service messaging, Postgres + Redis for storage. Worked on the customer onboarding flow which involved orchestrating multiple downstream services. Solid on the Spring ecosystem, transaction handling, and the operational side of Java services. Looking to either go deeper on distributed systems or expand into modern application stacks."
      },
      {
        "company": "Hooli",
        "title": "DevOps Engineer",
        "start_date": "2019-11-30",
        "end_date": "2022-09-15",
        "duration_months": 34,
        "is_current": false,
        "industry": "Software",
        "company_size": "1001-5000",
        "description": "Frontend engineering at a media company. React, TypeScript, and the typical surrounding tooling (Webpack, Jest, Cypress). Built the company's design system from scratch and led the migration from a legacy AngularJS app. Strong on the frontend craft \u2014 accessibility, performance, animations \u2014 but limited backend exposure."
      }
    ],
    "education": [
      {
        "institution": "VIT Chennai",
        "degree": "B.Sc",
        "field_of_study": "Computer Engineering",
        "start_year": 2015,
        "end_year": 2020,
        "grade": "70%",
        "tier": "tier_3"
      }
    ],
    "skills": [
      {
        "name": "Kubeflow",
        "proficiency": "intermediate",
        "endorsements": 3,
        "duration_months": 26
      },
      {
        "name": "Django",
        "proficiency": "beginner",
        "endorsements": 2,
        "duration_months": 18
      },
      {
        "name": "Redux",
        "proficiency": "intermediate",
        "endorsements": 3,
        "duration_months": 13
      },
      {
        "name": "Weaviate",
        "proficiency": "advanced",
        "endorsements": 37,
        "duration_months": 27
      },
      {
        "name": "PowerPoint",
        "proficiency": "beginner",
        "endorsements": 15,
        "duration_months": 9
      },
      {
        "name": "Figma",
        "proficiency": "beginner",
        "endorsements": 9,
        "duration_months": 8
      },
      {
        "name": "Docker",
        "proficiency": "beginner",
        "endorsements": 12,
        "duration_months": 3
      },
      {
        "name": "GraphQL",
        "proficiency": "intermediate",
        "endorsements": 13,
        "duration_months": 27
      },
      {
        "name": "Agile",
        "proficiency": "intermediate",
        "endorsements": 14,
        "duration_months": 24
      },
      {
        "name": "MLOps",
        "proficiency": "intermediate",
        "endorsements": 13,
        "duration_months": 26
      },
      {
        "name": "Azure",
        "proficiency": "intermediate",
        "endorsements": 14,
        "duration_months": 27
      }
    ],
    "certifications": [],
    "languages": [
      {
        "language": "English",
        "proficiency": "professional"
      },
      {
        "language": "Hindi",
        "proficiency": "conversational"
      }
    ],
    "redrob_signals": {
      "profile_completeness_score": 35.8,
      "signup_date": "2026-03-25",
      "last_active_date": "2026-03-31",
      "open_to_work_flag": true,
      "profile_views_received_30d": 102,
      "applications_submitted_30d": 9,
      "recruiter_response_rate": 0.2,
      "avg_response_time_hours": 61.0,
      "skill_assessment_scores": {},
      "connection_count": 316,
      "endorsements_received": 51,
      "notice_period_days": 90,
      "expected_salary_range_inr_lpa": {
        "min": 9.2,
        "max": 15.9
      },
      "preferred_work_mode": "flexible",
      "willing_to_relocate": true,
      "github_activity_score": 37.8,
      "search_appearance_30d": 300,
      "saved_by_recruiters_30d": 18,
      "interview_completion_rate": 0.75,
      "offer_acceptance_rate": -1,
      "verified_email": true,
      "verified_phone": true,
      "linkedin_connected": false
    }
  },
  {
    "candidate_id": "CAND_0000039",
    "profile": {
      "anonymized_name": "Sai Saxena",
      "headline": "Marketing Manager | Helping teams scale",
      "summary": "Professional with 3.9+ years of experience. My professional background is in marketing manager \u2014 I've built and led teams, owned KPIs, and driven business outcomes in this domain. Lately I've been curious about how AI tools could augment my work \u2014 I've experimented with ChatGPT and a few other tools for productivity and content creation, and I think the space is exciting. Open to roles where I can apply my domain expertise alongside emerging AI capabilities.",
      "location": "Bhubaneswar, Odisha",
      "country": "India",
      "years_of_experience": 3.9,
      "current_title": "Marketing Manager",
      "current_company": "Acme Corp",
      "current_company_size": "201-500",
      "current_industry": "Manufacturing"
    },
    "career_history": [
      {
        "company": "Acme Corp",
        "title": "Marketing Manager",
        "start_date": "2024-08-05",
        "end_date": null,
        "duration_months": 22,
        "is_current": true,
        "industry": "Manufacturing",
        "company_size": "201-500",
        "description": "Mechanical engineering design role at a hardware-product company. Led the design of two product subsystems through full lifecycle: concept, DFM/DFMA review, prototype, production tooling. Comfortable with CAD (SolidWorks, Creo), FEA (ANSYS), and the typical hardware-development cadence. Worked closely with manufacturing partners on production scale-up."
      },
      {
        "company": "Stark Industries",
        "title": "Mechanical Engineer",
        "start_date": "2022-08-16",
        "end_date": "2024-08-05",
        "duration_months": 24,
        "is_current": false,
        "industry": "Manufacturing",
        "company_size": "1001-5000",
        "description": "Brand design and creative direction at a consumer-products company. Owned brand identity (logo, visual system, typography), packaging design, and digital creative across web and social. Led the recent rebrand and managed a small external agency for production work. Comfortable across the Adobe suite, Figma, and the production side of brand and packaging design."
      }
    ],
    "education": [
      {
        "institution": "Chandigarh University",
        "degree": "B.Tech",
        "field_of_study": "Electrical Engineering",
        "start_year": 2009,
        "end_year": 2014,
        "grade": "66%",
        "tier": "tier_3"
      },
      {
        "institution": "Chandigarh University",
        "degree": "M.E.",
        "field_of_study": "Artificial Intelligence",
        "start_year": 2007,
        "end_year": 2011,
        "grade": "82%",
        "tier": "tier_3"
      }
    ],
    "skills": [
      {
        "name": "Spark",
        "proficiency": "intermediate",
        "endorsements": 9,
        "duration_months": 15
      },
      {
        "name": "Tailwind",
        "proficiency": "intermediate",
        "endorsements": 9,
        "duration_months": 8
      },
      {
        "name": "Sales",
        "proficiency": "beginner",
        "endorsements": 6,
        "duration_months": 8
      },
      {
        "name": "CI/CD",
        "proficiency": "intermediate",
        "endorsements": 11,
        "duration_months": 35
      },
      {
        "name": "Illustrator",
        "proficiency": "intermediate",
        "endorsements": 9,
        "duration_months": 21
      },
      {
        "name": "Hadoop",
        "proficiency": "intermediate",
        "endorsements": 15,
        "duration_months": 26
      },
      {
        "name": "Microservices",
        "proficiency": "intermediate",
        "endorsements": 13,
        "duration_months": 19
      },
      {
        "name": "REST APIs",
        "proficiency": "beginner",
        "endorsements": 15,
        "duration_months": 12
      },
      {
        "name": "AWS",
        "proficiency": "intermediate",
        "endorsements": 7,
        "duration_months": 18
      }
    ],
    "certifications": [],
    "languages": [
      {
        "language": "English",
        "proficiency": "native"
      },
      {
        "language": "Hindi",
        "proficiency": "conversational"
      }
    ],
    "redrob_signals": {
      "profile_completeness_score": 28.3,
      "signup_date": "2025-04-14",
      "last_active_date": "2026-04-18",
      "open_to_work_flag": false,
      "profile_views_received_30d": 22,
      "applications_submitted_30d": 0,
      "recruiter_response_rate": 0.52,
      "avg_response_time_hours": 40.1,
      "skill_assessment_scores": {},
      "connection_count": 102,
      "endorsements_received": 9,
      "notice_period_days": 30,
      "expected_salary_range_inr_lpa": {
        "min": 17.4,
        "max": 16.0
      },
      "preferred_work_mode": "hybrid",
      "willing_to_relocate": true,
      "github_activity_score": -1,
      "search_appearance_30d": 146,
      "saved_by_recruiters_30d": 6,
      "interview_completion_rate": 0.74,
      "offer_acceptance_rate": -1,
      "verified_email": false,
      "verified_phone": true,
      "linkedin_connected": true
    }
  },
  {
    "candidate_id": "CAND_0000040",
    "profile": {
      "anonymized_name": "Dev Vora",
      "headline": "Customer Support | Helping teams scale",
      "summary": "Professional with 1.6+ years of experience. I've spent my career in marketing manager roles, mostly focused on driving outcomes through process, people, and customer relationships. Lately I've been curious about how AI tools could augment my work \u2014 I've experimented with ChatGPT and a few other tools for productivity and content creation, and I think the space is exciting. Open to roles where I can apply my domain expertise alongside emerging AI capabilities.",
      "location": "Kochi, Kerala",
      "country": "India",
      "years_of_experience": 1.6,
      "current_title": "Customer Support",
      "current_company": "Globex Inc",
      "current_company_size": "501-1000",
      "current_industry": "Manufacturing"
    },
    "career_history": [
      {
        "company": "Globex Inc",
        "title": "Customer Support",
        "start_date": "2024-11-03",
        "end_date": null,
        "duration_months": 19,
        "is_current": true,
        "industry": "Manufacturing",
        "company_size": "501-1000",
        "description": "Enterprise sales of cloud software solutions into the mid-market segment. Carried a $1.8M ARR quota and consistently delivered against it across the last three years. Owned the full sales cycle: prospecting, discovery, technical evaluation (with SE support), commercial negotiation, and close. Strong on consultative selling for technical buyers; comfortable engaging with both engineering and finance stakeholders."
      }
    ],
    "education": [
      {
        "institution": "Local Engineering College",
        "degree": "B.Tech",
        "field_of_study": "MBA",
        "start_year": 2010,
        "end_year": 2013,
        "grade": "7.45 CGPA",
        "tier": "tier_4"
      }
    ],
    "skills": [
      {
        "name": "SQL",
        "proficiency": "beginner",
        "endorsements": 12,
        "duration_months": 4
      },
      {
        "name": "Spring Boot",
        "proficiency": "intermediate",
        "endorsements": 15,
        "duration_months": 27
      },
      {
        "name": "Accounting",
        "proficiency": "intermediate",
        "endorsements": 15,
        "duration_months": 16
      },
      {
        "name": "Rust",
        "proficiency": "beginner",
        "endorsements": 12,
        "duration_months": 15
      },
      {
        "name": "Redux",
        "proficiency": "intermediate",
        "endorsements": 2,
        "duration_months": 19
      },
      {
        "name": "SAP",
        "proficiency": "intermediate",
        "endorsements": 14,
        "duration_months": 25
      },
      {
        "name": "Weights & Biases",
        "proficiency": "intermediate",
        "endorsements": 10,
        "duration_months": 21
      },
      {
        "name": "REST APIs",
        "proficiency": "intermediate",
        "endorsements": 6,
        "duration_months": 18
      },
      {
        "name": "Spark",
        "proficiency": "beginner",
        "endorsements": 4,
        "duration_months": 14
      }
    ],
    "certifications": [],
    "languages": [
      {
        "language": "English",
        "proficiency": "professional"
      },
      {
        "language": "Hindi",
        "proficiency": "conversational"
      }
    ],
    "redrob_signals": {
      "profile_completeness_score": 39.5,
      "signup_date": "2024-10-03",
      "last_active_date": "2026-01-31",
      "open_to_work_flag": false,
      "profile_views_received_30d": 52,
      "applications_submitted_30d": 6,
      "recruiter_response_rate": 0.46,
      "avg_response_time_hours": 268.3,
      "skill_assessment_scores": {},
      "connection_count": 176,
      "endorsements_received": 35,
      "notice_period_days": 90,
      "expected_salary_range_inr_lpa": {
        "min": 7.6,
        "max": 8.2
      },
      "preferred_work_mode": "remote",
      "willing_to_relocate": false,
      "github_activity_score": -1,
      "search_appearance_30d": 95,
      "saved_by_recruiters_30d": 1,
      "interview_completion_rate": 0.8,
      "offer_acceptance_rate": 0.44,
      "verified_email": true,
      "verified_phone": false,
      "linkedin_connected": false
    }
  },
  {
    "candidate_id": "CAND_0000041",
    "profile": {
      "anonymized_name": "Anjali Khanna",
      "headline": "Operations Manager | Helping teams scale",
      "summary": "Professional with 13.7+ years of experience. I've spent my career in marketing manager roles, mostly focused on driving outcomes through process, people, and customer relationships. Lately I've been curious about how AI tools could augment my work \u2014 I've experimented with ChatGPT and a few other tools for productivity and content creation, and I think the space is exciting. Open to roles where I can apply my domain expertise alongside emerging AI capabilities.",
      "location": "Delhi, Delhi",
      "country": "India",
      "years_of_experience": 13.7,
      "current_title": "Operations Manager",
      "current_company": "Hooli",
      "current_company_size": "1001-5000",
      "current_industry": "Software"
    },
    "career_history": [
      {
        "company": "Hooli",
        "title": "Operations Manager",
        "start_date": "2022-12-14",
        "end_date": null,
        "duration_months": 42,
        "is_current": true,
        "industry": "Software",
        "company_size": "1001-5000",
        "description": "Customer support team lead at a SaaS product. Managed a team of 8 support agents handling tier-1 and tier-2 tickets; owned the escalation process to engineering and the customer-feedback loop to product. Built out the support knowledge base and the agent training program. Strong on the people-management side and the process side; lighter on technical depth beyond product expertise."
      },
      {
        "company": "Acme Corp",
        "title": "Business Analyst",
        "start_date": "2021-03-24",
        "end_date": "2022-12-14",
        "duration_months": 21,
        "is_current": false,
        "industry": "Manufacturing",
        "company_size": "201-500",
        "description": "Mechanical engineering design role at a hardware-product company. Led the design of two product subsystems through full lifecycle: concept, DFM/DFMA review, prototype, production tooling. Comfortable with CAD (SolidWorks, Creo), FEA (ANSYS), and the typical hardware-development cadence. Worked closely with manufacturing partners on production scale-up."
      },
      {
        "company": "Wayne Enterprises",
        "title": "Content Writer",
        "start_date": "2019-03-21",
        "end_date": "2021-03-10",
        "duration_months": 24,
        "is_current": false,
        "industry": "Conglomerate",
        "company_size": "10001+",
        "description": "Operations management role at a logistics company. Owned daily fulfillment operations across 3 warehouses, managing a team of 80 across receiving, picking, packing, and outbound. Built and tracked the operational KPIs (on-time fulfillment, accuracy, cost per order) and led the continuous improvement initiatives that drove a 22% productivity gain over 18 months."
      },
      {
        "company": "Infosys",
        "title": "Content Writer",
        "start_date": "2014-12-05",
        "end_date": "2019-03-14",
        "duration_months": 52,
        "is_current": false,
        "industry": "IT Services",
        "company_size": "10001+",
        "description": "Customer support team lead at a SaaS product. Managed a team of 8 support agents handling tier-1 and tier-2 tickets; owned the escalation process to engineering and the customer-feedback loop to product. Built out the support knowledge base and the agent training program. Strong on the people-management side and the process side; lighter on technical depth beyond product expertise."
      },
      {
        "company": "Dunder Mifflin",
        "title": "Mechanical Engineer",
        "start_date": "2013-01-07",
        "end_date": "2014-11-28",
        "duration_months": 23,
        "is_current": false,
        "industry": "Paper Products",
        "company_size": "201-500",
        "description": "Marketing leadership role at a B2B SaaS company. Owned the demand-generation function \u2014 content marketing, paid acquisition, SEO, email nurture. Built and managed a team of 5 across content, performance marketing, and marketing operations. Worked closely with sales on lead-quality definitions and the SDR-handoff process. Recent focus has been on account-based marketing for our enterprise segment."
      }
    ],
    "education": [
      {
        "institution": "Local Engineering College",
        "degree": "M.S.",
        "field_of_study": "Machine Learning",
        "start_year": 2013,
        "end_year": 2018,
        "grade": "8.73 CGPA",
        "tier": "tier_4"
      }
    ],
    "skills": [
      {
        "name": "Airflow",
        "proficiency": "intermediate",
        "endorsements": 13,
        "duration_months": 20
      },
      {
        "name": "SQL",
        "proficiency": "intermediate",
        "endorsements": 12,
        "duration_months": 12
      },
      {
        "name": "Go",
        "proficiency": "beginner",
        "endorsements": 13,
        "duration_months": 8
      },
      {
        "name": "GCP",
        "proficiency": "beginner",
        "endorsements": 0,
        "duration_months": 3
      },
      {
        "name": "Figma",
        "proficiency": "beginner",
        "endorsements": 14,
        "duration_months": 16
      },
      {
        "name": "React",
        "proficiency": "intermediate",
        "endorsements": 15,
        "duration_months": 22
      },
      {
        "name": "Webpack",
        "proficiency": "beginner",
        "endorsements": 3,
        "duration_months": 9
      },
      {
        "name": "Kubernetes",
        "proficiency": "beginner",
        "endorsements": 5,
        "duration_months": 3
      },
      {
        "name": "Angular",
        "proficiency": "intermediate",
        "endorsements": 2,
        "duration_months": 31
      }
    ],
    "certifications": [],
    "languages": [
      {
        "language": "English",
        "proficiency": "professional"
      },
      {
        "language": "Hindi",
        "proficiency": "professional"
      }
    ],
    "redrob_signals": {
      "profile_completeness_score": 75.9,
      "signup_date": "2025-08-18",
      "last_active_date": "2026-03-16",
      "open_to_work_flag": true,
      "profile_views_received_30d": 3,
      "applications_submitted_30d": 9,
      "recruiter_response_rate": 0.07,
      "avg_response_time_hours": 135.3,
      "skill_assessment_scores": {},
      "connection_count": 143,
      "endorsements_received": 19,
      "notice_period_days": 90,
      "expected_salary_range_inr_lpa": {
        "min": 5.4,
        "max": 9.3
      },
      "preferred_work_mode": "remote",
      "willing_to_relocate": true,
      "github_activity_score": -1,
      "search_appearance_30d": 150,
      "saved_by_recruiters_30d": 6,
      "interview_completion_rate": 0.85,
      "offer_acceptance_rate": 0.16,
      "verified_email": true,
      "verified_phone": true,
      "linkedin_connected": true
    }
  },
  {
    "candidate_id": "CAND_0000042",
    "profile": {
      "anonymized_name": "Riya Mukherjee",
      "headline": "HR Manager | 5.0+ yrs experience",
      "summary": "Professional with 5.0+ years of experience. I'm a marketing manager with substantial experience in cross-functional collaboration, stakeholder management, and execution. Lately I've been curious about how AI tools could augment my work \u2014 I've experimented with ChatGPT and a few other tools for productivity and content creation, and I think the space is exciting. Open to roles where I can apply my domain expertise alongside emerging AI capabilities.",
      "location": "Berlin",
      "country": "Germany",
      "years_of_experience": 5.0,
      "current_title": "HR Manager",
      "current_company": "Wayne Enterprises",
      "current_company_size": "10001+",
      "current_industry": "Conglomerate"
    },
    "career_history": [
      {
        "company": "Wayne Enterprises",
        "title": "HR Manager",
        "start_date": "2024-04-07",
        "end_date": null,
        "duration_months": 26,
        "is_current": true,
        "industry": "Conglomerate",
        "company_size": "10001+",
        "description": "Content writing and SEO strategy for a tech-focused publication. Wrote longform articles on developer tools, cloud platforms, and AI/ML topics \u2014 including some that ranked on the first page of search for high-competition keywords. Managed a freelance writer pool and the editorial calendar. Recent work has been on AI-assisted content production, using LLM tools for research, drafting, and editing while maintaining editorial quality."
      },
      {
        "company": "Wipro",
        "title": "Business Analyst",
        "start_date": "2023-03-14",
        "end_date": "2024-03-08",
        "duration_months": 12,
        "is_current": false,
        "industry": "IT Services",
        "company_size": "10001+",
        "description": "Enterprise sales of cloud software solutions into the mid-market segment. Carried a $1.8M ARR quota and consistently delivered against it across the last three years. Owned the full sales cycle: prospecting, discovery, technical evaluation (with SE support), commercial negotiation, and close. Strong on consultative selling for technical buyers; comfortable engaging with both engineering and finance stakeholders."
      },
      {
        "company": "Infosys",
        "title": "Customer Support",
        "start_date": "2021-04-23",
        "end_date": "2023-01-13",
        "duration_months": 21,
        "is_current": false,
        "industry": "IT Services",
        "company_size": "10001+",
        "description": "Marketing leadership role at a B2B SaaS company. Owned the demand-generation function \u2014 content marketing, paid acquisition, SEO, email nurture. Built and managed a team of 5 across content, performance marketing, and marketing operations. Worked closely with sales on lead-quality definitions and the SDR-handoff process. Recent focus has been on account-based marketing for our enterprise segment."
      }
    ],
    "education": [
      {
        "institution": "SRM Chennai",
        "degree": "B.Tech",
        "field_of_study": "Civil Engineering",
        "start_year": 2014,
        "end_year": 2019,
        "grade": "7.40 CGPA",
        "tier": "tier_3"
      },
      {
        "institution": "Symbiosis International",
        "degree": "B.E.",
        "field_of_study": "Mathematics",
        "start_year": 2017,
        "end_year": 2021,
        "grade": "8.07 CGPA",
        "tier": "tier_3"
      }
    ],
    "skills": [
      {
        "name": "Project Management",
        "proficiency": "intermediate",
        "endorsements": 3,
        "duration_months": 33
      },
      {
        "name": "gRPC",
        "proficiency": "beginner",
        "endorsements": 3,
        "duration_months": 10
      },
      {
        "name": "Marketing",
        "proficiency": "intermediate",
        "endorsements": 10,
        "duration_months": 24
      },
      {
        "name": "SAP",
        "proficiency": "beginner",
        "endorsements": 12,
        "duration_months": 18
      },
      {
        "name": "Illustrator",
        "proficiency": "beginner",
        "endorsements": 11,
        "duration_months": 14
      },
      {
        "name": "Node.js",
        "proficiency": "intermediate",
        "endorsements": 3,
        "duration_months": 14
      },
      {
        "name": "YOLO",
        "proficiency": "intermediate",
        "endorsements": 5,
        "duration_months": 22
      },
      {
        "name": "Tailwind",
        "proficiency": "beginner",
        "endorsements": 8,
        "duration_months": 16
      },
      {
        "name": "CSS",
        "proficiency": "beginner",
        "endorsements": 11,
        "duration_months": 12
      },
      {
        "name": "Figma",
        "proficiency": "beginner",
        "endorsements": 10,
        "duration_months": 7
      }
    ],
    "certifications": [
      {
        "name": "Six Sigma Green Belt",
        "issuer": "ASQ",
        "year": 2022
      },
      {
        "name": "Scrum Master Certified",
        "issuer": "Scrum Alliance",
        "year": 2021
      }
    ],
    "languages": [
      {
        "language": "English",
        "proficiency": "professional"
      },
      {
        "language": "Hindi",
        "proficiency": "conversational"
      }
    ],
    "redrob_signals": {
      "profile_completeness_score": 58.6,
      "signup_date": "2025-05-02",
      "last_active_date": "2025-10-23",
      "open_to_work_flag": false,
      "profile_views_received_30d": 57,
      "applications_submitted_30d": 8,
      "recruiter_response_rate": 0.58,
      "avg_response_time_hours": 24.8,
      "skill_assessment_scores": {},
      "connection_count": 591,
      "endorsements_received": 29,
      "notice_period_days": 30,
      "expected_salary_range_inr_lpa": {
        "min": 10.5,
        "max": 18.8
      },
      "preferred_work_mode": "flexible",
      "willing_to_relocate": true,
      "github_activity_score": -1,
      "search_appearance_30d": 34,
      "saved_by_recruiters_30d": 9,
      "interview_completion_rate": 0.35,
      "offer_acceptance_rate": -1,
      "verified_email": true,
      "verified_phone": true,
      "linkedin_connected": false
    }
  },
  {
    "candidate_id": "CAND_0000043",
    "profile": {
      "anonymized_name": "Aarav Sen",
      "headline": "Cloud Engineer | Full-stack development",
      "summary": "Software engineer with 8.3 years of experience across web, backend, and cloud systems. Strong fundamentals in software development and system design. I've worked across web frontends, REST APIs, and cloud deployments; comfortable in most parts of a typical SaaS stack. I've been keeping up with AI/ML at a self-learner level \u2014 taken some online courses, played with the OpenAI and Anthropic APIs, built a small RAG side project \u2014 but I haven't done it in a professional capacity yet. Open to roles where I can either deepen my software engineering work or, if the team is open to it, start contributing to ML-adjacent systems.",
      "location": "Chandigarh, Chandigarh",
      "country": "India",
      "years_of_experience": 8.3,
      "current_title": "Cloud Engineer",
      "current_company": "Swiggy",
      "current_company_size": "5001-10000",
      "current_industry": "Food Delivery"
    },
    "career_history": [
      {
        "company": "Swiggy",
        "title": "Cloud Engineer",
        "start_date": "2023-12-09",
        "end_date": null,
        "duration_months": 30,
        "is_current": true,
        "industry": "Food Delivery",
        "company_size": "5001-10000",
        "description": "Test automation and QA engineering for a fintech product. Built and maintained the end-to-end test suite using Selenium and pytest, plus the load-testing setup using Locust. Worked closely with developers on testability patterns and with product on acceptance criteria. Recent work has been on shifting test responsibility into the dev team \u2014 moving from QA-as-gate to QA-as-coach. Career has been entirely in QA/test engineering."
      },
      {
        "company": "HCL",
        "title": ".NET Developer",
        "start_date": "2021-12-19",
        "end_date": "2023-12-09",
        "duration_months": 24,
        "is_current": false,
        "industry": "IT Services",
        "company_size": "10001+",
        "description": "Cloud infrastructure and DevOps work at an enterprise SaaS company. Owned the AWS account architecture (VPC, IAM, networking), the Terraform modules for our service deployments, and the Kubernetes cluster operations. Designed the CI/CD pipelines (GitLab CI + ArgoCD) and the monitoring stack (Prometheus, Grafana, Loki). Strong on the infra and ops side; haven't done much application development."
      },
      {
        "company": "Mindtree",
        "title": "Frontend Engineer",
        "start_date": "2019-11-30",
        "end_date": "2021-12-19",
        "duration_months": 25,
        "is_current": false,
        "industry": "IT Services",
        "company_size": "10001+",
        "description": "Android mobile development using Java and (more recently) Kotlin at a consumer-app company. Built and maintained multiple production features including the main shopping flow, push notification system, and the offline-first sync layer. Comfortable with the Android framework, Jetpack components, and the typical patterns (MVVM, Hilt, Coroutines). My career has been entirely on mobile so far; interested in expanding into broader backend or platform engineering."
      },
      {
        "company": "Initech",
        "title": "DevOps Engineer",
        "start_date": "2018-04-09",
        "end_date": "2019-11-30",
        "duration_months": 20,
        "is_current": false,
        "industry": "Software",
        "company_size": "51-200",
        "description": "Android mobile development using Java and (more recently) Kotlin at a consumer-app company. Built and maintained multiple production features including the main shopping flow, push notification system, and the offline-first sync layer. Comfortable with the Android framework, Jetpack components, and the typical patterns (MVVM, Hilt, Coroutines). My career has been entirely on mobile so far; interested in expanding into broader backend or platform engineering."
      }
    ],
    "education": [
      {
        "institution": "Regional Technical Institute",
        "degree": "M.E.",
        "field_of_study": "Electronics",
        "start_year": 2012,
        "end_year": 2017,
        "grade": "8.77 CGPA",
        "tier": "tier_4"
      },
      {
        "institution": "Regional Technical Institute",
        "degree": "B.Sc",
        "field_of_study": "Physics",
        "start_year": 2001,
        "end_year": 2005,
        "grade": "9.29 CGPA",
        "tier": "tier_4"
      }
    ],
    "skills": [
      {
        "name": "Elasticsearch",
        "proficiency": "advanced",
        "endorsements": 54,
        "duration_months": 44
      },
      {
        "name": "OpenSearch",
        "proficiency": "intermediate",
        "endorsements": 21,
        "duration_months": 34
      },
      {
        "name": "Airflow",
        "proficiency": "beginner",
        "endorsements": 5,
        "duration_months": 2
      },
      {
        "name": "Kubeflow",
        "proficiency": "advanced",
        "endorsements": 12,
        "duration_months": 55
      },
      {
        "name": "Fine-tuning LLMs",
        "proficiency": "intermediate",
        "endorsements": 8,
        "duration_months": 14
      },
      {
        "name": "Haystack",
        "proficiency": "advanced",
        "endorsements": 11,
        "duration_months": 27
      },
      {
        "name": "OpenCV",
        "proficiency": "advanced",
        "endorsements": 54,
        "duration_months": 33
      },
      {
        "name": "TensorFlow",
        "proficiency": "intermediate",
        "endorsements": 0,
        "duration_months": 19
      },
      {
        "name": "PEFT",
        "proficiency": "intermediate",
        "endorsements": 5,
        "duration_months": 21
      },
      {
        "name": "LangChain",
        "proficiency": "intermediate",
        "endorsements": 37,
        "duration_months": 25
      },
      {
        "name": "Weights & Biases",
        "proficiency": "intermediate",
        "endorsements": 4,
        "duration_months": 26
      },
      {
        "name": "Reinforcement Learning",
        "proficiency": "advanced",
        "endorsements": 0,
        "duration_months": 30
      },
      {
        "name": "Deep Learning",
        "proficiency": "intermediate",
        "endorsements": 0,
        "duration_months": 16
      },
      {
        "name": "Image Classification",
        "proficiency": "advanced",
        "endorsements": 24,
        "duration_months": 50
      },
      {
        "name": "Node.js",
        "proficiency": "intermediate",
        "endorsements": 12,
        "duration_months": 24
      },
      {
        "name": "Project Management",
        "proficiency": "intermediate",
        "endorsements": 0,
        "duration_months": 36
      },
      {
        "name": "Feature Engineering",
        "proficiency": "intermediate",
        "endorsements": 0,
        "duration_months": 20
      }
    ],
    "certifications": [],
    "languages": [
      {
        "language": "English",
        "proficiency": "native"
      },
      {
        "language": "Hindi",
        "proficiency": "professional"
      }
    ],
    "redrob_signals": {
      "profile_completeness_score": 57.0,
      "signup_date": "2024-09-30",
      "last_active_date": "2026-01-01",
      "open_to_work_flag": false,
      "profile_views_received_30d": 38,
      "applications_submitted_30d": 8,
      "recruiter_response_rate": 0.04,
      "avg_response_time_hours": 223.5,
      "skill_assessment_scores": {},
      "connection_count": 102,
      "endorsements_received": 39,
      "notice_period_days": 120,
      "expected_salary_range_inr_lpa": {
        "min": 6.3,
        "max": 21.2
      },
      "preferred_work_mode": "remote",
      "willing_to_relocate": true,
      "github_activity_score": -1,
      "search_appearance_30d": 167,
      "saved_by_recruiters_30d": 2,
      "interview_completion_rate": 0.72,
      "offer_acceptance_rate": -1,
      "verified_email": true,
      "verified_phone": true,
      "linkedin_connected": false
    }
  },
  {
    "candidate_id": "CAND_0000044",
    "profile": {
      "anonymized_name": "Vihaan Naidu",
      "headline": "Frontend Engineer | Backend systems & APIs",
      "summary": "Software engineer with 5.7 years of experience across web, backend, and cloud systems. Strong fundamentals in software development and system design. I've spent most of my career on web and API development \u2014 Python/Django and Node.js mostly. I've been keeping up with AI/ML at a self-learner level \u2014 taken some online courses, played with the OpenAI and Anthropic APIs, built a small RAG side project \u2014 but I haven't done it in a professional capacity yet. Open to roles where I can either deepen my software engineering work or, if the team is open to it, start contributing to ML-adjacent systems.",
      "location": "Indore, Madhya Pradesh",
      "country": "India",
      "years_of_experience": 5.7,
      "current_title": "Frontend Engineer",
      "current_company": "Tech Mahindra",
      "current_company_size": "10001+",
      "current_industry": "IT Services"
    },
    "career_history": [
      {
        "company": "Tech Mahindra",
        "title": "Frontend Engineer",
        "start_date": "2022-04-18",
        "end_date": null,
        "duration_months": 50,
        "is_current": true,
        "industry": "IT Services",
        "company_size": "10001+",
        "description": "Java backend development at a large enterprise \u2014 Spring Boot microservices, Kafka for inter-service messaging, Postgres + Redis for storage. Worked on the customer onboarding flow which involved orchestrating multiple downstream services. Solid on the Spring ecosystem, transaction handling, and the operational side of Java services. Looking to either go deeper on distributed systems or expand into modern application stacks."
      },
      {
        "company": "Hooli",
        "title": "DevOps Engineer",
        "start_date": "2020-10-25",
        "end_date": "2022-04-18",
        "duration_months": 18,
        "is_current": false,
        "industry": "Software",
        "company_size": "1001-5000",
        "description": "Frontend engineering at a media company. React, TypeScript, and the typical surrounding tooling (Webpack, Jest, Cypress). Built the company's design system from scratch and led the migration from a legacy AngularJS app. Strong on the frontend craft \u2014 accessibility, performance, animations \u2014 but limited backend exposure."
      }
    ],
    "education": [
      {
        "institution": "Chandigarh University",
        "degree": "M.Sc",
        "field_of_study": "Information Technology",
        "start_year": 2016,
        "end_year": 2021,
        "grade": "84%",
        "tier": "tier_3"
      },
      {
        "institution": "Amity University",
        "degree": "B.E.",
        "field_of_study": "Civil Engineering",
        "start_year": 2002,
        "end_year": 2006,
        "grade": "9.33 CGPA",
        "tier": "tier_3"
      }
    ],
    "skills": [
      {
        "name": "Hadoop",
        "proficiency": "beginner",
        "endorsements": 3,
        "duration_months": 3
      },
      {
        "name": "JavaScript",
        "proficiency": "beginner",
        "endorsements": 5,
        "duration_months": 18
      },
      {
        "name": "Databricks",
        "proficiency": "beginner",
        "endorsements": 13,
        "duration_months": 5
      },
      {
        "name": "Python",
        "proficiency": "intermediate",
        "endorsements": 2,
        "duration_months": 26
      },
      {
        "name": "dbt",
        "proficiency": "intermediate",
        "endorsements": 3,
        "duration_months": 16
      },
      {
        "name": "CI/CD",
        "proficiency": "beginner",
        "endorsements": 11,
        "duration_months": 13
      }
    ],
    "certifications": [],
    "languages": [
      {
        "language": "English",
        "proficiency": "professional"
      },
      {
        "language": "Hindi",
        "proficiency": "professional"
      }
    ],
    "redrob_signals": {
      "profile_completeness_score": 30.6,
      "signup_date": "2023-02-16",
      "last_active_date": "2025-12-11",
      "open_to_work_flag": false,
      "profile_views_received_30d": 78,
      "applications_submitted_30d": 7,
      "recruiter_response_rate": 0.66,
      "avg_response_time_hours": 179.1,
      "skill_assessment_scores": {},
      "connection_count": 58,
      "endorsements_received": 38,
      "notice_period_days": 90,
      "expected_salary_range_inr_lpa": {
        "min": 8.8,
        "max": 12.3
      },
      "preferred_work_mode": "remote",
      "willing_to_relocate": false,
      "github_activity_score": 6.5,
      "search_appearance_30d": 288,
      "saved_by_recruiters_30d": 18,
      "interview_completion_rate": 0.66,
      "offer_acceptance_rate": -1,
      "verified_email": true,
      "verified_phone": false,
      "linkedin_connected": false
    }
  },
  {
    "candidate_id": "CAND_0000045",
    "profile": {
      "anonymized_name": "Vikram Mittal",
      "headline": "Project Manager | 12.2+ yrs experience",
      "summary": "Professional with 12.2+ years of experience. My professional background is in marketing manager \u2014 I've built and led teams, owned KPIs, and driven business outcomes in this domain. Lately I've been curious about how AI tools could augment my work \u2014 I've experimented with ChatGPT and a few other tools for productivity and content creation, and I think the space is exciting. Open to roles where I can apply my domain expertise alongside emerging AI capabilities.",
      "location": "Indore, Madhya Pradesh",
      "country": "India",
      "years_of_experience": 12.2,
      "current_title": "Project Manager",
      "current_company": "Initech",
      "current_company_size": "51-200",
      "current_industry": "Software"
    },
    "career_history": [
      {
        "company": "Initech",
        "title": "Project Manager",
        "start_date": "2025-03-03",
        "end_date": null,
        "duration_months": 15,
        "is_current": true,
        "industry": "Software",
        "company_size": "51-200",
        "description": "Enterprise sales of cloud software solutions into the mid-market segment. Carried a $1.8M ARR quota and consistently delivered against it across the last three years. Owned the full sales cycle: prospecting, discovery, technical evaluation (with SE support), commercial negotiation, and close. Strong on consultative selling for technical buyers; comfortable engaging with both engineering and finance stakeholders."
      },
      {
        "company": "Pied Piper",
        "title": "Civil Engineer",
        "start_date": "2024-02-07",
        "end_date": "2025-03-03",
        "duration_months": 13,
        "is_current": false,
        "industry": "Software",
        "company_size": "11-50",
        "description": "Mechanical engineering design role at a hardware-product company. Led the design of two product subsystems through full lifecycle: concept, DFM/DFMA review, prototype, production tooling. Comfortable with CAD (SolidWorks, Creo), FEA (ANSYS), and the typical hardware-development cadence. Worked closely with manufacturing partners on production scale-up."
      },
      {
        "company": "Infosys",
        "title": "Marketing Manager",
        "start_date": "2023-01-29",
        "end_date": "2024-01-24",
        "duration_months": 12,
        "is_current": false,
        "industry": "IT Services",
        "company_size": "10001+",
        "description": "Customer support team lead at a SaaS product. Managed a team of 8 support agents handling tier-1 and tier-2 tickets; owned the escalation process to engineering and the customer-feedback loop to product. Built out the support knowledge base and the agent training program. Strong on the people-management side and the process side; lighter on technical depth beyond product expertise."
      },
      {
        "company": "Wayne Enterprises",
        "title": "Content Writer",
        "start_date": "2021-10-06",
        "end_date": "2023-01-29",
        "duration_months": 16,
        "is_current": false,
        "industry": "Conglomerate",
        "company_size": "10001+",
        "description": "Marketing leadership role at a B2B SaaS company. Owned the demand-generation function \u2014 content marketing, paid acquisition, SEO, email nurture. Built and managed a team of 5 across content, performance marketing, and marketing operations. Worked closely with sales on lead-quality definitions and the SDR-handoff process. Recent focus has been on account-based marketing for our enterprise segment."
      },
      {
        "company": "TCS",
        "title": "Graphic Designer",
        "start_date": "2018-08-09",
        "end_date": "2021-09-22",
        "duration_months": 38,
        "is_current": false,
        "industry": "IT Services",
        "company_size": "10001+",
        "description": "Customer support team lead at a SaaS product. Managed a team of 8 support agents handling tier-1 and tier-2 tickets; owned the escalation process to engineering and the customer-feedback loop to product. Built out the support knowledge base and the agent training program. Strong on the people-management side and the process side; lighter on technical depth beyond product expertise."
      },
      {
        "company": "Wayne Enterprises",
        "title": "Graphic Designer",
        "start_date": "2016-04-21",
        "end_date": "2018-08-09",
        "duration_months": 28,
        "is_current": false,
        "industry": "Conglomerate",
        "company_size": "10001+",
        "description": "Enterprise sales of cloud software solutions into the mid-market segment. Carried a $1.8M ARR quota and consistently delivered against it across the last three years. Owned the full sales cycle: prospecting, discovery, technical evaluation (with SE support), commercial negotiation, and close. Strong on consultative selling for technical buyers; comfortable engaging with both engineering and finance stakeholders."
      },
      {
        "company": "Stark Industries",
        "title": "Operations Manager",
        "start_date": "2014-07-17",
        "end_date": "2016-04-07",
        "duration_months": 21,
        "is_current": false,
        "industry": "Manufacturing",
        "company_size": "1001-5000",
        "description": "Enterprise sales of cloud software solutions into the mid-market segment. Carried a $1.8M ARR quota and consistently delivered against it across the last three years. Owned the full sales cycle: prospecting, discovery, technical evaluation (with SE support), commercial negotiation, and close. Strong on consultative selling for technical buyers; comfortable engaging with both engineering and finance stakeholders."
      }
    ],
    "education": [
      {
        "institution": "Generic State University",
        "degree": "M.E.",
        "field_of_study": "Statistics",
        "start_year": 2002,
        "end_year": 2005,
        "grade": "7.91 CGPA",
        "tier": "tier_4"
      },
      {
        "institution": "KIIT University",
        "degree": "B.Tech",
        "field_of_study": "Machine Learning",
        "start_year": 2016,
        "end_year": 2020,
        "grade": "86%",
        "tier": "tier_3"
      }
    ],
    "skills": [
      {
        "name": "GCP",
        "proficiency": "beginner",
        "endorsements": 1,
        "duration_months": 3
      },
      {
        "name": "Sales",
        "proficiency": "intermediate",
        "endorsements": 2,
        "duration_months": 12
      },
      {
        "name": "Redux",
        "proficiency": "intermediate",
        "endorsements": 14,
        "duration_months": 25
      },
      {
        "name": "PostgreSQL",
        "proficiency": "intermediate",
        "endorsements": 1,
        "duration_months": 36
      },
      {
        "name": "Airflow",
        "proficiency": "intermediate",
        "endorsements": 5,
        "duration_months": 18
      },
      {
        "name": "SAP",
        "proficiency": "intermediate",
        "endorsements": 13,
        "duration_months": 27
      }
    ],
    "certifications": [
      {
        "name": "Scrum Master Certified",
        "issuer": "Scrum Alliance",
        "year": 2024
      },
      {
        "name": "Six Sigma Green Belt",
        "issuer": "ASQ",
        "year": 2024
      }
    ],
    "languages": [
      {
        "language": "English",
        "proficiency": "professional"
      },
      {
        "language": "Hindi",
        "proficiency": "professional"
      }
    ],
    "redrob_signals": {
      "profile_completeness_score": 25.4,
      "signup_date": "2023-04-15",
      "last_active_date": "2026-04-24",
      "open_to_work_flag": true,
      "profile_views_received_30d": 37,
      "applications_submitted_30d": 0,
      "recruiter_response_rate": 0.62,
      "avg_response_time_hours": 20.8,
      "skill_assessment_scores": {},
      "connection_count": 490,
      "endorsements_received": 2,
      "notice_period_days": 60,
      "expected_salary_range_inr_lpa": {
        "min": 9.7,
        "max": 12.3
      },
      "preferred_work_mode": "hybrid",
      "willing_to_relocate": true,
      "github_activity_score": -1,
      "search_appearance_30d": 23,
      "saved_by_recruiters_30d": 6,
      "interview_completion_rate": 0.33,
      "offer_acceptance_rate": -1,
      "verified_email": true,
      "verified_phone": true,
      "linkedin_connected": true
    }
  },
  {
    "candidate_id": "CAND_0000046",
    "profile": {
      "anonymized_name": "Dev Nair",
      "headline": "Mechanical Engineer | 7.8+ yrs experience",
      "summary": "Professional with 7.8+ years of experience. I've spent my career in marketing manager roles, mostly focused on driving outcomes through process, people, and customer relationships. Lately I've been curious about how AI tools could augment my work \u2014 I've experimented with ChatGPT and a few other tools for productivity and content creation, and I think the space is exciting. Open to roles where I can apply my domain expertise alongside emerging AI capabilities.",
      "location": "London",
      "country": "UK",
      "years_of_experience": 7.8,
      "current_title": "Mechanical Engineer",
      "current_company": "Hooli",
      "current_company_size": "1001-5000",
      "current_industry": "Software"
    },
    "career_history": [
      {
        "company": "Hooli",
        "title": "Mechanical Engineer",
        "start_date": "2023-12-09",
        "end_date": null,
        "duration_months": 30,
        "is_current": true,
        "industry": "Software",
        "company_size": "1001-5000",
        "description": "Customer support team lead at a SaaS product. Managed a team of 8 support agents handling tier-1 and tier-2 tickets; owned the escalation process to engineering and the customer-feedback loop to product. Built out the support knowledge base and the agent training program. Strong on the people-management side and the process side; lighter on technical depth beyond product expertise."
      },
      {
        "company": "Pied Piper",
        "title": "HR Manager",
        "start_date": "2021-02-22",
        "end_date": "2023-11-09",
        "duration_months": 33,
        "is_current": false,
        "industry": "Software",
        "company_size": "11-50",
        "description": "Marketing leadership role at a B2B SaaS company. Owned the demand-generation function \u2014 content marketing, paid acquisition, SEO, email nurture. Built and managed a team of 5 across content, performance marketing, and marketing operations. Worked closely with sales on lead-quality definitions and the SDR-handoff process. Recent focus has been on account-based marketing for our enterprise segment."
      },
      {
        "company": "Hooli",
        "title": "Marketing Manager",
        "start_date": "2018-08-23",
        "end_date": "2021-02-08",
        "duration_months": 30,
        "is_current": false,
        "industry": "Software",
        "company_size": "1001-5000",
        "description": "Operations management role at a logistics company. Owned daily fulfillment operations across 3 warehouses, managing a team of 80 across receiving, picking, packing, and outbound. Built and tracked the operational KPIs (on-time fulfillment, accuracy, cost per order) and led the continuous improvement initiatives that drove a 22% productivity gain over 18 months."
      }
    ],
    "education": [
      {
        "institution": "Christ University",
        "degree": "M.Tech",
        "field_of_study": "Electrical Engineering",
        "start_year": 2014,
        "end_year": 2017,
        "grade": "9.49 CGPA",
        "tier": "tier_3"
      },
      {
        "institution": "Chandigarh University",
        "degree": "B.E.",
        "field_of_study": "Statistics",
        "start_year": 2004,
        "end_year": 2009,
        "grade": "7.94 CGPA",
        "tier": "tier_3"
      }
    ],
    "skills": [
      {
        "name": "Agile",
        "proficiency": "beginner",
        "endorsements": 1,
        "duration_months": 9
      },
      {
        "name": "Scrum",
        "proficiency": "intermediate",
        "endorsements": 11,
        "duration_months": 28
      },
      {
        "name": "SAP",
        "proficiency": "intermediate",
        "endorsements": 6,
        "duration_months": 35
      },
      {
        "name": "React",
        "proficiency": "beginner",
        "endorsements": 7,
        "duration_months": 7
      },
      {
        "name": "Azure",
        "proficiency": "intermediate",
        "endorsements": 3,
        "duration_months": 36
      },
      {
        "name": "ETL",
        "proficiency": "beginner",
        "endorsements": 2,
        "duration_months": 8
      }
    ],
    "certifications": [],
    "languages": [
      {
        "language": "English",
        "proficiency": "professional"
      },
      {
        "language": "Hindi",
        "proficiency": "conversational"
      }
    ],
    "redrob_signals": {
      "profile_completeness_score": 74.8,
      "signup_date": "2023-02-12",
      "last_active_date": "2026-02-20",
      "open_to_work_flag": false,
      "profile_views_received_30d": 80,
      "applications_submitted_30d": 6,
      "recruiter_response_rate": 0.41,
      "avg_response_time_hours": 209.8,
      "skill_assessment_scores": {},
      "connection_count": 301,
      "endorsements_received": 29,
      "notice_period_days": 30,
      "expected_salary_range_inr_lpa": {
        "min": 7.6,
        "max": 28.0
      },
      "preferred_work_mode": "remote",
      "willing_to_relocate": true,
      "github_activity_score": 20.9,
      "search_appearance_30d": 166,
      "saved_by_recruiters_30d": 7,
      "interview_completion_rate": 0.4,
      "offer_acceptance_rate": 0.34,
      "verified_email": true,
      "verified_phone": true,
      "linkedin_connected": true
    }
  },
  {
    "candidate_id": "CAND_0000047",
    "profile": {
      "anonymized_name": "Avni Bansal",
      "headline": "Project Manager | Helping teams scale",
      "summary": "Professional with 2.4+ years of experience. My professional background is in marketing manager \u2014 I've built and led teams, owned KPIs, and driven business outcomes in this domain. Lately I've been curious about how AI tools could augment my work \u2014 I've experimented with ChatGPT and a few other tools for productivity and content creation, and I think the space is exciting. Open to roles where I can apply my domain expertise alongside emerging AI capabilities.",
      "location": "Kochi, Kerala",
      "country": "India",
      "years_of_experience": 2.4,
      "current_title": "Project Manager",
      "current_company": "TCS",
      "current_company_size": "10001+",
      "current_industry": "IT Services"
    },
    "career_history": [
      {
        "company": "TCS",
        "title": "Project Manager",
        "start_date": "2024-02-07",
        "end_date": null,
        "duration_months": 28,
        "is_current": true,
        "industry": "IT Services",
        "company_size": "10001+",
        "description": "Operations management role at a logistics company. Owned daily fulfillment operations across 3 warehouses, managing a team of 80 across receiving, picking, packing, and outbound. Built and tracked the operational KPIs (on-time fulfillment, accuracy, cost per order) and led the continuous improvement initiatives that drove a 22% productivity gain over 18 months."
      }
    ],
    "education": [
      {
        "institution": "Amity University",
        "degree": "B.Sc",
        "field_of_study": "Mechanical Engineering",
        "start_year": 2011,
        "end_year": 2016,
        "grade": "7.18 CGPA",
        "tier": "tier_3"
      }
    ],
    "skills": [
      {
        "name": "FastAPI",
        "proficiency": "beginner",
        "endorsements": 8,
        "duration_months": 4
      },
      {
        "name": "Java",
        "proficiency": "intermediate",
        "endorsements": 5,
        "duration_months": 28
      },
      {
        "name": "Excel",
        "proficiency": "intermediate",
        "endorsements": 10,
        "duration_months": 9
      },
      {
        "name": "Tally",
        "proficiency": "intermediate",
        "endorsements": 10,
        "duration_months": 9
      },
      {
        "name": "SQL",
        "proficiency": "intermediate",
        "endorsements": 11,
        "duration_months": 15
      },
      {
        "name": "Scrum",
        "proficiency": "intermediate",
        "endorsements": 1,
        "duration_months": 13
      },
      {
        "name": "Hadoop",
        "proficiency": "beginner",
        "endorsements": 10,
        "duration_months": 17
      }
    ],
    "certifications": [],
    "languages": [
      {
        "language": "English",
        "proficiency": "native"
      },
      {
        "language": "Hindi",
        "proficiency": "conversational"
      }
    ],
    "redrob_signals": {
      "profile_completeness_score": 79.7,
      "signup_date": "2025-06-07",
      "last_active_date": "2026-03-22",
      "open_to_work_flag": false,
      "profile_views_received_30d": 34,
      "applications_submitted_30d": 5,
      "recruiter_response_rate": 0.39,
      "avg_response_time_hours": 109.1,
      "skill_assessment_scores": {},
      "connection_count": 444,
      "endorsements_received": 48,
      "notice_period_days": 90,
      "expected_salary_range_inr_lpa": {
        "min": 13.3,
        "max": 19.2
      },
      "preferred_work_mode": "remote",
      "willing_to_relocate": false,
      "github_activity_score": -1,
      "search_appearance_30d": 14,
      "saved_by_recruiters_30d": 4,
      "interview_completion_rate": 0.54,
      "offer_acceptance_rate": 0.21,
      "verified_email": true,
      "verified_phone": true,
      "linkedin_connected": false
    }
  },
  {
    "candidate_id": "CAND_0000048",
    "profile": {
      "anonymized_name": "Vihaan Saxena",
      "headline": "Mobile Developer | Full-stack development",
      "summary": "Software engineer with 9.7 years of experience across web, backend, and cloud systems. Strong fundamentals in software development and system design. I've worked across web frontends, REST APIs, and cloud deployments; comfortable in most parts of a typical SaaS stack. I've been keeping up with AI/ML at a self-learner level \u2014 taken some online courses, played with the OpenAI and Anthropic APIs, built a small RAG side project \u2014 but I haven't done it in a professional capacity yet. Open to roles where I can either deepen my software engineering work or, if the team is open to it, start contributing to ML-adjacent systems.",
      "location": "Hyderabad, Telangana",
      "country": "India",
      "years_of_experience": 9.7,
      "current_title": "Mobile Developer",
      "current_company": "CRED",
      "current_company_size": "1001-5000",
      "current_industry": "Fintech"
    },
    "career_history": [
      {
        "company": "CRED",
        "title": "Mobile Developer",
        "start_date": "2024-02-07",
        "end_date": null,
        "duration_months": 28,
        "is_current": true,
        "industry": "Fintech",
        "company_size": "1001-5000",
        "description": "Frontend engineering at a media company. React, TypeScript, and the typical surrounding tooling (Webpack, Jest, Cypress). Built the company's design system from scratch and led the migration from a legacy AngularJS app. Strong on the frontend craft \u2014 accessibility, performance, animations \u2014 but limited backend exposure."
      },
      {
        "company": "Cognizant",
        "title": "Full Stack Developer",
        "start_date": "2022-06-17",
        "end_date": "2024-02-07",
        "duration_months": 20,
        "is_current": false,
        "industry": "IT Services",
        "company_size": "10001+",
        "description": "Android mobile development using Java and (more recently) Kotlin at a consumer-app company. Built and maintained multiple production features including the main shopping flow, push notification system, and the offline-first sync layer. Comfortable with the Android framework, Jetpack components, and the typical patterns (MVVM, Hilt, Coroutines). My career has been entirely on mobile so far; interested in expanding into broader backend or platform engineering."
      },
      {
        "company": "Stark Industries",
        "title": "Mobile Developer",
        "start_date": "2018-02-08",
        "end_date": "2022-04-18",
        "duration_months": 51,
        "is_current": false,
        "industry": "Manufacturing",
        "company_size": "1001-5000",
        "description": "Java backend development at a large enterprise \u2014 Spring Boot microservices, Kafka for inter-service messaging, Postgres + Redis for storage. Worked on the customer onboarding flow which involved orchestrating multiple downstream services. Solid on the Spring ecosystem, transaction handling, and the operational side of Java services. Looking to either go deeper on distributed systems or expand into modern application stacks."
      },
      {
        "company": "Initech",
        "title": "Full Stack Developer",
        "start_date": "2016-11-15",
        "end_date": "2018-02-08",
        "duration_months": 15,
        "is_current": false,
        "industry": "Software",
        "company_size": "51-200",
        "description": "Android mobile development using Java and (more recently) Kotlin at a consumer-app company. Built and maintained multiple production features including the main shopping flow, push notification system, and the offline-first sync layer. Comfortable with the Android framework, Jetpack components, and the typical patterns (MVVM, Hilt, Coroutines). My career has been entirely on mobile so far; interested in expanding into broader backend or platform engineering."
      }
    ],
    "education": [
      {
        "institution": "VIT Chennai",
        "degree": "B.E.",
        "field_of_study": "Data Science",
        "start_year": 2005,
        "end_year": 2009,
        "grade": "84%",
        "tier": "tier_3"
      },
      {
        "institution": "Anna University",
        "degree": "B.Tech",
        "field_of_study": "Statistics",
        "start_year": 2011,
        "end_year": 2016,
        "grade": "6.96 CGPA",
        "tier": "tier_2"
      }
    ],
    "skills": [
      {
        "name": "Hadoop",
        "proficiency": "beginner",
        "endorsements": 2,
        "duration_months": 15
      },
      {
        "name": "Terraform",
        "proficiency": "intermediate",
        "endorsements": 13,
        "duration_months": 26
      },
      {
        "name": "Vue.js",
        "proficiency": "intermediate",
        "endorsements": 2,
        "duration_months": 24
      },
      {
        "name": "Content Writing",
        "proficiency": "intermediate",
        "endorsements": 11,
        "duration_months": 26
      },
      {
        "name": "AWS",
        "proficiency": "intermediate",
        "endorsements": 1,
        "duration_months": 31
      }
    ],
    "certifications": [
      {
        "name": "Scrum Master Certified",
        "issuer": "Scrum Alliance",
        "year": 2023
      },
      {
        "name": "Six Sigma Green Belt",
        "issuer": "ASQ",
        "year": 2024
      }
    ],
    "languages": [
      {
        "language": "English",
        "proficiency": "native"
      },
      {
        "language": "Hindi",
        "proficiency": "conversational"
      }
    ],
    "redrob_signals": {
      "profile_completeness_score": 62.2,
      "signup_date": "2026-03-28",
      "last_active_date": "2026-04-06",
      "open_to_work_flag": true,
      "profile_views_received_30d": 58,
      "applications_submitted_30d": 3,
      "recruiter_response_rate": 0.65,
      "avg_response_time_hours": 97.9,
      "skill_assessment_scores": {},
      "connection_count": 225,
      "endorsements_received": 48,
      "notice_period_days": 120,
      "expected_salary_range_inr_lpa": {
        "min": 12.6,
        "max": 26.6
      },
      "preferred_work_mode": "flexible",
      "willing_to_relocate": false,
      "github_activity_score": -1,
      "search_appearance_30d": 131,
      "saved_by_recruiters_30d": 5,
      "interview_completion_rate": 0.42,
      "offer_acceptance_rate": 0.4,
      "verified_email": false,
      "verified_phone": true,
      "linkedin_connected": false
    }
  },
  {
    "candidate_id": "CAND_0000049",
    "profile": {
      "anonymized_name": "Tanya Chowdary",
      "headline": "Mechanical Engineer | Helping teams scale",
      "summary": "Professional with 11.8+ years of experience. I've spent my career in marketing manager roles, mostly focused on driving outcomes through process, people, and customer relationships. Lately I've been curious about how AI tools could augment my work \u2014 I've experimented with ChatGPT and a few other tools for productivity and content creation, and I think the space is exciting. Open to roles where I can apply my domain expertise alongside emerging AI capabilities.",
      "location": "Berlin",
      "country": "Germany",
      "years_of_experience": 11.8,
      "current_title": "Mechanical Engineer",
      "current_company": "Wayne Enterprises",
      "current_company_size": "10001+",
      "current_industry": "Conglomerate"
    },
    "career_history": [
      {
        "company": "Wayne Enterprises",
        "title": "Mechanical Engineer",
        "start_date": "2022-05-18",
        "end_date": null,
        "duration_months": 49,
        "is_current": true,
        "industry": "Conglomerate",
        "company_size": "10001+",
        "description": "Enterprise sales of cloud software solutions into the mid-market segment. Carried a $1.8M ARR quota and consistently delivered against it across the last three years. Owned the full sales cycle: prospecting, discovery, technical evaluation (with SE support), commercial negotiation, and close. Strong on consultative selling for technical buyers; comfortable engaging with both engineering and finance stakeholders."
      },
      {
        "company": "Hooli",
        "title": "Business Analyst",
        "start_date": "2017-11-10",
        "end_date": "2022-04-18",
        "duration_months": 54,
        "is_current": false,
        "industry": "Software",
        "company_size": "1001-5000",
        "description": "Senior accounting role at a mid-sized company \u2014 month-end close, financial reporting, statutory compliance (GAAP / Ind-AS), and tax filings. Owned the GL, fixed-asset register, and the audit-readiness function. Managed a team of 3 staff accountants. Built strong process discipline around the close cycle, reducing close time from 12 days to 7 over the last two years."
      },
      {
        "company": "Wayne Enterprises",
        "title": "Sales Executive",
        "start_date": "2014-09-27",
        "end_date": "2017-11-10",
        "duration_months": 38,
        "is_current": false,
        "industry": "Conglomerate",
        "company_size": "10001+",
        "description": "Operations management role at a logistics company. Owned daily fulfillment operations across 3 warehouses, managing a team of 80 across receiving, picking, packing, and outbound. Built and tracked the operational KPIs (on-time fulfillment, accuracy, cost per order) and led the continuous improvement initiatives that drove a 22% productivity gain over 18 months."
      }
    ],
    "education": [
      {
        "institution": "Symbiosis International",
        "degree": "M.Tech",
        "field_of_study": "Mathematics",
        "start_year": 2016,
        "end_year": 2019,
        "grade": "7.32 CGPA",
        "tier": "tier_3"
      }
    ],
    "skills": [
      {
        "name": "TypeScript",
        "proficiency": "beginner",
        "endorsements": 0,
        "duration_months": 8
      },
      {
        "name": "Rust",
        "proficiency": "intermediate",
        "endorsements": 1,
        "duration_months": 16
      },
      {
        "name": "Data Pipelines",
        "proficiency": "beginner",
        "endorsements": 6,
        "duration_months": 11
      },
      {
        "name": "Apache Beam",
        "proficiency": "beginner",
        "endorsements": 10,
        "duration_months": 4
      },
      {
        "name": "GraphQL",
        "proficiency": "intermediate",
        "endorsements": 14,
        "duration_months": 16
      },
      {
        "name": "Kubernetes",
        "proficiency": "intermediate",
        "endorsements": 5,
        "duration_months": 13
      }
    ],
    "certifications": [],
    "languages": [
      {
        "language": "English",
        "proficiency": "native"
      },
      {
        "language": "Hindi",
        "proficiency": "professional"
      }
    ],
    "redrob_signals": {
      "profile_completeness_score": 64.0,
      "signup_date": "2025-09-12",
      "last_active_date": "2026-05-13",
      "open_to_work_flag": false,
      "profile_views_received_30d": 6,
      "applications_submitted_30d": 2,
      "recruiter_response_rate": 0.59,
      "avg_response_time_hours": 109.3,
      "skill_assessment_scores": {},
      "connection_count": 514,
      "endorsements_received": 12,
      "notice_period_days": 120,
      "expected_salary_range_inr_lpa": {
        "min": 12.9,
        "max": 18.8
      },
      "preferred_work_mode": "onsite",
      "willing_to_relocate": false,
      "github_activity_score": -1,
      "search_appearance_30d": 100,
      "saved_by_recruiters_30d": 6,
      "interview_completion_rate": 0.56,
      "offer_acceptance_rate": -1,
      "verified_email": true,
      "verified_phone": false,
      "linkedin_connected": true
    }
  },
  {
    "candidate_id": "CAND_0000050",
    "profile": {
      "anonymized_name": "Naina Bose",
      "headline": "Business Analyst | Helping teams scale",
      "summary": "Professional with 13.5+ years of experience. I'm a marketing manager with substantial experience in cross-functional collaboration, stakeholder management, and execution. Lately I've been curious about how AI tools could augment my work \u2014 I've experimented with ChatGPT and a few other tools for productivity and content creation, and I think the space is exciting. Open to roles where I can apply my domain expertise alongside emerging AI capabilities.",
      "location": "Gurgaon, Haryana",
      "country": "India",
      "years_of_experience": 13.5,
      "current_title": "Business Analyst",
      "current_company": "Infosys",
      "current_company_size": "10001+",
      "current_industry": "IT Services"
    },
    "career_history": [
      {
        "company": "Infosys",
        "title": "Business Analyst",
        "start_date": "2022-09-15",
        "end_date": null,
        "duration_months": 45,
        "is_current": true,
        "industry": "IT Services",
        "company_size": "10001+",
        "description": "Mechanical engineering design role at a hardware-product company. Led the design of two product subsystems through full lifecycle: concept, DFM/DFMA review, prototype, production tooling. Comfortable with CAD (SolidWorks, Creo), FEA (ANSYS), and the typical hardware-development cadence. Worked closely with manufacturing partners on production scale-up."
      },
      {
        "company": "TCS",
        "title": "Marketing Manager",
        "start_date": "2019-08-02",
        "end_date": "2022-07-17",
        "duration_months": 36,
        "is_current": false,
        "industry": "IT Services",
        "company_size": "10001+",
        "description": "Operations management role at a logistics company. Owned daily fulfillment operations across 3 warehouses, managing a team of 80 across receiving, picking, packing, and outbound. Built and tracked the operational KPIs (on-time fulfillment, accuracy, cost per order) and led the continuous improvement initiatives that drove a 22% productivity gain over 18 months."
      },
      {
        "company": "Hooli",
        "title": "HR Manager",
        "start_date": "2017-03-15",
        "end_date": "2019-07-03",
        "duration_months": 28,
        "is_current": false,
        "industry": "Software",
        "company_size": "1001-5000",
        "description": "Senior accounting role at a mid-sized company \u2014 month-end close, financial reporting, statutory compliance (GAAP / Ind-AS), and tax filings. Owned the GL, fixed-asset register, and the audit-readiness function. Managed a team of 3 staff accountants. Built strong process discipline around the close cycle, reducing close time from 12 days to 7 over the last two years."
      },
      {
        "company": "Acme Corp",
        "title": "Content Writer",
        "start_date": "2012-12-22",
        "end_date": "2017-03-01",
        "duration_months": 51,
        "is_current": false,
        "industry": "Manufacturing",
        "company_size": "201-500",
        "description": "Senior accounting role at a mid-sized company \u2014 month-end close, financial reporting, statutory compliance (GAAP / Ind-AS), and tax filings. Owned the GL, fixed-asset register, and the audit-readiness function. Managed a team of 3 staff accountants. Built strong process discipline around the close cycle, reducing close time from 12 days to 7 over the last two years."
      }
    ],
    "education": [
      {
        "institution": "VIT Chennai",
        "degree": "Ph.D",
        "field_of_study": "Artificial Intelligence",
        "start_year": 2001,
        "end_year": 2005,
        "grade": "6.66 CGPA",
        "tier": "tier_3"
      },
      {
        "institution": "Georgia Tech",
        "degree": "B.Sc",
        "field_of_study": "Artificial Intelligence",
        "start_year": 2013,
        "end_year": 2017,
        "grade": "7.81 CGPA",
        "tier": "tier_1"
      }
    ],
    "skills": [
      {
        "name": "gRPC",
        "proficiency": "intermediate",
        "endorsements": 9,
        "duration_months": 11
      },
      {
        "name": "SEO",
        "proficiency": "beginner",
        "endorsements": 8,
        "duration_months": 18
      },
      {
        "name": "Feature Engineering",
        "proficiency": "advanced",
        "endorsements": 4,
        "duration_months": 42
      },
      {
        "name": "Marketing",
        "proficiency": "beginner",
        "endorsements": 0,
        "duration_months": 15
      },
      {
        "name": "Data Pipelines",
        "proficiency": "beginner",
        "endorsements": 0,
        "duration_months": 15
      },
      {
        "name": "Kafka",
        "proficiency": "beginner",
        "endorsements": 7,
        "duration_months": 13
      },
      {
        "name": "Excel",
        "proficiency": "intermediate",
        "endorsements": 10,
        "duration_months": 23
      }
    ],
    "certifications": [],
    "languages": [
      {
        "language": "English",
        "proficiency": "professional"
      },
      {
        "language": "Hindi",
        "proficiency": "conversational"
      }
    ],
    "redrob_signals": {
      "profile_completeness_score": 42.5,
      "signup_date": "2023-01-23",
      "last_active_date": "2025-10-22",
      "open_to_work_flag": false,
      "profile_views_received_30d": 34,
      "applications_submitted_30d": 2,
      "recruiter_response_rate": 0.42,
      "avg_response_time_hours": 108.7,
      "skill_assessment_scores": {
        "Feature Engineering": 60.8
      },
      "connection_count": 245,
      "endorsements_received": 22,
      "notice_period_days": 90,
      "expected_salary_range_inr_lpa": {
        "min": 7.6,
        "max": 22.9
      },
      "preferred_work_mode": "onsite",
      "willing_to_relocate": false,
      "github_activity_score": 44.7,
      "search_appearance_30d": 87,
      "saved_by_recruiters_30d": 2,
      "interview_completion_rate": 0.58,
      "offer_acceptance_rate": -1,
      "verified_email": true,
      "verified_phone": true,
      "linkedin_connected": false
    }
  }
]
```


# sample_submission.csv

```csv
candidate_id,rank,score,reasoning
CAND_0004989,1,0.9920,HR Manager with 6.1 yrs; 9 AI core skills; response rate 0.76.
CAND_0001195,2,0.9840,HR Manager with 8.7 yrs; 9 AI core skills; response rate 0.20.
CAND_0003114,3,0.9760,ML Engineer with 6.4 yrs; 4 AI core skills; response rate 0.88.
CAND_0000339,4,0.9680,Content Writer with 8.3 yrs; 8 AI core skills; response rate 0.72.
CAND_0001082,5,0.9600,HR Manager with 5.0 yrs; 8 AI core skills; response rate 0.62.
CAND_0001218,6,0.9520,Graphic Designer with 10.4 yrs; 9 AI core skills; response rate 0.56.
CAND_0004558,7,0.9440,Business Analyst with 5.1 yrs; 8 AI core skills; response rate 0.54.
CAND_0001753,8,0.9360,Content Writer with 8.3 yrs; 8 AI core skills; response rate 0.53.
CAND_0001503,9,0.9280,Marketing Manager with 8.0 yrs; 8 AI core skills; response rate 0.32.
CAND_0004548,10,0.9200,HR Manager with 7.3 yrs; 8 AI core skills; response rate 0.30.
CAND_0002164,11,0.9120,Marketing Manager with 13.2 yrs; 9 AI core skills; response rate 0.24.
CAND_0001154,12,0.9040,Mechanical Engineer with 6.9 yrs; 8 AI core skills; response rate 0.18.
CAND_0002622,13,0.8960,Accountant with 14.2 yrs; 9 AI core skills; response rate 0.18.
CAND_0000002,14,0.8880,Civil Engineer with 8.0 yrs; 8 AI core skills; response rate 0.15.
CAND_0000718,15,0.8800,Accountant with 8.2 yrs; 8 AI core skills; response rate 0.15.
CAND_0004224,16,0.8720,Graphic Designer with 5.0 yrs; 8 AI core skills; response rate 0.11.
CAND_0000239,17,0.8640,Project Manager with 5.0 yrs; 8 AI core skills; response rate 0.10.
CAND_0001771,18,0.8560,Accountant with 7.4 yrs; 8 AI core skills; response rate 0.06.
CAND_0002782,19,0.8480,Sales Executive with 7.8 yrs; 8 AI core skills; response rate 0.06.
CAND_0003693,20,0.8400,Sales Executive with 7.2 yrs; 7 AI core skills; response rate 0.77.
CAND_0004937,21,0.8320,Operations Manager with 13.5 yrs; 8 AI core skills; response rate 0.77.
CAND_0001397,22,0.8240,Business Analyst with 11.3 yrs; 8 AI core skills; response rate 0.76.
CAND_0001381,23,0.8160,Accountant with 14.1 yrs; 8 AI core skills; response rate 0.75.
CAND_0004201,24,0.8080,Mechanical Engineer with 13.7 yrs; 8 AI core skills; response rate 0.75.
CAND_0002019,25,0.8000,Marketing Manager with 2.0 yrs; 8 AI core skills; response rate 0.73.
CAND_0004645,26,0.7920,Project Manager with 10.2 yrs; 8 AI core skills; response rate 0.71.
CAND_0004824,27,0.7840,AI Engineer with 6.1 yrs; 3 AI core skills; response rate 0.71.
CAND_0002592,28,0.7760,Business Analyst with 11.4 yrs; 8 AI core skills; response rate 0.65.
CAND_0001586,29,0.7680,Operations Manager with 6.5 yrs; 7 AI core skills; response rate 0.60.
CAND_0001653,30,0.7600,Mechanical Engineer with 4.5 yrs; 8 AI core skills; response rate 0.59.
CAND_0000007,31,0.7520,AI Engineer with 6.6 yrs; 3 AI core skills; response rate 0.57.
CAND_0001795,32,0.7440,Mechanical Engineer with 4.4 yrs; 8 AI core skills; response rate 0.57.
CAND_0003531,33,0.7360,Operations Manager with 3.2 yrs; 8 AI core skills; response rate 0.55.
CAND_0002989,34,0.7280,Graphic Designer with 6.0 yrs; 7 AI core skills; response rate 0.54.
CAND_0000581,35,0.7200,HR Manager with 8.5 yrs; 7 AI core skills; response rate 0.53.
CAND_0004680,36,0.7120,Mechanical Engineer with 8.0 yrs; 7 AI core skills; response rate 0.53.
CAND_0001257,37,0.7040,Mechanical Engineer with 6.9 yrs; 7 AI core skills; response rate 0.52.
CAND_0002018,38,0.6960,Civil Engineer with 6.4 yrs; 7 AI core skills; response rate 0.52.
CAND_0004952,39,0.6880,Project Manager with 6.5 yrs; 7 AI core skills; response rate 0.52.
CAND_0001378,40,0.6800,Project Manager with 5.6 yrs; 7 AI core skills; response rate 0.51.
CAND_0000164,41,0.6720,Business Analyst with 3.0 yrs; 8 AI core skills; response rate 0.50.
CAND_0003406,42,0.6640,Graphic Designer with 6.0 yrs; 7 AI core skills; response rate 0.44.
CAND_0000557,43,0.6560,Civil Engineer with 14.3 yrs; 8 AI core skills; response rate 0.43.
CAND_0003107,44,0.6480,Customer Support with 6.6 yrs; 7 AI core skills; response rate 0.41.
CAND_0000168,45,0.6400,Marketing Manager with 6.3 yrs; 7 AI core skills; response rate 0.39.
CAND_0000268,46,0.6320,Accountant with 3.7 yrs; 8 AI core skills; response rate 0.39.
CAND_0000791,47,0.6240,Customer Support with 11.5 yrs; 8 AI core skills; response rate 0.39.
CAND_0003050,48,0.6160,ML Engineer with 6.0 yrs; 3 AI core skills; response rate 0.38.
CAND_0003241,49,0.6080,ML Engineer with 3.6 yrs; 4 AI core skills; response rate 0.36.
CAND_0000776,50,0.6000,Operations Manager with 14.2 yrs; 8 AI core skills; response rate 0.35.
CAND_0002234,51,0.5920,Content Writer with 9.9 yrs; 8 AI core skills; response rate 0.35.
CAND_0004217,52,0.5840,Accountant with 1.8 yrs; 8 AI core skills; response rate 0.33.
CAND_0003702,53,0.5760,Graphic Designer with 6.9 yrs; 7 AI core skills; response rate 0.26.
CAND_0004154,54,0.5680,HR Manager with 6.2 yrs; 7 AI core skills; response rate 0.26.
CAND_0000542,55,0.5600,Mechanical Engineer with 8.5 yrs; 7 AI core skills; response rate 0.25.
CAND_0002466,56,0.5520,Marketing Manager with 14.6 yrs; 8 AI core skills; response rate 0.25.
CAND_0002974,57,0.5440,Operations Manager with 13.4 yrs; 8 AI core skills; response rate 0.25.
CAND_0000450,58,0.5360,Operations Manager with 7.7 yrs; 7 AI core skills; response rate 0.24.
CAND_0002438,59,0.5280,Accountant with 1.0 yrs; 8 AI core skills; response rate 0.24.
CAND_0000217,60,0.5200,Sales Executive with 11.4 yrs; 8 AI core skills; response rate 0.23.
CAND_0001424,61,0.5120,Content Writer with 13.6 yrs; 8 AI core skills; response rate 0.22.
CAND_0004711,62,0.5040,Content Writer with 14.2 yrs; 8 AI core skills; response rate 0.22.
CAND_0001294,63,0.4960,HR Manager with 3.0 yrs; 8 AI core skills; response rate 0.21.
CAND_0001724,64,0.4880,Mechanical Engineer with 7.4 yrs; 7 AI core skills; response rate 0.20.
CAND_0002794,65,0.4800,Project Manager with 13.9 yrs; 8 AI core skills; response rate 0.20.
CAND_0001292,66,0.4720,Customer Support with 7.6 yrs; 7 AI core skills; response rate 0.16.
CAND_0004655,67,0.4640,Mechanical Engineer with 4.4 yrs; 8 AI core skills; response rate 0.16.
CAND_0004133,68,0.4560,Sales Executive with 8.5 yrs; 7 AI core skills; response rate 0.14.
CAND_0000958,69,0.4480,Business Analyst with 4.3 yrs; 8 AI core skills; response rate 0.13.
CAND_0003259,70,0.4400,Project Manager with 5.3 yrs; 7 AI core skills; response rate 0.13.
CAND_0004851,71,0.4320,HR Manager with 6.3 yrs; 7 AI core skills; response rate 0.12.
CAND_0002626,72,0.4240,Operations Manager with 11.0 yrs; 8 AI core skills; response rate 0.11.
CAND_0004410,73,0.4160,Marketing Manager with 11.6 yrs; 8 AI core skills; response rate 0.07.
CAND_0003477,74,0.4080,Junior ML Engineer with 6.9 yrs; 2 AI core skills; response rate 0.86.
CAND_0000799,75,0.4000,Senior Machine Learning Engineer with 6.3 yrs; 6 AI core skills; response rate 0.83.
CAND_0003242,76,0.3920,Project Manager with 13.9 yrs; 7 AI core skills; response rate 0.77.
CAND_0003846,77,0.3840,Content Writer with 8.2 yrs; 6 AI core skills; response rate 0.77.
CAND_0000459,78,0.3760,HR Manager with 1.9 yrs; 7 AI core skills; response rate 0.76.
CAND_0004223,79,0.3680,Civil Engineer with 5.6 yrs; 6 AI core skills; response rate 0.76.
CAND_0004640,80,0.3600,Civil Engineer with 11.2 yrs; 7 AI core skills; response rate 0.76.
CAND_0000251,81,0.3520,HR Manager with 12.6 yrs; 7 AI core skills; response rate 0.75.
CAND_0002255,82,0.3440,Accountant with 3.0 yrs; 7 AI core skills; response rate 0.73.
CAND_0003638,83,0.3360,Sales Executive with 13.3 yrs; 7 AI core skills; response rate 0.73.
CAND_0003002,84,0.3280,Project Manager with 11.0 yrs; 7 AI core skills; response rate 0.71.
CAND_0002880,85,0.3200,Mechanical Engineer with 11.9 yrs; 7 AI core skills; response rate 0.70.
CAND_0000084,86,0.3120,Sales Executive with 12.4 yrs; 7 AI core skills; response rate 0.69.
CAND_0003300,87,0.3040,Graphic Designer with 6.2 yrs; 6 AI core skills; response rate 0.69.
CAND_0000699,88,0.2960,Graphic Designer with 11.7 yrs; 7 AI core skills; response rate 0.68.
CAND_0002446,89,0.2880,Customer Support with 10.2 yrs; 7 AI core skills; response rate 0.67.
CAND_0003918,90,0.2800,Marketing Manager with 4.3 yrs; 7 AI core skills; response rate 0.66.
CAND_0002661,91,0.2720,Graphic Designer with 7.9 yrs; 6 AI core skills; response rate 0.65.
CAND_0000899,92,0.2640,Sales Executive with 10.2 yrs; 7 AI core skills; response rate 0.64.
CAND_0001550,93,0.2560,Mechanical Engineer with 2.4 yrs; 7 AI core skills; response rate 0.64.
CAND_0002317,94,0.2480,Content Writer with 7.2 yrs; 6 AI core skills; response rate 0.62.
CAND_0002720,95,0.2400,Civil Engineer with 7.4 yrs; 6 AI core skills; response rate 0.61.
CAND_0001355,96,0.2320,Civil Engineer with 12.9 yrs; 7 AI core skills; response rate 0.59.
CAND_0001839,97,0.2240,Operations Manager with 8.2 yrs; 6 AI core skills; response rate 0.58.
CAND_0004366,98,0.2160,Accountant with 3.6 yrs; 7 AI core skills; response rate 0.58.
CAND_0001021,99,0.2080,Data Scientist with 3.1 yrs; 3 AI core skills; response rate 0.57.
CAND_0002689,100,0.2000,Content Writer with 14.7 yrs; 7 AI core skills; response rate 0.57.

```


# README.docx

Redrob Hackathon — Participant Bundle
Welcome to the Intelligent Candidate Discovery & Ranking Challenge.
What's in this bundle

Getting started
1. Read the docs (~30 minutes)
In this order:
job_description.md — understand what role you're ranking candidates for
submission_spec.md — understand the rules and evaluation pipeline
redrob_signals_doc.md — understand the trap candidates and signal envelopes
candidate_schema.json — understand the candidate data structure
Open sample_candidates.json and skim a few candidates to see what real data looks like
2. Unpack the candidate pool
gunzip -k candidates.jsonl.gz   # -k keeps the .gz; you get both files
wc -l candidates.jsonl          # should print 100000
Or load the gzipped file directly in Python:
import gzip, json
with gzip.open("candidates.jsonl.gz", "rt") as f:
    candidates = [json.loads(line) for line in f if line.strip()]
print(len(candidates))  # 100000
3. Build your ranker
Your job: produce a CSV with the top 100 candidates for the JD, ranked best-fit first, with a 1-2 sentence reasoning for each.
The format is described in submission_spec.md Section 2-3. The compute constraints are in Section 3 (5 min, 16 GB, CPU only, no network during ranking).
4. Validate before submitting
This catches format errors before you upload. The validator handles both .jsonl and gzipped .jsonl.gz files.
5. Submit
Submit via the portal. You'll be asked for:
The CSV file
All the metadata from submission_metadata_template.yaml (team name, GitHub repo, sandbox link, AI tools declaration, etc.)
See submission_spec.md Section 10 for the full list
Sandbox link is required — a working hosted environment (HuggingFace Spaces, Streamlit Cloud, Replit, Colab, Docker, or Binder) where your ranker can be run on a small sample. See Section 10.5 for what counts as a valid sandbox.
Key things to know
No live leaderboard. Scores are revealed only after submissions close. There is no feedback during the competition.
Three submissions max. Your last valid submission counts.
AI tools are allowed. Declare them honestly. The evaluation is designed so that AI-assisted work where you did real engineering succeeds, while AI-only submissions fail at Stages 3-5.
The dataset contains traps. Keyword stuffers, plain-language Tier 5s, behavioral twins, and ~80 honeypots with subtly impossible profiles.Submissions with honeypot rate > 10% in top 100 are disqualified you. See redrob_signals_doc.md.
You will be interviewed if you reach the top X. Be prepared to walk through your architecture and defend your design choices.
Asking for help
If you find a bug in the bundle (e.g., schema doesn't match data, validator rejects valid format) please report it via the official hackathon support channel.
Good luck.


# job_description.docx

Job Description: Senior AI Engineer — Founding Team
Company: Redrob AI (Series A AI-native talent intelligence platform)
Location: Pune/Noida, India (Hybrid — flexible cadence) | Open to relocation candidates from Tier-1 Indian cities
Employment Type: Full-time
Experience Required: 5–9 years (see "what we mean by this" below)

Let's be honest about this role
We're going to write this JD differently from most. We're a Series A company that just raised our round and we're building a new AI Engineering org from scratch. This is the kind of role where the JD changes every six months because the company changes every six months. So instead of pretending we have a fixed checklist, we're going to tell you what we actually need and what we've gotten wrong before.
If you've spent your career at Google or Meta and you want a well-scoped role with a defined ladder, this isn't it.
If you've spent your career bouncing between early-stage startups and you want to "just code" without having to think about product or recruiter workflows or eval frameworks, this also isn't it.
We need someone who is simultaneously comfortable with two things that sound contradictory:
Deep technical depth in modern ML systems — embeddings, retrieval, ranking, LLMs, fine-tuning.
Scrappy product-engineering attitude — willing to ship a working ranker in a week even if the underlying ML is "obviously suboptimal," because we need to learn from real users before we know what to actually optimize for.
These are not contradictory in real life. They feel contradictory because of how engineering culture sorted itself into "researcher" vs "shipper" archetypes. We need both modes available in the same person, and we'd rather you tilt slightly toward shipper than toward researcher.

What you'd actually be doing
The high-level mandate: own the intelligence layer of Redrob's product. That means the ranking, retrieval, and matching systems that decide what recruiters see when they search for candidates and what candidates see when they search for roles.
In practical terms, your first 90 days will probably look like:
Weeks 1-3: Audit what we currently have (it's mostly BM25 + rule-based scoring, working but not great). Identify the 3-4 highest-leverage things to fix.
Weeks 4-8: Ship a v2 ranking system that demonstrably improves recruiter-engagement metrics. This will involve embeddings, hybrid retrieval, and probably some LLM-based re-ranking, but the architecture is your call.
Weeks 9-12: Set up the evaluation infrastructure — offline benchmarks, online A/B testing, recruiter-feedback loops — so we can keep improving without flying blind.
Beyond that, you'll be driving the long-term architecture of how we do candidate-JD matching at scale, mentoring the next round of hires (we're growing the team from 4 to 12 engineers in the next year), and working closely with our recruiter-experience PM on what to build.

What we mean by "5-9 years"
This is a range, not a requirement. Some people hit "senior engineer" judgment at 4 years; some never hit it after 15. We've used 5-9 because it's roughly where people we've hired into this kind of role have landed, but we'll seriously consider candidates outside the band if other signals are strong.
That said, here are the disqualifiers we actually apply:
If you've spent your career in pure research environments (academic labs, research-only roles) without any production deployment — we will not move forward. We are explicit about this. We've tried it twice and it didn't work for either side.
If your "AI experience" consists primarily of recent (under 12 months) projects using LangChain to call OpenAI — we will probably not move forward, unless you can demonstrate substantial pre-LLM-era ML production experience. We're looking for people who understood retrieval and ranking before it became fashionable.
If you are a senior engineer who hasn't written production code in the last 18 months because you've moved into "architecture" or "tech lead" roles — we will probably not move forward. This role writes code.

The skills inventory (please read carefully)
Most JDs list 20 skills and you're supposed to have all of them. We're going to do this differently.
Things you absolutely need
Production experience with embeddings-based retrieval systems (sentence-transformers, OpenAI embeddings, BGE, E5, or similar) deployed to real users. We don't care which model — we care that you've handled embedding drift, index refresh, retrieval-quality regression in production.
Production experience with vector databases or hybrid search infrastructure — Pinecone, Weaviate, Qdrant, Milvus, OpenSearch, Elasticsearch, FAISS, or something similar. Again, the specific tech doesn't matter; the operational experience does.
Strong Python. Yes really, we care about code quality.
Hands-on experience designing evaluation frameworks for ranking systems — NDCG, MRR, MAP, offline-to-online correlation, A/B test interpretation. If you've never thought about how to evaluate a ranking system rigorously, this role will be very painful.
Things we'd like you to have but won't reject you for
LLM fine-tuning experience (LoRA, QLoRA, PEFT)
Experience with learning-to-rank models (XGBoost-based or neural)
Prior exposure to HR-tech, recruiting tech, or marketplace products
Background in distributed systems or large-scale inference optimization
Open-source contributions in the AI/ML space
Things we explicitly do NOT want
This is the section most JDs skip but we think it's the most important:
Title-chasers. If your career trajectory shows you optimizing for "Senior" → "Staff" → "Principal" titles by switching companies every 1.5 years, we're not a fit. We need someone who plans to be here for 3+ years.
Framework enthusiasts. If your GitHub is full of LangChain tutorials and your blog posts are "How I used [hot framework] to build [demo]" — that's fine but it's not what we need. We need people who think about systems, not frameworks.
People who have only worked at consulting firms (TCS, Infosys, Wipro, Accenture, Cognizant, Capgemini, etc.) in their entire career. We've had bad fit experiences in both directions. If you're currently at one of these companies but have prior product-company experience, that's fine.
People whose primary expertise is computer vision, speech, or robotics without significant NLP/IR exposure. We respect your work but you'd be re-learning fundamentals here.
People whose work has been entirely on closed-source proprietary systems for 5+ years without external validation (papers, talks, open-source). We need to see how you think, not just trust that you can think.

On location, comp, and logistics
Location: Pune/Noida-preferred but flexible. We have offices in Noida and Pune(mostly used Tue/Thu). We don't require any specific number of in-office days but we expect quarterly travel for offsites. Candidates in Hyderabad, Pune, Mumbai, Delhi NCR welcome to apply. Outside India: case-by-case, but we don't sponsor work visas.
Notice period: We'd love sub-30-day notice. We can buy out up to 30 days. 30+ day notice candidates are still in scope but the bar gets higher.

The vibe check
We genuinely believe culture-fit matters more at this stage than skills-fit. Skills are teachable; the rest mostly isn't.
We work async-first and write a lot. If you find writing painful, you'll find this role painful.
We disagree openly and decide quickly. If you find that style abrasive, you'll find this role abrasive.
We move fast and break things, with the caveat that "things" are usually our internal assumptions, not user-facing systems. If you need a stable, mature codebase to be productive, you'll find this role unstable.

How to read between the lines
The "ideal candidate" we're imagining is roughly:
6-8 years total experience, of which 4-5 are in applied ML/AI roles at product companies (not pure services).
Has shipped at least one end-to-end ranking, search, or recommendation system to real users at meaningful scale.
Has strong opinions about retrieval (hybrid vs dense), evaluation (offline vs online), and LLM integration (when to fine-tune vs prompt) — and can defend them with reference to systems they actually built.
Located in or willing to relocate to Noida or Pune.
Active on Redrob platform (or has clear signal of being in the job market) so we can actually talk to them.
We are aware this is a narrow profile. We're not expecting to find many matches in a 100K candidate pool. We're explicitly OK with that — we'd rather see 10 great matches than 1000 maybes.

Final note for the participants of the Redrob hackathon
If you're reading this in the context of the Intelligent Candidate Discovery & Ranking Challenge:
The "right answer" to this JD is not "find candidates whose skills section contains the most AI keywords." That's a trap we've explicitly built into the dataset.
The right answer involves reasoning about the gap between what the JD says and what the JD means. A Tier 5 candidate may not use the words "RAG" or "Pinecone" in their profile, but if their career history shows they built a recommendation system at a product company, they're a fit. A candidate who has all the AI keywords listed as skills but whose title is "Marketing Manager" is not a fit, no matter how perfect their skill list looks.
Your ranking system should also weigh behavioral signals — a perfect-on-paper candidate who hasn't logged in for 6 months and has a 5% recruiter response rate is, for hiring purposes, not actually available. Down-weight them appropriately.
Good luck.


# redrob_signals_doc.docx

Redrob Behavioral Signals — Reference
This document explains the 23 behavioral signals embedded in each candidate's redrob_signals object, how they relate to candidate quality, and how they're constructed in the synthetic dataset.

What are Redrob signals?
In a real recruiting platform, candidates generate observable behavior beyond what they list in their profile:
Do they actually respond to recruiter messages?
Have they logged in recently?
Did they complete the assessments they started?
Are recruiters saving their profile?
Have they completed previous interview cycles?
These behavioral signals are often more predictive of whether a candidate can actually be hired than their static profile. A perfect-on-paper candidate who hasn't logged in for 6 months and has a 5% response rate is, for hiring purposes, not actually available.
This dataset includes these signals so that ranking systems can incorporate them as a multiplier or modifier on top of skill-match scoring.

The 23 signals



# submission_spec.docx

Submission Specification — Redrob Hackathon v4
Read this carefully before submitting. Submissions that don't match this spec will be auto-rejected by the validator without scoring.

1. What you're submitting
A CSV file ranking the top 100 candidates from candidates.jsonl for the released job description.
Rank 1 is the best fit; rank 100 is the 100th best fit.
You do not rank candidates 101 onward — only the top 100.

2. File format
Filename
Your team's registered participant ID, with .csv extension. For example: team_xxx.csv.
Encoding
UTF-8.
Required columns (in this order)
candidate_id,rank,score,reasoning

Example
candidate_id,rank,score,reasoning
CAND_0042871,1,0.987,"Senior AI Engineer with 7 years building RAG systems at product companies; strong recent engagement and Bangalore-based."
CAND_0019884,2,0.973,"6 years applied ML; previously shipped vector search at scale; matches the 'product over research' profile in the JD."
CAND_0091235,3,0.962,"Strong NLP + retrieval background; some concern on notice period (120 days) but otherwise strong fit."
...
CAND_0007729,100,0.412,"Adjacent skills only — likely below cutoff but included as final filler given experience and engagement signals."

3. Rules
Format
Exactly 100 rows of data (plus 1 header row).
Each rank (1 through 100) appears exactly once.
Each candidate_id appears exactly once.
Every candidate_id must exist in the released candidates.jsonl.
score is non-increasing with rank — i.e., score at rank 1 ≥ score at rank 2 ≥ ... ≥ score at rank 100. Ties are allowed.
If two candidates have the same score, you must still assign unique ranks. Break score ties deterministically using a secondary signal from your model, or by candidate_id ascending.
Compute constraints
Your code that produces the submission must satisfy the following constraints:

Why these constraints? This is a real-world recruiting system, not a benchmark. A system that calls GPT-4 or Claude per candidate cannot scale to a 200K candidate pool in production. We want systems that have thought about latency-quality tradeoffs.
In practice, running an LLM call for each of 100,000 candidates will not fit the 5-minute CPU budget, even if the model runs locally. Plan for a small ranker over precomputed features, indexes, or compact local models.
You CANNOT, during the ranking step:
Call hosted LLM APIs.
Use GPUs.
Exceed the runtime/memory limits.
Enforcement. At Stage 3, top-N submissions must provide their full code repository. Your ranking step will be reproduced inside a sandboxed Docker container matching these constraints exactly. If your submission cannot be reproduced within these limits, it is disqualified at Stage 3, regardless of your composite score. Make sure your code runs locally on a 16 GB CPU-only machine within 5 minutes before you submit.
Three-submission cap
You may make at most 3 submissions total during the competition window. Your final entry is your last valid submission. Earlier submissions are not preserved.
We've kept this number low intentionally — without a live leaderboard, multiple submissions have limited value, and a low cap reduces gaming.
Reasoning column
The reasoning column is optional but heavily recommended. Top N submissions are advanced to Stage 4 (manual review) where reasoning quality is part of the evaluation.
At Stage 4, we sample 10 random rows from your submission and check each reasoning entry against the following:

What's penalized:
Empty reasoning
All-identical reasoning strings
Templated reasoning that just inserts the candidate's name
Reasoning that mentions skills not in the candidate's profile (hallucination)
Reasoning that contradicts the rank
Plain-language reasoning that demonstrates you actually understood the candidate's profile will rank highly here. Don't try to be impressive; try to be specific and honest.

4. How submissions are scored
Metrics
Your top-100 ranking is scored against the hidden ground truth using these metrics:

Final composite
Final composite = 0.50 × NDCG@10 + 0.30 × NDCG@50 + 0.15 × MAP + 0.05 × P@10
Scoring happens once, after submissions close. There is no public partition, no live leaderboard, and no per-submission feedback during the competition. Your score is computed against the full hidden ground truth and is revealed only when final results are announced.
Tiebreaks
If two submissions have identical composites:
Higher P@5 wins.
Higher P@10 wins.
Earlier submission timestamp wins.

5. Evaluation pipeline (stages)
Your submission flows through these stages:

Note on AI tool usage: You are allowed to use AI tools (Claude, GPT-4, etc.) as part of your development workflow. We expect many participants will. The evaluation is designed so that AI-assisted submissions where the human did real engineering work will succeed, while submissions that are mostly LLM output with minimal human engineering will fail at Stages 3-5. The compute constraint, code repo check, and defend-your-work interview together filter for genuine engineering, not for absence of AI use.

6. Common rejections (we see these every hackathon)
99 rows or 101 rows instead of exactly 100.
Ranks starting at 0 instead of 1.
Duplicate candidate_ids.
candidate_id typos that don't exist in candidates.jsonl.
All scores set to the same value (model isn't differentiating).
Scores increasing as rank increases (rank 1 has lowest score).
Submission file submitted as .xlsx or .json instead of .csv.
Double-check these locally before uploading — the server-side auto-validator rejects on any of them.

7. Honeypot warning
The dataset contains a small number (~80) of honeypot candidates with subtly impossible profiles (e.g., 8 years of experience at a company founded 3 years ago; "expert" proficiency in 10 skills with 0 years used). These are forced to relevance tier 0 in the ground truth.
If your submission ranks honeypots in the top 10, this is a strong signal that your system isn't reading profiles — it's just doing keyword embedding. We use the honeypot rate as a Stage 3 filter: submissions with honeypot rate > 10% in top 100 are disqualified.
You can identify honeypots through careful profile inspection. We expect a good ranking system to naturally avoid them; you don't need to special-case them.

8. Leaderboard policy
The leaderboard is hidden during the competition. You will not see your score until final results are announced. We strongly recommend you validate your approach locally using methodology and reasoning, not by submitting many variations.

9. Sample submission
A sample submission CSV that matches this spec is included in your hackathon bundle as sample_submission.csv. It is not a high-quality ranking — it's only a format reference.

10. What you submit (full picture)
Your submission consists of three parts, all required:
10.1 The CSV file
The top-100 ranking, as specified in Sections 2 and 3.
10.2 Portal metadata
Collected at upload time via the submission form. Have these ready before you start the upload:

10.3 Code repository
Your GitHub repo should include:
A clear README.md with setup instructions and exact commands to reproduce your submission CSV
The full source code that produced the CSV (no hidden steps, no manual edits)
Any pre-computed artifacts your code depends on (embeddings, indexes, model weights), or a script that produces them
A requirements.txt, pyproject.toml, or equivalent specifying all dependencies and versions
A submission_metadata.yaml at the repo root mirroring your portal metadata (use the template provided in the hackathon bundle as submission_metadata_template.yaml)
For Stage 3 code reproduction, your README must indicate a single command that produces the submission CSV from the candidates file. For example:
python rank.py --candidates ./candidates.jsonl --out ./submission.csv
If your system requires pre-computation (e.g., generating embeddings), document this clearly — pre-computation may exceed the 5-minute window, but the ranking step that produces the CSV must complete within it.
10.4 AI tools declaration — what it means
The hackathon permits AI tool use. We've designed the evaluation pipeline so that AI-assisted submissions where the human did real engineering work will succeed, while AI-only submissions (paste-and-pray) will fail at Stage 3 (compute reproduction), Stage 4 (no real code repo), or Stage 5 (cannot defend the work).
The declaration is for transparency, not filtering. Be honest. If your interview answers contradict your declaration, that's a much stronger negative signal than the AI use itself.
10.5 Sandbox / demo link requirement
A sandbox is a hosted environment where organizers (and you) can verify your ranking system runs reproducibly. Acceptable sandbox platforms include:
HuggingFace Spaces (free tier is fine)
Streamlit Cloud (free tier is fine)
Replit (public repl)
Google Colab (with link to a notebook that runs end-to-end)
A docker pull + docker run link to a public registry image
A binder link for a runnable Jupyter notebook
Your sandbox needs to:
Accept a small candidate sample (≤100 candidates) as input — either via upload or pre-loaded
Run your ranking system end-to-end and produce a ranked CSV
Complete within the compute budget (≤5 min on CPU)
It does not need to handle the full 100K pool — small-sample reproducibility is what we're checking. The full reproduction at Stage 3 happens in our own sandbox.
Why it's mandatory: at Stage 3 we will reproduce your full ranking step from your GitHub repo. The sandbox is a faster, lower-stakes sanity check that lets us (and you) verify the code runs at all before we invest in full reproduction. Submissions without a working sandbox link are flagged at Stage 1.
If you have a strong reason a hosted sandbox is impractical for your approach, you can submit a self-contained docker run recipe in your GitHub README instead — but the dockerfile must build and run unmodified.
