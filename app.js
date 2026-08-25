(() => {
  "use strict";

  const nav = document.querySelector("[data-nav]");
  const menuToggle = document.querySelector("[data-menu-toggle]");
  const mobileMenu = document.querySelector("[data-mobile-menu]");
  const mobileActions = document.querySelector("[data-mobile-actions]");
  const hero = document.querySelector(".hero");
  const parallaxImage = document.querySelector("[data-parallax]");
  const desktopMedia = window.matchMedia("(min-width: 940px)");
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

  const setMenu = (open, restoreFocus = false) => {
    if (!nav || !menuToggle || !mobileMenu) return;
    const nextOpen = Boolean(open) && !desktopMedia.matches;
    nav.classList.toggle("is-open", nextOpen);
    menuToggle.setAttribute("aria-expanded", String(nextOpen));
    menuToggle.setAttribute(
      "aria-label",
      nextOpen ? "Close menu" : "Open menu",
    );
    menuToggle.textContent = nextOpen ? "Close" : "Menu";
    mobileMenu.hidden = !nextOpen;
    document.body.classList.toggle("menu-open", nextOpen);

    if (nextOpen) {
      window.requestAnimationFrame(() =>
        mobileMenu.querySelector("a")?.focus(),
      );
    } else if (restoreFocus) {
      menuToggle.focus();
    }
  };

  menuToggle?.addEventListener("click", () => {
    setMenu(menuToggle.getAttribute("aria-expanded") !== "true");
  });

  mobileMenu?.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => setMenu(false));
  });

  document.addEventListener("pointerdown", (event) => {
    if (menuToggle?.getAttribute("aria-expanded") !== "true") return;
    if (nav?.contains(event.target) || mobileMenu?.contains(event.target))
      return;
    setMenu(false);
  });

  document.addEventListener("keydown", (event) => {
    if (
      event.key === "Escape" &&
      menuToggle?.getAttribute("aria-expanded") === "true"
    ) {
      event.preventDefault();
      setMenu(false, true);
    }
  });

  desktopMedia.addEventListener?.("change", () => setMenu(false));

  document.querySelectorAll("[data-tabs]").forEach((tabGroup) => {
    const tabs = [...tabGroup.querySelectorAll('[role="tab"]')];
    const panels = [...tabGroup.querySelectorAll('[role="tabpanel"]')];

    const selectTab = (tab, moveFocus = false) => {
      const panelId = tab.getAttribute("aria-controls");
      tabs.forEach((item) => {
        const selected = item === tab;
        item.classList.toggle("is-active", selected);
        item.setAttribute("aria-selected", String(selected));
        item.tabIndex = selected ? 0 : -1;
      });
      panels.forEach((panel) => {
        panel.hidden = panel.id !== panelId;
      });
      tab.scrollIntoView({
        behavior: reducedMotion.matches ? "auto" : "smooth",
        block: "nearest",
        inline: "center",
      });
      if (moveFocus) tab.focus();
    };

    tabs.forEach((tab, index) => {
      tab.addEventListener("click", () => selectTab(tab));
      tab.addEventListener("keydown", (event) => {
        let nextIndex = null;
        if (event.key === "ArrowRight" || event.key === "ArrowDown")
          nextIndex = (index + 1) % tabs.length;
        if (event.key === "ArrowLeft" || event.key === "ArrowUp")
          nextIndex = (index - 1 + tabs.length) % tabs.length;
        if (event.key === "Home") nextIndex = 0;
        if (event.key === "End") nextIndex = tabs.length - 1;
        if (nextIndex === null) return;
        event.preventDefault();
        selectTab(tabs[nextIndex], true);
      });
    });
  });

  let frameRequested = false;
  const updateScrollState = () => {
    const y = window.scrollY;
    nav?.classList.toggle("is-solid", y > 24);
    if (mobileActions && hero) {
      mobileActions.classList.toggle(
        "is-visible",
        y > hero.offsetHeight * 0.72,
      );
    }
    if (parallaxImage && !reducedMotion.matches) {
      const offset = Math.min(y, 620) * 0.1;
      parallaxImage.style.transform = `scale(1.035) translate3d(0, ${offset}px, 0)`;
    }
    frameRequested = false;
  };

  const onScroll = () => {
    if (frameRequested) return;
    frameRequested = true;
    window.requestAnimationFrame(updateScrollState);
  };

  updateScrollState();
  window.addEventListener("scroll", onScroll, { passive: true });
  window.addEventListener("resize", onScroll, { passive: true });

  const revealTargets = [
    ...document.querySelectorAll(
      ".section-heading, .journey__layout, .plan-tabs, .practical__grid, .format-grid",
    ),
  ];
  if (reducedMotion.matches || !("IntersectionObserver" in window)) {
    revealTargets.forEach((element) => element.classList.add("is-visible"));
  } else {
    revealTargets.forEach((element) => element.classList.add("reveal"));
    const observer = new IntersectionObserver(
      (entries, currentObserver) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-visible");
          currentObserver.unobserve(entry.target);
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -7% 0px" },
    );
    revealTargets.forEach((element) => observer.observe(element));
  }
})();
