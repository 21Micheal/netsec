import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { authService, AuthUser } from '../services/auth';

const Settings: React.FC = () => {
  const { user } = useAuth();
  const [users, setUsers] = useState<AuthUser[]>([]);
  const [newUsername, setNewUsername] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newRole, setNewRole] = useState<'admin' | 'analyst'>('analyst');
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const isAdmin = user?.role === 'admin';

  const loadUsers = async () => {
    if (!isAdmin) return;
    try {
      const rows = await authService.listUsers();
      setUsers(rows);
    } catch (err: any) {
      setError(err.message || 'Failed to load users');
    }
  };

  useEffect(() => {
    loadUsers();
  }, [isAdmin]);

  const createUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage(null);
    setError(null);
    setSubmitting(true);
    try {
      await authService.register(newUsername, newPassword, newRole);
      setMessage(`User ${newUsername} created.`);
      setNewUsername('');
      setNewPassword('');
      setNewRole('analyst');
      await loadUsers();
    } catch (err: any) {
      setError(err.message || 'Failed to create user');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-gray-800 border border-gray-700 rounded-xl p-5">
        <h2 className="text-lg font-semibold mb-2">Session</h2>
        <p className="text-gray-300">
          Signed in as <span className="font-semibold">{user?.username}</span> ({user?.role})
        </p>
      </div>

      {isAdmin && (
        <>
          <div className="bg-gray-800 border border-gray-700 rounded-xl p-5">
            <h2 className="text-lg font-semibold mb-4">Create User</h2>
            <form onSubmit={createUser} className="grid md:grid-cols-3 gap-3">
              <input
                value={newUsername}
                onChange={(e) => setNewUsername(e.target.value)}
                placeholder="username"
                className="bg-gray-900 border border-gray-700 rounded px-3 py-2"
                required
              />
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="password (10+ chars)"
                className="bg-gray-900 border border-gray-700 rounded px-3 py-2"
                required
                minLength={10}
              />
              <div className="flex gap-2">
                <select
                  value={newRole}
                  onChange={(e) => setNewRole(e.target.value as 'admin' | 'analyst')}
                  className="bg-gray-900 border border-gray-700 rounded px-3 py-2 flex-1"
                >
                  <option value="analyst">analyst</option>
                  <option value="admin">admin</option>
                </select>
                <button
                  disabled={submitting}
                  className="bg-blue-600 hover:bg-blue-500 disabled:opacity-60 rounded px-4 py-2"
                >
                  Create
                </button>
              </div>
            </form>
            {message && <p className="text-green-400 text-sm mt-3">{message}</p>}
            {error && <p className="text-red-400 text-sm mt-3">{error}</p>}
          </div>

          <div className="bg-gray-800 border border-gray-700 rounded-xl p-5">
            <h2 className="text-lg font-semibold mb-4">Users</h2>
            <div className="space-y-2">
              {users.map((u) => (
                <div key={u.id} className="flex justify-between text-sm border-b border-gray-700 pb-2">
                  <span>{u.username}</span>
                  <span className="text-gray-400">{u.role}</span>
                </div>
              ))}
              {!users.length && <p className="text-gray-400 text-sm">No users found.</p>}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default Settings;
