"""
Vertex AI Client - Compatible with v1.25.0
Handles credentials correctly from Secret Manager
"""
import os
import json
from google.cloud import aiplatform
from google.cloud.aiplatform import gapic
from google.oauth2 import service_account

class VertexAIClient:
    def __init__(self):
        project_id = os.getenv("GCP_PROJECT_ID", "codegen-ai-479819")
        location = "us-central1"
        
        # Handle credentials from environment (Secret Manager injects as string)
        creds_env = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        
        credentials = None
        if creds_env:
            # If it's JSON content (from Secret Manager), parse it
            try:
                creds_dict = json.loads(creds_env)
                credentials = service_account.Credentials.from_service_account_info(creds_dict)
                print("✅ Using credentials from Secret Manager")
            except json.JSONDecodeError:
                # If it's a file path, use it directly
                if os.path.isfile(creds_env):
                    credentials = service_account.Credentials.from_service_account_file(creds_env)
                    print("✅ Using credentials from file")
        
        # Initialize Vertex AI with credentials
        aiplatform.init(
            project=project_id, 
            location=location,
            credentials=credentials
        )
        
        # Create prediction client
        client_options = {"api_endpoint": f"{location}-aiplatform.googleapis.com"}
        self.client = gapic.PredictionServiceClient(
            credentials=credentials,
            client_options=client_options
        )
        
        self.project_id = project_id
        self.location = location
        self.endpoint = f"projects/{project_id}/locations/{location}/publishers/google/models/text-bison"
        
        print(f"✅ Vertex AI initialized (project: {project_id}, model: text-bison)")
    
    class ChatCompletions:
        def __init__(self, client, endpoint):
            self.client = client
            self.endpoint = endpoint
        
        def create(self, model: str, messages: list, temperature: float = 0.7, **kwargs):
            """OpenAI-compatible interface"""
            
            prompt = self._convert_messages(messages)
            
            instance = {
                "prompt": prompt,
                "temperature": temperature,
                "maxOutputTokens": 2048,
                "topP": 0.95,
                "topK": 40,
            }
            
            try:
                response = self.client.predict(
                    endpoint=self.endpoint,
                    instances=[instance]
                )
                
                if response.predictions:
                    text = response.predictions[0]
                    return self._convert_response(text)
                else:
                    return self._convert_response("Error: No response generated")
                    
            except Exception as e:
                print(f"❌ Vertex AI error: {e}")
                return self._convert_response(f"Error: {str(e)}")
        
        def _convert_messages(self, messages: list) -> str:
            """Convert OpenAI messages to single prompt"""
            prompt_parts = []
            
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                
                if role == "system":
                    prompt_parts.append(f"Instructions: {content}\n\n")
                elif role == "user":
                    prompt_parts.append(f"{content}")
            
            return "".join(prompt_parts)
        
        def _convert_response(self, text: str):
            """Convert Vertex response to OpenAI format"""
            
            class Usage:
                def __init__(self, text):
                    self.prompt_tokens = 100
                    self.completion_tokens = len(str(text).split())
                    self.total_tokens = self.prompt_tokens + self.completion_tokens
            
            class Choice:
                def __init__(self, text):
                    self.message = type('Message', (), {'content': str(text)})()
            
            class Response:
                def __init__(self, text):
                    self.choices = [Choice(text)]
                    self.usage = Usage(text)
            
            return Response(text)
    
    @property
    def chat(self):
        class Chat:
            def __init__(self, client, endpoint):
                self.completions = VertexAIClient.ChatCompletions(client, endpoint)
        
        return Chat(self.client, self.endpoint)
