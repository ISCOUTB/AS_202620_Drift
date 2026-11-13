"use client";

import { useState } from "react";

import {
  DEVICE_KINDS,
  MAX_DEVICE_NAME_LENGTH,
  describeDevice,
  initialsOf,
  platformsOfDevices,
} from "../../domain/model/Account";

import styles from "./AccountPanel.module.css";

/** Botón de la cabecera: iniciar sesión, o el nombre de quien ya entró. */
export function AccountButton({ account, loginUrl, isOpen, onToggle }) {
  if (!account.loginAvailable) {
    return null;
  }

  if (!account.authenticated) {
    return (
      <a className={styles.loginButton} href={loginUrl}>
        <span className={styles.googleMark} aria-hidden="true">
          G
        </span>
        Iniciar sesión con Google
      </a>
    );
  }

  return (
    <button
      type="button"
      className={styles.accountButton}
      aria-expanded={isOpen}
      aria-controls="panel-de-cuenta"
      onClick={onToggle}
    >
      <span className={styles.accountName}>{account.user.name}</span>

      <span className={styles.avatar} aria-hidden="true">
        {initialsOf(account.user.name)}
      </span>
    </button>
  );
}

function DeviceRow({ device, isActive, onUse, onRemove, busy }) {
  return (
    <li className={styles.device}>
      <div className={styles.deviceText}>
        <strong>{device.name}</strong>

        <small>
          {DEVICE_KINDS[device.kind]?.label}
          {device.kind === "pc" ? ` · ${describeDevice(device)}` : ""}
        </small>
      </div>

      <div className={styles.deviceActions}>
        {device.kind === "pc" &&
          (isActive ? (
            <span className={styles.activeTag}>En uso</span>
          ) : (
            <button
              type="button"
              className={styles.secondaryButton}
              onClick={() => onUse(device)}
            >
              Usar este PC
            </button>
          ))}

        <button
          type="button"
          className={styles.dangerLink}
          disabled={busy}
          aria-label={`Eliminar ${device.name}`}
          onClick={() => onRemove(device)}
        >
          Eliminar
        </button>
      </div>
    </li>
  );
}

