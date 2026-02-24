import { io, Socket } from 'socket.io-client'

class SocketService {
  private socket: Socket | null = null

  connect() {
    if (!this.socket) {
      this.socket = io('http://localhost:5000', {
        transports: ['websocket', 'polling'],
      })

      this.socket.on('connect', () => console.log('Connected to server'))
      this.socket.on('disconnect', () => console.log('Disconnected from server'))
    }
    return this.socket
  }

  on(event: string, callback: (...args: any[]) => void) {
    this.socket?.on(event, callback)
  }

  off(event: string, callback?: (...args: any[]) => void) {
    this.socket?.off(event, callback)
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
    }
  }
}

export default new SocketService()
