const voteScrollKey = "vote-scroll-position";
const savedScroll = sessionStorage.getItem(voteScrollKey);

if (savedScroll !== null) {
  sessionStorage.removeItem(voteScrollKey);
  requestAnimationFrame(() => window.scrollTo(0, Number(savedScroll)));
}

const feed = document.querySelector("#feed");
const searchForm = document.querySelector("#search-form");
const layoutSelect = document.querySelector("#layout-select");

function updateSearchFilters(url) {
  const search = searchForm.querySelector('[name="q"]').value.trim();
  const type = searchForm.querySelector('[name="type"]').value;

  if (search) {
    url.searchParams.set("q", search);
  } else {
    url.searchParams.delete("q");
  }

  if (type === "all") {
    url.searchParams.delete("type");
  } else {
    url.searchParams.set("type", type);
  }
}

function setLayout(layout) {
  localStorage.setItem("yourstagram-layout", layout);
  if (!feed) return;

  feed.classList.remove("single-feed", "double-feed", "triple-feed");
  feed.classList.add(`${layout}-feed`);
}

const savedLayout = localStorage.getItem("yourstagram-layout") || "single";
if (layoutSelect) {
  layoutSelect.value = savedLayout;
  layoutSelect.addEventListener("change", () => setLayout(layoutSelect.value));
}
setLayout(savedLayout);

if (searchForm) {
  searchForm.addEventListener("submit", event => {
    event.preventDefault();
    const url = new URL(window.location.href);
    updateSearchFilters(url);
    window.location.assign(url);
  });

  searchForm.querySelectorAll("[data-route-filter]").forEach(select => {
    select.addEventListener("change", () => {
      const url = new URL(select.value, window.location.href);
      updateSearchFilters(url);
      window.location.assign(url);
    });
  });

  searchForm.querySelector('[name="type"]').addEventListener("change", () => {
    const url = new URL(window.location.href);
    updateSearchFilters(url);
    window.location.assign(url);
  });
}

