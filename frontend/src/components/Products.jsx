import { useEffect, useState } from 'react';
import api from '../api';
import { toast } from 'react-toastify';

const CATEGORY_CHOICES = [
  { value: 'PRINTING',   label: 'Printing' },
  { value: 'SCANNING',   label: 'Scanning' },
  { value: 'GOVERNMENT', label: 'Government Services' },
  { value: 'INTERNET',   label: 'Internet & Email' },
  { value: 'FINANCIAL',  label: 'Financial Services' },
  { value: 'DOCUMENTS',  label: 'Documents & Certificates' },
  { value: 'PHONE',      label: 'Phone Services' },
  { value: 'OTHER',      label: 'Other' },
];

export default function Products() {
  const [products, setProducts] = useState([]);
  const [form, setForm]         = useState({ name: '', price: '', category: 'OTHER' });
  const [editing, setEditing]   = useState(null);
  const [loading, setLoading]   = useState(false);

  const load = async () => {
    try {
      const r = await api.get('/products/');
      setProducts(r.data);
    } catch { toast.error('Failed to load products.'); }
  };

  useEffect(() => { load(); }, []);

  const submit = async e => {
    e.preventDefault();
    if (!form.name.trim() || !form.price || Number(form.price) <= 0) {
      return toast.warning('Enter a valid name and price.');
    }
    setLoading(true);
    try {
      if (editing) {
        await api.patch(`/products/${editing.id}/`, { ...form, price: Number(form.price) });
        toast.success('Product updated.');
        setEditing(null);
      } else {
        await api.post('/products/', { ...form, price: Number(form.price), active: true, is_service: true });
        toast.success('Product created.');
      }
      setForm({ name: '', price: '', category: 'OTHER' });
      await load();
    } catch (err) {
      toast.error(err?.response?.data?.name?.[0] || 'Failed to save product.');
    } finally { setLoading(false); }
  };

  const startEdit = p => {
    setEditing(p);
    setForm({ name: p.name, price: p.price, category: p.category || 'OTHER' });
  };

  const cancelEdit = () => {
    setEditing(null);
    setForm({ name: '', price: '', category: 'OTHER' });
  };

  const toggleActive = async p => {
    try {
      await api.patch(`/products/${p.id}/`, { active: !p.active });
      toast.success(`${p.name} ${p.active ? 'deactivated' : 'activated'}.`);
      await load();
    } catch { toast.error('Failed to update product.'); }
  };

  const grouped = {};
  products.forEach(p => {
    const cat = p.category || 'OTHER';
    (grouped[cat] = grouped[cat] || []).push(p);
  });
  const cats = CATEGORY_CHOICES.filter(c => grouped[c.value]);

  return (
    <div>
      <h2 className="fw-bold">Products Management</h2>
      <p className="text-muted" style={{ marginBottom: 24 }}>Add, edit, and manage services offered in your cyber café.</p>

      <div className="row mb-4">
        <div className="col-md-5">
          <div className="card">
            <div className="card-header">{editing ? 'Edit Product' : 'Add New Product'}</div>
            <div className="card-body">
              <form onSubmit={submit}>
                <label className="form-label">Name</label>
                <input className="form-control mb-2" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} required />

                <label className="form-label">Price (KES)</label>
                <input type="number" className="form-control mb-2" value={form.price} placeholder="0" onChange={e => setForm({ ...form, price: e.target.value })} required />

                <label className="form-label">Category</label>
                <select className="form-select mb-3" value={form.category} onChange={e => setForm({ ...form, category: e.target.value })}>
                  {CATEGORY_CHOICES.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
                </select>

                <div style={{ display: 'flex', gap: 8 }}>
                  <button className="btn btn-success flex-1" type="submit" disabled={loading}>
                    {loading ? 'Saving…' : editing ? 'Update Product' : 'Add Product'}
                  </button>
                  {editing && (
                    <button type="button" className="btn btn-outline-secondary" onClick={cancelEdit}>Cancel</button>
                  )}
                </div>
              </form>
            </div>
          </div>
        </div>

        <div className="col-md-7">
          <div className="card">
            <div className="card-header">
              All Products ({products.length})
              <span style={{ fontSize: 11, color: 'var(--text-muted)', marginLeft: 8 }}>
                {products.filter(p => p.active).length} active
              </span>
            </div>
            <div className="card-body" style={{ padding: 0 }}>
              {cats.length === 0 ? (
                <p className="text-muted" style={{ textAlign: 'center', padding: '32px 0' }}>
                  No products yet. Add your first service above or run python manage.py seed_services.
                </p>
              ) : (
                cats.map(cat => (
                  <div key={cat.value} style={{ marginBottom: 16 }}>
                    <div style={{ background: 'var(--surface2)', padding: '8px 16px', borderBottom: '1px solid var(--border)', fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                      {cat.label} ({grouped[cat.value].length})
                    </div>
                    <table className="table table-sm">
                      <thead>
                        <tr><th>Name</th><th>Price</th><th>Status</th><th>Actions</th></tr>
                      </thead>
                      <tbody>
                        {grouped[cat.value].map(p => (
                          <tr key={p.id} style={{ opacity: p.active ? 1 : 0.5 }}>
                            <td>{p.name}</td>
                            <td style={{ fontFamily: 'var(--mono)', fontSize: 13 }}>KES {Number(p.price).toLocaleString()}</td>
                            <td>
                              <span className={`status-badge ${p.active ? 'active' : 'inactive'}`}>
                                {p.active ? 'Active' : 'Inactive'}
                              </span>
                            </td>
                            <td>
                              <div style={{ display: 'flex', gap: 6 }}>
                                <button className="btn btn-sm btn-outline-dark" onClick={() => startEdit(p)}>Edit</button>
                                <button className="btn btn-sm btn-outline-secondary" onClick={() => toggleActive(p)}>
                                  {p.active ? 'Deactivate' : 'Activate'}
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>

      <style>{`
        .status-badge { display:inline-block; padding:2px 8px; border-radius:12px; font-size:11px; font-weight:500; }
        .status-badge.active { background:rgba(0,214,143,0.15); color:#00d68f; }
        .status-badge.inactive { background:rgba(138,151,176,0.15); color:var(--text-muted); }
        .flex-1 { flex:1; }
      `}</style>
    </div>
  );
}
