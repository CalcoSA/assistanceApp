"""Explicit, development-only GCS smoke test; never use application documents.

From backend, using its virtual environment: python scripts/check_gcs_connection.py --run
Without --run this script does not load configuration or contact GCS.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
import sys
import time
from urllib.parse import quote
from uuid import uuid4
from xml.etree import ElementTree


class CheckFailed(Exception):
    """A failure containing only a fixed, safe diagnostic."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CheckFailed(message)


def run() -> int:
    # HTTP debug/INFO output can contain signed URLs. Silence these loggers only
    # in this standalone process, before importing the application configuration.
    for loggerName in ("httpx", "httpcore", "urllib3", "google.auth"):
        logger = logging.getLogger(loggerName)
        logger.disabled = True
        logger.propagate = False
        logger.addHandler(logging.NullHandler())
        logger.setLevel(logging.CRITICAL + 1)

    backendPath = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(backendPath))
    try:
        import httpx

        from app.infrastructure.db.config import settings
        from app.infrastructure.storage.GcsStorage import GcsObjectAlreadyExistsError, GcsStorage
    except Exception:
        print("ERROR: no se pudo cargar la configuracion o las dependencias del backend.", file=sys.stderr)
        print("Ejecuta desde backend con su entorno virtual y revisa la configuracion local.", file=sys.stderr)
        return 1

    try:
        require(settings.GCS_ENVIRONMENT == "development", "La prueba solo permite GCS_ENVIRONMENT=development.")
        require(settings.GCS_AUTH_MODE == "hmac", "La prueba solo permite GCS_AUTH_MODE=hmac.")
        require(settings.GCS_PREFIX == "assistanceApp_dev/", "La prueba solo permite GCS_PREFIX=assistanceApp_dev/.")
        require(settings.GCS_BUCKET == "calco-storage", "La prueba solo permite GCS_BUCKET=calco-storage.")
        require(settings.GCS_ENDPOINT == "https://storage.googleapis.com", "La prueba requiere el endpoint HTTPS oficial de GCS.")
        for name in ("GCS_HMAC_ACCESS_KEY", "GCS_HMAC_SECRET_KEY"):
            value = getattr(settings, name, None)
            require(value is not None and bool(value.get_secret_value().strip()), f"Falta {name} en la configuracion del backend; no se hicieron solicitudes.")
    except CheckFailed as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except Exception:
        print("ERROR: configuracion GCS invalida; no se hicieron solicitudes.", file=sys.stderr)
        return 1

    relativePath = f"pensum/_connection-tests/{uuid4().hex}.txt"
    objectName = settings.GCS_PREFIX + relativePath
    objectUrl = f"{settings.GCS_ENDPOINT}/{settings.GCS_BUCKET}/{quote(objectName, safe='/')}"
    content = b"assistanceApp isolated GCS connection test; synthetic content only.\n"
    generation = None
    storage = None
    success = False
    cleanupOk = True
    stage = "inicializar el servicio"
    # This identifier is not a credential; retain it for a manual investigation
    # if an upload succeeds remotely but its response is lost in transit.
    print(f"Objeto exclusivo de esta prueba: {objectName}")
    try:
        storage = GcsStorage(configuration=settings)
        stage = "subir el objeto sintetico"
        generation = storage.upload(relativePath, content, "text/plain; charset=utf-8")
        require(type(generation) is int and generation > 0, "La subida no devolvio una generacion valida para limpieza segura.")
        stage = "consultar la existencia"
        require(storage.exists(relativePath), "El objeto subido no aparece en la consulta autenticada.")
        print("OK: subida y consulta autenticada.")

        stage = "comprobar la proteccion contra sobrescritura"
        try:
            storage.upload(relativePath, b"This overwrite must be rejected.\n", "text/plain")
        except GcsObjectAlreadyExistsError:
            pass
        else:
            raise CheckFailed("La subida repetida no fue rechazada: proteccion contra sobrescritura fallida.")
        print("OK: sobrescritura rechazada con HTTP 412.")

        with httpx.Client(
            timeout=settings.GCS_TIMEOUT_SECONDS,
            follow_redirects=False,
            trust_env=False,
            headers={"Cache-Control": "no-cache, no-store", "Pragma": "no-cache"},
        ) as anonymous:
            stage = "comprobar acceso anonimo"
            response = anonymous.get(objectUrl)
            require(response.status_code in (401, 403), "La lectura anonima no fue rechazada con HTTP 401/403.")
            # No unrelated object names or data are requested or printed.
            listing = anonymous.get(
                f"{settings.GCS_ENDPOINT}/{settings.GCS_BUCKET}",
                params={"prefix": objectName, "max-keys": "1"},
            )
            require(listing.status_code in (401, 403), "El listado anonimo del bucket no fue rechazado con HTTP 401/403.")
            print("OK: lectura del objeto y listado anonimos rechazados.")

            stage = "validar lectura por URL firmada"
            expirationSeconds = 8
            signedUrl = storage.generateReadUrl(relativePath, expiresInSeconds=expirationSeconds)
            response = anonymous.get(signedUrl)
            require(response.status_code == 200 and response.content == content, "La URL firmada no devolvio el contenido sintetico esperado.")
            print("OK: lectura temporal firmada (URL omitida).")

            stage = "validar expiracion de la URL firmada"
            print("Esperando la expiracion de 8 segundos y 5 segundos de margen...")
            time.sleep(expirationSeconds + 5)
            response = anonymous.get(signedUrl)
            try:
                expirationCode = ElementTree.fromstring(response.content).findtext("Code")
            except ElementTree.ParseError:
                expirationCode = None
            # GCS XML API returns HTTP 400 ExpiredToken for an expired V4 URL.
            # A generic permission error alone does not demonstrate expiration.
            require(
                response.status_code in (400, 403) and expirationCode == "ExpiredToken",
                f"La URL no devolvio ExpiredToken tras expirar (HTTP {response.status_code}).",
            )
            require(storage.exists(relativePath), "El objeto ya no existe: no se pudo comprobar la expiracion de la URL.")
            print("OK: URL expirada rechazada mientras el objeto sigue existiendo.")
            success = True
    except CheckFailed as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
    except KeyboardInterrupt:
        print("Prueba interrumpida; se intentara limpiar solo la generacion creada.", file=sys.stderr)
    except Exception:
        # Never display third-party exceptions, response bodies, authentication
        # headers or tracebacks: they can include credentials or signed URLs.
        print(f"ERROR al {stage}. Revisa conexion, configuracion y permisos; detalles sensibles omitidos.", file=sys.stderr)
    finally:
        if storage is not None:
            try:
                if type(generation) is int and generation > 0:
                    storage.delete(relativePath, expectedGeneration=generation)
                    require(not storage.exists(relativePath), "La consulta aun encuentra el objeto de prueba.")
                    print("OK: eliminada solo la generacion creada; ausencia confirmada.")
                elif not success:
                    print("No hay generacion confirmada: no se eliminara ningun objeto automaticamente.", file=sys.stderr)
            except Exception:
                cleanupOk = False
                print("ERROR: no se pudo confirmar la limpieza. Revisa en la consola unicamente el objeto de prueba indicado arriba; no borres carpetas.", file=sys.stderr)
            finally:
                try:
                    storage.close()
                except Exception:
                    cleanupOk = False
                    print("ERROR: no se pudo cerrar el cliente GCS correctamente.", file=sys.stderr)

    if success and cleanupOk:
        print("Prueba completada. La comprobacion anonima no sustituye revisar IAM y Public Access Prevention del bucket.")
        return 0
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Prueba controlada GCS, exclusivamente Development y con contenido sintetico.")
    parser.add_argument("--run", action="store_true", help="Autoriza las solicitudes reales y la limpieza del objeto exclusivo de esta prueba.")
    args = parser.parse_args()
    if not args.run:
        parser.print_help()
        print("Sin --run no se carga configuracion ni se realizan solicitudes.")
        return 0
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
