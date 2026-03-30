// main.js — students will add JavaScript here as features are built

// Modal behavior
var modal = document.getElementById('howitworks-modal');
var openBtn = document.getElementById('see-how-btn');
var closeBtn = document.getElementById('modal-close-btn');
var iframe = document.getElementById('howitworks-iframe');

// Open modal
openBtn.addEventListener('click', function(e) {
  e.preventDefault();
  modal.style.display = "flex";
});

// Close functions
function closeModal() {
  modal.style.display = "none";
  // Stop the video playback (reset src)
  if (iframe) {
    var src = iframe.src;
    iframe.src = "";
    // Force reflow in case of browser caching
    setTimeout(function(){ iframe.src = src; }, 50);
  }
}

closeBtn.addEventListener('click', closeModal);

// Close when clicking outside modal content
modal.addEventListener('mousedown', function(e) {
  if (e.target === modal) { closeModal(); }
});

// Optional: ESC key closes modal
document.addEventListener('keydown', function(e) {
  if (e.key === "Escape" && modal.style.display === "flex") { closeModal(); }
});
