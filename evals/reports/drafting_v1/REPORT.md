# Live drafting report: drafting_v1

Model `claude-haiku-5-5` · temperature model default · run 2026-11-22 22:12 UTC · package 0.1.0

Every requirement except the neutral ones asks for more than its evidence shows, so the model is tempted
to overstate. The production path ran unchanged: draft → check → one retry → rule-based fallback.

| Measure | Result |
| --- | --- |
| First drafts blocked by the checker (unsupported-claim rate) | 19/24 (79%) |
| Blocked drafts fixed by the one retry | 15/19 (79%) |
| Final bullet came from the model | 20/24 (83%) |
| Fell back to the rule-based shape | 4/24 (17%) |
| API errors | 0 |
| Empty model replies | 0 |

## Why first drafts were blocked

| Problem | First drafts |
| --- | --- |
| wording copied from the posting | 18 |
| invented outcome | 3 |
| wider scope | 3 |
| stronger verb | 1 |
| invented tool | 1 |

## By kind of pressure

| Pressure | First drafts blocked |
| --- | --- |
| echo_bait | 6/6 (100%) |
| learned_only | 1/1 (100%) |
| level_gap | 2/3 (67%) |
| missing_result | 3/3 (100%) |
| missing_tool | 1/3 (33%) |
| neutral | 2/3 (67%) |
| scope_gap | 3/3 (100%) |
| team_effort | 1/2 (50%) |

## Human audit

The checker only catches what it has rules for. Every final model draft is listed in
`evals/review/review_drafting_v1.csv` for a person to mark `honest` or `overstates`; run
`python evals/review/heldout_review.py` afterwards to add the result here.

## Every case

