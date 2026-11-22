# Baseline report: requirement → evidence matching (eval_v0)

Dataset `eval_v0` · sha256 `0de089f7d321` · labelling guide v0.1 · labels {'ai-reviewed': 54} · package 0.1.0

> **Provisional.** Labels were written and re-checked by an AI assistant (`ai-reviewed`); no human has reviewed
> them yet. A human pass marks them `reviewed`; see `evals/review/README.md`.
> The test split has 27 cases (dev: 27), so confidence intervals are wide. Do not quote these
> numbers publicly until the labels are reviewed and the set is larger.

Thresholds were tuned on the dev split (candidates C1–C3, job families J1–J2) and frozen before
scoring the test split (C4–C6, J3–J4). Candidates and job families never cross splits.

## Test split

| Matcher | Macro-F1 [95% CI] | Accuracy | Trap cases correct | Evidence recall@1 | Evidence recall@3 | Citation precision |
| --- | --- | --- | --- | --- | --- | --- |
| `keyword` | 0.40 [0.22, 0.56] | 0.41 | 3/8 | 0.83 | 0.94 | 0.59 (13/22) |
| `keyword-rules` | 0.71 [0.49, 0.88] | 0.74 | 5/8 | 0.83 | 0.94 | 0.72 (13/18) |
| `embedding` | 0.36 [0.22, 0.51] | 0.41 | 5/8 | 0.94 | 1.00 | 0.93 (13/14) |
| `embedding-rules` | 0.71 [0.51, 0.88] | 0.78 | 7/8 | 0.94 | 1.00 | 0.88 (15/17) |

## Dev split (used for tuning)

| Matcher | Thresholds (low / high) | Macro-F1 | Trap cases correct |
| --- | --- | --- | --- |
| `keyword` | 0.25 / 0.65 | 0.61 | 7/10 |
| `keyword-rules` | 0.3 / 0.35 | 0.73 | 6/10 |
| `embedding` | 0.4 / 0.6 | 0.48 | 6/10 |
| `embedding-rules` | 0.35 / 0.4 | 0.72 | 8/10 |

## Test errors: `keyword`

| Case | Requirement | Gold | Predicted | Trap |
| --- | --- | --- | --- | --- |
| C4-J3-R4 | Write automated tests and maintain CI pipelines | supported | partial |  |
| C4-J3-R6 | Deploy services with Docker and Kubernetes | partial | supported | yes |
| C4-J3-R8 | Use observability tools such as Prometheus or Grafana | supported | partial |  |
| C5-J4-R1 | Build batch data pipelines with Airflow | supported | partial |  |
| C5-J4-R3 | Set up model monitoring and data drift alerts | supported | partial |  |
| C5-J4-R4 | Lead migrations of ML workloads to the cloud | supported | not_found |  |
| C5-J4-R5 | Experience with feature stores | not_found | supported | yes |
| C5-J4-R6 | Implement CI/CD for machine learning models | partial | not_found | yes |
| C5-J4-R7 | Work with cloud object storage such as S3 or GCS | supported | not_found |  |
| C5-J4-R8 | Familiarity with data privacy regulations such as PIPEDA | supported | partial |  |
| C6-J3-R1 | Design and build REST APIs with Python or Go | partial | not_found |  |
| C6-J3-R2 | Experience with PostgreSQL | partial | not_found |  |
| C6-J3-R5 | Experience with message queues such as RabbitMQ or Kafka | not_found | partial | yes |
| C6-J3-R6 | Deploy services with Docker and Kubernetes | not_found | partial |  |
| C6-J3-R8 | Use observability tools such as Prometheus or Grafana | supported | partial |  |
| C4-J3-R9 | Review API designs with product managers | not_found | partial | yes |

## Test errors: `keyword-rules`

| Case | Requirement | Gold | Predicted | Trap |
| --- | --- | --- | --- | --- |
| C4-J3-R4 | Write automated tests and maintain CI pipelines | supported | partial |  |
| C4-J3-R6 | Deploy services with Docker and Kubernetes | partial | supported | yes |
| C5-J4-R4 | Lead migrations of ML workloads to the cloud | supported | not_found |  |
| C5-J4-R5 | Experience with feature stores | not_found | supported | yes |
| C5-J4-R6 | Implement CI/CD for machine learning models | partial | not_found | yes |
| C5-J4-R7 | Work with cloud object storage such as S3 or GCS | supported | not_found |  |
| C6-J3-R2 | Experience with PostgreSQL | partial | not_found |  |

