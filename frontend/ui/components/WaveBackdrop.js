"use client";

import { useEffect, useRef } from "react";

import styles from "./DriftHome.module.css";


const VERTEX_SHADER = `
attribute vec2 aPosition;

void main() {
  gl_Position = vec4(aPosition, 0.0, 1.0);
}
`;


const FRAGMENT_SHADER = `
#ifdef GL_FRAGMENT_PRECISION_HIGH
precision highp float;
#else
precision mediump float;
#endif

uniform vec2 uResolution;
uniform float uTime;

float hash(vec2 point) {
  return fract(sin(dot(point, vec2(12.9898, 78.233))) * 43758.5453);
}

// Ola con la cresta definida que se desvanece hacia abajo.
vec3 wave(
  vec2 uv,
  float x,
  float height,
  float amplitude,
  float frequency,
  float speed,
  float phase,
  vec3 color
) {
  float crest = height
    + amplitude * sin(x * frequency + uTime * speed + phase)
    + amplitude * 0.38 * sin(x * frequency * 2.3 - uTime * speed * 1.4 + phase);

  // El borde nunca es más fino que dos píxeles: a baja resolución no se pixela.
  float edge = max(0.006, 2.0 / uResolution.y);
  float inside = smoothstep(0.0, edge, crest - uv.y);
  float fade = clamp(uv.y / max(crest, 0.001), 0.0, 1.0);

  return color * inside * fade * fade;
}

void main() {
  vec2 uv = gl_FragCoord.xy / uResolution;
  float x = uv.x * uResolution.x / uResolution.y;
  float t = uTime;

  // Deformación suave del espacio: los colores fluyen como un líquido.
  vec2 q = vec2(x, uv.y);
  q += 0.30 * vec2(sin(q.y * 1.9 + t * 0.21), cos(q.x * 1.5 - t * 0.17));
  q += 0.18 * vec2(sin(q.y * 3.3 - t * 0.13 + 1.7), cos(q.x * 2.9 + t * 0.19 + 0.6));

  float a = 0.5 + 0.5 * sin(q.x * 1.3 + q.y * 0.9 + t * 0.23);
  float b = 0.5 + 0.5 * sin(q.x * 0.8 - q.y * 1.7 - t * 0.16 + 2.0);
  float c = 0.5 + 0.5 * sin((q.x + q.y) * 0.6 + t * 0.11 + 4.0);

  vec3 violet = vec3(0.36, 0.13, 0.56);
  vec3 blue = vec3(0.12, 0.20, 0.58);
  vec3 magenta = vec3(0.62, 0.14, 0.44);
  vec3 teal = vec3(0.06, 0.42, 0.52);

  vec3 color = mix(violet, blue, a);
  color = mix(color, magenta, b * 0.75);
  color = mix(color, teal, c * c * 0.55);

  color += wave(uv, x, 0.56, 0.050, 1.6, 0.20, 0.0, vec3(0.69, 0.42, 1.00) * 0.16);
  color += wave(uv, x, 0.42, 0.045, 2.1, -0.27, 2.1, vec3(0.35, 0.66, 1.00) * 0.18);
  color += wave(uv, x, 0.30, 0.040, 2.7, 0.36, 4.2, vec3(1.00, 0.44, 0.71) * 0.22);

  // Viñeta para que el contenido se lea bien encima.
  color *= mix(1.0, 0.5, smoothstep(0.25, 1.05, distance(uv, vec2(0.5, 0.68))));
  color *= 0.88;

  // Ruido mínimo que evita las bandas en los degradados.
  color += (hash(gl_FragCoord.xy) - 0.5) / 128.0;

  gl_FragColor = vec4(color, 1.0);
}
`;


// El fondo es difuso: pintarlo a menor resolución no se nota y cuesta mucho menos.
const INITIAL_SCALE = 0.6;
const MINIMUM_SCALE = 0.15;

// Sin aceleración por hardware el shader corre en la CPU: se parte de muy poco.
const SOFTWARE_SCALE = 0.2;

const FRAMES_PER_CHECK = 45;
const MAXIMUM_FRAME_SKIP = 3;
const WARM_UP_CHECKS = 3;


function createProgram(gl) {
  const program = gl.createProgram();

  for (const [type, source] of [
    [gl.VERTEX_SHADER, VERTEX_SHADER],
    [gl.FRAGMENT_SHADER, FRAGMENT_SHADER],
  ]) {
    const shader = gl.createShader(type);

    gl.shaderSource(shader, source);
    gl.compileShader(shader);

    if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
      return null;
    }

    gl.attachShader(program, shader);
  }

  gl.linkProgram(program);

  return gl.getProgramParameter(program, gl.LINK_STATUS)
    ? program
    : null;
}


/**
 * Fondo de olas de color dibujado en la GPU con un único shader.
 *
 * `requestAnimationFrame` se sincroniza con la frecuencia real de la
 * pantalla (60, 90, 120, 144 Hz…) y el movimiento depende del tiempo
 * transcurrido, así que la velocidad es la misma en cualquier monitor.
 * La resolución de dibujo se ajusta sola al equipo y al navegador.
 * Si WebGL no está disponible queda el degradado estático de CSS.
 */
