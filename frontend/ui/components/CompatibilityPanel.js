"use client";

import { useState } from "react";

import { gpuLevelNames } from "../../domain/model/GpuCatalog";
import { createPcProfile } from "../../domain/model/PcProfile";

import styles from "./CompatibilityPanel.module.css";


const RAM_OPTIONS = [4, 8, 12, 16, 24, 32, 64];

const STATUS_TONES = {
  "Compatible": "good",
  "Compatible con limitaciones": "warn",
  "No compatible": "bad",
};

const STATUS_HEADLINES = {
  "Compatible": "Tu PC cumple lo recomendado",
  "Compatible con limitaciones": "Corre, pero cerca del mínimo",
  "No compatible": "Tu PC no alcanza el mínimo",
};

const COMPONENT_LABELS = {
  ram: "Memoria RAM",
  cpu: "Procesador",
  gpu: "Tarjeta gráfica",
  storage: "Almacenamiento",
};

const LEVEL_LABELS = {
  recommended: "Cumple lo recomendado",
  minimum: "Cumple el mínimo",
  insufficient: "No alcanza el mínimo",
  unknown: "Sin comparar",
};

const DETAIL_LABELS = [
  ["os", "Sistema operativo"],
  ["processor", "Procesador"],
  ["memory", "Memoria"],
  ["graphics", "Gráficos"],
  ["storage", "Almacenamiento"],
];


function formatValue(value, unit) {
  if (value === null || value === undefined) {
    return "sin dato";
  }

  if (unit === "nivel") {
    return gpuLevelNames[value] || `nivel ${value}`;
  }

  return `${value} ${unit}`;
}


function describeCheck(check, profile) {
  if (check.level === "unknown") {
    if (check.component === "storage" && check.yours === null) {
      return "Agrega tu espacio libre en «Mi PC» para compararlo.";
    }

    if (check.component === "cpu" && check.yours === null) {
      return "Agrega tu procesador en «Mi PC» para compararlo.";
    }

    return "La tienda no publica un requisito que se pueda comparar.";
  }

  if (check.basis === "benchmark") {
    const parts = [
      `Tienes ${check.yours_name}`,
      `mínimo: ${check.minimum_name}`,
    ];

    if (check.recommended_name) {
      parts.push(`recomendado: ${check.recommended_name}`);
    }

    return parts.join(" · ");
  }

  const modelName = { gpu: profile.gpuName, cpu: profile.cpuName }[
    check.component
  ];

  const yours = modelName
    ? `${modelName} (${formatValue(check.yours, check.unit)})`
    : formatValue(check.yours, check.unit);

  const parts = [
    `Tienes ${yours}`,
    `mínimo ${formatValue(check.minimum, check.unit)}`,
  ];

  if (
    check.component !== "storage" &&
    check.recommended !== null &&
    check.recommended !== undefined
  ) {
    parts.push(`recomendado ${formatValue(check.recommended, check.unit)}`);
  }

  return parts.join(" · ");
}


function findOption(options, typedName) {
  const wanted = typedName.trim().toLocaleLowerCase("es");

  return options.find(
    (option) => option.name.toLocaleLowerCase("es") === wanted,
  );
}


