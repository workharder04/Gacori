(() => {
  const carousel = document.getElementById('carousel');
  const dotsContainer = document.getElementById('dots');
  const prevBtn = document.getElementById('prevBtn');
  const nextBtn = document.getElementById('nextBtn');
  const cards = Array.from(carousel.querySelectorAll('.card'));
  const total = cards.length;

  let current = 0;
  let isDragging = false;
  let startX = 0;
  let dragDelta = 0;
  let animating = false;

  // ── Layout constants ──
  const CARD_WIDTH = 300;
  const SIDE_SCALE = 0.78;
  const SIDE_OFFSET = 220;
  const SIDE_OPACITY = 0.45;
  const FAR_SCALE = 0.6;
  const FAR_OFFSET = 380;
  const FAR_OPACITY = 0.15;
  const DRAG_THRESHOLD = 60;

  // ── Build dots ──
  cards.forEach((_, i) => {
    const dot = document.createElement('button');
    dot.className = 'dot' + (i === 0 ? ' active' : '');
    dot.setAttribute('aria-label', `Go to slide ${i + 1}`);
    dot.addEventListener('click', () => goTo(i));
    dotsContainer.appendChild(dot);
  });

  function getDots() {
    return Array.from(dotsContainer.querySelectorAll('.dot'));
  }

  // ── Position logic ──
  function getPositionStyle(relIndex, dragX = 0) {
    // relIndex: distance from current (-2,-1,0,1,2...)
    const abs = Math.abs(relIndex);
    let translateX, scale, opacity, zIndex, rotateY;

    if (abs === 0) {
      translateX = dragX;
      scale = 1 - Math.abs(dragX) / (CARD_WIDTH * 8);
      opacity = 1;
      zIndex = 10;
      rotateY = -dragX / 20;
    } else if (abs === 1) {
      const sign = relIndex > 0 ? 1 : -1;
      const dragPull = sign === Math.sign(dragX) ? -dragX * 0.3 : dragX * 0.15;
      translateX = sign * SIDE_OFFSET + dragPull;
      scale = SIDE_SCALE + Math.abs(dragX) / (CARD_WIDTH * 20) * sign * Math.sign(dragX) * -1;
      opacity = SIDE_OPACITY + Math.abs(dragX) / (CARD_WIDTH * 5) * (sign === Math.sign(dragX) ? 0.3 : -0.1);
      zIndex = 5;
      rotateY = sign * -10;
    } else if (abs === 2) {
      const sign = relIndex > 0 ? 1 : -1;
      translateX = sign * FAR_OFFSET;
      scale = FAR_SCALE;
      opacity = FAR_OPACITY;
      zIndex = 2;
      rotateY = sign * -18;
    } else {
      translateX = (relIndex > 0 ? 1 : -1) * (FAR_OFFSET + 120);
      scale = 0.5;
      opacity = 0;
      zIndex = 1;
      rotateY = 0;
    }

    scale = Math.max(0.5, Math.min(1, scale));
    opacity = Math.max(0, Math.min(1, opacity));

    return { translateX, scale, opacity, zIndex, rotateY };
  }

  function applyPositions(dragX = 0, withTransition = true) {
    cards.forEach((card, i) => {
      let rel = i - current;
      // Wrap around
      if (rel > total / 2) rel -= total;
      if (rel < -total / 2) rel += total;

      const { translateX, scale, opacity, zIndex, rotateY } = getPositionStyle(rel, dragX);

      card.style.transition = withTransition
        ? 'transform 0.5s cubic-bezier(0.25,0.46,0.45,0.94), opacity 0.5s ease'
        : 'none';
      card.style.transform = `translateX(calc(-50% + ${translateX}px)) scale(${scale}) rotateY(${rotateY}deg)`;
      card.style.opacity = opacity;
      card.style.zIndex = zIndex;
      card.style.pointerEvents = rel === 0 ? 'auto' : 'none';
    });

    // Update dots
    getDots().forEach((dot, i) => {
      dot.classList.toggle('active', i === current);
    });
  }

  function goTo(index, direction) {
    if (animating) return;
    animating = true;
    current = ((index % total) + total) % total;
    applyPositions(0, true);
    setTimeout(() => { animating = false; }, 520);
  }

  function prev() {
    goTo(current - 1);
  }

  function next() {
    goTo(current + 1);
  }

  // ── Initial render ──
  applyPositions(0, false);

  // ── Keyboard ──
  document.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowLeft') { e.preventDefault(); prev(); }
    if (e.key === 'ArrowRight') { e.preventDefault(); next(); }
  });

  // ── Arrow buttons ──
  prevBtn.addEventListener('click', prev);
  nextBtn.addEventListener('click', next);

  // ── Mouse drag ──
  carousel.addEventListener('mousedown', (e) => {
    if (e.button !== 0) return;
    isDragging = true;
    startX = e.clientX;
    dragDelta = 0;
    carousel.classList.add('dragging');
    e.preventDefault();
  });

  document.addEventListener('mousemove', (e) => {
    if (!isDragging) return;
    dragDelta = e.clientX - startX;
    applyPositions(dragDelta, false);
  });

  document.addEventListener('mouseup', () => {
    if (!isDragging) return;
    isDragging = false;
    carousel.classList.remove('dragging');
    commitDrag();
  });

  // ── Touch drag ──
  carousel.addEventListener('touchstart', (e) => {
    isDragging = true;
    startX = e.touches[0].clientX;
    dragDelta = 0;
    e.preventDefault();
  }, { passive: false });

  carousel.addEventListener('touchmove', (e) => {
    if (!isDragging) return;
    dragDelta = e.touches[0].clientX - startX;
    applyPositions(dragDelta, false);
    e.preventDefault();
  }, { passive: false });

  carousel.addEventListener('touchend', () => {
    if (!isDragging) return;
    isDragging = false;
    commitDrag();
  });

  function commitDrag() {
    if (dragDelta < -DRAG_THRESHOLD) {
      next();
    } else if (dragDelta > DRAG_THRESHOLD) {
      prev();
    } else {
      // Snap back
      applyPositions(0, true);
    }
    dragDelta = 0;
  }

  // ── Click on side cards to navigate ──
  cards.forEach((card, i) => {
    card.addEventListener('click', () => {
      if (Math.abs(dragDelta) > 5) return;
      if (i !== current) goTo(i);
    });
  });
})();
