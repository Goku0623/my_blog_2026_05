import request from './index'

export type AssistantRole = 'user' | 'assistant'

export interface AssistantHistoryMessage {
  role: AssistantRole
  content: string
}

export interface AssistantChatRequest {
  message: string
  session_id?: string | null
  history?: AssistantHistoryMessage[]
}

export interface AssistantChatData {
  reply: string
  session_id?: string | null
}

export const assistantChat = (payload: AssistantChatRequest) => {
  return request.post<{ data: AssistantChatData }>('/assistant/chat', payload, {
    timeout: 65000,
  })
}
