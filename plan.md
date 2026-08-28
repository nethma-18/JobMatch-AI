You are working on my JobMatch AI final-year project (CSE6035).

IMPORTANT OBJECTIVE:
I already have a dataset somewhere inside the project folder. I want you to inspect the ACTUAL project and ACTUAL dataset, implement a complete and reproducible machine-learning training + evaluation pipeline based ONLY on what the dataset genuinely contains, run the pipeline, and update the project with REAL measured results.

ABSOLUTE RULE:
DO NOT fabricate, estimate, assume, invent, or manually enter dataset sizes, labels, accuracy, precision, recall, F1, ROC-AUC, NDCG, MAP, thresholds, improvement percentages, or model performance.

Every numerical result in the project must come from an actual executed experiment.

==================================================
PHASE 1 — FULL PROJECT + DATASET AUDIT
==================================================

Before modifying anything:

1. Inspect the entire repository recursively.

2. Locate every possible dataset file, including:
   - CSV
   - JSON
   - JSONL
   - XLSX/XLS
   - Parquet
   - TXT
   - database seed files
   - MongoDB seed/training files
   - files inside data/
   - files inside datasets/
   - files inside training/
   - files inside ml/
   - any other files containing resume/job/matching data.

3. Determine:
   - exact dataset path
   - file format
   - number of records
   - columns/fields
   - missing values
   - duplicate records
   - resume fields
   - job-description fields
   - candidate/job identifiers
   - labels/target fields
   - label distribution
   - whether labels are binary, multiclass, ordinal, or continuous
   - whether the dataset contains actual resume-job pairs
   - whether it contains relevance/match labels
   - whether negative examples exist
   - whether the dataset is suitable for supervised learning.

4. Inspect the existing JobMatch AI ML implementation.

Specifically inspect:
   - embeddings.py
   - similarity.py
   - skill_extractor.py
   - retrainer.py
   - validation code
   - any existing model-training code
   - any evaluation code
   - API routes related to ML/retraining
   - model storage directories
   - requirements.txt
   - configuration files.

5. Determine exactly what the CURRENT system does.

Do not rely on README, thesis, plan.md, comments, or previous claims if the implementation contradicts them.

Treat executable code and actual files as the source of truth.

6. Produce an internal audit before implementation.

The audit must explicitly answer:

   A. What dataset actually exists?
   B. Is it labeled?
   C. What is the target variable?
   D. How many usable samples exist?
   E. What ML task is genuinely supported?
   F. Is the existing model trained or only pretrained?
   G. What baseline currently exists?
   H. What evaluation can legitimately be performed?

==================================================
PHASE 2 — DATASET VALIDATION
==================================================

After identifying the dataset:

1. Load it programmatically.

2. Validate its schema.

3. Report:
   - total rows
   - usable rows
   - removed rows and exact reason
   - duplicate count
   - missing-value statistics
   - class distribution
   - class imbalance
   - unique resumes
   - unique jobs
   - unique resume-job pairs.

4. DO NOT create artificial labels merely to make supervised learning possible.

5. DO NOT randomly assign labels.

6. DO NOT convert unrelated fields into labels unless there is a clearly defensible existing target field in the dataset.

7. If the dataset is not suitable for supervised classification, STOP the supervised-training portion and explain exactly why.

8. If it supports supervised classification, continue.

==================================================
PHASE 3 — PREPROCESSING
==================================================

Implement a reproducible preprocessing pipeline.

Requirements:

1. Clean text safely without destroying meaningful information.

2. Handle missing values explicitly.

3. Remove exact duplicates.

4. Prevent data leakage.

5. If multiple rows belong to the same resume or job, consider grouped splitting where appropriate so the same resume/job does not appear across train and test in a way that inflates performance.

6. Preserve the original dataset.

7. Save the cleaned/processed dataset to an appropriate project location.

8. Create a reproducible preprocessing script rather than manually editing the dataset.

==================================================
PHASE 4 — TRAIN / VALIDATION / TEST SPLIT
==================================================

Create a proper reproducible split.

Preferred approach:

- Train: 70–80%
- Validation: 10–15%
- Test: 10–20%

Use stratification when appropriate.

If the dataset structure requires grouped splitting, use GroupShuffleSplit or another appropriate grouped method.

Set and document a fixed random seed.

Do NOT blindly use 80/10/10 if the dataset structure makes another split scientifically more appropriate.

Document the actual split sizes.

==================================================
PHASE 5 — BASELINE
==================================================

Evaluate the existing JobMatch AI matching method as a baseline.

The existing system may use:

- Sentence-BERT / sentence-transformers
- all-MiniLM-L6-v2
- semantic cosine similarity
- skill overlap
- the existing hybrid scoring formula.

Do NOT change the existing baseline merely to obtain better performance.

Implement a clean baseline evaluator that produces predictions on the SAME test data used for the trained model.

