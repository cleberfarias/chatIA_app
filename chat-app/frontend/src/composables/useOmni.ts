/**
 * Composable para integração omnichannel
 * Permite envio de mensagens para WhatsApp, Instagram e Facebook
 */

export interface SendOmniParams {
  channel: 'whatsapp' | 'instagram' | 'facebook' | 'wa-dev'
  recipient: string
  text: string
  session?: string // Obrigatório para wa-dev (WPPConnect)
}

export interface SendOmniResponse {
  success: boolean
  channel: string
  recipient: string
  messageId?: string
  error?: string
}

/**
 * Envia mensagem via canal omnichannel especificado
 * 
 * @param baseUrl - URL base da API (ex: http://localhost:3000)
 * @param params - Parâmetros da mensagem
 * @throws Error se a requisição falhar
 */
export async function sendOmni(
  baseUrl: string,
  params: SendOmniParams
): Promise<SendOmniResponse> {
  const response = await fetch(`${baseUrl}/omni/send`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(params)
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Erro desconhecido' }))
    throw new Error(error.detail || `Erro ao enviar mensagem: ${response.status}`)
  }

  return response.json()
}

/**
 * Inicia sessão WPPConnect (device-based WhatsApp)
 * Retorna QR code e informações da sessão
 * 
 * @param baseUrl - URL base da API
 * @param session - Nome da sessão (ex: "default")
 */
export async function startWppSession(
  baseUrl: string,
  session: string
): Promise<{ qr?: string; status: string }> {
  const response = await fetch(`${baseUrl}/omni/wpp/start`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ session })
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Erro desconhecido' }))
    throw new Error(error.detail || `Erro ao iniciar sessão: ${response.status}`)
  }

  return response.json()
}

/**
 * Obtém QR code de uma sessão WPPConnect existente
 * 
 * @param baseUrl - URL base da API
 * @param session - Nome da sessão
 */
export async function getWppQrCode(
  baseUrl: string,
  session: string
): Promise<{ qr: string }> {
  const response = await fetch(`${baseUrl}/omni/wpp/qr?session=${session}`)

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Erro desconhecido' }))
    throw new Error(error.detail || `Erro ao obter QR code: ${response.status}`)
  }

  return response.json()
}
