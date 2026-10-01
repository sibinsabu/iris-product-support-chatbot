/**
 * TechFix AI - Gadget Repair & Support Copilot
 * Fixing Mobiles, Laptops, Earphones, and Smart Gadgets
 */

// Global Repair Order / Cart State
let cart = [
  {
    id: "iphone-back-glass-repair",
    name: "iPhone Back Glass Laser Replacement",
    price: 2499,
    quantity: 1,
    category: "Mobile Repair",
    compatibility: "iPhone 12 / 13 / 14 / 15 series"
  }
];

document.addEventListener('DOMContentLoaded', () => {
  renderCart();
  initHealthBeacon();
  initDragAndDropZones();
});

// Toast Notifications
function showToast(message, type = 'info') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  
  let iconSvg = '';
  if (type === 'success') {
    iconSvg = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="width:18px;height:18px;"><polyline points="20 6 9 17 4 12"></polyline></svg>`;
  } else if (type === 'error') {
    iconSvg = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="width:18px;height:18px;"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>`;
  } else {
    iconSvg = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="width:18px;height:18px;"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>`;
  }

  toast.innerHTML = `
    ${iconSvg}
    <span>${escapeHtml(message)}</span>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// Copy to Clipboard
async function copyToClipboard(text, buttonElement) {
  try {
    await navigator.clipboard.writeText(text);
    if (buttonElement) {
      const origHtml = buttonElement.innerHTML;
      buttonElement.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="width:14px;height:14px;"><polyline points="20 6 9 17 4 12"></polyline></svg> Copied`;
      setTimeout(() => { buttonElement.innerHTML = origHtml; }, 2000);
    }
    showToast('Copied to clipboard', 'success');
  } catch (err) {
    showToast('Failed to copy', 'error');
  }
}

// Parse Markdown & Interactive Repair/Product Cards
function renderMarkdown(md) {
  if (!md) return '';

  let html = md;

  // Extract and replace :::product { ... } ::: blocks
  html = html.replace(/:::product\s*([\s\S]*?):::/g, (match, jsonStr) => {
    try {
      const product = JSON.parse(jsonStr.trim());
      const encodedProduct = encodeURIComponent(JSON.stringify(product));
      return `
        <div class="product-card-inline">
          <div class="product-thumb">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"></path></svg>
          </div>
          <div class="product-details">
            <div class="product-meta-row">
              <span class="product-badge">${escapeHtml(product.category || 'Repair Service')}</span>
              <span class="product-compat">${escapeHtml(product.compatibility || 'All Models')} &bull; ${escapeHtml(product.turnaround || 'Same Day')}</span>
            </div>
            <div class="product-title">${escapeHtml(product.name)}</div>
            <div class="product-desc">${escapeHtml(product.desc || '')}</div>
          </div>
          <div class="product-buy-row">
            <div class="product-price">₹${Math.round(parseFloat(product.price)).toLocaleString('en-IN')}</div>
            <button class="btn-add-to-cart" onclick="addProductFromChat('${encodedProduct}', this)">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="width:14px;height:14px;"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
              Book Repair
            </button>
          </div>
        </div>
      `;
    } catch (e) {
      return '';
    }
  });

  // Code blocks
  html = html.replace(/```([a-zA-Z0-9_\-\+]*)\n([\s\S]*?)```/g, (match, lang, code) => {
    const rawId = 'code-' + Math.random().toString(36).substring(2, 8);
    return `
      <div style="background:#0f172a; border:1px solid #e2e8f0; border-radius:8px; margin:0.75rem 0; overflow:hidden;">
        <div style="display:flex; justify-content:space-between; padding:0.35rem 0.8rem; background:rgba(255,255,255,0.05); font-family:var(--font-mono); font-size:0.72rem; color:#94a3b8;">
          <span>${lang || 'Diagnostic Code'}</span>
          <button style="background:none; border:none; color:var(--primary-400); cursor:pointer;" onclick="copyCodeBlock('${rawId}', this)">Copy</button>
        </div>
        <pre style="padding:0.85rem; font-family:var(--font-mono); font-size:0.84rem; overflow-x:auto; color:#f8fafc;"><code id="${rawId}">${escapeHtml(code.trim())}</code></pre>
      </div>
    `;
  });

  // Inline code
  html = html.replace(/`([^`]+)`/g, (match, code) => `<code style="font-family:var(--font-mono); font-size:0.85em; background:#f1f5f9; padding:0.15rem 0.35rem; border-radius:4px; color:var(--primary-600);">${escapeHtml(code)}</code>`);

  // Headers
  html = html.replace(/^### (.*$)/gim, '<h3 style="font-size:1.05rem; font-weight:700; color:var(--text-title); margin:0.8rem 0 0.3rem;">$1</h3>');
  html = html.replace(/^## (.*$)/gim, '<h2 style="font-size:1.15rem; font-weight:700; color:var(--text-title); margin:1rem 0 0.4rem;">$1</h2>');
  html = html.replace(/^# (.*$)/gim, '<h1 style="font-size:1.3rem; font-weight:800; color:var(--text-title); margin:1rem 0 0.5rem;">$1</h1>');

  // Bold & Italic
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');

  // Lists
  html = html.replace(/^\s*[-*]\s+(.*$)/gim, '<li style="margin-bottom:0.25rem;">$1</li>');
  html = html.replace(/(<li>.*<\/li>)/gms, '<ul style="margin:0.4rem 0 0.75rem 1.25rem; color:var(--text-body);">$1</ul>');
  html = html.replace(/<\/ul>\s*<ul[^>]*>/g, '');

  html = html.replace(/^\s*(\d+)\.\s+(.*$)/gim, '<li value="$1" style="margin-bottom:0.25rem;">$2</li>');

  // Paragraphs
  const parts = html.split(/\n{2,}/);
  html = parts.map(p => {
    p = p.trim();
    if (!p) return '';
    if (p.startsWith('<h') || p.startsWith('<div') || p.startsWith('<ul') || p.startsWith('<ol')) return p;
    return `<p style="margin-bottom:0.6rem; color:var(--text-body);">${p.replace(/\n/g, '<br>')}</p>`;
  }).join('');

  return html;
}

function copyCodeBlock(id, btn) {
  const el = document.getElementById(id);
  if (el) copyToClipboard(el.innerText, btn);
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// Repair Booking / Cart Functions
function addProductFromChat(encodedProduct, btn) {
  try {
    const product = JSON.parse(decodeURIComponent(encodedProduct));
    addToCart(product);

    if (btn) {
      const orig = btn.innerHTML;
      btn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="width:14px;height:14px;"><polyline points="20 6 9 17 4 12"></polyline></svg> Booked`;
      btn.style.background = '#059669';
      setTimeout(() => {
        btn.innerHTML = orig;
        btn.style.background = '';
      }, 1800);
    }
  } catch (e) {
    showToast('Could not add repair to order', 'error');
  }
}

function addToCart(item) {
  const existing = cart.find(i => i.id === item.id);
  if (existing) {
    existing.quantity += 1;
  } else {
    cart.push({
      id: item.id || 'repair-' + Math.random().toString(36).substr(2, 6),
      name: item.name || 'Gadget Repair Service',
      price: parseFloat(item.price) || 49.99,
      quantity: 1,
      category: item.category || 'Repair Service',
      compatibility: item.compatibility || 'Mobile / Laptop'
    });
  }

  renderCart();
  showToast(`Added "${item.name}" to repair booking`, 'success');
  
  // Auto open drawer so user sees their repair item
  const drawer = document.getElementById('checkout-drawer');
  if (drawer && !drawer.classList.contains('open')) {
    drawer.classList.add('open');
  }
}

function updateCartQuantity(id, delta) {
  const item = cart.find(i => i.id === id);
  if (!item) return;

  item.quantity += delta;
  if (item.quantity <= 0) {
    removeFromCart(id);
    return;
  }
  renderCart();
}

function removeFromCart(id) {
  cart = cart.filter(i => i.id !== id);
  renderCart();
  showToast('Removed from repair booking', 'info');
}

function renderCart() {
  const cartList = document.getElementById('cart-items-list');
  const cartCountBadges = document.querySelectorAll('.cart-count-badge');
  const topbarCount = document.getElementById('topbar-cart-count');
  const subtotalEl = document.getElementById('cart-subtotal');
  const taxEl = document.getElementById('cart-tax');
  const totalEl = document.getElementById('cart-total');
  const btnCheckout = document.getElementById('btn-checkout');

  const totalCount = cart.reduce((acc, i) => acc + i.quantity, 0);
  cartCountBadges.forEach(b => b.textContent = totalCount);
  if (topbarCount) topbarCount.textContent = totalCount;

  if (!cartList) return;

  if (cart.length === 0) {
    cartList.innerHTML = `
      <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:180px; text-align:center; color:var(--text-faint); gap:0.5rem; padding:1rem;">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="width:36px;height:36px;opacity:0.35;"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"></path></svg>
        <div style="font-weight:600; font-size:0.9rem; color:var(--text-title);">No Repairs in Booking</div>
        <p style="font-size:0.78rem;">Ask Iris or upload a photo of your broken mobile, laptop, or earphones to book a repair.</p>
      </div>
    `;
    if (subtotalEl) subtotalEl.textContent = '₹0';
    if (taxEl) taxEl.textContent = '₹0';
    if (totalEl) totalEl.textContent = '₹0';
    if (btnCheckout) btnCheckout.disabled = true;
    return;
  }

  let subtotal = 0;
  cartList.innerHTML = cart.map(item => {
    const itemTotal = item.price * item.quantity;
    subtotal += itemTotal;
    return `
      <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:12px; padding:0.85rem; display:flex; gap:0.75rem; align-items:center;">
        <div style="width:40px; height:40px; border-radius:8px; background:#e0e7ff; display:flex; align-items:center; justify-content:center; color:var(--primary-600); flex-shrink:0;">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:20px;height:20px;"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"></path></svg>
        </div>
        <div style="flex:1; overflow:hidden;">
          <div style="font-size:0.82rem; font-weight:700; color:var(--text-title); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${escapeHtml(item.name)}</div>
          <div style="font-size:0.78rem; font-weight:700; color:var(--primary-600); margin-top:0.1rem;">₹${Math.round(item.price).toLocaleString('en-IN')}</div>
        </div>
        <div style="display:flex; align-items:center; gap:0.35rem; background:#ffffff; border:1px solid #e2e8f0; border-radius:6px; padding:0.15rem 0.35rem;">
          <button style="background:none; border:none; color:var(--text-body); cursor:pointer; font-weight:700;" onclick="updateCartQuantity('${item.id}', -1)">&minus;</button>
          <span style="font-size:0.76rem; font-weight:600; min-width:14px; text-align:center;">${item.quantity}</span>
          <button style="background:none; border:none; color:var(--text-body); cursor:pointer; font-weight:700;" onclick="updateCartQuantity('${item.id}', 1)">&plus;</button>
        </div>
        <button style="background:none; border:none; color:var(--rose-500); cursor:pointer; padding:0.2rem;" onclick="removeFromCart('${item.id}')" title="Remove">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
        </button>
      </div>
    `;
  }).join('');

  const tax = Math.round(subtotal * 0.18);
  const grandTotal = subtotal + tax;

  if (subtotalEl) subtotalEl.textContent = `₹${Math.round(subtotal).toLocaleString('en-IN')}`;
  if (taxEl) taxEl.textContent = `₹${Math.round(tax).toLocaleString('en-IN')}`;
  if (totalEl) totalEl.textContent = `₹${Math.round(grandTotal).toLocaleString('en-IN')}`;
  if (btnCheckout) btnCheckout.disabled = false;
}

// 1-Click Instant Repair Booking / Checkout
async function executeCheckout() {
  if (cart.length === 0) return;

  const btnCheckout = document.getElementById('btn-checkout');
  if (btnCheckout) {
    btnCheckout.disabled = true;
    btnCheckout.innerHTML = `Confirming Repair Booking...`;
  }

  try {
    const subtotal = cart.reduce((acc, i) => acc + (i.price * i.quantity), 0);
    const tax = subtotal * 0.0825;
    const total = subtotal + tax;

    const res = await fetch('/api/checkout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ items: cart, total: total.toFixed(2) })
    });
    const data = await res.json();

    if (data.success) {
      showReceiptModal(data);
      cart = [];
      renderCart();
      const drawer = document.getElementById('checkout-drawer');
      if (drawer) drawer.classList.remove('open');
    } else {
      showToast(data.error || 'Repair booking failed', 'error');
    }
  } catch (err) {
    showToast('Network error during booking', 'error');
  } finally {
    if (btnCheckout) {
      btnCheckout.disabled = false;
      btnCheckout.innerHTML = `Confirm Repair Booking &rarr;`;
    }
  }
}

function showReceiptModal(order) {
  const modal = document.getElementById('receipt-modal');
  const orderIdEl = document.getElementById('receipt-order-id');
  const totalEl = document.getElementById('receipt-total');
  const deliveryEl = document.getElementById('receipt-delivery');

  if (orderIdEl) orderIdEl.textContent = `Repair Ticket: ${order.order_id}`;
  if (totalEl) totalEl.textContent = `₹${Number(order.total).toLocaleString('en-IN')}`;
  if (deliveryEl) deliveryEl.textContent = order.delivery_estimate;

  if (modal) modal.classList.add('open');
}

function closeReceiptModal() {
  const modal = document.getElementById('receipt-modal');
  if (modal) modal.classList.remove('open');
}

// Health check beacon
async function initHealthBeacon() {
  try {
    const res = await fetch('/health');
    const data = await res.json();
    const active = Object.values(data).filter(Boolean).length;
    const total = Object.keys(data).length;
    const textEl = document.getElementById('health-text');
    if (textEl) textEl.textContent = `Iris AI Live (${active}/${total})`;
  } catch (err) {
    const textEl = document.getElementById('health-text');
    if (textEl) textEl.textContent = 'Iris Online';
  }
}

function initDragAndDropZones() {
  document.querySelectorAll('.file-dropzone').forEach(zone => {
    const input = zone.querySelector('input[type="file"]');
    if (!input) return;
    ['dragenter', 'dragover'].forEach(n => zone.addEventListener(n, e => { e.preventDefault(); zone.classList.add('drag-active'); }));
    ['dragleave', 'drop'].forEach(n => zone.addEventListener(n, e => { e.preventDefault(); zone.classList.remove('drag-active'); }));
    zone.addEventListener('drop', e => {
      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        input.files = e.dataTransfer.files;
        input.dispatchEvent(new Event('change'));
      }
    });
  });
}
