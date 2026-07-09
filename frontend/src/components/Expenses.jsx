import { useEffect, useMemo, useState } from 'react';
import api from '../api';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer, Legend } from 'recharts';
import { toast } from 'react-toastify';

// FIX: category values must match backend CATEGORY_CHOICES keys (e.g. 'RENT' not 'Rent')
const CATEGORIES = [
  { label: 'Rent', value: 'RENT' }, { label: 'Internet', value: 'INTERNET' },
  { label: 'Electricity', value: 'ELECTRICITY' }, { label: 'Printing Paper', value: 'PAPER' },
  { label: 'Toner/Ink', value: 'TONER' }, { label: 'Employee Wages', value: 'WAGES' },
  { label: 'Transport', value: 'TRANSPORT' }, { label: 'Maintenance', value: 'MAINTENANCE' },
  { label: 'Other', value: 'OTHER' },
];

const PAYMENT_METHODS = [
  { label: 'Cash', value: 'CASH' }, { label: 'M-PESA', value: 'MPESA' },
  { label: 'Bank', value: 'BANK' }, { label: 'Other', value: 'OTHER' },
];

function Expenses({ user }) {
  const today = new Date().toISOString().slice(0, 10);
  const isStaff = Boolean(user?.is_staff || user?.is_superuser);
  const [form, setForm] = useState({ date: today, category: 'OTHER', description: '', amount: '', payment_method: 'CASH' });
  const [expenses, setExpenses] = useState([]);
  const [msg, setMsg] = useState('');
  const [loading, setLoading] = useState(false);

  const load = async () => {
    try {
      const r = await api.get('/expenses/');
      setExpenses(Array.isArray(r.data) ? r.data : []);
    } catch {
      const text = 'Failed to load expenses. Confirm backend is running.';
      setMsg(text);
      toast.warning(text);
    }
  };

  useEffect(() => { load(); }, []);

  const submit = async (e) => {
    e.preventDefault();
    if (!form.description.trim() || !form.amount || Number(form.amount) <= 0) {
      const text = 'Enter a valid description and amount.';
      setMsg(text);
      toast.warning(text);
      return;
    }
    setLoading(true);
    try {
      await api.post('/expenses/', { ...form, date: isStaff ? form.date : today, amount: Number(form.amount) });
      setMsg('Expense recorded successfully.');
      toast.success('Expense recorded successfully.');
      setForm({ date: today, category: 'OTHER', description: '', amount: '', payment_method: 'CASH' });
      await load();
    } catch {
      const text = 'Failed to save expense. Check the backend terminal.';
      setMsg(text);
      toast.error(text);
    }
    finally { setLoading(false); }
  };

  const totalExpenses = useMemo(() => expenses.reduce((s, i) => s + Number(i.amount || 0), 0), [expenses]);

  const byCategory = useMemo(() => {
    const g = {};
    expenses.forEach(i => {
      const k = i.category || 'OTHER';
      g[k] = g[k] || { category: CATEGORIES.find(c => c.value === k)?.label || k, total: 0 };
      g[k].total += Number(i.amount || 0);
    });
    return Object.values(g);
  }, [expenses]);

  const byDate = useMemo(() => {
    const g = {};
    expenses.forEach(i => {
      const k = i.date || i.created_at?.slice(0, 10) || today;
      g[k] = g[k] || { date: k, total: 0 };
      g[k].total += Number(i.amount || 0);
    });
    return Object.values(g).sort((a, b) => a.date.localeCompare(b.date));
  }, [expenses]);

  return (
    <div>
      <h2 className="fw-bold">Expenses</h2>
      <p className="text-muted" style={{ marginBottom: 24 }}>Record and visualize operating expenses.</p>

      {msg && <div className="alert alert-info">{msg}</div>}

      <div className="row mb-4">
        <div className="col-md-4">
          <div className="stat-card">
            <h6>Total Expenses</h6>
            <h3>KES {totalExpenses.toLocaleString()}</h3>
            <small>{expenses.length} records</small>
          </div>
        </div>
        <div className="col-md-8">
          <div className="card">
            <div className="card-header">Add Expense</div>
            <div className="card-body">
              <form onSubmit={submit}>
                <div className="row">
                  <div className="col-md-3">
                    <label className="form-label">Date</label>
                    <input type="date" className="form-control mb-2" value={form.date}
                      disabled={!isStaff}
                      title={!isStaff ? "Only staff can log an expense for a past date." : undefined}
                      onChange={e => setForm({ ...form, date: e.target.value })} />
                    {!isStaff && <small className="text-muted">Locked to today — only staff can backdate.</small>}
                  </div>
                  <div className="col-md-3">
                    <label className="form-label">Category</label>
                    <select className="form-select mb-2" value={form.category} onChange={e => setForm({ ...form, category: e.target.value })}>
                      {CATEGORIES.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
                    </select>
                  </div>
                  <div className="col-md-4">
                    <label className="form-label">Description</label>
                    <input className="form-control mb-2" value={form.description} placeholder="e.g. Bought printing paper" onChange={e => setForm({ ...form, description: e.target.value })} />
                  </div>
                  <div className="col-md-2">
                    <label className="form-label">Amount (KES)</label>
                    <input type="number" className="form-control mb-2" value={form.amount} placeholder="0" onChange={e => setForm({ ...form, amount: e.target.value })} />
                  </div>
                  <div className="col-md-3">
                    <label className="form-label">Payment</label>
                    <select className="form-select mb-2" value={form.payment_method} onChange={e => setForm({ ...form, payment_method: e.target.value })}>
                      {PAYMENT_METHODS.map(p => <option key={p.value} value={p.value}>{p.label}</option>)}
                    </select>
                  </div>
                  <div className="col-md-3 d-flex align-items-end">
                    <button className="btn btn-success w-100" type="submit" disabled={loading} style={{ marginBottom: 8 }}>
                      {loading ? 'Saving…' : 'Save Expense'}
                    </button>
                  </div>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>

      <div className="row mb-4">
        <div className="col-md-6">
          <div className="card">
            <div className="card-header">Expenses by Category</div>
            <div className="card-body">
              {byCategory.length > 0 ? (
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={byCategory}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="category" tick={{ fontSize: 11 }} />
                    <YAxis />
                    <Tooltip formatter={v => `KES ${Number(v).toLocaleString()}`} />
                    <Bar dataKey="total" name="Total" fill="#00d68f" radius={[4,4,0,0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : <p className="text-muted">No expense data yet.</p>}
            </div>
          </div>
        </div>
        <div className="col-md-6">
          <div className="card">
            <div className="card-header">Daily Expenses</div>
            <div className="card-body">
              {byDate.length > 0 ? (
                <ResponsiveContainer width="100%" height={280}>
                  <LineChart data={byDate}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                    <YAxis />
                    <Tooltip formatter={v => `KES ${Number(v).toLocaleString()}`} />
                    <Line dataKey="total" name="Daily Expense" stroke="#0066ff" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              ) : <p className="text-muted">No data yet.</p>}
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">Expense Register</div>
        <div className="card-body" style={{ padding: 0 }}>
          <table className="table">
            <thead>
              <tr>
                <th>Date</th><th>Category</th><th>Description</th><th>Payment</th><th>Amount</th><th>Recorded By</th>
              </tr>
            </thead>
            <tbody>
              {expenses.map(x => (
                <tr key={x.id}>
                  <td>{x.date}</td>
                  <td>{CATEGORIES.find(c => c.value === x.category)?.label || x.category}</td>
                  <td>{x.description}</td>
                  <td>{PAYMENT_METHODS.find(p => p.value === x.payment_method)?.label || x.payment_method}</td>
                  <td style={{ fontFamily: 'var(--mono)', color: 'var(--accent)' }}>KES {Number(x.amount).toLocaleString()}</td>
                  <td style={{ color: 'var(--text-muted)' }}>{x.recorded_by_username || 'Admin'}</td>
                </tr>
              ))}
              {expenses.length === 0 && <tr><td colSpan={6} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 24 }}>No expenses recorded yet.</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default Expenses;
