"""
InsightForge - Sample Data Generator
Creates realistic sample business datasets for demonstration purposes.
"""

import pandas as pd
import numpy as np
import os
from config import Config


def generate_sales_data(n_rows: int = 500) -> pd.DataFrame:
    """Generate a realistic sales dataset."""
    np.random.seed(42)

    regions = ["North America", "Europe", "Asia Pacific", "Latin America", "Middle East"]
    products = ["Enterprise Suite", "Cloud Platform", "Data Analytics", "Security Pro", "IoT Gateway"]
    categories = ["Software", "Hardware", "Services", "Subscriptions"]
    sales_reps = [f"Rep_{i:03d}" for i in range(1, 21)]

    dates = pd.date_range("2023-01-01", "2024-12-31", periods=n_rows)

    data = {
        "Date": dates,
        "Region": np.random.choice(regions, n_rows, p=[0.35, 0.25, 0.20, 0.12, 0.08]),
        "Product": np.random.choice(products, n_rows),
        "Category": np.random.choice(categories, n_rows, p=[0.40, 0.20, 0.25, 0.15]),
        "Sales_Rep": np.random.choice(sales_reps, n_rows),
        "Revenue": np.round(np.random.lognormal(mean=9, sigma=1.2, size=n_rows), 2),
        "Units_Sold": np.random.randint(1, 100, n_rows),
        "Discount_Pct": np.round(np.random.uniform(0, 30, n_rows), 1),
        "Customer_Satisfaction": np.round(np.random.uniform(3.0, 5.0, n_rows), 1),
        "Deal_Size": np.random.choice(["Small", "Medium", "Large", "Enterprise"], n_rows,
                                        p=[0.40, 0.30, 0.20, 0.10]),
    }

    df = pd.DataFrame(data)
    df["Cost"] = np.round(df["Revenue"] * np.random.uniform(0.4, 0.7, n_rows), 2)
    df["Profit"] = np.round(df["Revenue"] - df["Cost"], 2)
    df["Profit_Margin"] = np.round((df["Profit"] / df["Revenue"]) * 100, 1)

    return df


def generate_hr_data(n_rows: int = 300) -> pd.DataFrame:
    """Generate a realistic HR / employee dataset."""
    np.random.seed(123)

    departments = ["Engineering", "Sales", "Marketing", "HR", "Finance", "Operations", "Support"]
    positions = ["Junior", "Mid-Level", "Senior", "Lead", "Manager", "Director"]

    data = {
        "Employee_ID": [f"EMP_{i:04d}" for i in range(1, n_rows + 1)],
        "Department": np.random.choice(departments, n_rows,
                                        p=[0.30, 0.20, 0.15, 0.08, 0.10, 0.10, 0.07]),
        "Position_Level": np.random.choice(positions, n_rows,
                                            p=[0.25, 0.30, 0.20, 0.10, 0.10, 0.05]),
        "Years_Experience": np.random.randint(0, 25, n_rows),
        "Salary": np.round(np.random.lognormal(mean=11, sigma=0.4, size=n_rows), 0),
        "Performance_Score": np.round(np.random.normal(3.5, 0.8, n_rows).clip(1, 5), 1),
        "Training_Hours": np.random.randint(0, 120, n_rows),
        "Satisfaction_Score": np.round(np.random.uniform(2.0, 5.0, n_rows), 1),
        "Attrition_Risk": np.random.choice(["Low", "Medium", "High"], n_rows,
                                            p=[0.60, 0.25, 0.15]),
        "Remote_Work_Pct": np.random.choice([0, 25, 50, 75, 100], n_rows,
                                             p=[0.15, 0.10, 0.25, 0.30, 0.20]),
    }

    return pd.DataFrame(data)


def generate_marketing_data(n_rows: int = 200) -> pd.DataFrame:
    """Generate a realistic marketing campaign dataset."""
    np.random.seed(456)

    channels = ["Google Ads", "Facebook", "LinkedIn", "Email", "Content", "Referral", "Organic"]
    campaigns = [f"Campaign_{i}" for i in range(1, 16)]

    dates = pd.date_range("2024-01-01", "2024-12-31", periods=n_rows)

    data = {
        "Date": dates,
        "Channel": np.random.choice(channels, n_rows),
        "Campaign": np.random.choice(campaigns, n_rows),
        "Impressions": np.random.randint(1000, 500000, n_rows),
        "Clicks": np.random.randint(10, 10000, n_rows),
        "Conversions": np.random.randint(0, 500, n_rows),
        "Spend": np.round(np.random.lognormal(mean=7, sigma=1, size=n_rows), 2),
        "Revenue_Generated": np.round(np.random.lognormal(mean=8, sigma=1.5, size=n_rows), 2),
    }

    df = pd.DataFrame(data)
    df["CTR"] = np.round((df["Clicks"] / df["Impressions"]) * 100, 2)
    df["CPC"] = np.round(df["Spend"] / df["Clicks"].clip(1), 2)
    df["CPA"] = np.round(df["Spend"] / df["Conversions"].clip(1), 2)
    df["ROI"] = np.round(((df["Revenue_Generated"] - df["Spend"]) / df["Spend"]) * 100, 1)

    return df


def save_sample_datasets():
    """Save all sample datasets to the sample data directory."""
    Config.ensure_directories()

    datasets = {
        "sales_data.csv": generate_sales_data(),
        "hr_data.csv": generate_hr_data(),
        "marketing_data.csv": generate_marketing_data(),
    }

    for filename, df in datasets.items():
        filepath = os.path.join(Config.SAMPLE_DATA_DIR, filename)
        df.to_csv(filepath, index=False)
        print(f"[OK] Saved {filename} ({df.shape[0]} rows, {df.shape[1]} columns)")

    return datasets


if __name__ == "__main__":
    save_sample_datasets()