/** Mi cuenta: dispositivos registrados, cerrar sesión y borrar la cuenta. */
export default function AccountPanel({
  account,
  devices,
  devicesError,
  browserPcProfile,
  activePcDeviceId,
  onAddConsole,
  onAddPc,
  onUsePc,
  onRemoveDevice,
  onApplyPlatforms,
  onLogout,
  onDeleteAccount,
  onClose,
}) {
  const [consoleKind, setConsoleKind] = useState("playstation");
  const [consoleName, setConsoleName] = useState("");
  const [pcName, setPcName] = useState("Mi PC");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [confirmingDelete, setConfirmingDelete] = useState(false);

  const run = async (action) => {
    setBusy(true);
    setMessage("");

    try {
      await action();
    } catch (error) {
      setMessage(error.message);
    } finally {
      setBusy(false);
    }
  };

  const submitConsole = (event) => {
    event.preventDefault();

    void run(async () => {
      await onAddConsole(
        consoleKind,
        consoleName || DEVICE_KINDS[consoleKind].label,
      );
      setConsoleName("");
    });
  };

  const submitPc = (event) => {
    event.preventDefault();

    void run(() => onAddPc(pcName));
  };

  const ownedPlatforms = platformsOfDevices(devices);

  return (
    <section
      className={styles.panel}
      id="panel-de-cuenta"
      aria-label="Mi cuenta"
    >
      <div className={styles.header}>
        <div>
          <p className={styles.eyebrow}>MI CUENTA</p>

          <h2>{account.user.name}</h2>

          <p className={styles.email}>{account.user.email}</p>
        </div>

        <button
          type="button"
          className={styles.closeButton}
          aria-label="Cerrar mi cuenta"
          onClick={onClose}
        >
          ×
        </button>
      </div>

      <h3>Mis dispositivos</h3>

      <p className={styles.description}>
        Registra lo que tienes para ver solo las tiendas que te sirven y
        comprobar los juegos contra tu PC desde cualquier navegador.
      </p>

      {devicesError && <p className={styles.error}>{devicesError}</p>}

      {devices.length > 0 ? (
        <ul className={styles.devices}>
          {devices.map((device) => (
            <DeviceRow
              key={device.id}
              device={device}
              isActive={device.id === activePcDeviceId}
              busy={busy}
              onUse={onUsePc}
              onRemove={(target) => void run(() => onRemoveDevice(target))}
            />
          ))}
        </ul>
      ) : (
        !devicesError && (
          <p className={styles.empty}>Todavía no has registrado dispositivos.</p>
        )
      )}

      {ownedPlatforms.length > 0 && (
        <button
          type="button"
          className={styles.secondaryButton}
          onClick={() => onApplyPlatforms(ownedPlatforms)}
        >
          Ver solo tiendas de {ownedPlatforms.join(", ")}
        </button>
      )}

      <div className={styles.forms}>
        <form className={styles.form} onSubmit={submitConsole}>
          <h4>Agregar una consola</h4>

          <div className={styles.formRow}>
            <label>
              <span>Consola</span>

              <select
                value={consoleKind}
                onChange={(event) => setConsoleKind(event.target.value)}
              >
                <option value="playstation">PlayStation</option>
                <option value="xbox">Xbox</option>
              </select>
            </label>

            <label>
              <span>Nombre (opcional)</span>

              <input
                type="text"
                value={consoleName}
                maxLength={MAX_DEVICE_NAME_LENGTH}
                placeholder="PS5 de la sala"
                onChange={(event) => setConsoleName(event.target.value)}
              />
            </label>
          </div>

          <button type="submit" className={styles.primaryButton} disabled={busy}>
            Agregar consola
          </button>
        </form>

        <form className={styles.form} onSubmit={submitPc}>
          <h4>Guardar mi PC</h4>

          {browserPcProfile ? (
            <>
              <p className={styles.hint}>
                Se guarda el equipo que tienes en este navegador:{" "}
                {browserPcProfile.ramGb} GB
                {browserPcProfile.gpuName
                  ? ` · ${browserPcProfile.gpuName}`
                  : ""}
                .
              </p>

              <div className={styles.formRow}>
                <label>
                  <span>Nombre</span>

                  <input
                    type="text"
                    value={pcName}
                    maxLength={MAX_DEVICE_NAME_LENGTH}
                    onChange={(event) => setPcName(event.target.value)}
                  />
                </label>
              </div>

              <button
                type="submit"
                className={styles.primaryButton}
                disabled={busy}
              >
                Guardar este PC
              </button>
            </>
          ) : (
            <p className={styles.hint}>
              Primero abre un juego y llena «¿Tu PC puede ejecutarlo?». Después
              podrás guardar ese equipo aquí.
            </p>
          )}
        </form>
      </div>

      {message && (
        <p className={styles.error} role="alert">
          {message}
        </p>
      )}

      <div className={styles.footer}>
        <button
          type="button"
          className={styles.secondaryButton}
          disabled={busy}
          onClick={() => void run(onLogout)}
        >
          Cerrar sesión
        </button>

        {confirmingDelete ? (
          <span className={styles.confirm}>
            Se borran tu cuenta, tus dispositivos y tus favoritos. No se puede deshacer.
            <button
              type="button"
              className={styles.dangerButton}
              disabled={busy}
              onClick={() => void run(onDeleteAccount)}
            >
              Sí, eliminar
            </button>
            <button
              type="button"
              className={styles.secondaryButton}
              onClick={() => setConfirmingDelete(false)}
            >
              Cancelar
            </button>
          </span>
        ) : (
          <button
            type="button"
            className={styles.dangerLink}
            onClick={() => setConfirmingDelete(true)}
          >
            Eliminar mi cuenta
          </button>
        )}
      </div>

      <p className={styles.privacy}>
        DRIFT guarda de tu cuenta de Google solo tu nombre, tu correo y tu
        foto, los dispositivos que registres aquí y los juegos que guardes
        en favoritos.
      </p>
    </section>
  );
}
