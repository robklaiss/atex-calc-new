# Requisitos del Archivo DXF

## Capas Requeridas

El archivo DXF debe contener las siguientes capas con geometrías cerradas:

### 1. **superficieTotal**
- Debe contener exactamente **un polígono cerrado**
- Representa el contorno total de la losa
- Puede ser cualquier forma (rectangular, L, T, etc.)

### 2. **superficieCasetones**
- Debe contener **al menos un polígono cerrado**
- Representa las áreas donde se colocarán los casetones
- Cada polígono representa un casetón o grupo de casetones
- También se aceptan círculos en esta capa

### 3. **superficieMacizos** (Opcional)
- Contiene las áreas macizas de la losa
- Generalmente los bordes y vigas
- Si no se especifica, se asume que no hay áreas macizas

### 4. **superficieVacios** (Opcional)
- Contiene áreas vacías (huecos, shafts, etc.)
- Se restarán del cálculo total

## Entidades Soportadas

- **LWPOLYLINE**: Polilíneas ligeras (preferidas)
- **POLYLINE**: Polilíneas estándar
- **CIRCLE**: Círculos (solo en capa superficieCasetones)

## Requisitos de las Geometrías

- Todas las entidades deben estar **cerradas**
- Los polígonos deben tener al menos 3 puntos
- Las geometrías deben ser válidas (sin autointersecciones)

## Ejemplo de Estructura Típica

```
Losas 10m x 8m
├── superficieTotal: 1 rectángulo de 10x8m
├── superficieCasetones: 6 rectángulos de 2x2m
├── superficieMacizos: 2 rectángulos (bordes)
└── superficieVacios: 0 (ninguno)
```

## Tips para AutoCAD

1. Cree las capas exactamente con los nombres especificados
2. Use el comando `POLYLINE` o `RECTANGLE` para crear polígonos
3. Asegúrese de que los polígonos estén cerrados (opción "Close")
4. Verifique que no haya líneas o arcos sueltos
5. Use `AUDIT` en AutoCAD para verificar la integridad del archivo

## Problemas Comunes

- **"No se encontró superficieTotal"**: Verifique que haya exactamente un polígono cerrado en esa capa
- **"No se encontraron casetones"**: Asegúrese de tener al menos un polígono en la capa superficieCasetones
- **"Polígono inválido"**: La geometría puede tener autointersecciones o puntos duplicados

## Coordenadas

- Las coordenadas pueden estar en cualquier unidad (metros, centímetros, etc.)
- El sistema realiza cálculos relativos, por lo que la escala no afecta los resultados relativos
- Para mayor precisión, recomiendamos trabajar en metros
