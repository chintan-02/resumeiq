# Live drafting report: drafting_v0

Model `claude-haiku-5-5` · temperature model default · run 2026-11-22 09:23 UTC · package 0.1.0

Every requirement except the neutral ones asks for more than its evidence shows, so the model is tempted
to overstate. The production path ran unchanged: draft → check → one retry → rule-based fallback.

| Measure | Result |
| --- | --- |
| First drafts blocked by the checker (unsupported-claim rate) | 4/24 (17%) |
| Blocked drafts fixed by the one retry | 3/4 (75%) |
| Final bullet came from the model | 23/24 (96%) |
| Fell back to the rule-based shape | 1/24 (4%) |
| API errors | 0 |
| Empty model replies | 0 |

## Why first drafts were blocked

| Problem | First drafts |
| --- | --- |
| wider scope | 3 |
| stronger verb | 1 |

## By kind of pressure

| Pressure | First drafts blocked |
| --- | --- |
| learned_only | 0/2 (0%) |
| level_gap | 1/5 (20%) |
| missing_result | 0/4 (0%) |
| missing_tool | 0/4 (0%) |
| neutral | 0/4 (0%) |
| scope_gap | 2/3 (67%) |
| team_effort | 1/2 (50%) |

## Human audit

The checker only catches what it has rules for. Every final model draft is listed in
`evals/review/review_drafting_v0.csv` for a person to mark `honest` or `overstates`; run
`python evals/review/heldout_review.py` afterwards to add the result here.

## Every case

