'''
Assignment 1: Implementation of Data Preprocessing Techniques
'''


## Importing modules
import os
import csv
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.model_selection import train_test_split




## Task 1: Data Understanding and Importing

# File and code in same dirc
dataset = pd.read_csv(os.path.dirname(__file__) + "/" + "UCI_Credit_Card - UCI_Credit_Card - UCI_Credit_Card - UCI_Credit_Card.csv")

# Print first 10 rows
# print(dataset.head(10))
print()

# Describe the structure of the dataset (number of rows, columns, types of variables).
print(f"Number of rows and columns in the dataset: {dataset.shape[0]} rows and {dataset.shape[1]} columns.")
# print("Datatypes:")
# print(dataset.dtypes)
print()

# Preserve target column before any missing-value treatment
target_col = "default.payment.next.month"
y_full = dataset[target_col].copy()





## Task 2: Handling Missing Data

# Identify any missing values in the dataset.

# Null is easier to detect, but missing values are 0 in the code, so we replace now and then comeback
dataset.replace(int(0), np.nan, inplace=True)
dataset.replace(float(0), np.nan, inplace=True)

# Restore target column
dataset[target_col] = y_full

missing_values_col = dataset.isnull().sum()
missing_pct_col = missing_values_col * 100/ len(dataset)
missing_values_row = dataset.isnull().sum(axis=1)

# print(missing_values_col)
# print(missing_values_row)


'''
Explain the method you will use to handle missing data and justify your choice. ➢
Implement the method and show the result of the dataset after handling missing values.
'''

# education and marriage have very little empty dataset, so let's just fill with mode of the field
education_mode = int(dataset['EDUCATION'].mode()[0])
marriage_mode = int(dataset['MARRIAGE'].mode()[0])

dataset['EDUCATION'].replace(np.nan, education_mode, inplace=True)
dataset['MARRIAGE'].replace(np.nan, marriage_mode, inplace=True)


# The ones with ~10% empty data : we can safely use mean/median/mode
cols_missing10pct = missing_pct_col[(missing_pct_col>0) & (missing_pct_col <25)].index.tolist()
for col in cols_missing10pct:
    dataset[col] = dataset[col].fillna(dataset[col].median())


# The ones with ~50% empty data : we do the same thing, but may affect the model
cols_missing50pct = missing_pct_col[(missing_pct_col>=25) & (missing_pct_col <70)].index.tolist()
for col in cols_missing50pct:
    dataset[col] = dataset[col].fillna(dataset[col].median())

# The ones with ~80% empty data : just drop
cols_missing80pct = missing_pct_col[missing_pct_col>=70].index.tolist()
dataset = dataset.drop(columns=cols_missing80pct)


missing_values_col = dataset.isnull().sum()
missing_pct_col = missing_values_col * 100/ len(dataset)

# print("After cleaning")
# print(missing_values_col)


# Task 3: Data Transformation

# coeff of variation (standard deviation over mean gives an estimate of unitless spread)
# std dev is not unitless and difficult to decide which features to scale, 
# since the one with higher order of magnitude are ranked higher
# std dev / mean gives a better idea, but not conclusive
# for now we scale the ones with std dev / mean > 1

# print(dataset.std().sort_values(ascending=False))
dataset_cv = (dataset.std() / dataset.mean()).abs()
# print(dataset_cv.sort_values(ascending=False))

# we standardize the ones with dataset_cv >1
cols_cv_gt_1 = dataset_cv[dataset_cv > 1].index.tolist()
cols_cv_gt_1 = [c for c in cols_cv_gt_1 if c != target_col]  # never scale the target
scaler = StandardScaler()
dataset_scaled = dataset.copy()
dataset_scaled[cols_cv_gt_1] = scaler.fit_transform(dataset[cols_cv_gt_1])

# print(dataset_scaled)

# Visualize the effect of the transformation on one continuous variable.

print(dataset_scaled['BILL_AMT6'].max())

fig, axes = plt.subplots(1, 2, figsize=(12, 4))
axes[0].hist(dataset["BILL_AMT6"], bins=40, color="steelblue")
axes[0].set_title("BILL_AMT6 - Before Standardization")
axes[0].set_xlabel("BILL_AMT6")
axes[0].set_ylabel("Frequency")
 