export default function WaveBackdrop() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;

    const contextOptions = {
      alpha: false,
      antialias: false,
      depth: false,
      stencil: false,
    };

    // Primero se pide un contexto con GPU real; si el navegador solo puede
    // dibujar por software (aceleración desactivada) se acepta, pero liviano.
    let gl = canvas.getContext("webgl", {
      ...contextOptions,
      failIfMajorPerformanceCaveat: true,
    });

    const softwareRendering = !gl;

    if (!gl) {
      gl = canvas.getContext("webgl", contextOptions);
    }

    if (!gl) {
      return undefined;
    }

    const program = createProgram(gl);

    if (!program) {
      return undefined;
    }

    // Un solo triángulo que cubre toda la pantalla.
    const buffer = gl.createBuffer();

    gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
    gl.bufferData(
      gl.ARRAY_BUFFER,
      new Float32Array([-1, -1, 3, -1, -1, 3]),
      gl.STATIC_DRAW
    );

    gl.useProgram(program);

    const position = gl.getAttribLocation(program, "aPosition");

    gl.enableVertexAttribArray(position);
    gl.vertexAttribPointer(position, 2, gl.FLOAT, false, 0, 0);

    const resolutionUniform = gl.getUniformLocation(program, "uResolution");
    const timeUniform = gl.getUniformLocation(program, "uTime");

    const reducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    );

    let scale = softwareRendering ? SOFTWARE_SCALE : INITIAL_SCALE;
    let frameId = 0;
    let contextLost = false;
    let lastFrameAt = 0;
    let frameSkip = 1;
    let frameCount = 0;
    let displayInterval = Infinity;
    let intervals = [];
    let checkedWindows = 0;
    let slowWindows = 0;

    const draw = (now) => {
      gl.uniform1f(timeUniform, now / 1000);
      gl.drawArrays(gl.TRIANGLES, 0, 3);
    };

    const resize = () => {
      const width = Math.max(1, Math.round(window.innerWidth * scale));
      const height = Math.max(1, Math.round(window.innerHeight * scale));

      if (canvas.width !== width || canvas.height !== height) {
        canvas.width = width;
        canvas.height = height;
      }

      gl.viewport(0, 0, width, height);
      gl.uniform2f(resolutionUniform, width, height);

      if (reducedMotion.matches) {
        draw(0);
      }
    };

    /*
      Mide el ritmo real de fotogramas. El intervalo más corto que se logra
      sostener es el de la pantalla (6,9 ms a 144 Hz, 16,7 ms a 60 Hz…); si
      el promedio se aleja de él se están perdiendo fotogramas, y eso es lo
      que se ve como tirones. Entonces se baja la resolución y, si ya no se
      puede bajar más, se dibuja a un ritmo menor pero constante.
    */
    const adaptQuality = (now) => {
      if (lastFrameAt) {
        intervals.push(now - lastFrameAt);
      }

      lastFrameAt = now;

      if (intervals.length < FRAMES_PER_CHECK) {
        return;
      }

      const sorted = intervals.slice().sort((first, second) => first - second);
      const fastest = sorted[Math.floor(sorted.length * 0.1)];
      const average =
        sorted.reduce((total, interval) => total + interval, 0) / sorted.length;

      intervals = [];
      displayInterval = Math.min(displayInterval, fastest);

      checkedWindows += 1;

      // La carga inicial de la página y un tropiezo aislado no cuentan.
      if (checkedWindows <= WARM_UP_CHECKS || average < displayInterval * 1.3) {
        slowWindows = 0;
        return;
      }

      slowWindows += 1;

      if (slowWindows < 2) {
        return;
      }

      slowWindows = 0;

      if (scale > MINIMUM_SCALE) {
        scale = Math.max(MINIMUM_SCALE, scale * 0.7);
        resize();
        draw(now);
      } else if (frameSkip < MAXIMUM_FRAME_SKIP) {
        frameSkip += 1;
      }
    };

    const frame = (now) => {
      adaptQuality(now);

      frameCount += 1;

      if (frameCount % frameSkip === 0) {
        draw(now);
      }

      frameId = requestAnimationFrame(frame);
    };

    const start = () => {
      cancelAnimationFrame(frameId);
      lastFrameAt = 0;
      intervals = [];

      if (contextLost) {
        return;
      }

      if (reducedMotion.matches) {
        draw(0);
        return;
      }

      frameId = requestAnimationFrame(frame);
    };

    const handleContextLost = (event) => {
      event.preventDefault();
      contextLost = true;
      cancelAnimationFrame(frameId);
    };

    // Al volver a la pestaña no se cuentan como lentos los fotogramas en pausa.
    const handleVisibility = () => {
      lastFrameAt = 0;
      intervals = [];
    };

    resize();
    start();

    window.addEventListener("resize", resize);
    document.addEventListener("visibilitychange", handleVisibility);
    reducedMotion.addEventListener("change", start);
    canvas.addEventListener("webglcontextlost", handleContextLost);

    return () => {
      cancelAnimationFrame(frameId);

      window.removeEventListener("resize", resize);
      document.removeEventListener("visibilitychange", handleVisibility);
      reducedMotion.removeEventListener("change", start);
      canvas.removeEventListener("webglcontextlost", handleContextLost);

      gl.deleteBuffer(buffer);
      gl.deleteProgram(program);
    };
  }, []);

  return (
    <div className={styles.backdrop} aria-hidden="true">
      <canvas ref={canvasRef} className={styles.backdropCanvas} />
    </div>
  );
}