If the existing system's score is continuous but the ground truth is classification labels, determine a scientifically defensible threshold ONLY using the TRAINING/VALIDATION data.

NEVER select a threshold using the test set.

Document exactly how the threshold was selected.

==================================================
PHASE 6 — TRAINED MODEL
==================================================

Based on the ACTUAL dataset and target variable, choose an appropriate supervised ML algorithm.

Possible options include:

- Logistic Regression
- Random Forest
- Gradient Boosting
- SVM
- another suitable scikit-learn model.

Do NOT automatically choose Random Forest simply because previous documentation mentioned it.

Select the model based on the actual task and dataset.

Use the existing JobMatch AI NLP features where appropriate.

Potential features may include:

1. Sentence-BERT cosine similarity
2. skill overlap ratio
3. number of matched required skills
4. number of missing required skills
5. resume/JD length features
6. education overlap
7. certification overlap
8. experience overlap

BUT:

Only implement features that genuinely exist and can be extracted reliably from the actual project/data.

Do not create fake features.

Use a proper sklearn Pipeline where appropriate to prevent preprocessing leakage.

==================================================
PHASE 7 — TRAINING
==================================================

Train the selected model ONLY on the training set.

Use the validation set for:

- hyperparameter selection
- threshold selection
- model comparison.

Do not use the test set during model selection.

If cross-validation is appropriate, perform it ONLY inside the training data.

Document:

- model name
- hyperparameters
- random seed
- training sample count
- validation sample count
- test sample count
- feature list
- preprocessing steps.

Save the trained model to an appropriate model directory, for example:

JobMatch-Backend/data/models/

Use a reproducible format such as jobmatch_model.pkl/joblib, depending on the project's existing conventions.

Also save:

- feature metadata
- model version
- training timestamp
- dataset version/hash if practical
- training configuration.

==================================================
PHASE 8 — REAL EVALUATION
==================================================

Evaluate BOTH:

A. Existing baseline
B. Newly trained model

on the SAME untouched test set.

For classification, calculate only metrics that are appropriate for the actual task.

At minimum, where applicable:

- Accuracy
- Precision
- Recall
- F1-score
- Confusion Matrix

Also calculate ROC-AUC only if the task/data supports it.

For ranking/matching tasks, additionally consider:

- Precision@K
- Recall@K
- NDCG@K
- MAP
- MRR

ONLY if the dataset structure genuinely supports ranking evaluation.

Do NOT calculate meaningless metrics just to make the thesis look more impressive.

All metric values MUST be generated programmatically.

==================================================
PHASE 9 — MODEL COMPARISON
==================================================

Create a real comparison table such as:

Metric | Existing Baseline | Trained Model | Difference

The "Difference" must be calculated automatically.

Do not manually type improvement percentages.

If the trained model performs WORSE than the baseline, report that honestly.

Do not alter the experiment to hide poor performance.

If there is no statistically meaningful basis for claiming improvement, do not claim improvement.

==================================================
PHASE 10 — CONFUSION MATRIX + VISUALS
==================================================

Generate actual evaluation visualizations where appropriate:

1. Confusion matrix
2. Class distribution
3. Score/prediction distribution
4. ROC curve if applicable
5. Precision/Recall curve if applicable
6. Feature importance if the selected model supports it.

Save generated figures in a suitable project directory such as:

thesis-screenshots/ml/
or
results/

Use clear filenames.

Do not create fake screenshots or fake charts.

==================================================
PHASE 11 — INTEGRATE MODEL INTO JOBMATCH AI
==================================================

If the trained model is valid and compatible with the existing application:

1. Add model loading logic.

2. Update the matching/retraining architecture so the trained model can actually be used.

3. Preserve the existing Sentence-BERT + skill-based baseline.

4. Make it possible to compare:
   - baseline prediction
   - trained model prediction.

5. Do not break existing API contracts.

6. Do not remove existing functionality.

7. Keep backward compatibility wherever practical.

8. Add clear fallback behavior if the trained model is unavailable.

==================================================
PHASE 12 — API / ADMIN INTEGRATION
==================================================

Inspect the existing admin retraining functionality.

If it already exists, connect it to the REAL training pipeline.

The retraining process should:

1. Load approved training data.
2. Validate the data.
3. Train the model.
4. Evaluate it.
5. Save the model.
6. Save REAL metrics.
7. Store metrics in model_metrics if that collection exists.
8. Return actual metrics from the training run.

Do NOT return hardcoded values.

For example, NEVER do this:

accuracy = 0.857

Instead calculate it from predictions and labels.

==================================================
PHASE 13 — AUTOMATED TESTS
==================================================

Add tests for the new ML pipeline.

Tests should cover:

1. Dataset loading.
2. Dataset schema validation.
3. Preprocessing.
4. Train/test splitting.
5. Feature generation.
6. Model training.
7. Model persistence/loading.
8. Prediction shape.
9. Metric calculation.
10. No data leakage.
11. Existing baseline still works.
12. Existing API functionality remains intact.

