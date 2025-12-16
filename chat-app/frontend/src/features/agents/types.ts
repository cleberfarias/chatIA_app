export interface CustomAgentPayload {
  name: string
  emoji: string
  prompt: string
  specialties: string[]
  openaiApiKey: string
  openaiAccount?: string
}

export interface CustomAgentSummary {
  name: string
  emoji: string
  key: string
  specialties: string[]
  createdAt?: string
}
