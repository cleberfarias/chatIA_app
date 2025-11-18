import { z } from 'zod';

/**
 * 🆕 Status da mensagem (como WhatsApp)
 * - pending: Enviando... ⏳
 * - sent: Enviado ✓
 * - delivered: Entregue ✓✓
 * - read: Lido (azul) ✓✓
 */
export type MessageStatus = 'pending' | 'sent' | 'delivered' | 'read';

/**
 * 🆕 Informação de anexo (arquivo/imagem)
 */
export const AttachmentSchema = z.object({
  bucket: z.string(),
  key: z.string(),
  filename: z.string(),
  mimetype: z.string(),
});

export type Attachment = z.infer<typeof AttachmentSchema>;

/**
 * Schema de validação para mensagens do chat
 * ✅ Atualizado para suportar Optimistic UI e novos status
 * ✅ Atualizado para suportar anexos (imagens/arquivos)
 */
export const MessageSchema = z.object({
  id: z.string().min(1, 'ID é obrigatório').optional(), // 🔧 Agora opcional (tempId pode existir)
  tempId: z.string().optional(), // 🆕 ID temporário (antes do ACK do servidor)
  author: z.string().min(1, 'Autor é obrigatório'),
  text: z.string().min(1, 'Texto é obrigatório'),
  timestamp: z.number().positive('Timestamp inválido'),
  status: z.enum(['pending', 'sent', 'delivered', 'read']).optional().default('sent'), // 🔧 Adicionado 'pending'
  type: z.enum(['text', 'image', 'file', 'audio']).optional().default('text'),
  userId: z.string().optional(), // 🆕 ID do remetente (quem enviou)
  contactId: z.string().optional(), // 🆕 ID do destinatário (para quem foi enviado)
  attachment: AttachmentSchema.optional(), // 🆕 Dados do anexo (S3/MinIO)
  url: z.string().url().optional(), // 🆕 URL pré-assinada para download
});

/**
 * Schema para mensagens recebidas do socket que podem não ter ID/timestamp
 * Usado para validar payloads brutos antes de processar
 * ✅ Atualizado para suportar anexos
 */
export const IncomingMessageSchema = z.object({
  id: z.string().optional(),
  tempId: z.string().optional(), // 🆕 Suporte para tempId
  author: z.string().min(1),
  text: z.string().min(1),
  timestamp: z.number().optional(),
  status: z.enum(['pending', 'sent', 'delivered', 'read']).optional(), // 🔧 Adicionado 'pending'
  type: z.enum(['text', 'image', 'file', 'audio']).optional(),
  userId: z.string().optional(), // 🆕 ID do remetente
  contactId: z.string().optional(), // 🆕 ID do destinatário
  attachment: AttachmentSchema.optional(), // 🆕 Dados do anexo
  url: z.string().optional(), // 🆕 URL pré-assinada (não precisa validar URL aqui)
});

/**
 * 🆕 Informação de usuário digitando
 */
export type TypingInfo = {
  userId: string;
  author: string;
  chatId: string;
  isTyping: boolean;
};

/**
 * Type inference dos schemas
 */
export type Message = z.infer<typeof MessageSchema>;
export type IncomingMessage = z.infer<typeof IncomingMessageSchema>;

/**
 * Valida e normaliza uma mensagem recebida
 * 🔧 Atualizado para suportar tempId e status 'pending'
 */
export function validateAndNormalizeMessage(data: unknown): Message {
  // Valida o payload bruto
  const parsed = IncomingMessageSchema.safeParse(data);
  
  if (!parsed.success) {
    console.error('❌ Erro ao validar payload da mensagem:', {
      payload: data,
      errors: parsed.error.issues.map(e => ({
        path: e.path.join('.'),
        message: e.message,
        code: e.code,
      })),
    });
    throw new Error('Mensagem inválida: ' + parsed.error.issues.map((e) => e.message).join(', '));
  }

  // 🔧 Normaliza garantindo ID ou tempId
  const normalized: Message = {
    ...parsed.data,
    // Se tem ID, usa. Se não, gera tempId
    id: parsed.data.id,
    tempId: parsed.data.tempId || (parsed.data.id ? undefined : `temp_${Date.now()}`),
    timestamp: parsed.data.timestamp || Date.now(),
    type: parsed.data.type || 'text',
    status: parsed.data.status || 'sent',
  };

  // Valida a mensagem normalizada
  const validated = MessageSchema.safeParse(normalized);
  
  if (!validated.success) {
    console.error('❌ Falha ao normalizar mensagem:', {
      original: data,
      normalized,
      errors: validated.error.issues.map(e => ({
        path: e.path.join('.'),
        message: e.message,
        code: e.code,
      })),
    });
    throw new Error(
      'Falha na normalização: ' + 
      validated.error.issues.map((e) => `${e.path.join('.')}: ${e.message}`).join(', ')
    );
  }

  return validated.data;
}