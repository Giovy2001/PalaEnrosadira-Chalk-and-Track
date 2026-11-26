function createHold(data) {
  const container = document.getElementById('holdContainer');
  if (!container) return null;

  const hold = document.createElement('div');
  hold.classList.add('hold');
  hold.dataset.holdId = data.hold_id ?? '';
  container.appendChild(hold);

  const constraint = document.createElement('label');
  constraint.classList.add('constraint');
  hold.appendChild(constraint);

  updateHoldStyle(hold, data);
  updateConstraintStyle(hold, data);
  return hold;
}

function updateHoldStyle(hold, data) {
  hold.style.left = `${data.x * 100}%`;
  hold.style.top = `${data.y * 100}%`;
  hold.style.width = `${24 * data.size}px`;
  hold.style.height = `${24 * data.size}px`;
  hold.classList.remove('start', 'middle', 'top', 'zone');
  hold.classList.add(data.progression_id);
}

function updateConstraintStyle(hold, data) {
  const mapping = {
    foot: 'P', only_foot: 'SP', only_hand: 'SM',
    only_volume: 'SV', no_volume: 'NV', normal: ''
  };
  const constraint = hold.querySelector('.constraint');
  constraint.textContent = mapping[data.constraint_id] ?? '';
  constraint.style.left = `${24 * data.size + 2}px`;
  constraint.style.top = `${12 * data.size}px`;
}
