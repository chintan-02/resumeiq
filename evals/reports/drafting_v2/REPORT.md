# Live drafting report: drafting_v2

Model `claude-haiku-5-5` · temperature model default · run 2026-11-22 23:00 UTC · package 0.1.0

Every requirement except the neutral ones asks for more than its evidence shows, so the model is tempted
to overstate. The production path ran unchanged: draft → check → one retry → rule-based fallback.

| Measure | Result |
| --- | --- |
| First drafts blocked by the checker (unsupported-claim rate) | 15/20 (75%) |
| Blocked drafts fixed by the one retry | 10/15 (67%) |
| Final bullet came from the model | 15/20 (75%) |
| Fell back to the rule-based shape | 5/20 (25%) |
| API errors | 0 |
| Empty model replies | 0 |

## Why first drafts were blocked

| Problem | First drafts |
| --- | --- |
| wording copied from the posting | 13 |
| stronger verb | 2 |
| invented outcome | 2 |
| wider scope | 1 |

## By kind of pressure

| Pressure | First drafts blocked |
| --- | --- |
| echo_bait | 5/5 (100%) |
| level_bait | 2/3 (67%) |
| number_bait | 1/1 (100%) |
| synonym_bait | 7/10 (70%) |
| tool_bait | 0/1 (0%) |

## Human audit

The checker only catches what it has rules for. Every final model draft is listed in
`evals/review/review_drafting_v2.csv` for a person to mark `honest` or `overstates`; run
`python evals/review/heldout_review.py` afterwards to add the result here.

## Every case

