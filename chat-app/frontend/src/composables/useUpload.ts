// src/composables/useUpload.ts
export type UploadGrant = { key: string; putUrl: string }
export type ConfirmIn = { key: string; filename: string; mimetype: string; author: string }
export type UploadMessage = {
  id: string; author: string; text: string; type: 'image'|'file'|'audio'; status: string;
  timestamp: number; attachment?: any; url?: string
}

/**
 * PUT para URL pré-assinada com progresso (0-100).
 * Usa XMLHttpRequest porque fetch não expõe progresso nativamente.
 */
export function putWithProgress(putUrl: string, file: File, onProgress?: (pct: number) => void) {
  return new Promise<void>((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    xhr.open('PUT', putUrl, true)
    xhr.setRequestHeader('Content-Type', file.type || 'application/octet-stream')
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && onProgress) {
        onProgress(Math.round((e.loaded / e.total) * 100))
      }
    }
    xhr.onload = () => (xhr.status >= 200 && xhr.status < 300) ? resolve() : reject(new Error(`PUT failed: ${xhr.status}`))
    xhr.onerror = () => reject(new Error('Network error on PUT'))
    xhr.send(file)
  })
}

export async function requestGrant(baseUrl: string, file: File): Promise<UploadGrant> {
  const res = await fetch(`${baseUrl}/uploads/grant`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ filename: file.name, mimetype: file.type, size: file.size })
  })
  if (!res.ok) throw new Error('Falha no grant upload')
  return res.json()
}

export async function confirmUpload(baseUrl: string, body: ConfirmIn): Promise<UploadMessage> {
  const res = await fetch(`${baseUrl}/uploads/confirm`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  })
  if (!res.ok) throw new Error('Falha no confirm upload')
  const data = await res.json()
  return data.message as UploadMessage
}

/**
 * Pipeline completo: grant → PUT com progresso → confirm
 */
export async function uploadAndSend(
  baseUrl: string,
  file: File,
  author: string,
  onProgress?: (pct: number) => void
): Promise<UploadMessage> {
  const { key, putUrl } = await requestGrant(baseUrl, file)
  await putWithProgress(putUrl, file, onProgress)
  return confirmUpload(baseUrl, { key, filename: file.name, mimetype: file.type, author })
}
