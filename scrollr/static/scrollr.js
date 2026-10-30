(() => {
  const feed = document.querySelector("#feed-root");
  if (!feed) return;

  let layout = localStorage.getItem("scrollr-layout") || "mosaic";
  if (layout === "single") layout = "column";
  let videoObserver;
  let masonryObserver;

  const postForm = (form, body = new FormData(form)) => fetch(form.action, {
    method: "POST",
    body,
    headers: { "X-Requested-With": "XMLHttpRequest" },
  });

  function updateLayout(next) {
    layout = next;
    localStorage.setItem("scrollr-layout", layout);
    feed.className = `feed ${layout}-feed`;
    document.querySelectorAll("[data-layout]").forEach(button => {
      button.classList.toggle("is-active", button.dataset.layout === layout);
    });
    observeFeed();
  }

  function observeFeed() {
    videoObserver?.disconnect();
    videoObserver = new IntersectionObserver(entries => entries.forEach(({ target, isIntersecting, intersectionRatio }) => {
      if (isIntersecting && intersectionRatio >= 0.35) {
        target.muted = true;
        target.play().catch(() => { });
      } else target.pause();
    }), { threshold: [0, 0.35, 0.65, 0.9] });
    feed.querySelectorAll("video").forEach(video => videoObserver.observe(video));

    masonryObserver?.disconnect();
    if (layout !== "mosaic") return;
    const cards = feed.querySelectorAll(".clip-card");
    const packCards = () => {
      const style = getComputedStyle(feed);
      const row = parseFloat(style.gridAutoRows);
      const gap = parseFloat(style.rowGap);
      cards.forEach(card => {
        card.style.gridRowEnd = `span ${Math.ceil((card.offsetHeight + gap) / (row + gap))}`;
      });
    };
    masonryObserver = new ResizeObserver(packCards);
    cards.forEach(card => masonryObserver.observe(card));
    packCards();
  }

  document.querySelectorAll("[data-layout]").forEach(button => button.addEventListener("click", () => updateLayout(button.dataset.layout)));
  document.querySelector('.feed-controls select[name="category"]')?.addEventListener("change", event => {
    event.currentTarget.form.requestSubmit();
  });

  feed.addEventListener("submit", async event => {
    const form = event.target.closest(".favorite-form, .delete-form");
    if (!form) return;
    event.preventDefault();

    const button = form.querySelector("button");
    const isDelete = form.classList.contains("delete-form");
    if (isDelete) {
      const post = form.closest(".clip-card");
      const nextPost = post.nextElementSibling;
      const originalContent = post.innerHTML;
      const formData = new FormData(form);
      const deadline = Date.now() + 5000;
      let finished = false;
      post.innerHTML = '<div class="delete-undo-state"><p>Post deleted</p><button type="button" class="delete-undo-button">Undo · 5</button></div>';
      if (layout === "column" && nextPost) {
        requestAnimationFrame(() => nextPost.scrollIntoView({ behavior: "smooth", block: "center" }));
      }
      const undoButton = post.querySelector(".delete-undo-button");
      const restorePost = () => {
        if (finished) return;
        finished = true;
        clearTimeout(deleteTimer);
        clearInterval(countdownTimer);
        post.innerHTML = originalContent;
        observeFeed();
      };
      const deleteTimer = setTimeout(async () => {
        if (finished) return;
        finished = true;
        clearInterval(countdownTimer);
        post.innerHTML = '<div class="delete-undo-state"><p>Deleting…</p></div>';
        try {
          const response = await postForm(form, formData);
          if (!response.ok) throw new Error("Could not delete post");
          post.remove();
          observeFeed();
        } catch {
          finished = false;
          post.innerHTML = originalContent;
          observeFeed();
        }
      }, 5000);
      const countdownTimer = setInterval(() => {
        const remaining = Math.max(0, Math.ceil((deadline - Date.now()) / 1000));
        if (undoButton.isConnected) undoButton.textContent = `Undo · ${remaining}`;
      }, 1000);
      undoButton.addEventListener("click", restorePost, { once: true });
      return;
    }
    button.disabled = true;
    try {
      const response = await postForm(form);
      if (!response.ok) throw new Error("Post action failed");
      const result = await response.json();
      const post = form.closest(".clip-card");
      button.classList.toggle("is-active", result.favorite);
      if (!result.favorite && feed.dataset.favoriteFilter === "favorites") {
        post.remove();
        observeFeed();
      } else {
        button.disabled = false;
      }
    } catch {
      button.disabled = false;
    }
  });

  const searchDialog = document.querySelector("#search-dialog");
  document.querySelector("#search-toggle")?.addEventListener("click", () => {
    if (!searchDialog?.open) searchDialog?.showModal();
    searchDialog?.querySelector('[name="q"]')?.focus();
  });

  updateLayout(layout);

})();
