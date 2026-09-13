// Plays the session wipe demo on the landing page; nothing here touches real data.
(function () {
  var list = document.getElementById('items');
  var btn = document.getElementById('wipeBtn');
  var count = document.getElementById('count');
  var dot = document.getElementById('statusDot');
  var status = document.getElementById('statusText');
  var clock = document.getElementById('clock');

  var original = list.innerHTML;
  var seconds = 0;
  var timer = null;
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function tick() {
    seconds++;
    var m = String(Math.floor(seconds / 60)).padStart(2, '0');
    var s = String(seconds % 60).padStart(2, '0');
    clock.textContent = m + ':' + s;
  }
  timer = setInterval(tick, 1000);

  function showEmpty() {
    var box = document.createElement('div');
    box.className = 'empty';
    box.innerHTML = '<strong>Nothing left</strong>' +
      '<span>Your files, messages and search index have been removed from memory. ' +
      'Starting again gives you a blank session.</span>';
    list.replaceWith(box);
    box.id = 'items';

    btn.textContent = 'Start a new session';
    btn.disabled = false;
    btn.dataset.mode = 'reset';
  }

  function restore() {
    var box = document.getElementById('items');
    var fresh = document.createElement('ul');
    fresh.className = 'items';
    fresh.id = 'items';
    fresh.innerHTML = original;
    box.replaceWith(fresh);
    list = fresh;

    count.textContent = '4';
    dot.classList.remove('off');
    status.textContent = 'Session active';
    seconds = 0;
    clock.textContent = '00:00';
    timer = setInterval(tick, 1000);

    btn.textContent = 'Log out and wipe';
    btn.dataset.mode = 'wipe';
  }

  function wipe() {
    var rows = Array.prototype.slice.call(list.children);
    btn.disabled = true;
    btn.textContent = 'Wiping...';
    dot.classList.add('off');
    status.textContent = 'Clearing memory';
    clearInterval(timer);

    var step = reduced ? 0 : 260;

    rows.forEach(function (row, i) {
      setTimeout(function () {
        row.classList.add('burning');
        setTimeout(function () {
          row.classList.add('gone');
          count.textContent = String(rows.length - 1 - i);
        }, reduced ? 0 : 180);
      }, i * step);
    });

    setTimeout(function () {
      status.textContent = 'Session ended';
      showEmpty();
    }, rows.length * step + (reduced ? 0 : 450));
  }

  btn.dataset.mode = 'wipe';
  btn.addEventListener('click', function () {
    if (btn.dataset.mode === 'wipe') { wipe(); } else { restore(); }
  });
})();
