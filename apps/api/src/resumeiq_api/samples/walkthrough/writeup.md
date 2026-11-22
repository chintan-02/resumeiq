# Project write-up: shelf-life classifier (synthetic sample)

I built a classifier that flags produce batches likely to spoil within three days, using supplier, temperature and delivery-time features.

I designed a held-out evaluation set of 600 batches from two stores the model never saw in training, and reported precision and recall for the spoilage class each month.

I logged every training run with MLflow, including parameters, metrics and the dataset version.

The model is a gradient-boosting classifier; I compared it against a logistic regression baseline before choosing it.
