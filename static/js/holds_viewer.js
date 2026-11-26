document.addEventListener('DOMContentLoaded', () => {
  const holds = window.holds || [];
  holds.forEach((hold) => createHold(hold));
});
