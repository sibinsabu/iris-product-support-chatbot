/**
 * Iris AI - Gadget Repair & Diagnostic Copilot
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
  checkAuthStatus();
});

// Close floating menus on click outside
document.addEventListener('click', (e) => {
  const popover = document.getElementById('user-profile-popover');
  const userRow = document.getElementById('sidebar-user-logged');
  const topbarPill = document.getElementById('topbar-user-pill');
  if (popover && popover.classList.contains('open')) {
    if (!popover.contains(e.target) && (!userRow || !userRow.contains(e.target)) && (!topbarPill || !topbarPill.contains(e.target))) {
      closeUserMenu();
    }
  }
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

// =========================================================
// FIREBASE AUTHENTICATION MANAGER & CONTROLLER
// =========================================================
const FirebaseAuthManager = {
  auth: null,
  isInitialized: false,

  async init() {
    if (this.isInitialized && this.auth) return this.auth;
    if (typeof firebase === 'undefined') {
      console.warn('Firebase Web SDK not detected.');
      return null;
    }
    try {
      let config = {
        apiKey: "AIzaSyAfC-CSnBr3Gt0BUk3RN2Yt50WdBMth7_0",
        authDomain: "iris-gadget-repair.firebaseapp.com",
        projectId: "iris-gadget-repair",
        storageBucket: "iris-gadget-repair.firebasestorage.app",
        messagingSenderId: "650673193941",
        appId: "1:650673193941:web:2ffdbb5349d9922196b35c",
        measurementId: "G-TH1V9HGGPT"
      };

      try {
        const res = await fetch('/api/auth/firebase-config');
        if (res.ok) {
          const remoteConfig = await res.json();
          if (remoteConfig && remoteConfig.apiKey && !remoteConfig.apiKey.includes('YOUR_')) {
            config = remoteConfig;
          }
        }
      } catch (e) {}

      if (!firebase.apps.length) {
        firebase.initializeApp(config);
      }
      this.auth = firebase.auth();
      this.isInitialized = true;
      return this.auth;
    } catch (err) {
      console.warn('Firebase init error, using resilient mode:', err);
      return null;
    }
  },

  async signInEmail(email, password) {
    const auth = await this.init();
    if (auth) {
      try {
        const userCred = await auth.signInWithEmailAndPassword(email, password);
        return await this.syncWithBackend(userCred.user);
      } catch (fbErr) {
        // If Firebase recognized incorrect credentials, throw clean user-facing error
        if (fbErr.code === 'auth/wrong-password' || fbErr.code === 'auth/user-not-found' || fbErr.code === 'auth/invalid-credential') {
          throw new Error('Invalid email or password. Please verify and try again.');
        }
        if (fbErr.code === 'auth/invalid-email') {
          throw new Error('Please enter a valid email address.');
        }
        // If network/demo API key in development environment, gracefully sync with backend
        return await this.fallbackBackendAuth(email, password, false);
      }
    }
    return await this.fallbackBackendAuth(email, password, false);
  },

  async signUpEmail(name, email, password) {
    const auth = await this.init();
    if (auth) {
      try {
        const userCred = await auth.createUserWithEmailAndPassword(email, password);
        if (name && userCred.user.updateProfile) {
          try { await userCred.user.updateProfile({ displayName: name }); } catch (e) {}
        }
        return await this.syncWithBackend(userCred.user, name);
      } catch (fbErr) {
        if (fbErr.code === 'auth/email-already-in-use') {
          throw new Error('An account with this email already exists in Firebase. Please log in.');
        }
        if (fbErr.code === 'auth/weak-password') {
          throw new Error('Password must be at least 6 characters.');
        }
        return await this.fallbackBackendAuth(email, password, true, name);
      }
    }
    return await this.fallbackBackendAuth(email, password, true, name);
  },

  async signInProvider(providerName) {
    const auth = await this.init();
    if (auth) {
      let provider;
      if (providerName === 'google') {
        provider = new firebase.auth.GoogleAuthProvider();
        provider.addScope('profile');
        provider.addScope('email');
      } else if (providerName === 'microsoft') {
        provider = new firebase.auth.OAuthProvider('microsoft.com');
      } else if (providerName === 'apple') {
        provider = new firebase.auth.OAuthProvider('apple.com');
      } else {
        provider = new firebase.auth.GoogleAuthProvider();
      }

      try {
        const userCred = await auth.signInWithPopup(provider);
        return await this.syncWithBackend(userCred.user);
      } catch (fbErr) {
        if (fbErr.code === 'auth/popup-closed-by-user') {
          throw new Error('Sign-in popup was closed.');
        }
        // Fallback to demo social provider flow if domain or demo API key
        const res = await fetch('/api/auth/social', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ provider: providerName })
        });
        const data = await res.json();
        if (data.success) return data;
        throw new Error(data.error || 'Social sign-in failed');
      }
    }

    const res = await fetch('/api/auth/social', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ provider: providerName })
    });
    return await res.json();
  },

  async syncWithBackend(fbUser, customName = '') {
    let token = '';
    try { token = await fbUser.getIdToken(); } catch (e) {}
    const res = await fetch('/api/auth/firebase-session', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        id_token: token,
        user: {
          uid: fbUser.uid,
          email: fbUser.email,
          displayName: customName || fbUser.displayName || '',
          photoURL: fbUser.photoURL || '',
          providerId: fbUser.providerData?.[0]?.providerId || 'firebase'
        }
      })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Backend session sync failed');
    return data;
  },

  async fallbackBackendAuth(email, password, isSignup = false, name = '') {
    const endpoint = isSignup ? '/api/auth/signup' : '/api/auth/login';
    const payload = isSignup ? { name, email, password } : { email, password };
    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Authentication failed');
    return data;
  },

  async signOut() {
    try {
      if (this.auth) {
        await this.auth.signOut();
      }
    } catch (e) {}
    await fetch('/api/auth/logout', { method: 'POST' });
  }
};

let currentAuthUser = null;
let currentModalMode = 'login';

async function checkAuthStatus() {
  try {
    const res = await fetch('/api/auth/status');
    const data = await res.json();
    if (data.authenticated && data.user) {
      currentAuthUser = data.user;
      renderUserAuthUI(data.user);
    } else {
      currentAuthUser = null;
      renderGuestAuthUI();
    }
  } catch (err) {
    currentAuthUser = null;
    renderGuestAuthUI();
  }
}

function renderUserAuthUI(user) {
  // Sidebar
  const guestCard = document.getElementById('sidebar-auth-guest');
  const userRow = document.getElementById('sidebar-user-logged');
  const avatarEl = document.getElementById('sidebar-user-avatar');
  const nameEl = document.getElementById('sidebar-user-name');
  const subEl = document.getElementById('sidebar-user-sub');

  if (guestCard) guestCard.style.display = 'none';
  if (userRow) userRow.style.display = 'flex';
  if (avatarEl) {
    avatarEl.textContent = user.avatar_initials || 'U';
    avatarEl.style.backgroundColor = user.avatar_color || '#7c3aed';
  }
  if (nameEl) nameEl.textContent = user.name || 'Valued Customer';
  if (subEl) subEl.textContent = user.plan || (user.email ? user.email.split('@')[0] : 'Iris Member');

  // Popover info
  const popName = document.getElementById('popover-user-name');
  const popEmail = document.getElementById('popover-user-email');
  if (popName) popName.textContent = user.name || 'User';
  if (popEmail) popEmail.textContent = user.email || 'customer@iris.com';

  // Topbar
  const topbarLogin = document.getElementById('topbar-login-btn');
  const topbarUser = document.getElementById('topbar-user-pill');
  const topbarAvatar = document.getElementById('topbar-user-avatar');
  const topbarName = document.getElementById('topbar-user-name');

  if (topbarLogin) topbarLogin.style.display = 'none';
  if (topbarUser) topbarUser.style.display = 'inline-flex';
  if (topbarAvatar) {
    topbarAvatar.textContent = user.avatar_initials || 'U';
    topbarAvatar.style.backgroundColor = user.avatar_color || '#7c3aed';
  }
  if (topbarName) {
    topbarName.textContent = (user.name || 'User').split(' ')[0];
  }
}

function renderGuestAuthUI() {
  // Sidebar
  const guestCard = document.getElementById('sidebar-auth-guest');
  const userRow = document.getElementById('sidebar-user-logged');
  if (guestCard) guestCard.style.display = 'flex';
  if (userRow) userRow.style.display = 'none';

  // Popover close
  closeUserMenu();

  // Topbar
  const topbarLogin = document.getElementById('topbar-login-btn');
  const topbarUser = document.getElementById('topbar-user-pill');
  if (topbarLogin) topbarLogin.style.display = 'inline-block';
  if (topbarUser) topbarUser.style.display = 'none';
}

function openLoginModal(mode = 'login') {
  const modal = document.getElementById('login-modal');
  if (!modal) return;
  setModalAuthMode(mode);
  modal.classList.add('open');
}

function closeLoginModal() {
  const modal = document.getElementById('login-modal');
  if (modal) modal.classList.remove('open');
}

function setModalAuthMode(mode) {
  currentModalMode = mode;
  const title = document.getElementById('modal-auth-title');
  const sub = document.getElementById('modal-auth-subtitle');
  const nameGroup = document.getElementById('modal-name-group');
  const nameInput = document.getElementById('modal-name');
  const submitBtn = document.getElementById('btn-modal-auth-submit');
  const switchBox = document.getElementById('modal-auth-mode-switch');
  const forgotLink = document.getElementById('modal-forgot-link');
  const errBox = document.getElementById('modal-auth-error');

  if (errBox) errBox.style.display = 'none';

  if (mode === 'signup') {
    if (title) title.textContent = 'Create your account';
    if (sub) sub.textContent = 'Sign up with Firebase to diagnose devices, save repair estimates, and sync consultation history.';
    if (nameGroup) nameGroup.style.display = 'flex';
    if (nameInput) nameInput.required = true;
    if (submitBtn) submitBtn.querySelector('span').textContent = 'Create Account with Firebase';
    if (forgotLink) forgotLink.style.display = 'none';
    if (switchBox) switchBox.innerHTML = `<span>Already have an account? </span><a href="javascript:void(0)" onclick="setModalAuthMode('login')" style="color:#0f172a; font-weight:600; text-decoration:underline;">Log in</a>`;
  } else {
    if (title) title.textContent = 'Welcome back';
    if (sub) sub.textContent = 'Log in with Firebase to sync your diagnostics, track repair orders, and consult senior technicians.';
    if (nameGroup) nameGroup.style.display = 'none';
    if (nameInput) nameInput.required = false;
    if (submitBtn) submitBtn.querySelector('span').textContent = 'Continue with Firebase';
    if (forgotLink) forgotLink.style.display = 'inline';
    if (switchBox) switchBox.innerHTML = `<span>Don't have an account? </span><a href="javascript:void(0)" onclick="setModalAuthMode('signup')" style="color:#0f172a; font-weight:600; text-decoration:underline;">Sign up</a>`;
  }
}

async function handleModalAuthSubmit(e) {
  e.preventDefault();
  const errBox = document.getElementById('modal-auth-error');
  const submitBtn = document.getElementById('btn-modal-auth-submit');
  if (errBox) errBox.style.display = 'none';

  const email = (document.getElementById('modal-email')?.value || '').trim();
  const password = (document.getElementById('modal-password')?.value || '').trim();
  const name = (document.getElementById('modal-name')?.value || '').trim();

  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.querySelector('span').textContent = 'Authenticating with Firebase...';
  }

  try {
    let result;
    if (currentModalMode === 'signup') {
      result = await FirebaseAuthManager.signUpEmail(name, email, password);
    } else {
      result = await FirebaseAuthManager.signInEmail(email, password);
    }

    if (result && result.success && result.user) {
      currentAuthUser = result.user;
      renderUserAuthUI(result.user);
      closeLoginModal();
      showToast(result.message || `Welcome, ${result.user.name}! (Firebase Auth)`, 'success');
    } else {
      throw new Error(result?.error || 'Firebase authentication failed');
    }
  } catch (err) {
    if (errBox) {
      errBox.textContent = err.message || 'Firebase authentication error. Please verify credentials.';
      errBox.style.display = 'block';
    }
  } finally {
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.querySelector('span').textContent = currentModalMode === 'signup' ? 'Create Account with Firebase' : 'Continue with Firebase';
    }
  }
}

async function handleModalSocialAuth(provider) {
  const errBox = document.getElementById('modal-auth-error');
  if (errBox) errBox.style.display = 'none';

  try {
    const result = await FirebaseAuthManager.signInProvider(provider);
    if (result && result.success && result.user) {
      currentAuthUser = result.user;
      renderUserAuthUI(result.user);
      closeLoginModal();
      showToast(`Connected via Firebase ${provider.toUpperCase()}`, 'success');
    } else {
      throw new Error(result?.error || 'Social sign-in failed');
    }
  } catch (err) {
    if (errBox) {
      errBox.textContent = err.message || `Firebase ${provider} sign-in failed.`;
      errBox.style.display = 'block';
    }
  }
}

function quickFillModalLogin(email, password) {
  setModalAuthMode('login');
  const emailInput = document.getElementById('modal-email');
  const pwdInput = document.getElementById('modal-password');
  if (emailInput) emailInput.value = email;
  if (pwdInput) pwdInput.value = password;
  const form = document.getElementById('modal-auth-form');
  if (form) form.dispatchEvent(new Event('submit', { cancelable: true }));
}

async function handleLogout() {
  closeUserMenu();
  try {
    await FirebaseAuthManager.signOut();
    currentAuthUser = null;
    renderGuestAuthUI();
    showToast('Signed out from Firebase', 'info');
  } catch (err) {
    currentAuthUser = null;
    renderGuestAuthUI();
    showToast('Signed out', 'info');
  }
}

function toggleUserMenu(e) {
  if (e) e.stopPropagation();
  const popover = document.getElementById('user-profile-popover');
  if (!popover) return;
  popover.classList.toggle('open');
}

function closeUserMenu() {
  const popover = document.getElementById('user-profile-popover');
  if (popover) popover.classList.remove('open');
}
