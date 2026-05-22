# Planificación: Añadir categoría Excursión

## Objetivo
Incorporar un nuevo tipo de comida llamado "Excursión" en la aplicación para gestionar de manera paralela a Desayuno, Comida, Merienda y Cena.

## Pasos
1. Modificar la inicialización del diccionario `opciones_comida` en `streamlit_app.py` para que incluya `"Excursión": ["-- Ninguno --"]`.
2. Incluir `"Excursión"` en el bucle principal de renderizado de `streamlit_app.py` para que se dibuje el bloque expandible por día.
3. Actualizar el archivo `Maestro_Ingredientes.json` añadiendo un plato ejemplo con el atributo `"tipo_comida": "Excursión"`, de forma que alimente dinámicamente el dropdown de la interfaz.

## Filtros y Condiciones
- Se mantendrá el funcionamiento actual de ajustes manuales (+/-) para las comidas habituales.
- Para "Excursión", se ha creado un conjunto de contadores independientes (Base Exc., Celíacos, Lactosos) para que el conteo no dependa del día, permitiendo especificar explícitamente cuántos y quiénes van a la excursión.

## Lógica de negocio
- El calculador `tools/calculate_shopping.py` se ha modificado ligeramente para ser dinámico y permitir que cualquier comida pueda sobrescribir los valores diarios de `personas`, `celiacos` y `lactosos` si vienen en la configuración de la comida (como es el caso de "Excursión").
- La exportación a CSV/Excel hereda los resultados y desglose del calculador sin necesidad de modificar lógica específica.

## Criterios de éxito
- La app muestra la pestaña de "Excursión" para cada día.
- Se puede seleccionar la "Bolsa de Picnic" en el desplegable.
- La lista de la compra generada incluye correctamente los ingredientes de la bolsa de picnic.
