import time
from typing import List, Dict, Any
from openai import OpenAI
from config import OPENROUTER_BASE_URL, FREE_MODELS, DEFAULT_MODEL

class OpenRouterAgentRunner:
    def __init__(self, api_key: str, model_name: str = DEFAULT_MODEL):
        self.client = OpenAI(
            base_url=OPENROUTER_BASE_URL,
            api_key=api_key,
            default_headers={
                "HTTP-Referer": "https://legacylens.ai",
                "X-Title": "LegacyLens AI Code Archeologist"
            }
        )
        self.model_name = model_name

    def call_agent(self, system_prompt: str, user_prompt: str, retry_count: int = 3) -> str:
        """Executes agent call with OpenRouter model fallback on rate limits."""
        models_to_try = [self.model_name] + [m for m in FREE_MODELS if m != self.model_name]
        
        for model in models_to_try:
            for attempt in range(retry_count):
                try:
                    response = self.client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=0.2,
                        max_tokens=4000
                    )
                    return response.choices.message.content
                except Exception as e:
                    print(f"[OpenRouter Warning] Model {model} attempt {attempt+1} failed: {e}")
                    time.sleep(2)
        return "Error: Failed to process request across available OpenRouter free models."


class LegacyLensMultiAgentPipeline:
    def __init__(self, api_key: str):
        self.runner = OpenRouterAgentRunner(api_key=api_key)

    def agent_code_analyst(self, batch_files: List[Dict[str, Any]]) -> str:
        """Agent 1: Map Phase - Analyzes code batches for business logic, UI controls, and SQL."""
        code_snippets = ""
        for item in batch_files:
            try:
                with open(item["path"], "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()[:8000]  # Cap content length per file
                    code_snippets += f"\n--- File: {item['relative_path']} ---\n{content}\n"
            except Exception:
                continue

        system_prompt = """You are a Senior Java Enterprise Architect. Analyze the provided Java JSP, Class, JavaBean, and XML code snippets.
Extract and summarize:
1. UI Components, Form Actions, and Request Parameters (from JSPs).
2. Business Logic, Calculations, State Rules, and Validation Criteria (from Beans/Classes).
3. Data Access Layer (SQL queries, DAOs, Tables accessed).
4. External Service Integration or Session Attributes."""

        return self.runner.call_agent(system_prompt, f"Analyze this code batch:\n{code_snippets}")

    def agent_frs_synthesizer(self, module_analyses: List[str]) -> str:
        """Agent 2: Reduce Phase - Synthesizes IEEE 830 / ISO 29148 Compliant FRS."""
        combined_analysis = "\n\n".join(module_analyses[:20])  # Consolidate top summaries

        system_prompt = """You are a Lead Systems Analyst. Generate a formal, fully IEEE 830 / ISO 29148 compliant Functional Requirements Specification (FRS) based on the provided codebase analysis.

Your output MUST follow this exact IEEE structure:
1. INTRODUCTION
   1.1 Purpose
   1.2 Scope of Legacy Application
   1.3 Definitions, Acronyms, and Abbreviations
2. GENERAL DESCRIPTION
   2.1 Product Perspective & User Characteristics
   2.2 User Roles & Security Matrix
   2.3 General Constraints
3. SPECIFIC FUNCTIONAL REQUIREMENTS (Module by Module)
   - Feature/Module ID & Name
   - User Interface & Input Validation Rules (derived from JSPs)
   - Step-by-Step Business Logic & Workflows (derived from JavaBeans/Classes)
   - System Outputs & Screen Descriptions
4. BUSINESS RULES CATALOG
   - Comprehensive table of business constraints, calculations, and conditional rules."""

        return self.runner.call_agent(system_prompt, f"Generate IEEE FRS document based on this codebase analysis:\n{combined_analysis}")

    def agent_srs_synthesizer(self, module_analyses: List[str], catalog_stats: Dict[str, Any]) -> str:
        """Agent 3: Reduce Phase - Synthesizes IEEE 830 Compliant SRS with Mermaid diagrams."""
        combined_analysis = "\n\n".join(module_analyses[:20])

        system_prompt = """You are a Principal Software Architect. Generate a formal, fully IEEE 830 compliant Software Requirements Specification (SRS) based on the provided codebase analysis.

Your output MUST follow this exact IEEE structure:
1. SYSTEM ARCHITECTURE & TECH STACK
   1.1 High-Level Architecture Pattern (MVC, Layered)
   1.2 Frameworks, Application Server, & Java Standards
2. EXTERNAL INTERFACE REQUIREMENTS
   2.1 User Interfaces (JSP, Custom Tags)
   2.2 Hardware & Software Interfaces
   2.3 Communications Interfaces (Servlets, REST/SOAP)
3. SYSTEM DESIGN & COMPONENT SPECIFICATIONS
   - Package breakdown & JavaBean scope
   - Class interactions & Control Flow (Include Mermaid.js Sequence Diagrams)
4. DATA ARCHITECTURE & DATABASE SPECIFICATIONS
   - Database Tables, Schema Inferences, Foreign Keys
   - Mermaid.js Entity-Relationship (ER) Diagram
5. NON-FUNCTIONAL REQUIREMENTS
   - Performance, Security (Session/Auth), Reliability, Maintainability."""

        return self.runner.call_agent(system_prompt, f"Generate IEEE SRS document based on stats {catalog_stats} and analysis:\n{combined_analysis}")
