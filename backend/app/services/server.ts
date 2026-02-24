// server.ts (Node + Express + Socket.IO + PostgreSQL)
import express from 'express';
import http from 'http';
import { Server } from 'socket.io';
import { Pool } from 'pg';

const app = express();
const server = http.createServer(app);
const io = new Server(server, {
  cors: { origin: '*' }
});

const pool = new Pool({
  user: 'postgres',
  host: 'localhost',
  database: 'network_security',
  password: 'your_password',
  port: 5432,
});

// When a client connects
io.on('connection', (socket) => {
  console.log('Client connected:', socket.id);

  // Listen for real-time events
  socket.on('event:update', async (data) => {
    const { userId, eventType, eventData } = data;

    try {
      // Persist to PostgreSQL
      await pool.query(
        `INSERT INTO real_time_events (user_id, event_type, event_data)
         VALUES ($1, $2, $3)`,
        [userId, eventType, eventData]
      );

      console.log('Event saved to DB:', eventType);

      // Broadcast update to all clients
      io.emit('event:notify', { userId, eventType, eventData });
    } catch (error) {
      console.error('DB insert error:', error);
    }
  });

  socket.on('disconnect', () => {
    console.log('Client disconnected:', socket.id);
  });
});

server.listen(5000, () => console.log('Server running on port 5000'));