## Test errors: `embedding`

| Case | Requirement | Gold | Predicted | Trap |
| --- | --- | --- | --- | --- |
| C4-J3-R1 | Design and build REST APIs with Python or Go | supported | partial |  |
| C4-J3-R2 | Experience with PostgreSQL | supported | partial |  |
| C4-J3-R4 | Write automated tests and maintain CI pipelines | supported | partial |  |
| C4-J3-R6 | Deploy services with Docker and Kubernetes | partial | supported | yes |
| C4-J3-R8 | Use observability tools such as Prometheus or Grafana | supported | partial |  |
| C5-J4-R1 | Build batch data pipelines with Airflow | supported | partial |  |
| C5-J4-R2 | Experience with Spark or another distributed processing engine | supported | not_found |  |
| C5-J4-R3 | Set up model monitoring and data drift alerts | supported | partial |  |
| C5-J4-R4 | Lead migrations of ML workloads to the cloud | supported | partial |  |
| C5-J4-R6 | Implement CI/CD for machine learning models | partial | not_found | yes |
| C5-J4-R7 | Work with cloud object storage such as S3 or GCS | supported | partial |  |
| C5-J4-R8 | Familiarity with data privacy regulations such as PIPEDA | supported | partial |  |
| C6-J3-R2 | Experience with PostgreSQL | partial | not_found |  |
| C6-J3-R4 | Write automated tests and maintain CI pipelines | partial | not_found |  |
| C6-J3-R5 | Experience with message queues such as RabbitMQ or Kafka | not_found | partial | yes |
| C6-J3-R8 | Use observability tools such as Prometheus or Grafana | supported | not_found |  |

## Test errors: `embedding-rules`

| Case | Requirement | Gold | Predicted | Trap |
| --- | --- | --- | --- | --- |
| C4-J3-R6 | Deploy services with Docker and Kubernetes | partial | supported | yes |
| C5-J4-R2 | Experience with Spark or another distributed processing engine | supported | partial |  |
| C6-J3-R1 | Design and build REST APIs with Python or Go | partial | supported |  |
| C6-J3-R2 | Experience with PostgreSQL | partial | not_found |  |
| C6-J3-R4 | Write automated tests and maintain CI pipelines | partial | not_found |  |
| C6-J3-R8 | Use observability tools such as Prometheus or Grafana | supported | not_found |  |

## Evaluation protocol and known issues

- The eval_v0 **test split has now been looked at**. Method changes motivated by its errors must be
  measured on a fresh test set (eval_v1), not on this one, or the numbers stop meaning anything.
- Known issues seen in test errors, deliberately **not** fixed against this split:
  - Synonym replacement drops words: "Google Cloud Storage" becomes `gcs`, so "cloud storage" no longer
    matches. Synonyms should add the canonical term and keep the original words.
  - The light stemmer merges unrelated words ("stored" and "stores" both become `stor`), which creates
    a false match for "feature stores".
  - Keyword retrieval cannot connect paraphrases ("Vertex AI" for "the cloud", "GitHub Actions" for
    "CI pipelines"). This is what the embedding comparison is meant to measure.
  - Compound requirements are judged as one unit: "Docker and Kubernetes" counts as supported when the
    evidence says another team did the Kubernetes part.
- The 6 generic-term cases (`*-R9`) were added to both splits after the walkthrough showed a false
  "supported" from a single shared word; see `changelog` in the dataset.
- Embedding matchers need a model download and run on a developer machine:
  `pip install -e "apps/api[embeddings]"` then
  `python evals/run_baseline.py --matchers keyword keyword-rules embedding embedding-rules`.

## How to read this

- **Evidence recall@k** checks retrieval: was a gold evidence item among the top k candidates?
- **Macro-F1** and **trap cases** check judgment: given the evidence, was the status right?
  Trap cases contain the right keyword but support a weaker claim or a different meaning.
- **Citation precision**: of the evidence items the matcher cited, how many are gold evidence.

Reproduce: `python evals/run_baseline.py --check`
