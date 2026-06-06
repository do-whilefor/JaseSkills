function renderUnsafe(value) {
  document.getElementById('out').innerHTML = value;
}
function route() {
  const raw = new URLSearchParams(location.search).get('q');
  const copy = raw;
  renderUnsafe(copy);
}
route();
