/* ================================================================
   Clinico – Dashboard JavaScript
   ================================================================ */

/**
 * Tab switching for all dashboards.
 * Called by sidebar links: onclick="showTab('overview', this)"
 */
function showTab(tabId, clickedLink) {
  // Hide all tab contents
  document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));

  // Deactivate all nav items
  document.querySelectorAll('.nav-item').forEach(a => a.classList.remove('active'));

  // Show target tab
  const target = document.getElementById('tab-' + tabId);
  if (target) target.classList.add('active');

  // Mark clicked link as active
  if (clickedLink) clickedLink.classList.add('active');
}

/**
 * Auto-dismiss flash messages after 5 seconds
 */
document.addEventListener('DOMContentLoaded', function () {
  const flashes = document.querySelectorAll('.flash');
  flashes.forEach(f => {
    setTimeout(() => {
      f.style.transition = 'opacity 0.5s';
      f.style.opacity = '0';
      setTimeout(() => f.remove(), 500);
    }, 5000);
  });

  // ── Hero Slider (index.html) ──────────────────────────────────
  const slides   = document.querySelectorAll('.slide');
  const headings = [
    "Empowering<br>Your Health<br>Journey",
    "Advanced<br>Medical Care<br>For You"
  ];
  let slideIndex = 0;

  function updateHeading() {
    const el = document.getElementById('heroTitle');
    if (el) el.innerHTML = headings[slideIndex];
  }

  function showSlide() {
    const track = document.getElementById('slides');
    if (track) {
      track.style.transform = `translateX(-${slideIndex * 100}%)`;
      updateHeading();
    }
  }

  window.nextSlide = function () {
    if (slides.length) {
      slideIndex = (slideIndex + 1) % slides.length;
      showSlide();
    }
  };

  window.prevSlide = function () {
    if (slides.length) {
      slideIndex = (slideIndex - 1 + slides.length) % slides.length;
      showSlide();
    }
  };

  if (slides.length) {
    showSlide();
    setInterval(window.nextSlide, 5000); // auto-slide every 5s
  }

  // ── Doctor Team Slider ────────────────────────────────────────
  const teamSlider = document.getElementById('slider');

  window.slideRight = function () {
    if (teamSlider) teamSlider.scrollLeft += 330;
  };
  window.slideLeft = function () {
    if (teamSlider) teamSlider.scrollLeft -= 330;
  };

  // ── Patient Dashboard: set min date for booking ───────────────
  const dateInputs = document.querySelectorAll('input[type="date"]');
  const today = new Date().toISOString().split('T')[0];
  dateInputs.forEach(input => {
    if (!input.value && !input.min) input.min = today;
  });

  // ── Confirm before form submit (generic) ─────────────────────
  document.querySelectorAll('[data-confirm]').forEach(btn => {
    btn.addEventListener('click', function (e) {
      if (!confirm(this.dataset.confirm)) e.preventDefault();
    });
  });

  // ── Queue auto-refresh every 30 seconds (if on queue page) ───
  if (document.querySelector('.queue-live')) {
    setTimeout(() => window.location.reload(), 30000);
  }
});

/**
 * Show / hide doctor fields on register page
 * (also declared inline in register.html for safety)
 */
function toggleDoctorFields() {
  const dr = document.getElementById('r-doctor');
  const fields = document.getElementById('doctorFields');
  if (dr && fields) fields.style.display = dr.checked ? 'block' : 'none';
}