Run the complete backend test suite.

Do not delete existing tests simply because they fail.

Fix genuine regressions caused by your changes.

==================================================
PHASE 14 — RUN EVERYTHING
==================================================

Actually execute:

1. Dataset inspection.
2. Preprocessing.
3. Training.
4. Validation.
5. Testing.
6. Evaluation.
7. Model saving.
8. Full pytest suite.
9. Frontend build if backend changes could affect integration.
10. Relevant API integration tests.

Do not simply write scripts and claim they work.

Actually run them.

If something fails:

- investigate
- fix it
- rerun
- document the final result.

==================================================
PHASE 15 — GENERATE MACHINE-READABLE RESULTS
==================================================

Create a results file, for example:

results/ml_evaluation_results.json

containing REAL values such as:

{
  "dataset": {
    "path": "...",
    "total_samples": ...,
    "usable_samples": ...,
    "train_samples": ...,
    "validation_samples": ...,
    "test_samples": ...
  },
  "model": {
    "name": "...",
    "features": [...],
    "hyperparameters": {...}
  },
  "baseline": {
    "accuracy": ...,
    "precision": ...,
    "recall": ...,
    "f1": ...
  },
  "trained_model": {
    "accuracy": ...,
    "precision": ...,
    "recall": ...,
    "f1": ...
  }
}

Every value must be generated by the executed experiment.

==================================================
PHASE 16 — UPDATE PROJECT DOCUMENTATION
==================================================

Update README/documentation ONLY with verified results.

Remove or clearly mark any previous unsupported claims such as:

- "800 resume-job pairs"
- "F1 = 0.8414"
- "Accuracy = 0.857"
- "5-fold cross-validation"
- "Random Forest 100 estimators"
- "7% improvement"

unless the newly executed experiment actually produces those exact results.

Do not preserve unsupported numbers merely because they already appear in the documentation.

==================================================
PHASE 17 — THESIS RESULTS SUPPORT
==================================================

I have thesis documentation that discusses:

- dataset
- training
- validation
- testing
- matching engine
- ML model
- accuracy
- precision
- recall
- F1-score
- model comparison.

Create a thesis-results source file such as:

results/thesis_ml_results.md

containing:

1. Actual dataset description.
2. Actual dataset size.
3. Actual preprocessing.
4. Actual train/validation/test split.
5. Actual model.
6. Actual features.
7. Actual hyperparameters.
8. Actual baseline results.
9. Actual trained model results.
10. Actual confusion matrix interpretation.
11. Actual strengths/limitations.
12. Reproducibility instructions.

Use academic wording, but DO NOT exaggerate the results.

If the results are weak, report them honestly.

==================================================
PHASE 18 — IMPORTANT SCIENTIFIC INTEGRITY RULES
==================================================

NEVER:

- fabricate data
- fabricate labels
- fabricate accuracy
- fabricate precision
- fabricate recall
- fabricate F1
- fabricate dataset size
- fabricate training history
- fabricate cross-validation results
- fabricate model artifacts
- fabricate screenshots
- fabricate improvement percentages
- claim a model was trained if training did not execute
- claim a dataset was used if it was not actually loaded
- claim a test set was held out if it was used during tuning
- claim generalisation without an appropriate test/evaluation setup
- use the test set to select thresholds/hyperparameters
- duplicate data just to increase sample count
- generate synthetic data unless I explicitly approve it.

If the actual dataset is too small for reliable ML evaluation, say so and use the strongest scientifically defensible evaluation possible.

If the dataset is unlabeled, do NOT invent labels. Instead report that supervised evaluation is not currently supported and explain what additional labels are genuinely required.

==================================================
PHASE 19 — FINAL AUDIT REPORT
==================================================

At the end, produce a concise final report containing:

A. DATASET
- exact path
- format
- original sample count
- usable sample count
- label structure

B. TRAINING
- model trained
- features
- training samples
- validation samples
- test samples
- hyperparameters
- model artifact path

C. RESULTS

| Metric | Baseline | Trained Model | Difference |
|--------|----------|---------------|------------|
| Accuracy | REAL | REAL | CALCULATED |
| Precision | REAL | REAL | CALCULATED |
| Recall | REAL | REAL | CALCULATED |
| F1 | REAL | REAL | CALCULATED |

D. TESTING
- pytest result
- integration result
- build result

E. FILES CREATED/MODIFIED
List every relevant file.

F. THESIS-READY FACTS
Give me the exact verified numbers and statements that I can safely use in my thesis.

G. UNSUPPORTED CLAIMS
List any previous thesis/project claims that are still not supported by the actual implementation or experiment.

MOST IMPORTANT:
The actual repository and executed experiment are the source of truth.

Do not make the project look successful by inventing results.

If the experiment produces 62% accuracy, report 62%.
If it produces 84.14%, report 84.14%.
If it produces no valid supervised metric, report that.

REAL RESULTS ONLY.