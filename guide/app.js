(() => {
  "use strict";
  const guideKey = document.documentElement.dataset.guide || "milan-travel-guide";
  const storage = {
    get(key) { try { return localStorage.getItem(key); } catch (_) { return null; } },
    set(key, value) { try { localStorage.setItem(key, value); } catch (_) {} },
    remove(key) { try { localStorage.removeItem(key); } catch (_) {} }
  };

  const menuButton = document.querySelector("#guideMenuToggle");
  const navigation = document.querySelector("#guideNavigation");
  const sidebar = document.querySelector(".sidebar");
  const compact = matchMedia("(max-width: 900px)");
  const setMenu = (open, restoreFocus = false) => {
    if (!menuButton || !navigation) return;
    const isOpen = compact.matches ? Boolean(open) : true;
    navigation.hidden = !isOpen;
    menuButton.setAttribute("aria-expanded", String(isOpen));
    menuButton.setAttribute("aria-label", isOpen ? "Close guide menu" : "Open guide menu");
    menuButton.textContent = isOpen ? "Close" : "Menu";
    if (isOpen && compact.matches) {
      requestAnimationFrame(() => navigation.querySelector("a")?.focus());
    } else if (restoreFocus) {
      menuButton.focus();
    }
  };
  const syncMenu = () => setMenu(!compact.matches);
  menuButton?.addEventListener("click", () => setMenu(menuButton.getAttribute("aria-expanded") !== "true"));
  navigation?.querySelectorAll("a").forEach(link => link.addEventListener("click", () => {
    if (compact.matches) setMenu(false);
  }));
  document.addEventListener("pointerdown", event => {
    if (!compact.matches || menuButton?.getAttribute("aria-expanded") !== "true") return;
    if (!sidebar?.contains(event.target)) setMenu(false);
  });
  document.addEventListener("keydown", event => {
    if (event.key === "Escape" && compact.matches && menuButton?.getAttribute("aria-expanded") === "true") {
      event.preventDefault();
      setMenu(false, true);
    }
  });
  compact.addEventListener?.("change", syncMenu);
  syncMenu();

  const search = document.querySelector("#guideSearch");
  const searchStatus = document.querySelector("#searchStatus");
  const searchable = [...document.querySelectorAll("main > section[id]")];
  search?.addEventListener("input", () => {
    const term = search.value.trim().toLocaleLowerCase();
    let matches = 0;
    searchable.forEach(section => {
      const match = !term || section.textContent.toLocaleLowerCase().includes(term);
      section.hidden = !match;
      if (match) matches += 1;
    });
    if (searchStatus) searchStatus.textContent = term ? `${matches} sections match` : "";
  });

  const planInputs = [...document.querySelectorAll('.day-plan-card input[type="checkbox"]')];
  const builderDays = document.querySelector("#builderDays");
  const builderText = document.querySelector("#builderText");
  const updateBuilder = () => {
    const selected = planInputs.filter(input => input.checked);
    const days = selected.reduce((total, input) => total + Number(input.dataset.days || 1), 0);
    if (builderDays) builderDays.textContent = `${days} day${days === 1 ? "" : "s"} selected`;
    if (builderText) builderText.textContent = selected.length
      ? selected.map(input => input.dataset.title).join(" · ")
      : "Choose one or more day plans to shape your trip.";
  };
  planInputs.forEach(input => input.addEventListener("change", updateBuilder));
  document.querySelector("#builderClear")?.addEventListener("click", () => {
    planInputs.forEach(input => { input.checked = false; });
    updateBuilder();
  });
  updateBuilder();

  document.querySelectorAll('.check input[type="checkbox"]').forEach((input, index) => {
    const key = `${guideKey}-check-${input.dataset.key || index}`;
    input.checked = storage.get(key) === "1";
    input.addEventListener("change", () => storage.set(key, input.checked ? "1" : "0"));
  });
  document.querySelector("#resetChecks")?.addEventListener("click", () => {
    document.querySelectorAll('.check input[type="checkbox"]').forEach((input, index) => {
      input.checked = false;
      storage.remove(`${guideKey}-check-${input.dataset.key || index}`);
    });
  });

  const budgetInputs = [...document.querySelectorAll('.budget input[type="number"]')];
  const budgetTotal = document.querySelector("#budgetTotal");
  const updateBudget = () => {
    const total = budgetInputs.reduce((sum, input) => sum + (Number(input.value) || 0), 0);
    if (budgetTotal) budgetTotal.textContent = `${total.toFixed(0)} ${budgetTotal.dataset.currency || ""}`.trim();
  };
  budgetInputs.forEach(input => input.addEventListener("input", updateBudget));
  updateBudget();

  const photoButtons = [...document.querySelectorAll(".photo-open[data-photo]")];
  const photos = [];
  const seen = new Set();
  photoButtons.forEach(button => {
    if (!seen.has(button.dataset.photo)) {
      seen.add(button.dataset.photo);
      photos.push(button);
    }
  });
  const lightbox = document.querySelector("#lightbox");
  const lightboxImage = document.querySelector("#lightboxImage");
  const lightboxCaption = document.querySelector("#lightboxCaption");
  const lightboxSource = document.querySelector("#lightboxSource");
  let currentPhoto = "";
  let returnFocus = null;
  const backgroundNodes = [document.querySelector(".app"), document.querySelector(".footer"), document.querySelector(".guide-skip")].filter(Boolean);
  const showPhoto = button => {
    if (!button || !lightboxImage || !lightboxCaption || !lightboxSource) return;
    currentPhoto = button.dataset.photo;
    lightboxImage.src = button.dataset.full;
    lightboxImage.alt = button.dataset.title;
    lightboxCaption.textContent = `${button.dataset.title} · ${button.dataset.creator}`;
    lightboxSource.href = button.dataset.source;
  };
  const openPhoto = button => {
    if (!lightbox) return;
    returnFocus = button;
    showPhoto(button);
    lightbox.classList.add("open");
    lightbox.setAttribute("aria-hidden", "false");
    backgroundNodes.forEach(node => { node.inert = true; });
    document.body.style.overflow = "hidden";
    document.querySelector("#lightboxClose")?.focus();
  };
  const closePhoto = () => {
    if (!lightbox) return;
    lightbox.classList.remove("open");
    lightbox.setAttribute("aria-hidden", "true");
    backgroundNodes.forEach(node => { node.inert = false; });
    document.body.style.overflow = "";
    returnFocus?.focus();
  };
  const shiftPhoto = delta => {
    const index = photos.findIndex(button => button.dataset.photo === currentPhoto);
    if (index >= 0) showPhoto(photos[(index + delta + photos.length) % photos.length]);
  };
  photoButtons.forEach(button => button.addEventListener("click", () => openPhoto(button)));
  document.querySelector("#lightboxClose")?.addEventListener("click", closePhoto);
  document.querySelector("#lightboxPrev")?.addEventListener("click", () => shiftPhoto(-1));
  document.querySelector("#lightboxNext")?.addEventListener("click", () => shiftPhoto(1));
  lightbox?.addEventListener("click", event => { if (event.target === lightbox) closePhoto(); });
  document.addEventListener("keydown", event => {
    if (!lightbox?.classList.contains("open")) return;
    if (event.key === "Escape") closePhoto();
    if (event.key === "ArrowLeft") shiftPhoto(-1);
    if (event.key === "ArrowRight") shiftPhoto(1);
    if (event.key === "Tab") {
      const focusable = [...lightbox.querySelectorAll("button:not([disabled]), a[href]")].filter(element => element.offsetParent !== null);
      const first = focusable[0];
      const last = focusable.at(-1);
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
      if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
    }
  });

  const visibleSections = [...document.querySelectorAll("main > section[id]")];
  if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver(entries => {
      const current = entries.filter(entry => entry.isIntersecting).sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
      if (!current) return;
      navigation?.querySelectorAll("a").forEach(link => link.classList.toggle("active", link.getAttribute("href") === `#${current.target.id}`));
    }, { rootMargin: "-20% 0px -68%", threshold: [0, .15, .4] });
    visibleSections.forEach(section => observer.observe(section));
  }
})();
