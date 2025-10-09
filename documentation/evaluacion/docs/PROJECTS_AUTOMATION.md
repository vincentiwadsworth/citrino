# ACTUALIZANDO: Automatización de GitHub Projects

## Resumen

Este proyecto tiene un sistema de automatización para mantener el tablero de GitHub Projects sincronizado con los commits realizados.

## ¿Cómo funciona?

### Automáticamente (Opción recomendada)

El sistema se activa automáticamente después de cada commit mediante un **Git Hook**:

1. **Post-commit hook**: `.git/hooks/post-commit`
   - Se ejecuta automáticamente después de cada commit
   - Llama al agente de actualización
   - Actualiza las tarjetas correspondientes

### Manualmente (Si falla lo automático)

Si el hook no funciona, puedes ejecutar manualmente:

```bash
python agents/github_projects_updater.py
```

## Mapeo de Commits a Tarjetas

El sistema actualiza automáticamente las tarjetas basado en palabras clave en los mensajes de commit:

| Palabra Clave | Tarjeta | Descripción |
|---|---|---|
| `commit 1`, `estructura`, `docs`, `readme` | Commit 1 | Estructura y documentación |
| `commit 2`, `motor`, `feat`, `fix` | Commit 2 | Motor de recomendación |
| `commit 3`, `test` | Commit 3 | Tests unitarios |
| `commit 4`, `cli` | Commit 4 | Interfaz CLI |
| `commit 5`, `optimizacion`, `refactor`, `chore` | Commit 5 | Optimización y mejoras |

## Flujo de Trabajo Ideal

1. **Haces cambios** al código o README
2. **Commiteas** los cambios con un mensaje claro
3. **Automáticamente** se actualiza GitHub Projects
4. **Verificas** el tablero para ver el progreso

## Personalización

### Añadir nuevos mapeos

Edita el archivo `agents/github_projects_updater.py` y añade nuevos entries al diccionario `item_mapping`:

```python
item_mapping = {
    'nueva_palabra_clave': 'ID_DEL_ITEM',
    # ... otros mapeos
}
```

### Crear nuevas tarjetas

Si necesitas una nueva tarjeta, puedes:

1. Crearla manualmente en GitHub Projects
2. Copiar su ID desde la URL
3. Añadir el mapeo en el script

## Troubleshooting

### El hook no se ejecuta

1. Verifica que el hook sea ejecutable: `chmod +x .git/hooks/post-commit`
2. Verifica los permisos de ejecución
3. Revisa el log de errores

### No se actualiza la tarjeta correcta

1. Verifica que el mensaje del commit contenga la palabra clave correcta
2. Revisa el mapeo en el script
3. Verifica los IDs de las tarjetas

### Errores de autenticación

1. Verifica que `gh auth status` esté funcionando
2. Revisa los permisos del token de GitHub
3. Vuelve a autenticar con `gh auth login`

## Notas Importantes

- El sistema solo funciona con commits que se hagan localmente
- Necesitas tener `gh` (GitHub CLI) instalado y autenticado
- Las tarjetas deben existir en el proyecto antes de poder actualizarlas
- Los IDs del proyecto y campos están configurados para este proyecto específico