function ProfileForm({ profile, gpuOptions, cpuOptions, onSave, onCancel }) {
  const [ramGb, setRamGb] = useState(String(profile?.ramGb ?? 8));
  const [gpuName, setGpuName] = useState(profile?.gpuName ?? "");
  const [cpuName, setCpuName] = useState(profile?.cpuName ?? "");
  const [storageGb, setStorageGb] = useState(
    profile?.storageGb ? String(profile.storageGb) : "",
  );
  const [formError, setFormError] = useState("");

  const submit = (event) => {
    event.preventDefault();

    const selectedGpu = findOption(gpuOptions, gpuName);

    if (!selectedGpu) {
      setFormError("Elige tu tarjeta gráfica de la lista.");
      return;
    }

    // El procesador es opcional, pero si se escribe debe ser uno de la lista.
    const selectedCpu = findOption(cpuOptions, cpuName);

    if (cpuName.trim() && !selectedCpu) {
      setFormError("Elige tu procesador de la lista o deja el campo vacío.");
      return;
    }

    try {
      onSave(
        createPcProfile({
          ramGb,
          gpuName: selectedGpu.name,
          gpuScore: selectedGpu.score,
          cpuName: selectedCpu?.name,
          cpuScore: selectedCpu?.score,
          storageGb,
        }),
      );
    } catch (profileError) {
      setFormError(profileError.message);
    }
  };

  return (
    <form className={styles.form} onSubmit={submit}>
      <label>
        <span>Memoria RAM</span>

        <select
          value={ramGb}
          onChange={(event) => setRamGb(event.target.value)}
        >
          {RAM_OPTIONS.map((option) => (
            <option key={option} value={option}>
              {option} GB
            </option>
          ))}
        </select>
      </label>

      <label>
        <span>Procesador (opcional)</span>

        <input
          type="text"
          list="drift-cpu-options"
          placeholder="Escribe para buscar: i5-12400, Ryzen 5 5600…"
          autoComplete="off"
          value={cpuName}
          onChange={(event) => setCpuName(event.target.value)}
        />

        <datalist id="drift-cpu-options">
          {cpuOptions.map((option) => (
            <option key={option.name} value={option.name} />
          ))}
        </datalist>
      </label>

      <label>
        <span>Tarjeta gráfica</span>

        <input
          type="text"
          list="drift-gpu-options"
          placeholder="Escribe para buscar: RTX 3060, RX 580, notebook…"
          autoComplete="off"
          value={gpuName}
          onChange={(event) => setGpuName(event.target.value)}
        />

        <datalist id="drift-gpu-options">
          {gpuOptions.map((option) => (
            <option key={option.name} value={option.name} />
          ))}
        </datalist>
      </label>

      <label>
        <span>Espacio libre (GB, opcional)</span>

        <input
          type="number"
          min="1"
          inputMode="numeric"
          placeholder="Ej.: 200"
          value={storageGb}
          onChange={(event) => setStorageGb(event.target.value)}
        />
      </label>

      <div className={styles.formActions}>
        <button type="submit" className={styles.primaryButton}>
          Guardar y comprobar
        </button>

        {onCancel && (
          <button
            type="button"
            className={styles.ghostButton}
            onClick={onCancel}
          >
            Cancelar
          </button>
        )}
      </div>

      {formError && <p className={styles.error}>{formError}</p>}
    </form>
  );
}


function RequirementsText({ text, source }) {
  const blocks = [
    ["Mínimo", text?.minimum],
    ["Recomendado", text?.recommended],
  ].filter(([, details]) => details && Object.keys(details).length > 0);

  if (blocks.length === 0) {
    return null;
  }

  return (
    <details className={styles.requirements}>
      <summary>Ver requisitos publicados por {source}</summary>

      <div className={styles.requirementColumns}>
        {blocks.map(([title, details]) => (
          <div key={title}>
            <h4>{title}</h4>

            <dl>
              {DETAIL_LABELS.filter(([key]) => details[key]).map(
                ([key, label]) => (
                  <div key={key}>
                    <dt>{label}</dt>
                    <dd>{details[key]}</dd>
                  </div>
                ),
              )}
            </dl>
          </div>
        ))}
      </div>
    </details>
  );
}