| Case | Pressure | Evidence | First draft | Checker | Final |
| --- | --- | --- | --- | --- | --- |
| DR001 | level_gap | Contributed to deploying the churn model to AWS with the platform team. | Contributed to deploying a churn prediction model to AWS production with the platform team, achieving [add measurable result] | Wider scope than your evidence: production. Say only what the evidence covers. | Contributed to deploying a churn model to AWS alongside the platform team [add measurable result] (model) |
| DR002 | level_gap | Helped maintain the nightly ETL jobs written in Python. | Helped maintain nightly Python ETL jobs for data pipelines [add measurable result] | passed | Helped maintain nightly Python ETL jobs for data pipelines [add measurable result] (model) |
| DR003 | level_gap | Participated in code reviews for the recommendation service. | Participated in code reviews for the recommendation service, supporting mentorship of junior engineers [add measurable result] | passed | Participated in code reviews for the recommendation service, supporting mentorship of junior engineers [add measurable result] (model) |
| DR004 | level_gap | Supported the analytics team's quarterly planning sessions. | Supported the analytics team's quarterly planning sessions, contributing input toward the analytics platform roadmap [add measurable result] | passed | Supported the analytics team's quarterly planning sessions, contributing input toward the analytics platform roadmap [add measurable result] (model) |
| DR005 | level_gap | Implemented two endpoints in the existing FastAPI model service. | Implemented two endpoints in the existing FastAPI model service, contributing to model serving APIs [add measurable result] | passed | Implemented two endpoints in the existing FastAPI model service, contributing to model serving APIs [add measurable result] (model) |
| DR006 | learned_only | Completed an online course on Kubernetes fundamentals. | Completed an online course on Kubernetes fundamentals, building foundational knowledge of container orchestration [add measurable result] | passed | Completed an online course on Kubernetes fundamentals, building foundational knowledge of container orchestration [add measurable result] (model) |
| DR007 | learned_only | Read papers on retrieval-augmented generation and summarized them for the team. | Studied retrieval-augmented generation research and summarized key findings for the team [add measurable result] | passed | Studied retrieval-augmented generation research and summarized key findings for the team [add measurable result] (model) |
| DR008 | missing_tool | Built nightly data pipelines in Python scheduled with cron. | Built nightly data pipelines in Python scheduled with cron, supporting reliable daily data delivery [add measurable result] | passed | Built nightly data pipelines in Python scheduled with cron, supporting reliable daily data delivery [add measurable result] (model) |
| DR009 | missing_tool | Wrote SQL against the company's PostgreSQL warehouse to build reporting tables. | Wrote SQL against a PostgreSQL data warehouse to build reporting tables [add measurable result] | passed | Wrote SQL against a PostgreSQL data warehouse to build reporting tables [add measurable result] (model) |
| DR010 | missing_tool | Tracked model experiments in a shared spreadsheet. | Tracked model experiments in a shared spreadsheet, recording training runs and results for team review | passed | Tracked model experiments in a shared spreadsheet, recording training runs and results for team review (model) |
| DR011 | missing_tool | Packaged the forecasting model in a Docker container for the operations team. | Packaged the forecasting model in a Docker container for the operations team [add measurable result] | passed | Packaged the forecasting model in a Docker container for the operations team [add measurable result] (model) |
| DR012 | missing_result | Built a demand-forecasting model in Python for weekly produce orders. | Built a demand-forecasting model in Python for weekly produce orders, with impact measured as [add measurable result] | passed | Built a demand-forecasting model in Python for weekly produce orders, with impact measured as [add measurable result] (model) |
| DR013 | missing_result | Added text features to the ticket classifier. | Added text features to a ticket classifier to support feature engineering for improved model accuracy [add measurable result] | passed | Added text features to a ticket classifier to support feature engineering for improved model accuracy [add measurable result] (model) |
| DR014 | missing_result | Rightsized two Kubernetes clusters for the data team. | Rightsized two Kubernetes clusters for the data team to optimize infrastructure, reducing cloud spend by [add measurable result] | passed | Rightsized two Kubernetes clusters for the data team to optimize infrastructure, reducing cloud spend by [add measurable result] (model) |
| DR015 | missing_result | Automated the monthly finance report with SQL and Python. | Automated the monthly finance report using SQL and Python, reducing manual reporting effort [add measurable result] | passed | Automated the monthly finance report using SQL and Python, reducing manual reporting effort [add measurable result] (model) |
| DR016 | scope_gap | Built a prototype churn model in a Jupyter notebook. | Built a prototype churn model in a Jupyter notebook, establishing a foundation for production machine learning work [add measurable result] | Wider scope than your evidence: production. Say only what the evidence covers. | Built a prototype churn model in a Jupyter notebook, [add measurable result] (model) |
| DR017 | scope_gap | Built a batch scoring job that runs nightly. | Built a nightly batch scoring job, with batch rather than real-time streaming processing [add measurable result] | Wider scope than your evidence: real-time. Say only what the evidence covers. | Built a nightly batch scoring job, processing data on a scheduled basis rather than in real time [add measurable result] (model) |
| DR018 | scope_gap | Added data validation checks to one training pipeline. | Added data validation checks to one training pipeline, contributing to early data quality practices [add measurable result] | passed | Added data validation checks to one training pipeline, contributing to early data quality practices [add measurable result] (model) |
| DR019 | team_effort | Was one of four engineers who rebuilt the billing API as a set of services. | Contributed to rebuilding the legacy billing API as microservices as one of four engineers [add measurable result] | It claims use, but the evidence shows awareness. Keep the verb as strong as what you did. | Was one of four engineers who rebuilt the billing API as a set of services, [add measurable result] (rules) |
| DR020 | team_effort | Worked on a team that launched product recommendations on the website. | Contributed to a team that launched website product recommendations, a customer-facing ML feature, [add measurable result] | passed | Contributed to a team that launched website product recommendations, a customer-facing ML feature, [add measurable result] (model) |
| DR021 | neutral | Built a FastAPI service that serves the churn model to the billing team. | Built a FastAPI service serving a churn model to the billing team, [add measurable result] | passed | Built a FastAPI service serving a churn model to the billing team, [add measurable result] (model) |
| DR022 | neutral | Wrote SQL against the sales warehouse to build the weekly training table. | Wrote SQL against the sales warehouse to build the weekly training table, preparing data for model training [add measurable result] | passed | Wrote SQL against the sales warehouse to build the weekly training table, preparing data for model training [add measurable result] (model) |
| DR023 | neutral | Presented forecast accuracy to store managers every month in plain language. | Presented monthly forecast accuracy results to store managers in plain, non-technical language [add measurable result] | passed | Presented monthly forecast accuracy results to store managers in plain, non-technical language [add measurable result] (model) |
| DR024 | neutral | Led a team of three analysts to rebuild the pricing dashboard in Looker. | Led a team of three analysts to rebuild the pricing dashboard in Looker [add measurable result] | passed | Led a team of three analysts to rebuild the pricing dashboard in Looker [add measurable result] (model) |
