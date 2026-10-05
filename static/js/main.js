/**
 * Iris AI - Gadget Repair & Diagnostic Copilot
 */

document.addEventListener('DOMContentLoaded', () => {
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
            <div class="product-price-label">Estimated cost: <strong>₹${Math.round(parseFloat(product.price)).toLocaleString('en-IN')}</strong></div>
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

      // Handle redirect sign-in result if user came back from Google redirect
      this.auth.getRedirectResult().then(async (result) => {
        if (result && result.user) {
          const syncRes = await this.syncWithBackend(result.user);
          if (syncRes && syncRes.user) {
            currentAuthUser = syncRes.user;
            renderUserAuthUI(syncRes.user);
            showToast(`Welcome back, ${syncRes.user.name}!`, 'success');
          }
        }
      }).catch(e => {
        console.warn('Redirect sign-in check:', e);
      });

      return this.auth;
    } catch (err) {
      console.warn('Authentication init error:', err);
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
          throw new Error('An account with this email already exists. Please log in.');
        }
        if (fbErr.code === 'auth/weak-password') {
          throw new Error('Password must be at least 6 characters.');
        }
        return await this.fallbackBackendAuth(email, password, true, name);
      }
    }
    return await this.fallbackBackendAuth(email, password, true, name);
  },

  async signInGoogle() {
    const auth = await this.init();
    if (!auth) {
      throw new Error('Authentication service is initializing. Please try again.');
    }

    const provider = new firebase.auth.GoogleAuthProvider();
    provider.addScope('profile');
    provider.addScope('email');
    provider.setCustomParameters({ prompt: 'select_account' });

    try {
      const userCred = await auth.signInWithPopup(provider);
      return await this.syncWithBackend(userCred.user);
    } catch (fbErr) {
      console.error('Google Sign-In Error:', fbErr);
      if (fbErr.code === 'auth/popup-closed-by-user') {
        throw new Error('Google sign-in popup was closed.');
      }
      if (fbErr.code === 'auth/popup-blocked') {
        await auth.signInWithRedirect(provider);
        return { success: true, redirecting: true };
      }
      if (fbErr.code === 'auth/unauthorized-domain') {
        const isLocalIp = window.location.hostname === '127.0.0.1' || /^(\d{1,3}\.){3}\d{1,3}$/.test(window.location.hostname);
        const port = window.location.port ? `:${window.location.port}` : '';
        const localhostUrl = `${window.location.protocol}//localhost${port}${window.location.pathname}${window.location.search}`;

        if (isLocalIp) {
          if (typeof showToast === 'function') {
            showToast('Switching to http://localhost (authorized by Firebase by default)...', 'info');
          }
          setTimeout(() => {
            window.location.href = localhostUrl;
          }, 1200);
          return { success: false, redirecting: true };
        }

        throw new Error(`Domain <strong>${window.location.hostname}</strong> is not authorized for Google Sign-In in Firebase.<br><br>Please add <code>${window.location.hostname}</code> in <a href="https://console.firebase.google.com/" target="_blank" rel="noopener" style="text-decoration:underline; font-weight:600; color:#3b82f6;">Firebase Console</a> &gt; Authentication &gt; Settings &gt; Authorized domains.`);
      }
      if (fbErr.code === 'auth/operation-not-allowed') {
        throw new Error('Google sign-in is not enabled in Firebase Console. Please enable Google under Authentication > Sign-in method.');
      }
      throw new Error(fbErr.message || 'Google sign-in failed. Please try again.');
    }
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
  const pwdBox = document.getElementById('modal-pwd-validation-box');
  const confirmGroup = document.getElementById('modal-confirm-group');
  const confirmInput = document.getElementById('modal-confirm-password');
  const pwdInput = document.getElementById('modal-password');
  const matchIndicator = document.getElementById('modal-pwd-match-indicator');

  if (errBox) errBox.style.display = 'none';

  if (mode === 'signup') {
    if (title) title.textContent = 'Create your account';
    if (sub) sub.textContent = 'Enter your details to diagnose devices, save repair estimates, and track tickets.';
    if (nameGroup) { nameGroup.style.display = 'flex'; nameGroup.style.flexDirection = 'column'; }
    if (nameInput) nameInput.required = true;
    if (pwdBox) pwdBox.style.display = 'flex';
    if (confirmGroup) { confirmGroup.style.display = 'flex'; confirmGroup.style.flexDirection = 'column'; }
    if (confirmInput) confirmInput.required = true;
    if (pwdInput) pwdInput.setAttribute('autocomplete', 'new-password');
    if (submitBtn) submitBtn.querySelector('span').textContent = 'Create account';
    if (forgotLink) forgotLink.style.display = 'none';
    if (switchBox) switchBox.innerHTML = `<span>Already have an account? </span><a href="javascript:void(0)" onclick="setModalAuthMode('login')">Log in</a>`;
    updateModalPasswordValidation();
  } else {
    if (title) title.textContent = 'Welcome back';
    if (sub) sub.textContent = 'Log in to Iris AI to sync your diagnostics, track repair orders, and consult senior technicians.';
    if (nameGroup) nameGroup.style.display = 'none';
    if (nameInput) { nameInput.required = false; nameInput.value = ''; }
    if (pwdBox) pwdBox.style.display = 'none';
    if (confirmGroup) confirmGroup.style.display = 'none';
    if (confirmInput) { confirmInput.required = false; confirmInput.value = ''; confirmInput.classList.remove('invalid', 'valid'); }
    if (pwdInput) { pwdInput.setAttribute('autocomplete', 'current-password'); pwdInput.classList.remove('invalid', 'valid'); }
    if (matchIndicator) { matchIndicator.textContent = ''; matchIndicator.className = 'pwd-match-indicator'; }
    if (submitBtn) submitBtn.querySelector('span').textContent = 'Continue';
    if (forgotLink) forgotLink.style.display = 'inline';
    if (switchBox) switchBox.innerHTML = `<span>Don't have an account? </span><a href="javascript:void(0)" onclick="setModalAuthMode('signup')">Sign up</a>`;
  }
}

