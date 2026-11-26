/* Bootstrap dell'identità e utility condivise. */

function getCookie(name) {
  const prefix = `${name}=`;
  const found = document.cookie.split('; ').find((row) => row.startsWith(prefix));
  return found ? decodeURIComponent(found.slice(prefix.length)) : null;
}

function updateBottomNav() {
  const item = document.getElementById('create-button-hidden');
  if (!item) return;
  const username = localStorage.getItem('chalk_and_track_username');
  item.style.display = username ? 'flex' : 'none';
}

function rememberSession(username, token) {
  if (username) localStorage.setItem('chalk_and_track_username', username);
  if (token) localStorage.setItem('chalk_and_track_token', token);
}

async function appFetch(url, options = {}) {
  const token = localStorage.getItem('chalk_and_track_token');
  const headers = new Headers(options.headers || {});
  if (options.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }
  if (token) headers.set('X-Auth-Token', token);
  return fetch(url, { ...options, headers });
}

async function bootstrapAuth() {
  if (window.APP_TOKEN) {
    rememberSession(window.APP_USER, window.APP_TOKEN);
    updateBottomNav();
    return;
  }

  const token = localStorage.getItem('chalk_and_track_token') || getCookie('chalk_and_track_token');
  if (token) {
    try {
      const response = await appFetch('/backend_login', {
        method: 'POST',
        body: JSON.stringify({ auth_token: token })
      });
      if (response.ok) {
        const data = await response.json();
        rememberSession(data.username, data.auth_token);
      } else {
        localStorage.removeItem('chalk_and_track_token');
      }
    } catch (error) {
      console.warn('Login automatico non riuscito', error);
    }
  }
  updateBottomNav();
}

document.addEventListener('DOMContentLoaded', bootstrapAuth);
window.updateBottomNav = updateBottomNav;
window.appFetch = appFetch;
