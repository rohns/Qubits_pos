import { useEffect, useMemo, useState } from 'react';
import api from '../api';
import { toast } from 'react-toastify';

export default function Credit() {
  const [data, setData]         = useState(null);
  const [search, setSearch]     = useState('');
  const [loading, setLoading]   = useState(false);
  const [paying, setPaying]     = useState(null); // the sale currently being paid against
  const [amount, setAmount]     = useState('');
  const [method, setMethod]     = useState('CASH');
  const [mpesaRef, setMpesaRef] = useState('');
  const [busy, setBusy]         = useState(false);

  const load = async (name = '') => {
    setLoading(true);
    try {
      const r = await api.get('/sales/credit/', { params: name ? { customer_name: name } : {} });
      setData(r.data);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to load the credit ledger.');
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const openPay = sale => {
    setPaying(sale);
    setAmount(sale.remaining_balance);
    setMethod('CASH');
    setMpesaRef('');
  };

  const submitPayment = async () => {
    if (!paying) return;
    if (!amount || Number(amount) <= 0) return toast.warning('Enter an amount greater than zero.');
    if (Number(amount) > paying.remaining_balance) {
      return toast.warning(`Amount can't exceed the remaining balance of KES ${paying.remaining_balance.toLocaleString()}.`);
    }
    if (method === 'MPESA' && !mpesaRef.trim()) return toast.warning("Enter the M-PESA confirmation code from the customer's SMS.");
    setBusy(true);
    try {
      const payload = { sale_id: paying.sale_id, amount, method };
      if (method === 'MPESA') payload.mpesa_reference = mpesaRef.trim().toUpperCase();
      const r = await api.post('/payments/credit-payment/', payload);
      if (r.data.fully_settled) {
        toast.success(`${paying.customer_name}'s tab fully settled.`);
      } else {
        toast.info(`Payment recorded — KES ${Number(r.data.remaining_balance).toLocaleString()} still owed by ${paying.customer_name}.`);
      }
      setPaying(null);
      await load(search);
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to record this payment.');
    } finally { setBusy(false); }
  };

  const timeAgo = iso => {
    const days = Math.floor((Date.now() - new Date(iso)) / 86400000);
    if (days <= 0) return 'today';
    if (days === 1) return '1 day ago';
    return `${days} days ago`;
  };

  const sales = data?.sales || [];

  return (
    <div>
      <div className="d-flex align-items-center justify-content-between mb-3" style={{ flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h2 className="fw-bold">Credit / Tab Ledger</h2>
          <p className="text-muted">Services given out but not yet paid for — who owes what, and since when.</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <input className="form-control form-control-sm" style={{ width: 200 }} placeholder="Search customer name…"
            value={search} onChange={e => setSearch(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && load(search)} />
          <button className="btn btn-outline-secondary btn-sm" onClick={() => load(search)} disabled={loading}>
            {loading ? 'Loading…' : 'Search'}
          </button>
          {search && (
            <button className="btn btn-outline-secondary btn-sm" onClick={() => { setSearch(''); load(); }}>Clear</button>
          )}
        </div>
      </div>

      <div className="row mb-4">
        <div className="col-md-4">
          <div className="stat-card" style={{ borderLeft: '3px solid #ff4757' }}>
            <h6>Total Outstanding</h6>
            <h3 style={{ color: '#ff4757' }}>{data?.total_outstanding_display || 'KES 0.00'}</h3>
            <small>{data?.count || 0} unpaid sales</small>
          </div>
        </div>
        <div className="col-md-8">
          <div className="card">
            <div className="card-header">Owed By Customer</div>
            <div className="card-body" style={{ padding: 0 }}>
              <table className="table table-sm mb-0">
                <thead><tr><th>Customer</th><th>Open Sales</th><th style={{ textAlign: 'right' }}>Total Owed</th></tr></thead>
                <tbody>
                  {(data?.by_customer || []).map((c, i) => (
                    <tr key={i}>
                      <td>{c.customer_name}</td>
                      <td>{c.open_sales}</td>
                      <td style={{ textAlign: 'right', fontFamily: 'var(--mono)', color: '#ff4757' }}>{c.total_owed_display}</td>
                    </tr>
                  ))}
                  {!(data?.by_customer || []).length && (
                    <tr><td colSpan={3} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 16 }}>Nobody currently owes you anything 🎉</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      {paying && (
        <div className="card mb-4" style={{ borderColor: 'var(--accent)' }}>
          <div className="card-header">
            Record Payment — {paying.customer_name} · {paying.receipt_number}
            <button className="btn btn-sm btn-outline-secondary" onClick={() => setPaying(null)}>✕</button>
          </div>
          <div className="card-body">
            <p className="text-muted" style={{ fontSize: 13, marginBottom: 12 }}>
              Owed: <strong>{paying.remaining_balance_display}</strong> of {paying.total_amount_display} total
              {paying.amount_paid_so_far > 0 && <> ({paying.amount_paid_so_far_display} already paid)</>}.
              You can enter any amount up to the balance — partial payments are fine.
            </p>
            <div className="row">
              <div className="col-md-3">
                <label className="form-label">Amount Received (KES)</label>
                <input type="number" className="form-control mb-2" value={amount}
                  max={paying.remaining_balance} onChange={e => setAmount(e.target.value)} autoFocus />
              </div>
              <div className="col-md-3">
                <label className="form-label">Method</label>
                <select className="form-select mb-2" value={method} onChange={e => setMethod(e.target.value)}>
                  <option value="CASH">💵 Cash</option>
                  <option value="MPESA">📱 M-PESA</option>
                </select>
              </div>
              {method === 'MPESA' && (
                <div className="col-md-4">
                  <label className="form-label">M-PESA Confirmation Code (required)</label>
                  <input className="form-control mb-2" placeholder="e.g. QGH8XABCDE" value={mpesaRef}
                    onChange={e => setMpesaRef(e.target.value.toUpperCase())} style={{ textTransform: 'uppercase' }} />
                </div>
              )}
              <div className={method === 'MPESA' ? 'col-md-2' : 'col-md-6'} style={{ display: 'flex', alignItems: 'flex-end' }}>
                <button className="btn btn-success w-100 mb-2" onClick={submitPayment} disabled={busy}>
                  {busy ? 'Saving…' : 'Record Payment'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="card">
        <div className="card-header">All Outstanding Tabs — oldest first</div>
        <div className="card-body" style={{ padding: 0 }}>
          <table className="table">
            <thead>
              <tr><th>Customer</th><th>Phone</th><th>Items</th><th>Offered</th><th>Cashier</th><th style={{ textAlign: 'right' }}>Amount</th><th style={{ textAlign: 'right' }}>Paid</th><th style={{ textAlign: 'right' }}>Owed</th><th>Action</th></tr>
            </thead>
            <tbody>
              {sales.map(s => (
                <tr key={s.sale_id}>
                  <td>{s.customer_name || 'Unknown'}</td>
                  <td style={{ color: 'var(--text-muted)' }}>{s.customer_phone || '—'}</td>
                  <td style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                    {s.items.map(it => `${it.service} ×${it.quantity}`).join(', ')}
                  </td>
                  <td style={{ fontSize: 12 }}>
                    {new Date(s.offered_at).toLocaleString('en-KE')}
                    <div className="text-muted" style={{ fontSize: 11 }}>{timeAgo(s.offered_at)}</div>
                  </td>
                  <td>{s.cashier || '—'}</td>
                  <td style={{ textAlign: 'right', fontFamily: 'var(--mono)' }}>{s.total_amount_display}</td>
                  <td style={{ textAlign: 'right', fontFamily: 'var(--mono)', color: 'var(--text-muted)' }}>
                    {s.amount_paid_so_far > 0 ? s.amount_paid_so_far_display : '—'}
                  </td>
                  <td style={{ textAlign: 'right', fontFamily: 'var(--mono)', color: '#ff4757', fontWeight: 600 }}>{s.remaining_balance_display}</td>
                  <td>
                    <button className="btn btn-sm btn-outline-success" onClick={() => openPay(s)}>Record Payment</button>
                  </td>
                </tr>
              ))}
              {!sales.length && (
                <tr><td colSpan={9} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 24 }}>
                  {loading ? 'Loading…' : 'No outstanding tabs.'}
                </td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