function updateModalPasswordValidation() {
  if (currentModalMode !== 'signup') return;
  const pwdInput = document.getElementById('modal-password');
  const confirmInput = document.getElementById('modal-confirm-password');
  if (!pwdInput) return;

  const val = pwdInput.value;
  const confirmVal = confirmInput ? confirmInput.value : '';

  const hasLength = val.length >= 8;
  const hasNumber = /\d/.test(val);
  const hasLetter = /[A-Za-z]/.test(val);
  const hasSpecial = /[^A-Za-z0-9]/.test(val);

  const setRule = (id, met) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.classList.toggle('met', met);
    const icon = el.querySelector('.rule-icon');
    if (icon) icon.textContent = met ? '✓' : '○';
  };
  setRule('modal-rule-length', hasLength);
  setRule('modal-rule-number', hasNumber);
  setRule('modal-rule-letter', hasLetter);

  // Strength score 0-4
  let score = 0;
  if (val.length >= 6) score++;
  if (hasLength) score++;
  if (hasNumber && hasLetter) score++;
  if ((val.length >= 10 && hasNumber && hasLetter) || hasSpecial) score++;

  const strengthMeta = {
    0: { color: '#e2e8f0', text: '', textColor: '#64748b' },
    1: { color: '#ef4444', text: 'Weak',   textColor: '#ef4444' },
    2: { color: '#f59e0b', text: 'Fair',   textColor: '#f59e0b' },
    3: { color: '#3b82f6', text: 'Good',   textColor: '#3b82f6' },
    4: { color: '#10b981', text: 'Strong', textColor: '#10b981' }
  };
  const level = val.length === 0 ? 0 : Math.max(1, score);
  const meta = strengthMeta[level];

  [1, 2, 3, 4].forEach(i => {
    const seg = document.getElementById(`modal-pwd-seg-${i}`);
    if (seg) seg.style.background = i <= level ? meta.color : '#e2e8f0';
  });
  const strengthText = document.getElementById('modal-pwd-strength-text');
  if (strengthText) { strengthText.textContent = meta.text; strengthText.style.color = meta.textColor; }

  // Match indicator
  const matchIndicator = document.getElementById('modal-pwd-match-indicator');
  if (matchIndicator && confirmInput) {
    if (!confirmVal) {
      matchIndicator.textContent = '';
      matchIndicator.className = 'pwd-match-indicator';
      confirmInput.classList.remove('invalid', 'valid');
    } else if (confirmVal === val) {
      matchIndicator.innerHTML = '<span style="font-weight:700;">✓</span> Passwords match';
      matchIndicator.className = 'pwd-match-indicator match';
      confirmInput.classList.remove('invalid'); confirmInput.classList.add('valid');
    } else {
      matchIndicator.innerHTML = '<span style="font-weight:700;">✕</span> Passwords do not match';
      matchIndicator.className = 'pwd-match-indicator mismatch';
      confirmInput.classList.remove('valid'); confirmInput.classList.add('invalid');
    }
  }

  // Password border
  if (hasLength && hasNumber && hasLetter) {
    pwdInput.classList.remove('invalid'); pwdInput.classList.add('valid');
  } else if (val.length > 0) {
    pwdInput.classList.remove('valid'); pwdInput.classList.add('invalid');
  } else {
    pwdInput.classList.remove('invalid', 'valid');
  }
}