function Verdict({ result, profile }) {
  const tone = STATUS_TONES[result.status];

  if (!tone) {
    return (
      <div className={`${styles.verdict} ${styles.neutral}`}>
        <strong>Sin requisitos para este juego</strong>

        <p>
          No encontramos requisitos de PC publicados, así que no podemos
          compararlo con tu equipo.
        </p>
      </div>
    );
  }

  const benchmarkSources = [result.gpu_benchmark, result.cpu_benchmark].filter(
    Boolean,
  );

  const comparedByLevel = result.checks.some(
    (check) => check.basis === "level" && check.level !== "unknown",
  );

  return (
    <>
      <div className={`${styles.verdict} ${styles[tone]}`}>
        <span className={styles.verdictDot} aria-hidden="true" />

        <div>
          <strong>{STATUS_HEADLINES[result.status]}</strong>

          <p>{result.status}</p>
        </div>
      </div>

      <ul className={styles.checks}>
        {result.checks.map((check) => (
          <li
            key={check.component}
            className={styles[`level-${check.level}`]}
          >
            <span className={styles.checkName}>
              {COMPONENT_LABELS[check.component]}
            </span>

            <span className={styles.checkLevel}>
              {check.component === "storage" && check.level === "recommended"
                ? "Espacio suficiente"
                : LEVEL_LABELS[check.level]}
            </span>

            <span className={styles.checkDetail}>
              {describeCheck(check, profile)}
            </span>
          </li>
        ))}
      </ul>

      <p className={styles.note}>
        {benchmarkSources.map(
          (source) =>
            `Comparado por benchmark: ${source.benchmark}. Fuente: ${source.source}, datos del ${source.retrieved_at}. `,
        )}
        {comparedByLevel &&
          "Cuando tu componente o el del requisito no está en el catálogo de benchmarks, se compara por niveles aproximados. "}
        {result.partial &&
          "El resultado es parcial: algún componente no se pudo comparar. "}
        Fuente de los requisitos: {result.source}.
      </p>

      <RequirementsText
        text={result.requirements_text}
        source={result.source}
      />
    </>
  );
}


/**
 * Sección «¿Tu PC puede ejecutarlo?». El equipo se registra una vez y se
 * reutiliza para todos los juegos.
 */
export default function CompatibilityPanel({
  profile,
  compatibility,
  gpuOptions,
  cpuOptions,
  onSaveProfile,
}) {
  const [editing, setEditing] = useState(false);

  const saveProfile = (newProfile) => {
    setEditing(false);
    onSaveProfile(newProfile);
  };

  if (!profile || editing) {
    return (
      <div className={styles.panel}>
        <h3>¿Tu PC puede ejecutarlo?</h3>

        <p className={styles.description}>
          Cuéntanos tu equipo una sola vez. Se guarda en este navegador y lo
          usamos para comprobar cada juego. Si tu equipo es portátil, elige la
          tarjeta marcada como «notebook».
        </p>

        <ProfileForm
          profile={profile}
          gpuOptions={gpuOptions}
          cpuOptions={cpuOptions}
          onSave={saveProfile}
          onCancel={profile ? () => setEditing(false) : null}
        />
      </div>
    );
  }

  return (
    <div className={styles.panel}>
      <div className={styles.header}>
        <h3>¿Tu PC puede ejecutarlo?</h3>

        <div className={styles.profileChip}>
          <span>
            Mi PC: {profile.ramGb} GB de RAM
            {profile.cpuName ? ` · ${profile.cpuName}` : ""}
            {profile.gpuName ? ` · ${profile.gpuName}` : ""}
            {profile.storageGb ? ` · ${profile.storageGb} GB libres` : ""}
          </span>

          <button
            type="button"
            className={styles.ghostButton}
            onClick={() => setEditing(true)}
          >
            Editar
          </button>
        </div>
      </div>

      {(!compatibility || compatibility.state === "loading") && (
        <p className={styles.description}>Comprobando compatibilidad…</p>
      )}

      {compatibility?.state === "error" && (
        <p className={styles.error}>{compatibility.message}</p>
      )}

      {compatibility?.state === "done" && (
        <Verdict result={compatibility.data} profile={profile} />
      )}
    </div>
  );
}
