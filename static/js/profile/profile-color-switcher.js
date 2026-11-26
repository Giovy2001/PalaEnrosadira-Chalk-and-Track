/* Selettore colore profilo: 8 colori, sincronizzati con il backend. */

let currentColorId = 0;

function paletteColor(colorId) {
  const cssVar = `--user-color-${colorId + 1}`;
  return getComputedStyle(document.documentElement).getPropertyValue(cssVar).trim();
}

function updateWebsiteIcon(colorId) {
  const icon = document.getElementById('apple-icon');
  if (icon) icon.href = `/static/icons/profile/Icon_${colorId}.png?v=${colorId}`;
}

function applyColor(colorId) {
  const id = Number(colorId) || 0;
  const swatch = document.getElementById('profile-color-active');
  const image = document.getElementById('profile-image');
  if (swatch) swatch.style.backgroundColor = paletteColor(id);
  if (image) image.src = `/static/icons/profile/Icon_${id}.png`;
  updateWebsiteIcon(id);
}

function setColor(colorId) {
  currentColorId = Number(colorId) || 0;
  applyColor(currentColorId);
  localStorage.setItem('chalk_and_track_color', String(currentColorId));
}

async function switch_profile_color() {
  const next = (currentColorId + 1) % 8;
  const username = getUsername();
  if (!username) {
    setColor(next);
    return;
  }
  try {
    const response = await appFetch('/backend_update_color', {
      method: 'POST',
      body: JSON.stringify({ username, color_id: next })
    });
    const data = await response.json();
    if (!response.ok || !data.success) throw new Error(data.message || 'Aggiornamento non riuscito');
    setColor(next);
  } catch (error) {
    console.error('Errore aggiornamento colore', error);
    applyColor(currentColorId);
  }
}
