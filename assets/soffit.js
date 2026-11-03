// Bookend grounds: "Soffit", a GetLayers free layer (commercial use licensed, no credit required).
// Plain WebGL2, one fullscreen triangle per canvas, no libraries, nothing fetched. Recoloured for
// JCare through CONFIG only; the shader below is the shipped source, untouched.
// Every canvas[data-soffit] gets its own context and preset (hero, footer).
// WCAG 2.2.2 by design, no pause button needed: the field animates for at most SETTLE_MS after
// load, then eases to a stop and stops drawing. Only user input (pointer, touch, wheel, keys)
// wakes it (not scroll events: anchoring and layout shift scroll without a person), and IDLE_MS after the last input it settles again. Nothing wakes on a timer.
// Under reduced motion each canvas shows one static frame and never wakes. Off-screen canvases
// and hidden tabs never draw. If WebGL2 is missing or anything fails, the CSS field stays.
(() => {
  const SETTLE_MS = 4000; // auto-motion after load, before easing to rest
  const IDLE_MS = 3000; // after the last input, before easing to rest
  const RAMP_MS = 600; // ease the time rate to 0 (ease-out on the rate)
  const WAKE_MS = 250; // ease the time rate back up to 1 on input

  const BASE = {
    bgColor: "#061B4A", colorA: "#0A3A9E", colorB: "#2B6FD4", colorC: "#0593C6", colorD: "#E4F5C8",
    scale: 0.2, speed: 0.33, tilt: -1.3, rock: 0.11, horizon: -0.52, breathe: 0.09, spread: 1.3, curve: 2.6,
    direct: 0.72, bounce: 0.06, bounceCurve: 1.7, spillCentre: 0.04, spillWidth: 0.2, spillFloor: 0.16,
    amount: 0.22, warp: 1.1, warpScale: 0.72, flow: 0.15, roughness: 0.52, lacunarity: 2.05, motes: 0.03,
    moteScale: 7, ambient: 0.04, contrast: 1.6, midpoint: 0.57, sink: 0.26, glow: 0.34, grain: 0.035,
    grainAnim: 0, dither: 1.2, vignette: 0.44, steer: 0.22, lift: 0.2, sweep: 0.3, cursor: 1,
    parallax: 0.002, maxDpr: 1,
  };
  // Composition presets, CONFIG only. The footer mirrors the hero: bright spill to the left,
  // behind its circle window, with the copy side kept deep.
  const PRESETS = {
    hero: {},
    footer: { tilt: -1.84, spillCentre: -0.04, sweep: -0.3 },
  };

    const VERT = `#version 300 es
void main(){ vec2 p = vec2((gl_VertexID<<1)&2, gl_VertexID&2); gl_Position = vec4(p*2.0-1.0,0.0,1.0); }`;

    const FRAG = `#version 300 es
precision highp float;
out vec4 fragColor;

uniform vec2  iResolution;
uniform float iTime;
uniform vec2  iMouse;
uniform float uScale;

uniform vec3  uBg, uColorA, uColorB, uColorC, uColorD;
uniform float uSpeed, uTilt, uRock, uHorizon, uBreathe, uSpread, uCurve, uDirect;
uniform float uBounce, uBounceCurve;
uniform float uSpillCentre, uSpillWidth, uSpillFloor;
uniform float uAmount, uWarp, uWarpScale, uFlow, uRoughness, uLacunarity, uMotes, uMoteScale;
uniform float uAmbient, uContrast, uMidpoint, uSink, uGlow;
uniform float uGrain, uDither, uVignette;
uniform float uSteer, uLift, uSweep, uParallax;

#define OCTAVES 4

vec2 hash2(vec2 p) {
  p = vec2(dot(p, vec2(127.1, 311.7)), dot(p, vec2(269.5, 183.3)));
  return -1.0 + 2.0 * fract(sin(p) * 43758.5453123);
}

float snoise(vec2 p) {
  const float K1 = 0.366025404, K2 = 0.211324865;
  vec2 i = floor(p + (p.x + p.y) * K1);
  vec2 a = p - i + (i.x + i.y) * K2;
  float m = step(a.y, a.x);
  vec2 o = vec2(m, 1.0 - m);
  vec2 b = a - o + K2;
  vec2 c = a - 1.0 + 2.0 * K2;
  vec3 h = max(0.5 - vec3(dot(a, a), dot(b, b), dot(c, c)), 0.0);
  vec3 n = h * h * h * h * vec3(dot(a, hash2(i)), dot(b, hash2(i + o)), dot(c, hash2(i + 1.0)));
  return dot(n, vec3(70.0));
}

float fbm(vec2 p) {
  float v = 0.0, amp = 0.5;
  for (int i = 0; i < OCTAVES; i++) {
    v += amp * snoise(p);
    p *= uLacunarity;
    amp *= uRoughness;
  }
  return v;
}

vec3 ramp4(float t) {
  vec3 c = mix(uColorA, uColorB, smoothstep(0.00, 0.36, t));
  c = mix(c, uColorC, smoothstep(0.32, 0.70, t));
  c = mix(c, uColorD, smoothstep(0.66, 1.00, t));
  return c;
}

float triDither(vec2 fc) {
  float a = fract(sin(dot(fc, vec2(12.9898, 78.233))) * 43758.5453);
  float b = fract(sin(dot(fc + 17.0, vec2(12.9898, 78.233))) * 43758.5453);
  return (a + b - 1.0) / 255.0;
}

uniform float uGrainAnim;
float houseGrain(vec2 fc) {
  uvec2 q = uvec2(fc) * uvec2(1597334677u, 3812015801u)
          + uint(floor(iTime * 24.0 * uGrainAnim)) * 2654435769u;
  uint n = q.x ^ q.y; n = n * 1664525u + 1013904223u; n ^= n >> 16u; n *= 2246822519u; n ^= n >> 13u;
  float a = float(n & 0xffffu) / 65535.0;
  n *= 3266489917u; n ^= n >> 16u;
  float b = float(n & 0xffffu) / 65535.0;
  return a + b - 1.0;
}
void main() {
  vec2 uv = (gl_FragCoord.xy - 0.5 * iResolution) / iResolution.y;
  uv *= uScale;
  vec2 iM = iMouse * uScale;
  float t = iTime * uSpeed;

  vec2 p = uv - iM * uParallax;

  float tilt = uTilt + sin(t * 0.13) * uRock + iM.x * uSteer;
  vec2 dir = vec2(cos(tilt), sin(tilt));
  float axis = dot(p, dir);
  float across = dot(p, vec2(-dir.y, dir.x));

  vec2 q = vec2(fbm(p * uWarpScale + vec2(0.0, t * uFlow)),
                fbm(p * uWarpScale + vec2(5.2, 1.3) - t * uFlow * 0.7));
  float air = fbm(p + uWarp * q + vec2(t * 0.12, -t * 0.09)) * 0.5 + 0.5;

  float horizon = uHorizon + sin(t * 0.09 + 2.1) * uBreathe - iM.y * uLift;
  float alt = clamp(0.5 + (axis - horizon) * uSpread + (air - 0.5) * uAmount, 0.0, 1.0);

  float ac = (across - uSpillCentre - iM.x * uSweep) / max(0.05, uSpillWidth);
  float spill = mix(uSpillFloor, 1.0, exp(-ac * ac));

  float direct = pow(alt, max(0.05, uCurve)) * uDirect * spill;
  float bounce = uBounce * pow(1.0 - alt, max(0.05, uBounceCurve));

  float f = uAmbient + direct + bounce;
  f += uMotes * snoise(p * uMoteScale + vec2(-t * 0.5, t * 0.35)) * 0.5 * alt;

  f = clamp((f - uMidpoint) * uContrast + 0.5, 0.0, 1.0);

  vec3 col = ramp4(f);
  col += uColorD * uGlow * pow(f, 4.0);
  col = mix(uBg, col, smoothstep(0.0, max(0.01, uSink), f) * 0.90 + 0.10);

  col *= 1.0 - uVignette * dot(uv, uv);
  { float hgL = clamp(dot(col, vec3(0.299, 0.587, 0.114)), 0.0, 1.0);
    col += houseGrain(gl_FragCoord.xy) * uGrain * mix(1.0, 4.0 * hgL * (1.0 - hgL), 0.6); }
  col += triDither(gl_FragCoord.xy) * uDither;

  fragColor = vec4(clamp(col, 0.0, 1.0), 1.0);
}`;

  const instances = [];
  let reduce = null;

  const fallBack = (inst) => {
    inst.lost = true;
    inst.canvas.hidden = true;
    inst.host.classList.remove("is-live");
  };

  const rgb = (hex) => [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255);

  const setup = (canvas) => {
    const host = canvas.closest(".bookend") || canvas.parentElement;
    const config = { ...BASE, ...(PRESETS[canvas.getAttribute("data-soffit")] || {}) };
    const gl = canvas.getContext("webgl2", {
      alpha: false, antialias: false, depth: false, stencil: false, powerPreference: "high-performance",
    });
    if (!gl) return null;

    const compile = (type, source) => {
      const shader = gl.createShader(type);
      gl.shaderSource(shader, source);
      gl.compileShader(shader);
      return gl.getShaderParameter(shader, gl.COMPILE_STATUS) ? shader : null;
    };
    const vs = compile(gl.VERTEX_SHADER, VERT);
    const fs = compile(gl.FRAGMENT_SHADER, FRAG);
    if (!vs || !fs) return null;
    const program = gl.createProgram();
    gl.attachShader(program, vs);
    gl.attachShader(program, fs);
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) return null;
    gl.useProgram(program);
    gl.bindVertexArray(gl.createVertexArray());

    // Each CONFIG key maps to u + Key (bgColor maps to uBg); colours go in as 0..1 vec3.
    for (const [key, value] of Object.entries(config)) {
      if (key === "cursor" || key === "maxDpr") continue;
      const name = key === "bgColor" ? "uBg" : "u" + key[0].toUpperCase() + key.slice(1);
      const at = gl.getUniformLocation(program, name);
      if (!at) continue;
      if (typeof value === "string") gl.uniform3fv(at, rgb(value));
      else gl.uniform1f(at, value);
    }

    return {
      canvas, host, gl, config,
      uRes: gl.getUniformLocation(program, "iResolution"),
      uTime: gl.getUniformLocation(program, "iTime"),
      uMouse: gl.getUniformLocation(program, "iMouse"),
      target: { x: 0, y: 0 }, lead: { x: 0, y: 0 }, body: { x: 0, y: 0 },
      onScreen: true, resizeQueued: true, lost: false,
    };
  };

  // Size to the element, not the window. DPR capped at maxDpr. Resizes coalesce into the next draw.
  const resize = (inst) => {
    inst.resizeQueued = false;
    const { canvas, gl } = inst;
    const dpr = Math.min(window.devicePixelRatio || 1, inst.config.maxDpr);
    const w = Math.max(1, Math.round(canvas.clientWidth * dpr));
    const h = Math.max(1, Math.round(canvas.clientHeight * dpr));
    if (canvas.width !== w || canvas.height !== h) {
      canvas.width = w;
      canvas.height = h;
      gl.viewport(0, 0, w, h);
    }
  };

  let clock = 0;
  const draw = (inst) => {
    if (inst.lost) return;
    if (inst.resizeQueued) resize(inst);
    const { gl } = inst;
    gl.uniform2f(inst.uRes, inst.canvas.width, inst.canvas.height);
    gl.uniform1f(inst.uTime, clock);
    gl.uniform2f(inst.uMouse, inst.body.x, inst.body.y);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
  };

  // Shared time behaviour, so both bookends settle and wake together.
  let rate = 1; // how fast the shader clock runs, 0..1
  let awakeUntil = 0; // performance.now() before which the field may move on its own
  let settleStart = 0;
  let settleFrom = 1;
  let raf = 0;
  let last = 0;

  const visible = () => instances.filter((i) => i.onScreen && !i.lost);
  const followerMoving = () =>
    instances.some((i) => Math.abs(i.target.x - i.body.x) + Math.abs(i.target.y - i.body.y) > 1e-3);

  const frame = (now) => {
    raf = 0;
    let ms = last ? now - last : 16.667;
    last = now;
    ms = Math.min(50, Math.max(4.167, ms));
    const s = ms > 36.7 ? 2.2 : ms * 0.06;

    let resting = false;
    if (now < awakeUntil) {
      settleStart = 0;
      rate += (1 - rate) * Math.min(1, ms / WAKE_MS);
    } else {
      if (!settleStart) {
        settleStart = now;
        settleFrom = rate;
      }
      const p = Math.min(1, (now - settleStart) / RAMP_MS);
      rate = settleFrom * (1 - p) * (1 - p) * (1 - p); // ease-out: most of the slowing happens first
      resting = p >= 1;
    }
    clock += ms * 0.001 * rate;

    const kLead = 0.105 * s;
    const kBody = 0.043 * s;
    for (const inst of instances) {
      inst.lead.x += (inst.target.x - inst.lead.x) * kLead;
      inst.lead.y += (inst.target.y - inst.lead.y) * kLead;
      inst.body.x += (inst.lead.x - inst.body.x) * kBody;
      inst.body.y += (inst.lead.y - inst.body.y) * kBody;
    }
    visible().forEach(draw);

    // Settled: no clock, no pointer drift. Stop issuing frames until the next input.
    if (resting && !followerMoving()) return;
    sync();
  };

  const running = () => !document.hidden && !reduce.matches && visible().length > 0;
  function sync() {
    if (running()) {
      if (!raf) {
        if (!last || performance.now() - last > 100) last = 0;
        raf = window.requestAnimationFrame(frame);
      }
    } else if (raf) {
      window.cancelAnimationFrame(raf);
      raf = 0;
      last = 0;
    }
  }

  // While stopped, a resize still needs one fresh frame.
  let still = 0;
  const redrawStill = () => {
    instances.forEach((i) => (i.resizeQueued = true));
    if (raf || still) return;
    still = window.requestAnimationFrame(() => {
      still = 0;
      visible().forEach(draw);
    });
  };

  // User input wakes the field; nothing else does.
  const wake = () => {
    if (reduce.matches || !instances.length) return;
    awakeUntil = Math.max(awakeUntil, performance.now() + IDLE_MS);
    sync();
  };
  const onPointer = (e) => {
    if (reduce.matches) return;
    for (const inst of instances) {
      const r = inst.canvas.getBoundingClientRect();
      if (!r.width || !r.height) continue;
      inst.target.x = ((e.clientX - r.left) / r.width - 0.5) * (r.width / r.height) * inst.config.cursor;
      inst.target.y = (0.5 - (e.clientY - r.top) / r.height) * inst.config.cursor;
    }
    wake();
  };

  try {
    reduce = window.matchMedia("(prefers-reduced-motion: reduce)");
    document.querySelectorAll("canvas[data-soffit]").forEach((canvas) => {
      try {
        const inst = setup(canvas);
        if (!inst) return;
        // First frame before any loop, so the canvas never shows blank.
        canvas.hidden = false;
        draw(inst);
        inst.host.classList.add("is-live");
        canvas.addEventListener("webglcontextlost", (e) => {
          e.preventDefault();
          fallBack(inst);
          sync();
        });
        instances.push(inst);
      } catch (e) {
        canvas.hidden = true;
      }
    });
    if (!instances.length) return;

    if ("ResizeObserver" in window) {
      const ro = new ResizeObserver(redrawStill);
      instances.forEach((i) => ro.observe(i.canvas));
    } else {
      window.addEventListener("resize", redrawStill);
    }
    if ("IntersectionObserver" in window) {
      const io = new IntersectionObserver((entries) => {
        for (const entry of entries) {
          const inst = instances.find((i) => i.canvas === entry.target);
          if (inst) inst.onScreen = entry.isIntersecting;
        }
        // Coming back on screen never wakes the field by itself: draw one still frame instead.
        redrawStill();
        sync();
      });
      instances.forEach((i) => io.observe(i.canvas));
    }

    window.addEventListener("pointermove", onPointer, { passive: true });
    window.addEventListener("pointerdown", onPointer, { passive: true });
    window.addEventListener("touchmove", wake, { passive: true });
    window.addEventListener("wheel", wake, { passive: true });
    window.addEventListener("keydown", wake);
    document.addEventListener("visibilitychange", sync);
    const onReduceChange = () => {
      if (reduce.matches) awakeUntil = 0;
      sync();
      redrawStill();
    };
    if (reduce.addEventListener) reduce.addEventListener("change", onReduceChange);
    else if (reduce.addListener) reduce.addListener(onReduceChange);

    // The load allowance: at most SETTLE_MS of motion, then it eases to rest.
    if (!reduce.matches) awakeUntil = performance.now() + SETTLE_MS;
    sync();
  } catch (e) {
    instances.forEach(fallBack);
  }
})();
