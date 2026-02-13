"""
InsightForge - Data Loader Module
Handles ingestion and preprocessing of various file types (CSV, Excel, PDF, DOCX, TXT, JSON).
"""

import os
import json
import pandas as pd
import streamlit as st
from typing import Tuple, Optional

from config import Config


class DataLoader:
    """Loads and preprocesses business data from multiple file formats."""

    TABULAR_EXTENSIONS = {"csv", "xlsx", "xls", "json"}
    DOCUMENT_EXTENSIONS = {"pdf", "docx", "txt"}

    @staticmethod
    def get_file_extension(filename: str) -> str:
        """Extract file extension (lowercase, without dot)."""
        return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    @classmethod
    def is_tabular(cls, filename: str) -> bool:
        """Check whether a file is tabular data."""
        return cls.get_file_extension(filename) in cls.TABULAR_EXTENSIONS

    @classmethod
    def is_document(cls, filename: str) -> bool:
        """Check whether a file is a document."""
        return cls.get_file_extension(filename) in cls.DOCUMENT_EXTENSIONS

    # ── Tabular Data Loading ────────────────────────────────

    @staticmethod
    def load_csv(file_path: str) -> pd.DataFrame:
        """Load CSV file into a DataFrame."""
        return pd.read_csv(file_path)

    @staticmethod
    def load_excel(file_path: str) -> pd.DataFrame:
        """Load Excel file into a DataFrame."""
        return pd.read_excel(file_path, engine="openpyxl")

    @staticmethod
    def load_json_tabular(file_path: str) -> pd.DataFrame:
        """Load JSON file into a DataFrame."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return pd.DataFrame(data)
        elif isinstance(data, dict):
            # Try to find a list of records inside the dict
            for key, value in data.items():
                if isinstance(value, list):
                    return pd.DataFrame(value)
            return pd.DataFrame([data])
        return pd.DataFrame()

    @classmethod
    def load_tabular(cls, file_path: str) -> pd.DataFrame:
        """Load any supported tabular file."""
        ext = cls.get_file_extension(file_path)
        loaders = {
            "csv": cls.load_csv,
            "xlsx": cls.load_excel,
            "xls": cls.load_excel,
            "json": cls.load_json_tabular,
        }
        loader = loaders.get(ext)
        if loader is None:
            raise ValueError(f"Unsupported tabular format: {ext}")
        return loader(file_path)

    # ── Document Loading ────────────────────────────────────

    @staticmethod
    def load_pdf(file_path: str) -> str:
        """Extract text from a PDF file."""
        from pypdf import PdfReader

        reader = PdfReader(file_path)
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        return "\n\n".join(text_parts)

    @staticmethod
    def load_docx(file_path: str) -> str:
        """Extract text from a DOCX file."""
        from docx import Document

        doc = Document(file_path)
        return "\n".join(para.text for para in doc.paragraphs if para.text.strip())

    @staticmethod
    def load_txt(file_path: str) -> str:
        """Load a plain text file."""
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    @classmethod
    def load_document(cls, file_path: str) -> str:
        """Load any supported document file and return text."""
        ext = cls.get_file_extension(file_path)
        loaders = {
            "pdf": cls.load_pdf,
            "docx": cls.load_docx,
            "txt": cls.load_txt,
        }
        loader = loaders.get(ext)
        if loader is None:
            raise ValueError(f"Unsupported document format: {ext}")
        return loader(file_path)

    # ── Unified Loader ──────────────────────────────────────

    @classmethod
    def load_file(cls, uploaded_file) -> Tuple[Optional[pd.DataFrame], Optional[str], str]:
        """
        Save an uploaded file and load its content.

        Returns:
            Tuple of (DataFrame or None, document_text or None, saved_file_path)
        """
        filename = uploaded_file.name
        save_path = os.path.join(Config.UPLOAD_DIR, filename)

        # Save to disk
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        df = None
        doc_text = None

        if cls.is_tabular(filename):
            df = cls.load_tabular(save_path)
        elif cls.is_document(filename):
            doc_text = cls.load_document(save_path)
        else:
            raise ValueError(f"Unsupported file type: {filename}")

        return df, doc_text, save_path

    # ── Data Profiling ──────────────────────────────────────

    @staticmethod
    def profile_dataframe(df: pd.DataFrame) -> dict:
        """Generate a comprehensive profile of a DataFrame."""
        profile = {
            "shape": df.shape,
            "columns": list(df.columns),
            "dtypes": df.dtypes.astype(str).to_dict(),
            "missing_values": df.isnull().sum().to_dict(),
            "missing_pct": (df.isnull().sum() / len(df) * 100).round(2).to_dict(),
            "numeric_columns": list(df.select_dtypes(include=["number"]).columns),
            "categorical_columns": list(df.select_dtypes(include=["object", "category"]).columns),
            "datetime_columns": list(df.select_dtypes(include=["datetime"]).columns),
        }

        # Numeric statistics
        if profile["numeric_columns"]:
            profile["numeric_stats"] = df[profile["numeric_columns"]].describe().to_dict()

        # Categorical value counts (top 10 per column)
        if profile["categorical_columns"]:
            profile["categorical_stats"] = {}
            for col in profile["categorical_columns"]:
                profile["categorical_stats"][col] = {
                    "unique_count": df[col].nunique(),
                    "top_values": df[col].value_counts().head(10).to_dict(),
                }

        return profile

    @staticmethod
    def dataframe_to_context(df: pd.DataFrame, max_rows: int = 50) -> str:
        """Convert a DataFrame into a text context string for LLM consumption."""
        lines = []
        lines.append(f"Dataset Shape: {df.shape[0]} rows × {df.shape[1]} columns")
        lines.append(f"Columns: {', '.join(df.columns.tolist())}")
        lines.append(f"\nColumn Types:\n{df.dtypes.to_string()}")
        lines.append(f"\nBasic Statistics:\n{df.describe(include='all').to_string()}")
        lines.append(f"\nMissing Values:\n{df.isnull().sum().to_string()}")

        sample_size = min(max_rows, len(df))
        lines.append(f"\nSample Data ({sample_size} rows):\n{df.head(sample_size).to_string()}")

        return "\n".join(lines)
