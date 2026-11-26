// Selettore interattivo delle prese sulla foto della via.

document.addEventListener('DOMContentLoaded', () => {
  const holdsLabel = document.getElementById('jsonHoldsHidden');
  const holdsForm = document.getElementById('holdsForm');
  const holdContainer = document.getElementById('holdContainer');
  const holdTypeSelect = document.getElementById('hold_type_select');
  const holdUseSelect = document.getElementById('hold_use_select');
  const holdSize = document.getElementById('hold_size');
  const deleteBtn = document.getElementById('delete_hold');

  if (!holdsLabel || !holdsForm || !holdContainer) return;

  const previousData = window.previous_data || {};
  let holds = [];
  let selectedHold = null;
  let holdId = 0;

  function clamp(value) {
    return Math.min(Math.max(value, 0), 1);
  }

  function addExisting(data) {
    const hold = createHold(data);
    if (!hold) return;
    holds.push({ element: hold, data });
    addHoldEvents(hold);
  }

  const existing = Array.isArray(previousData.holds_array) ? previousData.holds_array : [];
  existing.forEach((hold) => {
    const data = {
      hold_id: hold.hold_id ?? hold.id ?? holdId,
      x: Number(hold.x),
      y: Number(hold.y),
      size: Number(hold.size),
      progression_id: hold.progression_id,
      constraint_id: hold.constraint_id
    };
    holdId = Math.max(holdId, Number(data.hold_id) + 1);
    addExisting(data);
  });

  function addHoldEvents(hold) {
    hold.addEventListener('pointerdown', (event) => {
      event.stopPropagation();
      selectHold(hold);
      startDrag(event, hold);
    });
  }

  function selectHold(hold) {
    document.querySelectorAll('.hold').forEach((item) => item.classList.remove('selected'));
    hold.classList.add('selected');
    selectedHold = hold;

    const found = holds.find((item) => item.element === hold);
    if (!found) return;
    holdTypeSelect.value = found.data.progression_id;
    holdUseSelect.value = found.data.constraint_id;
    holdSize.value = String(found.data.size);
    if (deleteBtn) deleteBtn.style.display = 'block';
  }

  function deselectHold() {
    document.querySelectorAll('.hold').forEach((item) => item.classList.remove('selected'));
    selectedHold = null;
    if (deleteBtn) deleteBtn.style.display = 'none';
  }

  function startDrag(event, hold) {
    const rect = holdContainer.getBoundingClientRect();
    hold.setPointerCapture(event.pointerId);

    function move(moveEvent) {
      const x = clamp((moveEvent.clientX - rect.left) / rect.width);
      const y = clamp((moveEvent.clientY - rect.top) / rect.height);
      hold.style.left = `${x * 100}%`;
      hold.style.top = `${y * 100}%`;
      const found = holds.find((item) => item.element === hold);
      if (found) {
        found.data.x = x;
        found.data.y = y;
      }
    }

    function stop() {
      hold.removeEventListener('pointermove', move);
      hold.removeEventListener('pointerup', stop);
      hold.removeEventListener('pointercancel', stop);
    }

    hold.addEventListener('pointermove', move);
    hold.addEventListener('pointerup', stop);
    hold.addEventListener('pointercancel', stop);
  }

  holdContainer.addEventListener('pointerdown', (event) => {
    if (event.target.classList.contains('hold')) return;
    if (selectedHold) {
      deselectHold();
      return;
    }
    const rect = holdContainer.getBoundingClientRect();
    const data = {
      hold_id: holdId++,
      x: clamp((event.clientX - rect.left) / rect.width),
      y: clamp((event.clientY - rect.top) / rect.height),
      size: parseFloat(holdSize.value),
      progression_id: holdTypeSelect.value,
      constraint_id: holdUseSelect.value
    };
    addExisting(data);
  });

  holdTypeSelect.addEventListener('change', () => {
    const found = holds.find((item) => item.element === selectedHold);
    if (!found) return;
    found.data.progression_id = holdTypeSelect.value;
    updateHoldStyle(selectedHold, found.data);
  });

  holdUseSelect.addEventListener('change', () => {
    const found = holds.find((item) => item.element === selectedHold);
    if (!found) return;
    found.data.constraint_id = holdUseSelect.value;
    updateConstraintStyle(selectedHold, found.data);
  });

  holdSize.addEventListener('input', () => {
    const found = holds.find((item) => item.element === selectedHold);
    if (!found) return;
    found.data.size = parseFloat(holdSize.value);
    updateHoldStyle(selectedHold, found.data);
    updateConstraintStyle(selectedHold, found.data);
  });

  if (deleteBtn) {
    deleteBtn.addEventListener('click', () => {
      if (!selectedHold) return;
      const index = holds.findIndex((item) => item.element === selectedHold);
      selectedHold.remove();
      holds.splice(index, 1);
      deselectHold();
    });
  }

  holdsForm.addEventListener('submit', (event) => {
    if (holds.length === 0) {
      event.preventDefault();
      holdsLabel.value = '';
      alert('Seleziona almeno una presa prima di continuare.');
      return;
    }
    holdsLabel.value = JSON.stringify(holds.map((item) => ({ data: item.data })));
  });
});
