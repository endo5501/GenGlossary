export const DEFAULT_OLLAMA_BASE_URL = 'http://localhost:11434'

export const LLM_PROVIDERS = [
  { value: 'ollama', label: 'Ollama' },
  { value: 'openai', label: 'OpenAI' },
] as const