async function handleModalAuthSubmit(e) {
  e.preventDefault();
  const errBox = document.getElementById('modal-auth-error');
  const submitBtn = document.getElementById('btn-modal-auth-submit');
  const pwdInput = document.getElementById('modal-password');
  const confirmInput = document.getElementById('modal-confirm-password');
  if (errBox) errBox.style.display = 'none';

  const email = (document.getElementById('modal-email')?.value || '').trim();
  const password = (pwdInput?.value || '').trim();
  const name = (document.getElementById('modal-name')?.value || '').trim();
  const confirmPassword = (confirmInput?.value || '').trim();

  const showErr = (msg, focusEl) => {
    if (errBox) { errBox.textContent = msg; errBox.style.display = 'block'; }
    if (focusEl) focusEl.focus();
  };

  // --- Signup validation ---
  if (currentModalMode === 'signup') {
    if (!name) { showErr('Please enter your full name.', document.getElementById('modal-name')); return; }
    if (!email || !email.includes('@')) { showErr('Please enter a valid email address.', document.getElementById('modal-email')); return; }
    if (password.length < 8) { showErr('Password must be at least 8 characters long.', pwdInput); if (pwdInput) pwdInput.classList.add('invalid'); return; }
    if (!/\d/.test(password)) { showErr('Password must contain at least one number (0-9).', pwdInput); if (pwdInput) pwdInput.classList.add('invalid'); return; }
    if (!/[A-Za-z]/.test(password)) { showErr('Password must contain at least one letter (A-Z or a-z).', pwdInput); if (pwdInput) pwdInput.classList.add('invalid'); return; }
    if (!confirmPassword) { showErr('Please re-enter your password.', confirmInput); if (confirmInput) confirmInput.classList.add('invalid'); return; }
    if (password !== confirmPassword) { showErr('Passwords do not match. Please check both fields.', confirmInput); if (confirmInput) confirmInput.classList.add('invalid'); return; }
  }

  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.querySelector('span').textContent = currentModalMode === 'signup' ? 'Creating account...' : 'Signing in...';
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
      showToast(result.message || `Welcome, ${result.user.name}!`, 'success');
    } else {
      throw new Error(result?.error || 'Authentication failed. Please verify credentials.');
    }
  } catch (err) {
    if (errBox) {
      errBox.textContent = err.message || 'Authentication error. Please verify credentials.';
      errBox.style.display = 'block';
    }
  } finally {
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.querySelector('span').textContent = currentModalMode === 'signup' ? 'Create account' : 'Continue';
    }
  }
}

async function handleModalGoogleAuth() {
  const errBox = document.getElementById('modal-auth-error');
  if (errBox) errBox.style.display = 'none';

  try {
    const result = await FirebaseAuthManager.signInGoogle();
    if (result && result.redirecting) return;
    if (result && result.success && result.user) {
      currentAuthUser = result.user;
      renderUserAuthUI(result.user);
      closeLoginModal();
      showToast(result.message || `Welcome, ${result.user.name}!`, 'success');
    } else {
      throw new Error(result?.error || 'Google sign-in failed');
    }
  } catch (err) {
    if (errBox) {
      errBox.textContent = err.message || 'Google sign-in failed. Please try again.';
      errBox.style.display = 'block';
    }
  }
}

async function handleLogout() {
  closeUserMenu();
  try {
    await FirebaseAuthManager.signOut();
    currentAuthUser = null;
    renderGuestAuthUI();
    showToast('Signed out', 'info');
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
