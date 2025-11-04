import { z } from 'zod';

/**
 * Schema de validação para mensagens do chat
 * Garante que todas as mensagens tenham os campos obrigatórios
 */
export const MessageSchema = z.object({
  id: z.string().min(1, 'ID é obrigatório'),
  author: z.string().min(1, 'Autor é obrigatório'),
  text: z.string().min(1, 'Texto é obrigatório'),
  timestamp: z.number().positive('Timestamp inválido'),
  status: z.enum(['sent', 'delivered', 'read']).optional(),
  type: z.enum(['text', 'image', 'file', 'audio']).optional().default('text'),
});

/**
 * Schema para mensagens recebidas do socket que podem não ter ID/timestamp
 * Usado para validar payloads brutos antes de processar
 */
export const IncomingMessageSchema = z.object({
  id: z.string().optional(),
  author: z.string().min(1),
  text: z.string().min(1),
  timestamp: z.number().optional(),
  status: z.enum(['sent', 'delivered', 'read']).optional(),
  type: z.enum(['text', 'image', 'file', 'audio']).optional(),
});

/**
 * Type inference dos schemas
 */
export type Message = z.infer<typeof MessageSchema>;
export type IncomingMessage = z.infer<typeof IncomingMessageSchema>;

/**
 * Valida e normaliza uma mensagem recebida
 * Garante que tenha ID e timestamp válidos
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

  // Normaliza garantindo ID e timestamp
  const normalized: Message = {
    ...parsed.data,
    id: parsed.data.id || crypto.randomUUID(),
    timestamp: parsed.data.timestamp || Date.now(),
    type: parsed.data.type || 'text',
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
