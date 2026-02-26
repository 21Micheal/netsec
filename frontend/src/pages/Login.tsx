import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { authService } from '../services/auth';

const Login: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, bootstrap } = useAuth();

  const from = (location.state as any)?.from || '/dashboard';
  const [mode, setMode] = useState<'login' | 'bootstrap'>('login');
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('');
  const [persist, setPersist] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [bootstrapRequired, setBootstrapRequired] = useState<boolean | null>(null);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const status = await authService.bootstrapStatus();
        if (!active) return;
        setBootstrapRequired(status.bootstrap_required);
        if (!status.bootstrap_required) {
          setMode('login');
        }
      } catch {
        if (!active) return;
        setBootstrapRequired(false);
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      if (mode === 'bootstrap') {
        await bootstrap(username, password, persist);
      } else {
        await login(username, password, persist);
      }
      navigate(from, { replace: true });
    } catch (err: any) {
      setError(err.message || 'Authentication failed');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 grid place-items-center px-4">
      <div className="w-full max-w-md bg-gray-900 border border-gray-800 rounded-xl p-6">
        <h1 className="text-xl font-semibold mb-2">NetSec Access</h1>
        <p className="text-sm text-gray-400 mb-6">
          {mode === 'login' ? 'Sign in to your operator account.' : 'Bootstrap initial admin account.'}
        </p>
        {bootstrapRequired === false && (
          <div className="text-xs text-amber-300 bg-amber-950/50 border border-amber-800 rounded px-3 py-2 mb-4">
            Bootstrap is already completed on this instance. Use existing credentials to sign in.
          </div>
        )}

        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="block text-xs text-gray-400 mb-1">Username</label>
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 outline-none focus:border-blue-500"
              autoComplete="username"
              required
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 outline-none focus:border-blue-500"
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
              required
            />
          </div>
          <label className="flex items-center gap-2 text-sm text-gray-300">
            <input type="checkbox" checked={persist} onChange={(e) => setPersist(e.target.checked)} />
            Keep session on this browser
          </label>

          {error && <div className="text-sm text-red-400">{error}</div>}

          <button
            type="submit"
            disabled={submitting}
            className="w-full bg-blue-600 hover:bg-blue-500 disabled:opacity-60 rounded py-2 font-medium"
          >
            {submitting ? 'Processing...' : mode === 'login' ? 'Sign In' : 'Bootstrap Admin'}
          </button>
        </form>

        {bootstrapRequired && (
          <button
            className="w-full mt-4 text-sm text-gray-400 hover:text-gray-200"
            onClick={() => setMode((m) => (m === 'login' ? 'bootstrap' : 'login'))}
          >
            {mode === 'login' ? 'Need initial setup? Bootstrap admin' : 'Already have an account? Sign in'}
          </button>
        )}
      </div>
    </div>
  );
};

export default Login;
