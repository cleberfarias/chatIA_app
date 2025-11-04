import express from 'express'
import http from 'http'
import { Server } from 'socket.io'
import cors from 'cors'
import { z } from 'zod'
import { randomUUID } from 'crypto'
import { prisma } from './prisma'



async function bootstrap(){


const app = express()
app.use(cors())
app.use(express.json())

app.get('/health', (_req, res) => res.json({ ok: true }))

// Histórico: últimas N mensagens (padrão 50)
app.get('/messages', async (req, res) => {
  const limit = Math.min(Number(req.query.limit ?? 50), 200)
  const docs = await prisma.message.findMany({
    orderBy: { createdAt: 'desc' },
    take: limit
  })
  
  // Transforma para o formato esperado pelo frontend
  const messages = docs.map(doc => ({
    id: doc.id,
    author: doc.author,
    text: doc.text,
    timestamp: doc.createdAt.getTime(),
    status: doc.status || 'sent',
    type: doc.type,
  })).reverse() // antigo → novo
  
  res.json(messages)
})

const server = http.createServer(app)
const io = new Server(server, {
  cors: { origin: '*', methods: ['GET','POST'] }
})

const MessageSchema = z.object({
  id: z.string().optional(),
  author: z.string().min(1),
  text: z.string().min(1),
  timestamp: z.number().optional(),
  status: z.enum(['sent', 'delivered', 'read']).optional(),
})

io.on('connection', (socket) => {
  console.log('client connected:', socket.id)

  socket.on('chat:send', async (payload) => {
    const parsed = MessageSchema.safeParse(payload)
    if (!parsed.success) {
      console.log('❌ Mensagem inválida:', parsed.error)
      return
    }
    
    // Salva no MongoDB
    try {
      const doc = await prisma.message.create({
        data: {
          author: parsed.data.author,
          text: parsed.data.text,
          status: parsed.data.status || 'sent',
          type: 'text',
        }
      })
      
      console.log('💾 Mensagem salva no MongoDB:', doc.id)
      
      // Envia para todos os clientes conectados
      io.emit('chat:new-message', {
        id: doc.id,
        author: doc.author,
        text: doc.text,
        timestamp: doc.createdAt.getTime(),
        status: doc.status || 'sent',
        type: doc.type,
      })
    } catch (error) {
      console.error('❌ Erro ao salvar mensagem:', error)
    }
  })

  socket.on('disconnect', () => {
    console.log('client disconnected:', socket.id)
  })
})

const PORT = process.env.PORT || 3000
server.listen(PORT, () => console.log(`API on http://localhost:${PORT}`))
}

bootstrap().catch((err) => {
  console.error('Fatal bootstrap error:', err)
  process.exit(1)
})