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
    CORE_VERSION = "1.7.5-PRO"
    
    def __init__(self, model_name: str = "llama-3.3-70b-versatile", ollama_url: str = "http://localhost:11434"):
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
            7. Matching Explanation: Provide a mathematical scorecard breakdown of the 'match_percentage'. It MUST include a transparent calculation (e.g., Technical Skills 50/50, Experience 20/30, etc.) and explain the specific weights used. Use a clear, structured format (like a Markdown table or detailed bullet points) that justifies the final percentage.
            8. Interview Questions: Generate 3-5 high-impact interview questions tailored to this candidate's specific resume and the JD requirements. Focus on validating their claimed skills or probing areas where they might be weak.

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
              "matching_explanation": "detailed breakdown of scoring logic",
              "interview_questions": ["question 1", "question 2", "question 3"]
            }}
            """
        )

    def _get_llm(self, provider: str, model_name: str, temperature: float, max_tokens: int, api_key: str = None, ollama_url: str = None, azure_config: dict = None):
        """Factory to get the correct LLM based on provider."""
        # --- Ultra-Robust API Key Sanitizer (v1.7.5-PRO) ---
        clean_key = None
        if api_key:
            # 1. Remove obvious wrapping junk (quotes, backticks, outer spaces)
            clean_key = api_key.strip().replace('"', '').replace("'", "").replace("`", "")
            
            # 2. Handle "Bearer " or "bearer " prefixes BEFORE removing internal spaces
            if clean_key.lower().startswith("bearer "):
                clean_key = clean_key[7:].strip()
            
            # 3. Remove common environment variable prefixes if pasted by mistake
            for prefix in ["GROQ_API_KEY", "OPENAI_API_KEY", "SARVAM_API_KEY", "DEEPSEEK_API_KEY", "GEMINI_API_KEY"]:
                if clean_key.upper().startswith(prefix + "="):
                    clean_key = clean_key[len(prefix)+1:].strip()
            
            # 4. Final scrub: remove ALL internal spaces or hidden tabs
            clean_key = "".join(clean_key.split())

        if provider == "OpenAI" and clean_key:
            return ChatOpenAI(model=model_name, temperature=temperature, max_tokens=max_tokens, api_key=clean_key)
        elif provider == "Groq" and clean_key:
            # Use both possible name variations for robustness in different library versions
            return ChatGroq(model=model_name, temperature=temperature, max_tokens=max_tokens, groq_api_key=clean_key, api_key=clean_key)
        elif provider == "SarvamAI" and clean_key:
            try:
                from sarvamai import SarvamAI
                class SarvamSDKWrapper:
                    def __init__(self, key, model, temp, tokens):
                        self.client = SarvamAI(api_subscription_key=key)
                        self.model = model
                        self.temp = temp
                        self.tokens = tokens
                    def invoke(self, prompt):
                        # The Sarvam SDK uses client.chat.completions() as a method directly
                        # NOTE: The current SDK version does NOT accept 'model' as a keyword argument.
                        # It is selected based on your API subscription level or defaults to sarvam-m.
                        res = self.client.chat.completions(
                            messages=[{"role": "user", "content": prompt}],
                            temperature=self.temp,
                            max_tokens=self.tokens
                        )
                        # The response object structure
                        if hasattr(res, 'choices') and len(res.choices) > 0:
                            return res.choices[0].message.content
                        return str(res)
                return SarvamSDKWrapper(clean_key, model_name, temperature, max_tokens)
            except Exception as e:
                # Fallback to OpenAI compatible if SDK fails
                # For Sarvam, we MUST use api-subscription-key header and often an empty Bearer
                return ChatOpenAI(
                    model=model_name,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    api_key=clean_key,
                    base_url="https://api.sarvam.ai/v1",
                    default_headers={"api-subscription-key": clean_key}
                )
        elif provider == "DeepSeek" and clean_key:
            return ChatOpenAI(
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                api_key=clean_key,
                base_url="https://api.deepseek.com"
            )
        elif provider == "Gemini" and clean_key:
            if ChatGoogleGenerativeAI:
                import os
                os.environ["GOOGLE_API_KEY"] = clean_key
                return ChatGoogleGenerativeAI(model=model_name, temperature=temperature, max_output_tokens=max_tokens, google_api_key=clean_key)
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
        response_text = ""
        json_str = ""
        try:
            target_model = model_name if model_name else self.llm.model
            print(f"DEBUG: Analying with v{self.CORE_VERSION} | Provider={provider}, Model={target_model}")
            llm = self._get_llm(provider, target_model, temperature, max_tokens, api_key, ollama_url, azure_config)
            response = llm.invoke(prompt)
            
            # Handle both BaseMessage (OpenAI/Groq) and str (Ollama)
            if hasattr(response, 'content'):
                response_text = response.content
            else:
                response_text = str(response)
            
            # --- High-Performance JSON Engine (v1.7.5-PRO) ---
            import re
            text = response_text.strip()

            # 1. Broad Extraction: Remove markdown and find all { or [ blocks
            clean_text = re.sub(r'```(?:json)?', '', text).strip()
            
            json_blocks = []
            # Find every possible start segment
            starts = [m.start() for m in re.finditer(r'[\{\[]', clean_text)]
            for s_idx in starts:
                # Find the last potential closer that appears AFTER this start
                last_curly = clean_text.rfind('}')
                last_bracket = clean_text.rfind(']')
                e_idx = max(last_curly, last_bracket)
                
                if e_idx > s_idx:
                    json_blocks.append(clean_text[s_idx:e_idx+1].strip())
                else:
                    # Truncated segment: take from start to end of text
                    json_blocks.append(clean_text[s_idx:].strip())
            
            if not json_blocks:
                # Last resort: use the whole text
                json_str = clean_text
            else:
                # Pick the segment with the most structure (best chance of being the main payload)
                json_str = max(json_blocks, key=len)

            # --- Smart JSON Repair Logic ---
            data = None
            
            # Pre-cleaning for "Invalid Control Character" errors (ASCII 0-31)
            # Many LLMs return unescaped newlines or tabs inside strings.
            def clean_control_chars(s):
                # Remove actual control characters but keep common structural ones if needed
                # Actually, json.loads(s, strict=False) handles most cases, 
                # but we clean extremes here.
                return re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', s)

            try:
                # Pre-clean: strip leading conversational noise and control chars
                json_str = re.sub(r'^[^\{\[\"]*', '', json_str).strip()
                # Use strict=False to allow unescaped newlines/tabs inside strings
                data = json.loads(json_str, strict=False)
            except json.JSONDecodeError:
                # Emergency Repair for truncated/malformed models
                r_json = clean_control_chars(json_str.strip())
                
                # A. Handle mid-word/mid-sentence truncation
                r_json = re.sub(r'[a-zA-Z0-9]*\.\.\.\s*$', '', r_json)
                
                if not r_json.endswith(('"', '}', ']', 'true', 'false', 'null')) and not r_json[-1].isdigit():
                    last_safe = max(r_json.rfind(','), r_json.rfind('"'), r_json.rfind(':'), r_json.rfind('{'), r_json.rfind('['))
                    if last_safe != -1:
                        r_json = r_json[:last_safe+1].strip()
                
                # B. String & List Maintenance
                r_json = re.sub(r',\s*$', '', r_json)
                
                if r_json.count('"') % 2 != 0:
                    r_json += '"'
                
                # C. Balance Structural Tags
                open_braces = r_json.count('{') - r_json.count('}')
                open_brackets = r_json.count('[') - r_json.count(']')
                
                if open_brackets > 0:
                    r_json += ']' * open_brackets
                if open_braces > 0:
                    r_json += '}' * open_braces
                
                try:
                    data = json.loads(r_json, strict=False)
                except:
                    # Final Deep Clean
                    r_json = re.sub(r',\s*([\]}])', r'\1', r_json)
                    r_json = re.sub(r',\s*""\s*]', ']', r_json)
                    data = json.loads(r_json, strict=False)
            

            # --- Type-Safety Guard (v1.7.5-PRO) ---
            if data and isinstance(data, dict):
                # 1. Ensure string fields are strings (not dicts/lists)
                for str_field in ['matching_explanation', 'candidate_summary', 'experience_evaluation', 'ranking']:
                    if str_field in data and not isinstance(data[str_field], str):
                        if isinstance(data[str_field], (dict, list)):
                            data[str_field] = json.dumps(data[str_field], indent=2)
                        else:
                            data[str_field] = str(data[str_field])
                
                # 2. Ensure match_percentage is an integer
                if 'match_percentage' in data:
                    try:
                        if isinstance(data['match_percentage'], str):
                            data['match_percentage'] = int(re.sub(r'[^0-9]', '', data['match_percentage']))
                        else:
                            data['match_percentage'] = int(data['match_percentage'])
                        # Clamp 0-100
                        data['match_percentage'] = max(0, min(100, data['match_percentage']))
                    except:
                        data['match_percentage'] = 0

            # Ensure return is a valid EvaluationResult
            return EvaluationResult(**data)

        except Exception as e:
            # Fallback or error handling
            error_details = f"{str(e)}"
            
            # Diagnostic Checklist
            diag = []
            if provider == "Ollama":
                diag.append("Check local model path")
                diag.append("Check memory/VRAM")
            else:
                diag.append("Verify API Key/Subscription")
                if hasattr(e, 'status_code'):
                    diag.append(f"Stat: {e.status_code}")

            is_parse_error = isinstance(e, json.JSONDecodeError) or "extra fields" in error_details.lower() or "validation error" in error_details.lower()
            
            short_msg = "Parse Error" if is_parse_error else "Engine Error"
            summary_hint = f"[{self.CORE_VERSION}] {provider} Diagnostics:"
            
            if "insufficient_quota" in error_details.lower() or "insufficient balance" in error_details.lower() or "402" in error_details:
                short_msg = "Quota Exceeded"
                summary_hint = "Insufficient Credits."

            if response_text:
                snippet = response_text[:250] + "..." if len(response_text) > 250 else response_text
                error_details += f" | RAW_V1.7.5: {snippet}"
            
            if json_str:
                failed_json = json_str[:150] + "..." if len(json_str) > 150 else json_str
                error_details += f" | ATTEMPTED_JSON: {failed_json}"
            
            # Key Masking for troubleshooting
            if api_key and len(api_key) > 8:
                masked = f"{api_key[:4]}...{api_key[-4:]}"
                error_details += f" | KEY_MASK: {masked} (Len: {len(api_key)})"
            
            print(f"DEBUG_V1.7.5: {error_details}")
            checklist_text = " -> ".join(diag)
            
            return EvaluationResult(**data) if 'data' in locals() and data else EvaluationResult(
                match_percentage=0,
                matched_skills=[],
                missing_skills=[short_msg],
                experience_evaluation=f"SYSTEM CHECK: {checklist_text}",
                candidate_summary=f"{summary_hint} Detail: {error_details}",
                ranking="Internal Error",
                matching_explanation=f"Matching core v{self.CORE_VERSION} encountered a processing exception.",
                interview_questions=["Please restart the session and try again."]
            )

    def chat(self, message: str, history: list, model_name: str = "llama-3.3-70b-versatile", temperature: float = 0.7, max_tokens: int = 1000, provider: str = "Groq", api_key: str = None, ollama_url: str = None, azure_config: dict = None, **kwargs) -> str:
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
