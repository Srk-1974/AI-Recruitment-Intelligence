import json
import requests
from langchain_ollama import OllamaLLM
from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain_groq import ChatGroq
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None

from langchain_core.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder
from core.models import EvaluationResult, ChatResponse

class HRAnalyzer:
    def __init__(self, model_name: str = "llama3.2", ollama_url: str = "http://localhost:11434"):
        self.ollama_base_url = ollama_url
        self.llm = OllamaLLM(model=model_name, base_url=self.ollama_base_url)
        self.prompt_template = PromptTemplate(
            input_variables=["resume_text", "jd_text"],
            template="""
            You are an expert HR Recruitment Assistant. Your task is to compare the provided Resume with the Job Description and provide a highly accurate evaluation.

            Analyze both documents carefully and return results in structured JSON format.

            Evaluation Requirements:
            1. Match Percentage: Provide an overall match percentage (0-100).
            2. Matched Skills: List skills present in both resume and JD.
            3. Missing Skills: Identify key requirements from JD missing in the resume.
            4. Experience Evaluation: Evaluate if the candidate's years and depth of experience are relevant.
            5. Candidate Summary: A short professional summary (2-3 sentences) of suitability.
            6. Ranking: One of "Strong Match", "Moderate Match", or "Weak Match".
            7. Interview Questions: Generate 3-5 high-impact interview questions tailored to this candidate's specific resume and the JD requirements. Focus on validating their claimed skills or probing areas where they might be weak.

            Guidelines:
            - Be objective and realistic.
            - Do NOT assume skills not explicitly mentioned.
            - Focus on technologies, domain relevance, and professional experience.

            Resume Content:
            {resume_text}

            Job Description Content:
            {jd_text}

            Return Output ONLY in valid JSON format using this exact structure:
            {{
              "match_percentage": number,
              "matched_skills": ["skill1", "skill2"],
              "missing_skills": ["skillA", "skillB"],
              "experience_evaluation": "detailed text",
              "candidate_summary": "summary text",
              "ranking": "Strong/Moderate/Weak Match",
              "interview_questions": ["question 1", "question 2", "question 3"]
            }}
            """
        )

    def _get_llm(self, provider: str, model_name: str, temperature: float, max_tokens: int, api_key: str = None, ollama_url: str = None, azure_config: dict = None):
        """Factory to get the correct LLM based on provider."""
        if provider == "OpenAI" and api_key:
            return ChatOpenAI(model=model_name, temperature=temperature, max_tokens=max_tokens, api_key=api_key)
        elif provider == "Groq" and api_key:
            return ChatGroq(model=model_name, temperature=temperature, max_tokens=max_tokens, api_key=api_key)
        elif provider == "SarvamAI" and api_key:
             return ChatOpenAI(
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                api_key=api_key,
                base_url="https://api.sarvam.ai/v1"
            )
        elif provider == "DeepSeek" and api_key:
            return ChatOpenAI(
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                api_key=api_key,
                base_url="https://api.deepseek.com"
            )
        elif provider == "Gemini" and api_key:
            if ChatGoogleGenerativeAI:
                import os
                os.environ["GOOGLE_API_KEY"] = api_key
                return ChatGoogleGenerativeAI(model=model_name, temperature=temperature, max_output_tokens=max_tokens, google_api_key=api_key)
            else:
                raise ImportError("langchain-google-genai not installed")
        elif provider == "AzureOpenAI" and azure_config:
            return AzureChatOpenAI(
                azure_deployment=azure_config.get("deployment_name"),
                openai_api_version=azure_config.get("api_version"),
                azure_endpoint=azure_config.get("endpoint"),
                api_key=azure_config.get("api_key"),
                temperature=temperature,
                max_tokens=max_tokens
            )
        else: # Default to Ollama
            target_url = ollama_url if ollama_url else self.ollama_base_url
            return OllamaLLM(
                model=model_name, 
                temperature=temperature, 
                num_predict=max_tokens, 
                base_url=target_url,
                headers={
                    'ngrok-skip-browser-warning': 'true',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
            )

    def analyze(self, resume_text: str, jd_text: str, model_name: str = None, temperature: float = 0.1, max_tokens: int = 2000, provider: str = "Ollama", api_key: str = None, ollama_url: str = None, azure_config: dict = None, **kwargs) -> EvaluationResult:
        """Sends the extraction task to the LLM and parses the result."""
        target_model = model_name if model_name else self.llm.model
        prompt = self.prompt_template.format(resume_text=resume_text, jd_text=jd_text)
        try:
            target_model = model_name if model_name else self.llm.model
            print(f"DEBUG: Analying with Provider={provider}, Model={target_model}, KeyPresent={bool(api_key)}")
            llm = self._get_llm(provider, target_model, temperature, max_tokens, api_key, ollama_url, azure_config)
            response = llm.invoke(prompt)
            
            # Handle both BaseMessage (OpenAI/Groq) and str (Ollama)
            if hasattr(response, 'content'):
                response_text = response.content
            else:
                response_text = str(response)
            
            # Clean response text and try to extract JSON
            response_text = response_text.strip()
            
            # Look for JSON between triple backticks first
            import re
            json_match = re.search(r"```json\s*(.*?)\s*```", response_text, re.DOTALL)
            if not json_match:
                json_match = re.search(r"```\s*(\{.*?\})\s*```", response_text, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(1).strip()
            else:
                # If no backticks, try to find the first '{' and last '}'
                first_curly = response_text.find('{')
                last_curly = response_text.rfind('}')
                if first_curly != -1 and last_curly != -1:
                    json_str = response_text[first_curly:last_curly+1].strip()
                else:
                    json_str = response_text
            
            if not json_str:
                raise ValueError("LLM returned an empty response.")
                
            data = json.loads(json_str)
            return EvaluationResult(**data)
        except Exception as e:
            # Fallback or error handling
            error_details = f"{str(e)}"
            
            # Special hint for quota issues
            short_msg = "Analysis Error"
            summary_hint = f"Troubleshooting: Make sure the model '{target_model}' is correctly loaded."
            
            if "insufficient_quota" in error_details.lower() or "insufficient balance" in error_details.lower() or "402" in error_details:
                short_msg = "Quota Exceeded / No Balance"
                summary_hint = "Your API provider account has insufficient credits. Please top up your balance or switch execution providers."

            if 'response_text' in locals() and response_text:
                snippet = response_text[:200] + "..." if len(response_text) > 200 else response_text
                error_details += f" | Raw Snippet: {snippet}"
            
            print(f"Error during analysis: {error_details}")
            return EvaluationResult(
                match_percentage=0,
                matched_skills=[],
                missing_skills=[short_msg],
                experience_evaluation="The AI failed to complete the request.",
                candidate_summary=f"{summary_hint} Error logic: {error_details}",
                ranking="System Error",
                interview_questions=["Please check your AI configuration."]
            )

    def chat(self, message: str, history: list, model_name: str = "llama3.2", temperature: float = 0.7, max_tokens: int = 1000, provider: str = "Ollama", api_key: str = None, ollama_url: str = None, azure_config: dict = None, **kwargs) -> str:
        """General purpose chat with system context about the HR app."""
        system_prompt = """
        You are the 'HR Intelligence Assistant', a helpful AI built to explain and assist with the Intelligent HR Recruitment Assistant application.
        
        About the App:
        - It compares candidate Resumes (PDF/DOCX) with Job Descriptions.
        - Features: Single Evaluation, Batch Ranking, Visual Dashboard.
        - Engine: Uses local LLMs via Ollama (default llama3.2).
        - Backend: FastAPI, Frontend: Streamlit.
        
        Your Goal:
        - Explain how to use the app.
        - Answer general HR and recruitment questions.
        - Help users troubleshoot or understand analysis results.
        - Be professional, modern, and concise.
        """
        
        history_str = ""
        for msg in history[-5:]: # Last 5 messages for context
            role = msg.get("role", "user")
            content = msg.get("content", "")
            history_str += f"{role}: {content}\n"
            
        full_prompt = f"{system_prompt}\n\nRecent History:\n{history_str}\nUser: {message}\nAssistant:"
        
        try:
            llm = self._get_llm(provider, model_name, temperature, max_tokens, api_key, ollama_url, azure_config)
            response = llm.invoke(full_prompt)
            
            if hasattr(response, 'content'):
                return response.content
            return str(response).strip()
        except Exception as e:
            return f"I encountered an error connecting to the model: {str(e)}"

    def get_available_models(self, custom_url: str = None) -> list:
        """Fetches the list of models currently pulled in Ollama."""
        target_url = custom_url if custom_url else self.ollama_base_url
        headers = {
            'ngrok-skip-browser-warning': 'true',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        try:
            response = requests.get(f"{target_url}/api/tags", timeout=5, headers=headers)
            if response.status_code == 200:
                models_data = response.json().get('models', [])
                return [m['name'] for m in models_data]
            return ["llama3.2"] # Fallback
        except Exception as e:
            print(f"Ollama fetch error: {e}")
            return ["llama3.2"] # Fallback
