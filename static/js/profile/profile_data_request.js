/* Caricamento dei dati reali del profilo dal backend. */

const TAG_THRESHOLDS = [
  ['PRO', 5000], ['EXP', 2500], ['ADV', 1000],
  ['INT', 500], ['BEG', 200], ['NEW', 0]
];

function getUsername() {
  return window.PROFILE_USER || window.APP_USER || localStorage.getItem('chalk_and_track_username');
}

function getHighestGrade(routes) {
  const grades = window.GRADES || [];
  let best = null;
  let bestIndex = Infinity;
  for (const route of routes) {
    const index = grades.indexOf(route.route_grade);
    if (index !== -1 && index < bestIndex) {
      bestIndex = index;
      best = route.route_grade;
    }
  }
  return best;
}

function tagFor(points) {
  const value = Number(points) || 0;
  const found = TAG_THRESHOLDS.find(([, threshold]) => value >= threshold);
  return found ? found[0] : 'NEW';
}

function showError(message) {
  const list = document.getElementById('myRoutesList');
  if (list) list.textContent = message;
}

function renderRouteList(container, routes, emptyMessage) {
  if (!container) return;
  container.replaceChildren();
  if (!routes || routes.length === 0) {
    const empty = document.createElement('p');
    empty.className = 'empty-state';
    empty.textContent = emptyMessage;
    container.appendChild(empty);
    return;
  }
  for (const route of routes) {
    const link = document.createElement('a');
    link.className = 'route-list-item';
    link.href = `/route_${route.route_id}`;

    const title = document.createElement('strong');
    title.textContent = route.route_name || 'Senza nome';

    const meta = document.createElement('span');
    meta.textContent = route.route_grade ? `Grado ${route.route_grade}` : 'Grado non impostato';

    link.append(title, meta);
    container.appendChild(link);
  }
}

function setProfileData(user) {
  const score = document.getElementById('profile-score');
  const tag = document.getElementById('profile-tag');
  if (score) score.textContent = String(user.points ?? 0);
  if (tag) tag.textContent = tagFor(user.points);
  if (typeof setColor === 'function') setColor(Number(user.user_color) || 0);
}

function setRoutesData(routes, completed) {
  const created = document.getElementById('stat-created-n');
  const hardest = document.getElementById('stat-created-hardest');
  if (created) created.textContent = String(routes.length);
  const grade = getHighestGrade(routes);
  if (hardest) hardest.textContent = grade || '-';

  renderRouteList(
    document.getElementById('myRoutesList'), routes, 'Non hai ancora creato blocchi.'
  );
  renderRouteList(
    document.getElementById('completedList'), completed, 'Nessun blocco completato.'
  );
}

async function requestProfileData() {
  const username = getUsername();
  if (!username) {
    window.location.href = '/create_user';
    return;
  }
  try {
    const response = await appFetch('/backend_get_profile', {
      method: 'POST',
      body: JSON.stringify({ username })
    });
    const data = await response.json();
    if (!response.ok || !data.success) {
      showError(data.message || 'Impossibile caricare il profilo');
      return;
    }
    setProfileData(data.user);
    setRoutesData(data.routes || [], data.completed || []);
  } catch (error) {
    console.error('Errore caricamento profilo', error);
    showError('Impossibile caricare il profilo. Riprova più tardi.');
  }
}

document.addEventListener('DOMContentLoaded', requestProfileData);
