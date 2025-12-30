import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from crewai.tools import tool

@tool
def logistic_regression(data: list[dict] | dict | str, y: str, X: list[str]) -> dict:
    """
    Perform logistic regression on data provided as list of records, a dict, or a CSV/Excel path.
    Converts input to DataFrame internally. Returns coefficients, intercept, and accuracy.
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

    X_data = df[X]
    y_data = df[y]

    model = LogisticRegression(max_iter=1000)
    model.fit(X_data, y_data)

    preds = model.predict(X_data)

    return {
        "coefficients": dict(zip(X, model.coef_[0])),
        "intercept": model.intercept_[0],
        "accuracy": accuracy_score(y_data, preds)
    }
