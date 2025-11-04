import express from 'express'
import http from 'http'
import { Server } from 'socket.io'
import cors from 'cors'
import { z } from 'zod'
import { randomUUID } from 'crypto'

const app = express()
app.use(cors())
app.use(express.json())

app.get('/health', (_req, res) => res.json({ ok: true }))

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

  socket.on('chat:new-message', (payload) => {
    const parsed = MessageSchema.safeParse(payload)
    if (!parsed.success) {
      console.log('❌ Mensagem inválida:', parsed.error)
      return
    }
    
    // Garante que a mensagem tenha ID e timestamp
    const message = {
      ...parsed.data,
      id: parsed.data.id || randomUUID(),
      timestamp: parsed.data.timestamp || Date.now(),
    }
    
    console.log('📨 Mensagem processada:', message)
    
    // Envia para todos os clientes conectados
    io.emit('chat:new-message', message)
  })

  socket.on('disconnect', () => {
    console.log('client disconnected:', socket.id)
  })
})

const PORT = process.env.PORT || 3000
server.listen(PORT, () => console.log(`API on http://localhost:${PORT}`))