if (feed) {
  const videos = feed.querySelectorAll("video");
  const toast = document.querySelector("#speed-toast");
  const controlTimers = new WeakMap();
  let holdTimer;
  let heldVideo;
  let holdStart;

  function loadVideo(video) {
    if (!video.src && video.dataset.src) {
      video.src = video.dataset.src;
      video.load();
    }
  }

  function updateAudioButton(video) {
    const button = video.closest(".clip-card").querySelector("[data-audio]");
    if (!button) return;

    button.setAttribute("aria-pressed", String(!video.muted));
    button.setAttribute("aria-label", video.muted ? "Turn audio on" : "Mute audio");
  }

  function showControls(card) {
    card.classList.add("controls-visible");
    clearTimeout(controlTimers.get(card));
    controlTimers.set(
      card,
      setTimeout(() => card.classList.remove("controls-visible"), 3000)
    );
  }

  const loadObserver = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) loadVideo(entry.target);
    });
  }, { rootMargin: "180px 0px" });

  const playObserver = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      const video = entry.target;
      if (entry.isIntersecting) {
        loadVideo(video);
        video.muted = true;
        updateAudioButton(video);
        video.play().catch(() => {});
      } else {
        video.pause();
      }
    });
  }, { threshold: [0, 0.01] });

  videos.forEach(video => {
    loadObserver.observe(video);
    playObserver.observe(video);
    video.addEventListener("webkitendfullscreen", () => {
      video.controls = false;
      video.muted = true;
      updateAudioButton(video);
    });
  });

  document.addEventListener("fullscreenchange", () => {
    const activeVideo = document.fullscreenElement?.querySelector("video");
    videos.forEach(video => {
      video.controls = video === activeVideo;
      if (!activeVideo) video.muted = true;
      updateAudioButton(video);
    });
  });

  feed.addEventListener("submit", async event => {
    const voteForm = event.target.closest(".vote-form");
    if (!voteForm) return;

    event.preventDefault();
    const buttons = voteForm.querySelectorAll("button[name=choice]");
    buttons.forEach(button => button.disabled = true);

    const choice = event.submitter?.value || voteForm.dataset.choice;
    if (!choice) {
      voteForm.submit();
      return;
    }

    const formData = new FormData(voteForm);
    formData.set("choice", choice);

    try {
      const response = await fetch(voteForm.action, {
        method: "POST",
        body: formData,
        headers: { "X-Requested-With": "XMLHttpRequest" },
      });
      const result = await response.json();
      if (!response.ok) throw new Error("Could not save vote");

      buttons.forEach(button => {
        const selected = button.value === result.vote;
        button.setAttribute("aria-pressed", String(selected));
        button.querySelector("path").setAttribute(
          "fill",
          selected ? "currentColor" : "none"
        );
      });

      const currentFilter = feed.dataset.voteFilter;
      if (
        (currentFilter === "all" && result.vote === "dislike") ||
        (currentFilter === "like" && result.vote !== "like") ||
        (currentFilter === "dislike" && result.vote !== "dislike")
      ) {
        voteForm.closest(".clip-card").remove();
      }
      delete voteForm.dataset.choice;
    } catch (error) {
      voteForm.querySelector('input[name="choice"][type="hidden"]').value = choice;
      sessionStorage.setItem(voteScrollKey, String(window.scrollY));
      voteForm.submit();
    } finally {
      buttons.forEach(button => button.disabled = false);
    }
  });

  feed.addEventListener("click", event => {
    const card = event.target.closest(".clip-card");
    if (!card) return;

    const voteButton = event.target.closest(".vote-form button[name=choice]");
    if (voteButton) {
      voteButton.form.dataset.choice = voteButton.value;
      return;
    }

    const video = card.querySelector("video");
    if (event.target.closest("[data-audio]")) {
      event.preventDefault();
      loadVideo(video);
      video.muted = !video.muted;
      updateAudioButton(video);
      video.play().catch(() => {});
      showControls(card);
    } else if (event.target.closest("[data-fullscreen]")) {
      event.preventDefault();
      if (video) {
        loadVideo(video);
        video.controls = true;
        video.muted = false;
        updateAudioButton(video);
        video.play().catch(() => {});
      }
      showControls(card);

      const frame = card.querySelector(".video-frame");
      if (frame.requestFullscreen) {
        frame.requestFullscreen().catch(() => video?.webkitEnterFullscreen?.());
      } else {
        video?.webkitEnterFullscreen?.();
      }
    } else if (!event.target.closest(".vote-form")) {
      showControls(card);
    }
  });

  function stopFastPlayback() {
    clearTimeout(holdTimer);
    if (heldVideo) {
      heldVideo.playbackRate = 1;
      heldVideo.closest(".clip-card").classList.remove("fast-playing");
      toast.hidden = true;
    }
    heldVideo = null;
    holdStart = null;
  }

  feed.addEventListener("pointerdown", event => {
    const video = event.target.closest("video");
    if (!video || event.button !== 0) return;

    holdStart = { x: event.clientX, y: event.clientY };
    holdTimer = setTimeout(() => {
      heldVideo = video;
      loadVideo(video);
      video.playbackRate = 2;
      video.play().catch(() => {});
      video.closest(".clip-card").classList.add("fast-playing");
      toast.hidden = false;
    }, 360);
  });

  feed.addEventListener("pointermove", event => {
    if (!holdStart) return;
    const distance = Math.hypot(event.clientX - holdStart.x, event.clientY - holdStart.y);
    if (distance > 12) stopFastPlayback();
  });

  ["pointerup", "pointercancel", "pointerleave"].forEach(eventName => {
    feed.addEventListener(eventName, stopFastPlayback);
  });

  feed.addEventListener("contextmenu", event => {
    if (event.target.closest("video")) event.preventDefault();
  });
}
