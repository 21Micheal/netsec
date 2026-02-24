import { useEffect, useRef, useState, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';
import { SocketEvent } from '../types';

const SOCKET_URL = 'http://localhost:5000';

export const useSocket = () => {
  const socketRef = useRef<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<SocketEvent | null>(null);
  const subscribedJobsRef = useRef<Set<string>>(new Set());
  const isConnectingRef = useRef(false); // Prevent multiple connection attempts

  // **FIXED: Connection management**
  useEffect(() => {
    // Prevent multiple connection attempts
    if (socketRef.current || isConnectingRef.current) {
      return;
    }

    isConnectingRef.current = true;
    console.log('🔄 Initializing WebSocket connection...');

    try {
      socketRef.current = io(SOCKET_URL, {
        transports: ['websocket', 'polling'],
        autoConnect: true,
        reconnection: true,
        reconnectionAttempts: 5,
        reconnectionDelay: 1000,
      });

      // Connection events
      const handleConnect = () => {
        console.log('✅ Connected to WebSocket server');
        setIsConnected(true);
        isConnectingRef.current = false;
        
        // **FIXED: Resubscribe to jobs after reconnection**
        if (subscribedJobsRef.current.size > 0) {
          console.log(`🔄 Resubscribing to ${subscribedJobsRef.current.size} jobs after reconnect`);
          subscribedJobsRef.current.forEach(jobId => {
            socketRef.current?.emit('subscribe', { job_id: jobId });
          });
        }
      };

      const handleDisconnect = (reason: string) => {
        console.log('❌ Disconnected from WebSocket server:', reason);
        setIsConnected(false);
        isConnectingRef.current = false;
      };

      const handleConnectError = (error: Error) => {
        console.error('❌ WebSocket connection error:', error);
        setIsConnected(false);
        isConnectingRef.current = false;
      };

      // Message events
      const handleScanUpdate = (data: any) => {
        console.log('📡 Scan update received:', data);
        setLastMessage({ type: 'scan_update', data });
      };

      const handleScanLog = (data: any) => {
        console.log('📝 Scan log:', data);
        setLastMessage({ type: 'scan_log', data });
      };

      const handleError = (data: any) => {
        console.error('💥 WebSocket error:', data);
        setLastMessage({ type: 'error', data });
      };

      const handleSubscribed = (data: any) => {
        console.log('✅ Subscribed to job:', data);
      };

      const handleUnsubscribed = (data: any) => {
        console.log('✅ Unsubscribed from job:', data);
      };

      // Register event listeners
      socketRef.current.on('connect', handleConnect);
      socketRef.current.on('disconnect', handleDisconnect);
      socketRef.current.on('connect_error', handleConnectError);
      socketRef.current.on('scan_update', handleScanUpdate);
      socketRef.current.on('scan_log', handleScanLog);
      socketRef.current.on('error', handleError);
      socketRef.current.on('subscribed', handleSubscribed);
      socketRef.current.on('unsubscribed', handleUnsubscribed);

      // **FIXED: Proper cleanup function**
      return () => {
        console.log('🧹 Cleaning up WebSocket connection');
        
        if (socketRef.current) {
          // Remove all event listeners
          socketRef.current.off('connect', handleConnect);
          socketRef.current.off('disconnect', handleDisconnect);
          socketRef.current.off('connect_error', handleConnectError);
          socketRef.current.off('scan_update', handleScanUpdate);
          socketRef.current.off('scan_log', handleScanLog);
          socketRef.current.off('error', handleError);
          socketRef.current.off('subscribed', handleSubscribed);
          socketRef.current.off('unsubscribed', handleUnsubscribed);
          
          // Disconnect socket
          socketRef.current.disconnect();
          socketRef.current = null;
        }
        
        isConnectingRef.current = false;
        setIsConnected(false);
        // Don't clear subscribedJobsRef here - we want to remember subscriptions
      };

    } catch (error) {
      console.error('❌ Failed to initialize WebSocket:', error);
      isConnectingRef.current = false;
    }
  }, []);

  // **FIXED: Improved subscription with better logging**
  const subscribeToJob = useCallback((jobId: string) => {
    if (!jobId || typeof jobId !== 'string') {
      console.error('❌ Invalid jobId for subscription:', jobId);
      return;
    }

    if (subscribedJobsRef.current.has(jobId)) {
      console.log('🔄 Already subscribed to job:', jobId);
      return;
    }

    if (socketRef.current && isConnected) {
      console.log('🔔 Subscribing to job:', jobId);
      socketRef.current.emit('subscribe', { job_id: jobId });
      subscribedJobsRef.current.add(jobId);
    } else {
      console.log('⏳ Queueing subscription for job (socket not ready):', jobId);
      subscribedJobsRef.current.add(jobId);
    }
  }, [isConnected]);

  // **FIXED: Improved unsubscription**
  const unsubscribeFromJob = useCallback((jobId: string) => {
    if (!jobId) {
      console.error('❌ Invalid jobId for unsubscription');
      return;
    }

    if (!subscribedJobsRef.current.has(jobId)) {
      console.log('🔄 Not subscribed to job:', jobId);
      return;
    }

    if (socketRef.current && isConnected) {
      console.log('🔕 Unsubscribing from job:', jobId);
      socketRef.current.emit('unsubscribe', { job_id: jobId });
    }
    
    subscribedJobsRef.current.delete(jobId);
  }, [isConnected]);

  // **FIXED: Improved bulk unsubscription**
  const unsubscribeFromAllJobs = useCallback(() => {
    if (socketRef.current && isConnected) {
      const jobCount = subscribedJobsRef.current.size;
      console.log(`🔕 Unsubscribing from ${jobCount} jobs`);
      
      subscribedJobsRef.current.forEach(jobId => {
        socketRef.current?.emit('unsubscribe', { job_id: jobId });
      });
    }
    
    subscribedJobsRef.current.clear();
  }, [isConnected]);

  // **ADDED: Debug function**
  const debugSubscriptions = useCallback(() => {
    console.log('📊 Current subscriptions:', Array.from(subscribedJobsRef.current));
    console.log('🔗 Socket connected:', isConnected);
    console.log('🔌 Socket instance:', socketRef.current ? 'exists' : 'null');
  }, [isConnected]);

  return {
    isConnected,
    lastMessage,
    subscribeToJob,
    unsubscribeFromJob,
    unsubscribeFromAllJobs,
    debugSubscriptions, // Added for debugging
    socket: socketRef.current,
  };
};