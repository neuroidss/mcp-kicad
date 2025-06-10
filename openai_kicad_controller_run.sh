source venv/bin/activate

#export GEMINI_API_KEY="your-google-ai-key"
export OPENAI_API_KEY=$GEMINI_API_KEY
export OPENAI_API_BASE_URL="https://generativelanguage.googleapis.com/v1beta/openai"
export OPENAI_LLM_MODEL="gemini-2.5-flash-preview-05-20"

python openai_kicad_controller.py
