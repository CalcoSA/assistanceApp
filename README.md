# AssistanceApp

## Carga de pensum: error 413 en QA

El frontend desplegado usa Nginx como proxy de `/api/`. Sin una configuración
explícita, Nginx limita el cuerpo de cada petición a `1m` (1 MiB), por lo que un
archivo de aproximadamente 1.125 KB supera ese límite. Esto es independiente del
espacio libre en disco y de la cantidad de páginas del PDF.

`frontend/nginx.conf` configura `client_max_body_size 5m` dentro de `location
/api/`. El límite de 5 MiB incluye el archivo y los datos adicionales del
formulario multipart; no equivale a admitir un archivo de exactamente 5 MiB.
Esta configuración se comparte con producción cuando allí se despliegue el cambio.

Referencia: [client_max_body_size en Nginx](https://nginx.org/en/docs/http/ngx_http_core_module.html#client_max_body_size).

### Aplicar el cambio

El workflow `.github/workflows/deploy-qa.yml` reconstruye las imágenes cuando se
publican cambios en la rama `qa`. La configuración de Nginx se copia dentro de la
imagen del frontend: reiniciar el contenedor existente no incorpora el cambio.

Para aplicarlo manualmente en `calco-contingencia-dian`, primero actualiza el
archivo `frontend/nginx.conf` en la carpeta del despliegue de QA (`QA_PATH` en el
workflow). Desde esa carpeta, con los archivos `.env` del despliegue disponibles:

```bash
docker compose --env-file .env -f docker-compose.qa.yml -f docker-compose.onlyoffice.yml up -d --build --no-deps frontend
docker exec assistance-app-qa-frontend nginx -t
docker exec assistance-app-qa-frontend nginx -T 2>&1 | grep -n -A 8 'location /api/'
```

El último comando debe mostrar `client_max_body_size 5m;` dentro de `/api/`.

### Si persiste el 413

Puede existir otro proxy delante del contenedor, encargado de HTTPS. Todos los
proxies que reciban la carga deben permitir el tamaño de la petición. Si ese
proxy es un Nginx instalado en la VM, inspecciona su configuración activa:

```bash
sudo nginx -T 2>&1 | grep -n -E 'configuration file|server_name|client_max_body_size|proxy_pass'
```

En el bloque `server` que atiende HTTPS para `qa-assistanceapp.calcoweb.net`,
configura `client_max_body_size 5m;`. Revisa que el `location` que recibe `/api/`
no establezca un límite menor. Después valida y recarga:

```bash
sudo nginx -t && sudo systemctl reload nginx
```

Si el proxy externo también está en Docker, realiza la misma comprobación en su
contenedor y conserva el cambio en su configuración de despliegue.

### Verificar la carga

Inicia sesión y adjunta de nuevo el PDF desde la edición de un evento existente.
En Network, `POST /api/events/{id}/pensum` debe devolver una respuesta exitosa y
el archivo debe poder previsualizarse. Para revisar errores del proxy interno:

```bash
docker logs --since 10m assistance-app-qa-frontend 2>&1 | grep -E 'too large body|/pensum'
```

El estado 401 es un problema separado de autenticación. Si persiste después de
iniciar sesión, identifica la petición que falla y revisa su respuesta y el envío
de `Authorization: Bearer ...`, sin compartir el token.

La creación del evento y la carga del pensum son dos peticiones distintas. Si la
primera tuvo éxito y la segunda falló, el evento puede haber quedado creado sin
adjunto. Revisa el listado y edítalo para adjuntar el pensum antes de crearlo otra
vez.
