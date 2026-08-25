(() => {
  const DAYS = [
    {
      kicker: "M1 · Historic core",
      title: "Milan historic core",
      body: "Duomo, Galleria, Sforza and Brera — the reservation-led city day that orients every lake and hill excursion.",
      stay: "Base · Duomo / Sant’Ambrogio hotels",
      img: "assets/images/module-core.jpg",
      alt: "Galleria Vittorio Emanuele II in Milan",
    },
    {
      kicker: "M2 · Design evening",
      title: "Navigli and Tortona",
      body: "Canals, design district rhythm and a slower Milan after the monumental core — evening-first by intention.",
      stay: "Mood · canals after the Duomo",
      img: "assets/images/module-navigli.jpg",
      alt: "Navigli canals in Milan",
    },
    {
      kicker: "M3 · Lake day",
      title: "Varenna and Bellagio",
      body: "Ferry geometry on Lake Como — Varenna stone, Bellagio terraces, and a schedule that respects boat gaps.",
      stay: "Gate · ferry and weather windows",
      img: "assets/images/module-como.jpg",
      alt: "Varenna on Lake Como",
    },
    {
      kicker: "M4 · Upper city",
      title: "Bergamo Città Alta",
      body: "Venetian walls, hillside streets and a compact historic day — close enough for rail, distinct enough to reset Milan.",
      stay: "Rail · fast return to Milano",
      img: "assets/images/module-bergamo.jpg",
      alt: "Bergamo Città Alta",
    },
    {
      kicker: "M5 · Charterhouse day",
      title: "Pavia and Certosa",
      body: "Covered bridge, historic centre, then the Certosa — a composed southbound day with clear access gates.",
      stay: "Gate · Certosa opening hours",
      img: "assets/images/module-pavia.jpg",
      alt: "Certosa di Pavia",
    },
    {
      kicker: "M6 · Royal park",
      title: "Monza Villa, park and cathedral",
      body: "Royal Villa, cathedral and one of Europe’s great parks — green scale without leaving the Milan orbit.",
      stay: "Pace · villa then park",
      img: "assets/images/module-monza.jpg",
      alt: "Royal Villa of Monza",
    },
    {
      kicker: "M7 · Borromean day",
      title: "Stresa and the Borromean Islands",
      body: "Stresa lakefront and island hops — Isola Bella and companions when boats, tickets and weather all clear.",
      stay: "Gate · island boat operations",
      img: "assets/images/module-stresa.jpg",
      alt: "Isola Bella on Lago Maggiore",
    },
  ];

  const MODULES = {
    core: {
      tag: "Historic core · Reservation-led",
      title: "Milan historic core",
      body: "The cathedral, rooftop light, Galleria geometry and castle courts — timed so the city still feels walkable.",
      facts: ["Duomo and rooftop", "Galleria and Sforza Castle", "GO / caution / NO-GO gate included"],
      img: "assets/images/module-core.jpg",
    },
    navigli: {
      tag: "Canals · Design district",
      title: "Navigli and Tortona",
      body: "A second Milan register — water, workshops and evening pace after the monumental morning.",
      facts: ["Navigli canals", "Tortona design district", "Evening-first combinations"],
      img: "assets/images/module-navigli.jpg",
    },
    como: {
      tag: "Lake Como · Ferry day",
      title: "Varenna and Bellagio",
      body: "The classic lake pairing with ferry logic written in — not a vague ‘do Como’ day.",
      facts: ["Varenna and Bellagio", "Lake Como ferry sequence", "Weather and timetable gates"],
      img: "assets/images/module-como.jpg",
    },
    bergamo: {
      tag: "Città Alta · Hill day",
      title: "Bergamo Città Alta",
      body: "Walls, upper streets and Venetian air — a short rail hop that changes the whole register.",
      facts: ["Città Alta and walls", "Compact one-day schedule", "Rail return to Milan"],
      img: "assets/images/module-bergamo.jpg",
    },
    pavia: {
      tag: "Certosa · Southbound",
      title: "Pavia and Certosa di Pavia",
      body: "Historic centre plus the charterhouse — beautiful when opening hours and transport align.",
      facts: ["Pavia covered bridge", "Certosa di Pavia", "Access and timing gates"],
      img: "assets/images/module-pavia.jpg",
    },
    monza: {
      tag: "Royal Villa · Park day",
      title: "Monza Villa, park and cathedral",
      body: "Architecture and parkland at Milan’s edge — quieter scale with royal bones.",
      facts: ["Royal Villa of Monza", "Cathedral and park", "Easy orbit from the city"],
      img: "assets/images/module-monza.jpg",
    },
    stresa: {
      tag: "Borromean Islands · Lake Maggiore",
      title: "Stresa and the Borromean Islands",
      body: "Island gardens and lakefront polish — only after boat status and tickets are real for the day.",
      facts: ["Stresa lakefront", "Isola Bella and islands", "Boat operation gates"],
      img: "assets/images/module-stresa.jpg",
    },
  };

  const nav = document.querySelector("[data-nav]");
  const menuToggle = document.querySelector("[data-menu-toggle]");
  const drawer = document.querySelector("[data-drawer]");
  const toast = document.querySelector("[data-toast]");
  const parallax = document.querySelector("[data-parallax]");
  const mobileBar = document.querySelector("[data-mobile-bar]");

  const onScroll = () => {
    if (!nav) return;
    const y = window.scrollY;
    nav.classList.toggle("is-solid", y > 24);
    if (mobileBar) {
      const heroH = Math.max(320, window.innerHeight * 0.72);
      mobileBar.classList.toggle("is-visible", y > heroH);
    }
  };
  onScroll();
  window.addEventListener("scroll", onScroll, { passive: true });

  if (menuToggle && drawer) {
    menuToggle.addEventListener("click", () => {
      const open = !nav.classList.contains("is-open");
      nav.classList.toggle("is-open", open);
      menuToggle.setAttribute("aria-expanded", String(open));
      drawer.hidden = !open;
    });
    drawer.querySelectorAll("a").forEach((a) => {
      a.addEventListener("click", () => {
        nav.classList.remove("is-open");
        menuToggle.setAttribute("aria-expanded", "false");
        drawer.hidden = true;
      });
    });
  }

  if (parallax && !matchMedia("(prefers-reduced-motion: reduce)").matches) {
    window.addEventListener(
      "scroll",
      () => {
        const y = Math.min(window.scrollY, 600);
        parallax.style.transform = `scale(1.06) translate3d(0, ${y * 0.18}px, 0)`;
      },
      { passive: true }
    );
  }

  const dayButtons = [...document.querySelectorAll("[data-day]")];
  const dayImg = document.querySelector("[data-day-img]");
  const dayKicker = document.querySelector("[data-day-kicker]");
  const dayTitle = document.querySelector("[data-day-title]");
  const dayBody = document.querySelector("[data-day-body]");
  const dayStay = document.querySelector("[data-day-stay]");

  const setDay = (index) => {
    const day = DAYS[index];
    if (!day) return;
    dayButtons.forEach((btn, i) => {
      const on = i === index;
      btn.classList.toggle("is-active", on);
      btn.setAttribute("aria-selected", String(on));
    });
    dayKicker.textContent = day.kicker;
    dayTitle.textContent = day.title;
    dayBody.textContent = day.body;
    dayStay.textContent = day.stay;
    if (dayImg) {
      dayImg.classList.add("is-swap");
      window.setTimeout(() => {
        dayImg.src = day.img;
        dayImg.alt = day.alt;
        dayImg.classList.remove("is-swap");
      }, 180);
    }
  };

  dayButtons.forEach((btn) => {
    btn.addEventListener("click", () => setDay(Number(btn.dataset.day)));
  });

  const modButtons = [...document.querySelectorAll("[data-mod]")];
  const modImg = document.querySelector("[data-mod-img]");
  const modTag = document.querySelector("[data-mod-tag]");
  const modTitle = document.querySelector("[data-mod-title]");
  const modBody = document.querySelector("[data-mod-body]");
  const modFacts = document.querySelector("[data-mod-facts]");

  const setMod = (key) => {
    const mod = MODULES[key];
    if (!mod) return;
    modButtons.forEach((btn) => {
      const on = btn.dataset.mod === key;
      btn.classList.toggle("is-active", on);
      btn.setAttribute("aria-selected", String(on));
    });
    modTag.textContent = mod.tag;
    modTitle.textContent = mod.title;
    modBody.textContent = mod.body;
    modFacts.innerHTML = mod.facts.map((f) => `<li>${f}</li>`).join("");
    if (modImg) {
      modImg.classList.add("is-swap");
      window.setTimeout(() => {
        modImg.src = mod.img;
        modImg.classList.remove("is-swap");
      }, 180);
    }
  };

  modButtons.forEach((btn) => {
    btn.addEventListener("click", () => setMod(btn.dataset.mod));
  });

  const counters = [...document.querySelectorAll("[data-count]")];
  const animateCount = (el) => {
    const target = Number(el.dataset.count);
    const duration = 1100;
    const start = performance.now();
    const step = (now) => {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      el.textContent = String(Math.round(target * eased));
      if (t < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  };

  if ("IntersectionObserver" in window) {
    const io = new IntersectionObserver(
      (entries, obs) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          animateCount(entry.target);
          obs.unobserve(entry.target);
        });
      },
      { threshold: 0.5 }
    );
    counters.forEach((el) => io.observe(el));
  } else {
    counters.forEach(animateCount);
  }

  document
    .querySelectorAll(".section__head, .timeline, .module-board, .stats, .checks, .hashes, .dl-grid, .caution__inner")
    .forEach((el) => el.classList.add("reveal"));

  if ("IntersectionObserver" in window) {
    const revealIo = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) entry.target.classList.add("is-in");
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -8% 0px" }
    );
    document.querySelectorAll(".reveal").forEach((el) => revealIo.observe(el));
  } else {
    document.querySelectorAll(".reveal").forEach((el) => el.classList.add("is-in"));
  }

  let toastTimer;
  const showToast = (msg) => {
    if (!toast) return;
    toast.textContent = msg;
    toast.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
      toast.hidden = true;
    }, 1600);
  };

  document.querySelectorAll("[data-hash-row]").forEach((row) => {
    const btn = row.querySelector("[data-copy]");
    const value = row.querySelector(".hash__value");
    if (!btn || !value) return;
    btn.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(value.textContent.trim());
        btn.textContent = "Copied";
        btn.classList.add("is-done");
        showToast("Hash copied");
        setTimeout(() => {
          btn.textContent = "Copy";
          btn.classList.remove("is-done");
        }, 1400);
      } catch {
        showToast("Copy failed");
      }
    });
  });

  const track = document.querySelector("[data-timeline]");
  if (track) {
    track.addEventListener("keydown", (e) => {
      const active = dayButtons.findIndex((b) => b.classList.contains("is-active"));
      if (e.key === "ArrowRight") {
        e.preventDefault();
        const next = Math.min(DAYS.length - 1, active + 1);
        setDay(next);
        dayButtons[next]?.focus();
      }
      if (e.key === "ArrowLeft") {
        e.preventDefault();
        const prev = Math.max(0, active - 1);
        setDay(prev);
        dayButtons[prev]?.focus();
      }
    });
  }
})();
