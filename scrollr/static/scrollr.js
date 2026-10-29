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
  if (layout === "single") layout = "column";
  let videoObserver;
  let pageObserver;

  function updateLayout(next) {
    layout = next;
    localStorage.setItem("scrollr-layout", layout);
    feed.className = `feed ${layout}-feed`;
    document.querySelectorAll("[data-layout]").forEach(button => {
      button.setAttribute("aria-pressed", String(button.dataset.layout === layout));
    });
    observeFeed();
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
    if (feed.dataset.nextPage && lastPost) {
      pageObserver = new IntersectionObserver(async ([entry]) => {
        if (!entry.isIntersecting) return;
        pageObserver.disconnect();
        try {
          const response = await fetch(feed.dataset.nextPage);
          if (!response.ok) throw new Error("Could not load more posts");
          const page = new DOMParser().parseFromString(await response.text(), "text/html");
          const nextFeed = page.querySelector("#feed-root");
          if (!nextFeed) return;
          feed.append(...nextFeed.querySelectorAll(".clip-card"));
          feed.dataset.nextPage = nextFeed.dataset.nextPage;
          observeFeed();
        } catch {
          pageObserver.observe(lastPost);
        }
      }, { rootMargin: "300px" });
      pageObserver.observe(lastPost);
    }
  }

  document.querySelectorAll("[data-layout]").forEach(button => button.addEventListener("click", () => updateLayout(button.dataset.layout)));

  feed.addEventListener("submit", async event => {
    const form = event.target.closest(".vote-form");
    if (!form) return;
    event.preventDefault();

    const button = form.querySelector("button");
    button.disabled = true;
    try {
      const response = await fetch(form.action, {
        method: "POST",
        body: new FormData(form),
        headers: { "X-Requested-With": "XMLHttpRequest" },
      });
      if (!response.ok) throw new Error("Vote failed");

      const { choice } = await response.json();
      const post = form.closest(".clip-card");
      post.querySelectorAll(".vote-action").forEach(voteButton => {
        const active = voteButton.dataset.vote === choice;
        voteButton.classList.toggle("is-active", active);
        voteButton.setAttribute("aria-pressed", String(active));
      });

      const voteFilter = feed.dataset.voteFilter;
      if ((voteFilter === "all" && choice === "dislike") || (voteFilter !== "all" && voteFilter !== choice)) {
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
  const libraryDialog = document.querySelector("#library-dialog");
  document.querySelector("#library-toggle")?.addEventListener("click", () => libraryDialog?.showModal());
  document.querySelector("#search-toggle")?.addEventListener("click", () => {
    if (!searchDialog?.open) searchDialog?.showModal();
    searchDialog?.querySelector('[name="q"]')?.focus();
  });

  updateLayout(layout);

})();
