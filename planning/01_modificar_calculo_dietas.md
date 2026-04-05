# Plan: Modificar cálculo de dietas separadas

## Objetivo
Modificar la estructura de datos de ingredientes y la lógica de cálculo para generar listas de compra separadas por necesidades dietéticas (base/sin dieta, celíacos y lactosos), permitiendo gestionar menú y cantidades de forma precisa.

## Pasos
1. Actualizar `Maestro_Ingredientes.json`:
   - Cambiar la propiedad `ingredientes` actual por un desglose en `ingredientes_base`, `ingredientes_lactosa`, y `ingredientes_celiacos` para cada plato.
   - Proveer ejemplos de ingredientes alternativos para celíacos (ej. "Macarrones sin gluten") y lactosos (ej. "Leche sin lactosa", "Queso sin lactosa").
2. Actualizar `tools/calculate_shopping.py`:
   - Leer `celiacos` y `lactosos` del plan diario.
   - Calcular `personas_totales_comida = personas_base + ajuste`.
   - Calcular las personas por tipo de dieta: 
     - Celíacos = `celiacos`
     - Lactosos = `lactosos`
     - Sin dieta (base) = `personas_totales_comida - celiacos - lactosos` (asegurando un mínimo de 0).
   - Iterar sobre `ingredientes_base` multiplicando por `personas_sin_dieta`.
   - Iterar sobre `ingredientes_celiacos` multiplicando por celíacos.
   - Iterar sobre `ingredientes_lactosa` multiplicando por lactosos.
   - Ajustar el desglose para indicar para qué dieta se calcula cada registro, o consolidar todo en la lista general manteniendo un buen nivel de log de las operaciones.
3. Verificar su correcto funcionamiento comprobando el retorno de output para la app en Streamlit.

## Filtros y Condiciones
- El número de personas sin dieta no puede ser menor a 0. `max(0, personas_totales_comida - celiacos - lactosos)`
- Si un plato no tiene ingredientes para celíacos o lactosos (lista vacía), no sumar nada para ese grupo.
- Si no hay celíacos o lactosos en un día específico, evitar iteraciones o multiplicaciones innecesarias, multiplicando sus cantidades base por 0.

## Lógica de negocio
- Los multiplicadores de personas se aplican explícitamente a las listas correspondientes para cada dieta definida.
- Las personas ajustadas en cada comida (el `ajuste`) afectarán a las personas *sin dieta* para simplificar el modelo, salvo que alteren el total por debajo de la suma de intolerantes.
- En `desglose`, debe figurar la dieta a la que aplica esa cantidad (ej. añadiendo el campo "Dieta").

## Criterios de éxito
- Ejecutar el programa sin errores de cálculo.
- Obtener ingredientes diferenciados en la lista de compra como "Macarrones" y "Macarrones sin gluten" generados en base al nuevo `Maestro_Ingredientes.json`.
- El resultado del JSON final será más completo y robusto.
