import { STATUS_ORDER } from "./labels";
import type { Coverage, FitMap } from "./types";

/**
 * Skill taxonomy, ported from the v0.9 skill_taxonomy module and grouped into
 * fewer, reader-facing areas. Each skill lists the phrases that name it.
 */
const TAXONOMY: Record<string, Record<string, string[]>> = {
  Programming: {
    Python: ["python"],
    Java: ["java"],
    JavaScript: ["javascript"],
    TypeScript: ["typescript"],
    "C++": ["c++"],
    Bash: ["bash"],
  },
  "Machine learning": {
    "Machine learning": ["machine learning"],
    "scikit-learn": ["scikit-learn", "sklearn"],
    XGBoost: ["xgboost"],
    LightGBM: ["lightgbm"],
    "Feature engineering": ["feature engineering"],
    "Model evaluation": ["model evaluation", "evaluation sets?", "model metrics"],
    "Deep learning": ["deep learning", "neural networks?"],
    PyTorch: ["pytorch"],
    TensorFlow: ["tensorflow", "keras"],
    NLP: ["nlp", "natural language processing"],
    LLMs: ["llms?", "large language models?"],
    RAG: ["rag", "retrieval augmented generation"],
    "Computer vision": ["computer vision", "opencv"],
  },
  "MLOps and cloud": {
    Docker: ["docker", "dockerfile"],
    Kubernetes: ["kubernetes", "k8s"],
    MLflow: ["mlflow"],
    "Experiment tracking": ["experiment tracking"],
    "CI/CD": ["ci/cd", "github actions"],
    Airflow: ["airflow"],
    "Model monitoring": ["model monitoring"],
    AWS: ["aws", "sagemaker"],
    Azure: ["azure"],
    GCP: ["gcp", "google cloud"],
  },
  "Data and databases": {
    SQL: ["sql"],
    PostgreSQL: ["postgresql", "postgres"],
    MySQL: ["mysql"],
    MongoDB: ["mongodb"],
    pandas: ["pandas"],
    NumPy: ["numpy"],
    "Data warehouse": ["data warehouse", "warehouse"],
  },
  "Backend and APIs": {
    FastAPI: ["fastapi"],
    Flask: ["flask"],
    "REST APIs": ["rest apis?"],
    React: ["react"],
  },
  Communication: {
    "Stakeholder communication": ["stakeholders?", "non-technical"],
    Leadership: ["leadership", "mentor(?:ed|ing)?"],
    Collaboration: ["collaborat(?:ed|ion|ing)", "cross-functional"],
  },
};

const PATTERNS = Object.entries(TAXONOMY).flatMap(([area, skills]) =>
  Object.entries(skills).map(([label, phrases]) => ({
    area,
    label,
    // Word edges that also respect "+", "#" and "/" so "c++" and "ci/cd" work.
    re: new RegExp(`(?<![\\w+#/])(?:${phrases.map((p) => p.replace(/[+/]/g, "\\$&")).join("|")})(?![\\w+#])`, "i"),
  })),
);

export interface Skill {
  area: string;
  label: string;
}

export function skillsIn(text: string): Skill[] {
  return PATTERNS.filter((p) => p.re.test(text)).map(({ area, label }) => ({ area, label }));
}

export interface SkillChip extends Skill {
  status: Coverage;
}

/** Skills the job asks for, grouped by area, each with its best evidence status. */
export function skillsByArea(fitMap: FitMap): { area: string; skills: SkillChip[] }[] {
  const best = new Map<string, SkillChip>();
  for (const result of fitMap.results) {
    for (const skill of skillsIn(result.requirement.text)) {
      const seen = best.get(skill.label);
      if (!seen || STATUS_ORDER[result.status] < STATUS_ORDER[seen.status]) {
        best.set(skill.label, { ...skill, status: result.status });
      }
    }
  }
  return Object.keys(TAXONOMY)
    .map((area) => ({ area, skills: [...best.values()].filter((s) => s.area === area) }))
    .filter((group) => group.skills.length > 0);
}
