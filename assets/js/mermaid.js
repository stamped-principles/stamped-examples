// Site-level override of Congo's mermaid.js
// Adds svg-pan-zoom integration and fullscreen toggle after mermaid renders diagrams.

function css(name) {
  return "rgb(" + getComputedStyle(document.documentElement).getPropertyValue(name) + ")";
}

let isDark = document.documentElement.classList.contains("dark");

mermaid.initialize({
  theme: "base",
  themeVariables: {
    background: css("--color-neutral"),
    primaryTextColor: isDark ? css("--color-neutral-200") : css("--color-neutral-700"),
    primaryColor: isDark ? css("--color-primary-700") : css("--color-primary-200"),
    secondaryColor: isDark ? css("--color-secondary-700") : css("--color-secondary-200"),
    tertiaryColor: isDark ? css("--color-neutral-700") : css("--color-neutral-100"),
    primaryBorderColor: isDark ? css("--color-primary-500") : css("--color-primary-400"),
    secondaryBorderColor: css("--color-secondary-400"),
    tertiaryBorderColor: isDark ? css("--color-neutral-300") : css("--color-neutral-400"),
    lineColor: isDark ? css("--color-neutral-300") : css("--color-neutral-600"),
    fontFamily:
      "ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,segoe ui,Roboto,helvetica neue,Arial,noto sans,sans-serif",
    fontSize: "16px",
    pieTitleTextSize: "19px",
    pieSectionTextSize: "16px",
    pieLegendTextSize: "16px",
    pieStrokeWidth: "1px",
    pieOuterStrokeWidth: "0.5px",
    pieStrokeColor: isDark ? css("--color-neutral-300") : css("--color-neutral-400"),
    pieOpacity: "1",
  },
});

// After mermaid initializes and renders SVGs, apply svg-pan-zoom and fullscreen button.
// Mermaid renders asynchronously, so we use a MutationObserver to detect
// when SVG elements appear inside .mermaid containers.
(function () {
  var containers = document.querySelectorAll(".mermaid");
  if (!containers.length) return;

  // Track pan-zoom instances per container so we can re-fit on fullscreen change
  var panZoomInstances = new Map();
  // Save pre-fullscreen state so we can restore exactly on exit
  var preFullscreenState = new Map();

  function applySvgPanZoom(svg, container) {
    // Skip if already processed
    if (svg.dataset.panZoomApplied) return;
    svg.dataset.panZoomApplied = "true";

    // Remove mermaid's inline max-width constraint so the SVG can fill the container
    svg.style.maxWidth = "none";
    svg.removeAttribute("width");

    // Set explicit pixel dimensions from the container so svg-pan-zoom can
    // compute correct transforms (it strips viewBox, so % / auto won't work)
    svg.setAttribute("width", container.clientWidth);
    svg.setAttribute("height", container.clientHeight);
    svg.style.width = "100%";
    svg.style.height = "100%";

    var instance = svgPanZoom(svg, {
      zoomEnabled: true,
      controlIconsEnabled: true,
      fit: true,
      center: true,
      minZoom: 0.5,
      maxZoom: 10,
      zoomScaleSensitivity: 0.3,
    });

    panZoomInstances.set(container, instance);
  }

  function addFullscreenButton(container) {
    // Don't add twice
    if (container.querySelector(".mermaid-fullscreen-btn")) return;

    var btn = document.createElement("button");
    btn.className = "mermaid-fullscreen-btn";
    btn.title = "Toggle fullscreen";
    btn.textContent = "\u26F6";
    btn.addEventListener("click", function () {
      if (!document.fullscreenElement) {
        // Save current state before entering fullscreen so we can restore on exit
        var instance = panZoomInstances.get(container);
        var svg = container.querySelector("svg");
        if (instance && svg) {
          preFullscreenState.set(container, {
            pan: instance.getPan(),
            zoom: instance.getZoom(),
            width: svg.getAttribute("width"),
            height: svg.getAttribute("height"),
          });
        }
        container.requestFullscreen().catch(function () {});
      } else {
        document.exitFullscreen();
      }
    });
    container.appendChild(btn);
  }

  // Re-fit the diagram when entering or leaving fullscreen
  document.addEventListener("fullscreenchange", function () {
    // Use double-rAF to wait for the browser to finish the fullscreen layout
    requestAnimationFrame(function () {
      requestAnimationFrame(function () {
        if (document.fullscreenElement) {
          // Entering fullscreen — expand to fill and fit/center
          var instance = panZoomInstances.get(document.fullscreenElement);
          var svg = document.fullscreenElement.querySelector("svg");
          if (instance && svg) {
            svg.setAttribute("width", document.fullscreenElement.clientWidth);
            svg.setAttribute("height", document.fullscreenElement.clientHeight);
            instance.resize();
            instance.fit();
            instance.center();
          }
        } else {
          // Exiting fullscreen — restore saved dimensions and pan/zoom state
          preFullscreenState.forEach(function (state, container) {
            var instance = panZoomInstances.get(container);
            var svg = container.querySelector("svg");
            if (instance && svg) {
              svg.setAttribute("width", state.width);
              svg.setAttribute("height", state.height);
              instance.resize();
              instance.zoom(state.zoom);
              instance.pan(state.pan);
            }
          });
          preFullscreenState.clear();
        }
      });
    });
  });

  // Observe each .mermaid container for child SVG additions
  var observer = new MutationObserver(function (mutations) {
    mutations.forEach(function (mutation) {
      mutation.addedNodes.forEach(function (node) {
        if (node.nodeName && node.nodeName.toLowerCase() === "svg") {
          var container = node.closest(".mermaid");
          // Small delay to let mermaid finish any post-render adjustments
          setTimeout(function () {
            applySvgPanZoom(node, container);
            addFullscreenButton(container);
          }, 100);
        }
      });
    });
  });

  containers.forEach(function (container) {
    // Check if SVG is already rendered (in case observer attaches late)
    var existingSvg = container.querySelector("svg");
    if (existingSvg) {
      setTimeout(function () {
        applySvgPanZoom(existingSvg, container);
        addFullscreenButton(container);
      }, 100);
    }

    // Watch for future SVG insertions
    observer.observe(container, { childList: true });
  });
})();
