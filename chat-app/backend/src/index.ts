import express from 'express'
import http from 'http'
import { Server } from 'socket.io'
import cors from 'cors'
import { z } from 'zod'

const app = express()
app.use(cors())
app.use(express.json())

app.get('/health', (_req, res) => res.json({ ok: true }))

const server = http.createServer(app)
const io = new Server(server, {
  cors: { origin: '*', methods: ['GET','POST'] }
})

const MessageSchema = z.object({
  author: z.string().min(1),
  text: z.string().min(1),
  timestamp: z.number().optional()
})

io.on('connection', (socket) => {
  console.log('client connected:', socket.id)

  socket.on('chat:new-message', (payload) => {
    const parsed = MessageSchema.safeParse(payload)
    if (!parsed.success) return
    io.emit('chat:new-message', parsed.data)
  })

  socket.on('disconnect', () => {
    console.log('client disconnected:', socket.id)
  })
})

const PORT = process.env.PORT || 3000
server.listen(PORT, () => console.log(`API on http://localhost:${PORT}`))
