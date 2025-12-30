import pandas as pd
import numpy as np
from scipy.stats import chi2_contingency
from crewai.tools import tool



@tool
def chi_square_test(
    data: list[dict] | dict | str,
    outcome: str,
    predictors: list[str]
) -> dict:
    """
    Perform a Chi-Square test of independence between two categorical variables.

    Parameters:
    - data: list of records, dict, or CSV/Excel file path
    - outcome: dependent categorical column name
    - predictors: list with ONE categorical column name

    Returns:
    - outcome, predictor
    - chi-square statistic
    - p-value
    - degrees of freedom
    - expected frequencies
    - significance flag
    """

   
    if isinstance(data, str):
        if data.endswith(".csv"):
            df = pd.read_csv(data)
        else:
            df = pd.read_excel(data)
    elif isinstance(data, dict):
        df = pd.DataFrame([data])
    else:
        df = pd.DataFrame(data)

    if not predictors or len(predictors) != 1:
        raise ValueError("Chi-square test requires exactly ONE predictor column")

    predictor = predictors[0]

   
    if outcome not in df.columns:
        raise ValueError(f"Outcome column '{outcome}' not found in dataset")

    if predictor not in df.columns:
        raise ValueError(f"Predictor column '{predictor}' not found in dataset")

   
    subset = df[[outcome, predictor]].dropna()

    if subset.empty:
        raise ValueError("No valid data after removing missing values")

    
    contingency_table = pd.crosstab(
        subset[outcome],
        subset[predictor]
    )

    
    if contingency_table.shape[0] < 2 or contingency_table.shape[1] < 2:
        return {
            "outcome": outcome,
            "predictor": predictor,
            "error": "Chi-square test requires at least two categories in each variable"
        }

    
    chi2, p, dof, expected = chi2_contingency(contingency_table)

    
    return {
        "outcome": outcome,
        "predictor": predictor,
        "chi_square": round(float(chi2), 4),
        "p_value": round(float(p), 4),
        "degrees_of_freedom": int(dof),
        "significant": bool(p < 0.05),
        "expected_frequencies": expected.round(2).tolist()
    }


@tool
def cronbach_alpha(data: list[dict] | dict | str) -> dict:
    """
    Calculate Cronbach's alpha for a set of item responses provided as list of records,
    a dict, or a CSV/Excel path. Converts to DataFrame internally.
    """
    if isinstance(data, str):
        if data.endswith(".csv"):
            df = pd.read_csv(data)
        else:
            df = pd.read_excel(data)
    elif isinstance(data, dict):
        df = pd.DataFrame([data])
    else:
        df = pd.DataFrame(data)

    df = df.apply(lambda x: x.astype("category").cat.codes)

    k = df.shape[1]
    variances = df.var(axis=0, ddof=1)
    total_var = df.sum(axis=1).var(ddof=1)

    raw_alpha = (k / (k - 1)) * (1 - variances.sum() / total_var)

    corr = df.corr().values
    mean_corr = np.nanmean(corr[np.triu_indices(k, 1)])
    standardized_alpha = (k * mean_corr) / (1 + (k - 1) * mean_corr)

    return {
        "raw_alpha": round(raw_alpha, 4),
        "standardized_alpha": round(standardized_alpha, 4),
        "items": k
    }