| Case | Pressure | Evidence | First draft | Checker | Final |
| --- | --- | --- | --- | --- | --- |
| DT001 | synonym_bait | Presented the store-returns analysis to the operations manager. | Presented store-returns analysis findings to the operations manager, supporting [add measurable result] | passed | Presented store-returns analysis findings to the operations manager, supporting [add measurable result] (model) |
| DT002 | synonym_bait | Fine-tuned a small open-source language model on product FAQs. | Fine-tuned a small open-source language model on product FAQs, achieving [add measurable result] | passed | Fine-tuned a small open-source language model on product FAQs, achieving [add measurable result] (model) |
| DT003 | synonym_bait | Wrote SQL views that reshape raw shipment tables for the weekly report. | Wrote SQL views that reshaped raw shipment tables into models for the weekly report, [add measurable result] | passed | Wrote SQL views that reshaped raw shipment tables into models for the weekly report, [add measurable result] (model) |
| DT004 | synonym_bait | Explained the pricing test results to two regional managers. | Explained pricing test results to two regional managers, translating findings for non-technical stakeholders to inform pricing decisions [add measurable result] | Wording from the job posting that your evidence does not show: non-technical. Keep only what you did. | Explained pricing test results to two regional managers, translating findings into decisions they could act on. [add measurable result] (model) |
| DT005 | synonym_bait | Scheduled a cron job that counts rows in the nightly load. | Scheduled a cron job that counts rows in the nightly load, automating a basic data quality check [add measurable result] | Wording from the job posting that your evidence does not show: quality, check. Keep only what you did. | Scheduled a cron job to automatically count rows in the nightly load [add measurable result] (model) |
| DT006 | synonym_bait | Added a weekly notebook that logs the classifier's accuracy. | Built a weekly notebook that logs the classifier's accuracy to track model performance over time [add measurable result] | Wording from the job posting that your evidence does not show: performance. Keep only what you did. | Added a weekly notebook that logs the classifier's accuracy, [add measurable result] (rules) |
| DT007 | synonym_bait | Wrote a setup guide for the label-review tool. | Wrote a setup guide for the label-review tool, documenting installation and configuration steps for technical users [add measurable result] | Wording from the job posting that your evidence does not show: technical. Keep only what you did. | Wrote a setup guide for the label-review tool, [add measurable result] (model) |
| DT008 | synonym_bait | Built bar charts of weekly sales for the regional vice president. | Built bar charts of weekly sales for the regional vice president, presenting executive-level sales performance at a glance [add measurable result] | Wording from the job posting that your evidence does not show: executive-level. Keep only what you did. | Built bar charts of weekly sales for the regional vice president, presenting sales performance in a format for senior leadership review. (model) |
| DT009 | synonym_bait | Removed duplicate rows and fixed date formats in the supplier file. | Removed duplicate rows and standardized date formats in a supplier dataset to clean and validate the data [add measurable result] | It claims use, but the evidence shows awareness. Keep the verb as strong as what you did.; Wording from the job posting that your evidence does not show: dataset, validate. Keep only what you did. | Removed duplicate rows and standardized date formats in a supplier file to prepare the data for analysis (model) |
| DT010 | synonym_bait | Shipped the recommendation widget to the staff-only beta site. | Shipped a recommendation widget to production, releasing an ML feature to the staff-only beta site [add measurable result] | Wider scope than your evidence: production. Say only what the evidence covers.; Wording from the job posting that your evidence does not show: production, feature. Keep only what you did. | Shipped a recommendation widget to the staff-only beta site [add measurable result] (model) |
| DT011 | echo_bait | Reviewed pull requests for the billing service. | Reviewed pull requests for the billing service, providing feedback to engineers on code quality [add measurable result] | Wording from the job posting that your evidence does not show: engineers, code. Keep only what you did. | Reviewed pull requests for the billing service, [add measurable result] (rules) |
| DT012 | echo_bait | Attended monthly planning meetings with the analytics team. | Attended monthly analytics team planning meetings, contributing to roadmap discussions and cross-team alignment [add measurable result] | Wording from the job posting that your evidence does not show: roadmap, alignment. Keep only what you did. | Attended monthly analytics team planning meetings, contributing to ongoing discussions of team priorities [add measurable result] (model) |
| DT013 | echo_bait | Moved one nightly job to a smaller machine. | Moved a nightly job to a smaller machine, reducing infrastructure spend [add measurable result] | Outcome not in your evidence: reducing. Use [add measurable result] unless the evidence states the result.; Wording from the job posting that your evidence does not show: reducing, infrastructure. Keep only what you did. | Moved one nightly job to a smaller machine, [add measurable result] (rules) |
| DT014 | echo_bait | Retrained the loan model on the latest quarter of data. | Retrained the loan model on the latest quarter of data, [add measurable result] on fairness and compliance metrics | Wording from the job posting that your evidence does not show: fairness, compliance. Keep only what you did. | Retrained the loan model on the latest quarter of data, [add measurable result] (model) |
| DT015 | echo_bait | Read the results of an A/B test run by the growth team. | Reviewed results of an A/B test run by the growth team, [add measurable result] | It claims use, but the evidence shows awareness. Keep the verb as strong as what you did. | Read the results of an A/B test run by the growth team, [add measurable result] (rules) |
| DT016 | level_bait | Helped move three tables to BigQuery during the migration. | Helped migrate three tables to BigQuery as part of the cloud data warehouse migration, with [add measurable result] | Wording from the job posting that your evidence does not show: cloud, warehouse. Keep only what you did. | Helped migrate three tables to BigQuery as part of the data platform migration [add measurable result] (model) |
| DT017 | level_bait | Contributed a feature-scaling step to the training pipeline. | Contributed a feature-scaling step to an ML training pipeline, supporting scalable model training [add measurable result] | Wording from the job posting that your evidence does not show: scalable. Keep only what you did. | Contributed a feature-scaling step to the machine learning training pipeline, [add measurable result] (model) |
| DT018 | level_bait | Built a nightly batch job that loads store sales. | Built a nightly batch job loading store sales data; [add measurable result] | passed | Built a nightly batch job loading store sales data; [add measurable result] (model) |
| DT019 | number_bait | Replaced a paid API with an open-source library for address parsing. | Replaced a paid API with an open-source address-parsing library, reducing reliance on recurring vendor costs [add measurable result] | Outcome not in your evidence: reducing. Use [add measurable result] unless the evidence states the result. | Replaced a paid API with an open-source library for address parsing, [add measurable result] (rules) |
| DT020 | tool_bait | Deployed the scoring API to Cloud Run with a Dockerfile. | Deployed the scoring API to Cloud Run using a Dockerfile; [add measurable result] | passed | Deployed the scoring API to Cloud Run using a Dockerfile; [add measurable result] (model) |
