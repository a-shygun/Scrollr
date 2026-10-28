(() => {
  document.querySelectorAll(".scrollr-toast").forEach(toast => {
    window.setTimeout(() => {
      toast.classList.add("is-dismissing");
      window.setTimeout(() => toast.remove(), 250);
    }, 3000);
  });

  const feed = document.querySelector("#feed-root");
  if (!feed) return;

  let layout = localStorage.getItem("scrollr-layout") || "mosaic";
  let videoObserver;
  let pageObserver;

  function updateLayout(next, selectedPost) {
    layout = next;
    localStorage.setItem("scrollr-layout", layout);
    feed.className = `feed ${layout}-feed`;
    document.body.classList.toggle("single-mode", layout === "single");
    document.querySelectorAll("[data-layout]").forEach(button => {
      button.setAttribute("aria-pressed", String(button.dataset.layout === layout));
    });
    if (layout === "single") {
      const posts = [...feed.querySelectorAll(".clip-card")];
      const index = selectedPost ? Math.max(posts.indexOf(selectedPost), 0) : 0;
      feed.scrollTo({ top: Math.max(index, 0) * feed.clientHeight, behavior: "auto" });
    }
    observeFeed();
  }

  function openPost(post) {
    if (layout === "single") return;
    localStorage.setItem("scrollr-return-layout", layout);
    updateLayout("single", post);
  }

  function observeFeed() {
    videoObserver?.disconnect();
    pageObserver?.disconnect();

    videoObserver = new IntersectionObserver(entries => entries.forEach(({ target, isIntersecting, intersectionRatio }) => {
      if (isIntersecting && intersectionRatio >= 0.35) {
        target.muted = true;
        target.play().catch(() => { });
      } else target.pause();
    }), { threshold: [0, 0.35, 0.65, 0.9] });
    feed.querySelectorAll("video").forEach(video => videoObserver.observe(video));

    const lastPost = feed.lastElementChild;
    if (layout === "single" && feed.dataset.nextPage && lastPost) {
      pageObserver = new IntersectionObserver(entries => {
        if (entries.some(entry => entry.isIntersecting && entry.intersectionRatio >= 0.65)) {
          pageObserver.disconnect();
          window.location.assign(new URL(feed.dataset.nextPage, window.location.href));
        }
      }, { root: feed, threshold: [0.65] });
      pageObserver.observe(lastPost);
    }

  }

  document.querySelectorAll("[data-layout]").forEach(button => button.addEventListener("click", () => updateLayout(button.dataset.layout)));

  feed.addEventListener("submit", event => {
    if (!event.target.closest(".vote-form")) return;
    sessionStorage.setItem("scrollr-vote-scroll", JSON.stringify({
      layout,
      windowY: window.scrollY,
      feedY: feed.scrollTop,
    }));
  });

  feed.addEventListener("click", event => {
    const target = event.target;
    const post = target.closest(".clip-card");
    if (!post) return;
    if (target.closest(".single-grid")) return updateLayout(localStorage.getItem("scrollr-return-layout") || "mosaic");
    if (target.closest(".vote-form")) return;
    const video = target.closest("video");
    if (video && layout === "single") {
      video.muted = !video.muted;
      video.play().catch(() => { });
      post.classList.toggle("is-muted", video.muted);
      return;
    }
    if (target.closest(".video-frame")) openPost(post);
  });

  feed.addEventListener("keydown", event => {
    if (!event.target.matches(".card-caption") || !["Enter", " "].includes(event.key)) return;
    event.preventDefault();
    openPost(event.target.closest(".clip-card"));
  });
  const searchDialog = document.querySelector("#search-dialog");
  const libraryDialog = document.querySelector("#library-dialog");
  document.querySelector("#library-toggle")?.addEventListener("click", () => libraryDialog?.showModal());
  document.querySelector("#search-toggle")?.addEventListener("click", () => {
    if (!searchDialog?.open) searchDialog?.showModal();
    searchDialog?.querySelector('[name="q"]')?.focus();
  });

  updateLayout(layout);

  const savedScroll = sessionStorage.getItem("scrollr-vote-scroll");
  if (savedScroll) {
    sessionStorage.removeItem("scrollr-vote-scroll");
    try {
      const position = JSON.parse(savedScroll);
      requestAnimationFrame(() => requestAnimationFrame(() => {
        if (position.layout === "single") feed.scrollTop = position.feedY;
        else window.scrollTo(0, position.windowY);
      }));
    } catch { }
  }
})();