axes[1].hist(dataset_scaled["BILL_AMT6"], bins=40, color="darkorange")
axes[1].set_title("BILL_AMT6 - After Standardization")
axes[1].set_xlabel("Standardized BILL_AMT6")
axes[1].set_ylabel("Frequency")
 
plt.tight_layout()
# plt.show()
plt.close()


# Task 4: Encoding categorical variables
# these are columns with discrete values that may mislead distance based models
categorical_cols = ["SEX", "EDUCATION", "MARRIAGE"]
 
dataset_encoded = pd.get_dummies(dataset_scaled, columns=categorical_cols,
                             prefix=categorical_cols, drop_first=True)
 
print("Columns after one-hot encoding:")
print(dataset_encoded.columns.tolist())
print(f"Shape after encoding: {dataset_encoded.shape}")


# Task 5: Feature Selection and Engineering

# Removing ID
dataset_encoded = dataset_encoded.drop(columns=["ID"])
print("Dropped 'ID' column as it is not predictive")
 
# Feature engineering: create an average bill amount and average payment amount across the 6 months, which can capture overall spending/repayment
bill_cols = ["BILL_AMT1", "BILL_AMT2", "BILL_AMT3",
             "BILL_AMT4", "BILL_AMT5", "BILL_AMT6"]
pay_amt_cols = ["PAY_AMT1", "PAY_AMT2", "PAY_AMT3",
                "PAY_AMT4", "PAY_AMT5", "PAY_AMT6"]
 
dataset_encoded["AVG_BILL_AMT"] = dataset_encoded[bill_cols].mean(axis=1)
dataset_encoded["AVG_PAY_AMT"] = dataset_encoded[pay_amt_cols].mean(axis=1)

# Adding ratio of average payment to average bill, representing repayment behavior relative to billed amount
dataset_encoded["PAY_TO_BILL_RATIO"] = dataset_encoded["AVG_PAY_AMT"] / (dataset_encoded["AVG_BILL_AMT"] + 1e-6)


# Task 6: Data Splitting
 
# Target variable: default payment next month
target_col = "default.payment.next.month"

X = dataset_encoded.drop(columns=[target_col])
y = dataset_encoded[target_col]
 
# Split into 80% training and 20% testing sets.
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)
 
print(f"Training set size: {X_train.shape[0]} rows")
print(f"Testing set size: {X_test.shape[0]} rows")
print(f"Training target distribution:\n{y_train.value_counts()}")
print(f"Testing target distribution:\n{y_test.value_counts()}")



# Task 7: Summary of Data Preprocessing

'''
Write a brief summary of the data preprocessing steps you implemented.

1. Data Understanding: Loaded 30,000 records x 25 columns and inspected
   structure, data types, and summary statistics.
2. Missing Data: The NaNs were present as 0s, so 0 values were treated
   as missing and replaced with NaN. Columns with >70% missing data
   were dropped as unrecoverable; columns with ~10-70% missing data
   were imputed with the median (numeric) or mode (EDUCATION, MARRIAGE),
   while the target column was excluded from this treatment since its
   0 values are a valid class label.
3. Data Transformation: Standardized continuous financial variables
   using z-score scaling so all continuous features are on a comparable scale.
4. Encoding: One-hot encoded the nominal categorical variables (SEX,
   EDUCATION, MARRIAGE) to avoid implying false relationships
5. Feature Selection/Engineering: Dropped the non-predictive ID column
   and engineered AVG_BILL_AMT, AVG_PAY_AMT, and PAY_TO_BILL_RATIO to
   summarize repayment behavior across the 6-month history.
6. Data Splitting: Split into 80% training / 20% testing sets using
   stratified sampling on the target variable.
'''

'''
Discuss how these steps improve the quality of data for further analysis and modeling.

These steps improve data quality for modeling by: removing ambiguous or
invalid category codes that could distort statistics, putting numeric
features on comparable scales (important for distance- and gradient-based
algorithms), encoding categoricals in a way models can consume without
introducing false order, eliminating uninformative noise (ID), adding
potentially more predictive engineered features, and enabling a fair,
unbiased evaluation of any model trained on this data via train/test
separation.
'''


dataset_encoded.to_csv("UCI_Credit_Card_preprocessed.csv", index=False)
print("Saved final preprocessed dataset to UCI_Credit_Card_preprocessed.csv")
 