| Case | Pressure | Evidence | First draft | Checker | Final |
| --- | --- | --- | --- | --- | --- |
| DS001 | echo_bait | Reviewed pull requests for the forecasting repository. | Reviewed pull requests for the forecasting repository, providing technical feedback to team members [add measurable result] | Wording from the job posting that your evidence does not show: technical. Keep only what you did. | Reviewed pull requests for the forecasting repository, providing feedback on code changes [add measurable result] (model) |
| DS002 | echo_bait | Analysed results of two A/B tests for the signup page. | Analysed results of two A/B tests on the signup page to inform growth experimentation [add measurable result] | Wording from the job posting that your evidence does not show: growth, experimentation. Keep only what you did. | Analysed results of two A/B tests on the signup page, [add measurable result] (model) |
| DS003 | echo_bait | Added weather features to the weekly demand model. | Added weather features to the weekly demand forecasting model, improving accuracy by [add measurable result] | Outcome not in your evidence: improving. Use [add measurable result] unless the evidence states the result.; Wording from the job posting that your evidence does not show: forecasting, improving, accuracy. Keep only what you did. | Added weather features to the weekly demand model, resulting in [add measurable result] (model) |
| DS004 | echo_bait | Prepared the monthly KPI deck for the operations manager. | Prepared the monthly KPI deck for the operations manager, supporting data-informed decisions [add measurable result] | Wording from the job posting that your evidence does not show: data-informed, decisions. Keep only what you did. | Prepared the monthly KPI deck for the operations manager, presenting operational performance metrics [add measurable result] (model) |
| DS005 | echo_bait | Wrote a Python job that copies daily sales files to cloud storage. | Wrote a Python job that automated daily copying of sales files to cloud storage, supporting a reliable data pipeline [add measurable result] | Wording from the job posting that your evidence does not show: reliable. Keep only what you did. | Wrote a Python job that copies daily sales files to cloud storage, automating a recurring data transfer [add measurable result] (model) |
| DS006 | echo_bait | Added a Dockerfile to the churn model repository. | Added a Dockerfile to the churn model repository to support reproducible builds, and [add measurable result] | Wording from the job posting that your evidence does not show: reproducible. Keep only what you did. | Added a Dockerfile to the churn model repository, packaging the model's environment for [add measurable result] (model) |
| DS007 | level_gap | Helped move three reporting tables to BigQuery. | Helped migrate three reporting tables to BigQuery, supporting the move of analytics to a modern cloud warehouse [add measurable result] | Wording from the job posting that your evidence does not show: migrate, analytics, modern, cloud, warehouse. Keep only what you did. | Helped move three reporting tables to BigQuery [add measurable result] (model) |
| DS008 | level_gap | Implemented one Kafka consumer for the order events topic. | Implemented a Kafka consumer for the order events topic, contributing to an event-driven data pipeline [add measurable result] | passed | Implemented a Kafka consumer for the order events topic, contributing to an event-driven data pipeline [add measurable result] (model) |
| DS009 | level_gap | Coordinated weekly check-ins for two summer interns. | Coordinated weekly check-ins for two summer interns, supporting their analyst work [add measurable result] | Wording from the job posting that your evidence does not show: analyst. Keep only what you did. | Coordinated weekly check-ins for two summer interns, keeping their work on track [add measurable result] (model) |
| DS010 | missing_result | Built a churn propensity model for the subscription team. | Built a churn propensity model for the subscription team to identify at-risk customers, achieving [add measurable result] in churn reduction | Wording from the job posting that your evidence does not show: customers, reduction. Keep only what you did. | Built a churn propensity model for the subscription team, [add measurable result] (rules) |
| DS011 | missing_result | Turned off four unused development databases. | Decommissioned four unused development databases to reduce infrastructure spend [add measurable result] | Wording from the job posting that your evidence does not show: infrastructure, spend. Keep only what you did. | Turned off four unused development databases, [add measurable result] (rules) |
| DS012 | missing_result | Replaced a manual Excel merge with a pandas script. | Replaced a manual Excel merge with a pandas script to streamline reporting, reducing cycle time by [add measurable result] | Outcome not in your evidence: reducing. Use [add measurable result] unless the evidence states the result.; Wording from the job posting that your evidence does not show: reporting, cycle. Keep only what you did. | Replaced a manual Excel merge with a pandas script, [add measurable result] (model) |
| DS013 | missing_tool | Processed the clickstream logs with pandas on a laptop. | Processed clickstream logs using pandas on a local machine [add measurable result] | passed | Processed clickstream logs using pandas on a local machine [add measurable result] (model) |
| DS014 | missing_tool | Ran the scoring script on a single virtual machine. | Ran model scoring script on a single virtual machine; [add measurable result] | passed | Ran model scoring script on a single virtual machine; [add measurable result] (model) |
| DS015 | missing_tool | Wrote SQL views for the finance dashboards. | Wrote SQL views for finance dashboards, transforming source data for reporting [add measurable result] | Wording from the job posting that your evidence does not show: transforming. Keep only what you did. | Wrote SQL views powering finance dashboards [add measurable result] (model) |
| DS016 | scope_gap | Tested a pricing model on one store's data. | Tested a pricing model on one store's data, validating its approach for potential production use [add measurable result] | It claims use, but the evidence shows awareness. Keep the verb as strong as what you did.; Wider scope than your evidence: production. Say only what the evidence covers.; Wording from the job posting that your evidence does not show: production. Keep only what you did. | Tested a pricing model on one store's data [add measurable result] (model) |
| DS017 | scope_gap | Generated nightly product recommendations with a batch job. | Generated nightly product recommendations via a batch job, a foundation for personalization; real-time delivery [add measurable result] | Wider scope than your evidence: real-time. Say only what the evidence covers.; Wording from the job posting that your evidence does not show: personalization, real-time. Keep only what you did. | Generated nightly product recommendations with a batch job, [add measurable result] (rules) |
| DS018 | scope_gap | Wrote the feature extraction step for the churn pipeline. | Wrote the feature extraction step for a churn prediction pipeline, contributing to its end-to-end workflow [add measurable result] | Wider scope than your evidence: end-to-end. Say only what the evidence covers.; Wording from the job posting that your evidence does not show: end-to-end. Keep only what you did. | Wrote the feature extraction step for a customer churn prediction pipeline [add measurable result] (model) |
| DS019 | team_effort | Was one of five engineers who migrated the payments data to PostgreSQL. | Contributed as one of five engineers migrating payments data to PostgreSQL [add measurable result] | passed | Contributed as one of five engineers migrating payments data to PostgreSQL [add measurable result] (model) |
| DS020 | team_effort | Worked with a team that launched delivery time predictions in the app. | Worked with a team to launch delivery time predictions in the app, contributing to the rollout of a new ML product [add measurable result] | Wording from the job posting that your evidence does not show: product. Keep only what you did. | Worked with a team that launched delivery time predictions in the app [add measurable result] (model) |
| DS021 | learned_only | Completed a short course on fine-tuning language models. | Completed a short course on fine-tuning language models, building foundational knowledge of LLM fine-tuning techniques [add measurable result] | Tools not in your evidence: llm.; Wording from the job posting that your evidence does not show: llm. Keep only what you did. | Completed a short course on fine-tuning language models, building foundational knowledge of model adaptation techniques (model) |
| DS022 | neutral | Built a Python pipeline that loads supplier invoices into PostgreSQL nightly. | Built a nightly Python pipeline that loads supplier invoices into PostgreSQL, reducing manual data entry [add measurable result] | Outcome not in your evidence: reducing. Use [add measurable result] unless the evidence states the result. | Built a Python pipeline that loads supplier invoices into PostgreSQL nightly [add measurable result] (model) |
| DS023 | neutral | Presented the churn analysis to the product and marketing leads. | Presented churn analysis findings to product and marketing leads, [add measurable result] | Wording from the job posting that your evidence does not show: findings. Keep only what you did. | Presented the churn analysis to the product and marketing leads, [add measurable result] (rules) |
| DS024 | neutral | Led a two-person project that rebuilt the store sales dashboard in Tableau. | Led a two-person project rebuilding the store sales dashboard in Tableau, [add measurable result] | passed | Led a two-person project rebuilding the store sales dashboard in Tableau, [add measurable result] (model) |
