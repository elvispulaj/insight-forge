"""
InsightForge - LLM Engine Module
Manages LLM interactions via LangChain with specialized prompts
for business intelligence analysis, insight generation, and recommendations.
"""

from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage

import base64
from config import Config


# ── Prompt Templates ────────────────────────────────────────

SYSTEM_PROMPT = """You are InsightForge, an expert AI Business Intelligence Analyst. 
You help organizations transform raw data into actionable business insights.

Your capabilities include:
- Identifying key trends, patterns, and anomalies in business data
- Generating clear, actionable recommendations
- Explaining complex data findings in accessible business language
- Suggesting appropriate visualizations for different data types
- Providing strategic business advice based on data analysis

Guidelines:
- Be specific and data-driven in your analysis
- Provide actionable recommendations, not just observations
- Use professional business language
- Structure your responses with clear sections and bullet points
- When relevant, suggest specific KPIs to track
- Highlight both opportunities and risks
"""

DATA_ANALYSIS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", """Analyze the following business data and provide comprehensive insights.

DATA CONTEXT:
{data_context}

ADDITIONAL CONTEXT FROM KNOWLEDGE BASE:
{rag_context}

Please provide:
1. **Executive Summary**: A brief overview of the key findings
2. **Key Trends & Patterns**: Important trends identified in the data
3. **Anomalies & Concerns**: Any unusual patterns or potential issues
4. **Actionable Recommendations**: Specific, prioritized actions to take
5. **KPIs to Monitor**: Key performance indicators to track going forward
""")
])

QUESTION_ANSWER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", """Answer the following business question using the provided data and context.

DATA CONTEXT:
{data_context}

RELEVANT CONTEXT FROM KNOWLEDGE BASE:
{rag_context}

QUESTION: {question}

Provide a thorough, data-backed answer with specific references to the data when possible.
""")
])

VISUALIZATION_SUGGESTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", """Based on the following data profile, suggest the most effective visualizations.

DATA PROFILE:
{data_context}

For each visualization, provide:
1. Chart type (bar, line, scatter, pie, heatmap, etc.)
2. Which columns to use for X-axis, Y-axis, and any grouping
3. Why this visualization is insightful
4. What business question it answers

Suggest 3-5 visualizations, ordered by importance. Format each suggestion as:
- **Chart Type**: [type]
- **X-Axis**: [column]
- **Y-Axis**: [column]  
- **Group By**: [column or None]
- **Title**: [descriptive title]
- **Insight**: [what it reveals]
""")
])

CUSTOM_ANALYSIS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", """Perform the following custom analysis on the business data.

DATA CONTEXT:
{data_context}

RELEVANT CONTEXT FROM KNOWLEDGE BASE:
{rag_context}

ANALYSIS REQUEST: {analysis_request}

Provide detailed findings with supporting data points and actionable recommendations.
""")
])


class LLMEngine:
    """
    LLM-powered analysis engine using LangChain and OpenAI.
    Provides structured business intelligence analysis capabilities.
    """

    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or Config.OPENAI_API_KEY
        self.model = model or Config.OPENAI_MODEL
        self._llm = None
    
    @staticmethod
    def _encode_image(image_path: str) -> str:
        """Encode image to base64."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    @property
    def llm(self) -> ChatOpenAI:
        """Lazy-load the LLM."""
        if self._llm is None:
            self._llm = ChatOpenAI(
                model=self.model,
                api_key=self.api_key,
                temperature=0.3,
                max_tokens=4096,
            )
        return self._llm

    # ── Analysis Methods ────────────────────────────────────

    def analyze_image(self, image_path: str, prompt: str = "Analyze this business chart/image.") -> str:
        """Analyze an image using the multimodal capabilities of the LLM."""
        base64_image = self._encode_image(image_path)
        
        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    },
                },
            ]
        )
        
        response = self.llm.invoke([SystemMessage(content=SYSTEM_PROMPT), message])
        return response.content

    def analyze_data(self, data_context: str, rag_context: str = "") -> str:
        """Perform comprehensive data analysis."""
        if not rag_context:
            rag_context = "No additional context available."
        chain = DATA_ANALYSIS_PROMPT | self.llm
        response = chain.invoke({
            "data_context": data_context,
            "rag_context": rag_context,
        })
        return response.content

    def answer_question(self, question: str, data_context: str, rag_context: str = "") -> str:
        """Answer a specific business question about the data."""
        if not rag_context:
            rag_context = "No additional context available."
        chain = QUESTION_ANSWER_PROMPT | self.llm
        response = chain.invoke({
            "question": question,
            "data_context": data_context,
            "rag_context": rag_context,
        })
        return response.content

    def suggest_visualizations(self, data_context: str) -> str:
        """Get visualization suggestions for the data."""
        chain = VISUALIZATION_SUGGESTION_PROMPT | self.llm
        response = chain.invoke({
            "data_context": data_context,
        })
        return response.content

    def custom_analysis(self, analysis_request: str, data_context: str, rag_context: str = "") -> str:
        """Perform a custom analysis requested by the user."""
        if not rag_context:
            rag_context = "No additional context available."
        chain = CUSTOM_ANALYSIS_PROMPT | self.llm
        response = chain.invoke({
            "analysis_request": analysis_request,
            "data_context": data_context,
            "rag_context": rag_context,
        })
        return response.content

    def chat(self, message: str, data_context: str = "", rag_context: str = "") -> str:
        """General chat interaction with business context."""
        messages = [SystemMessage(content=SYSTEM_PROMPT)]

        if data_context:
            context_msg = f"Current data context:\n{data_context}"
            if rag_context:
                context_msg += f"\n\nAdditional context:\n{rag_context}"
            messages.append(SystemMessage(content=context_msg))

        messages.append(HumanMessage(content=message))
        response = self.llm.invoke(messages)
        return response.content

    # ── Status ──────────────────────────────────────────────

    def test_connection(self) -> bool:
        """Test the LLM connection."""
        try:
            response = self.llm.invoke([HumanMessage(content="Say 'connected' if you can read this.")])
            return "connected" in response.content.lower()
        except Exception:
            return False
