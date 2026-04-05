"""
Descripcion: Agrega ingredientes considerando ajustes por comida y personas base.
Input: Lista de planificación diaria y maestro de ingredientes.
Output: Diccionario con el listado consolidado y desglose por día.
"""
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main(plan_data: list, maestro_data: list) -> dict:
    """Funcion principal. Retorna dict con status y metricas."""
    logger.info("Iniciando agregación de ingredientes")
    try:
        platos_map = {p["plato"]: p for p in maestro_data}
        resultado = {}
        desglose = {}
        
        for dia_plan in plan_data:
            dia = dia_plan.get("dia")
            personas_base = dia_plan.get("personas", 0)
            
            desglose[dia] = []
            
            for tipo, config in dia_plan.get("comidas", {}).items():
                plato_nombre = config.get("plato")
                ajuste = config.get("ajuste", 0)
                
                if not plato_nombre or plato_nombre not in platos_map: 
                    continue
                
                # Calcular número final de personas para esta comida puntual
                personas_comida = personas_base + ajuste
                if personas_comida <= 0: 
                    continue
                
                celiacos = dia_plan.get("celiacos", 0)
                lactosos = dia_plan.get("lactosos", 0)
                personas_sin_dieta = max(0, personas_comida - celiacos - lactosos)
                
                plato = platos_map[plato_nombre]
                
                # Definir los grupos a procesar
                grupos_dietas = [
                    ("Base", plato.get("ingredientes_base", []), personas_sin_dieta),
                    ("Celíacos", plato.get("ingredientes_celiacos", []), celiacos),
                    ("Lactosos", plato.get("ingredientes_lactosa", []), lactosos)
                ]
                
                for dieta, ingredientes, pax_dieta in grupos_dietas:
                    if pax_dieta <= 0:
                        continue
                        
                    for ing in ingredientes:
                        nombre = ing.get("nombre")
                        cant = ing.get("cantidad")
                        uni = ing.get("unidad")
                        
                        if not nombre: continue
                        
                        # Breakdown
                        cant_total_comida = (cant * pax_dieta) if cant is not None else None
                        desglose[dia].append({
                            "Comida": tipo,
                            "Plato": plato_nombre,
                            "Dieta": dieta,
                            "Pax Final": pax_dieta,
                            "Ingrediente": nombre,
                            "Cantidad": cant_total_comida,
                            "Unidad": uni if uni else "N/A"
                        })
                        
                        # Totals
                        key = f"{nombre}_{uni}" if uni else nombre
                        if key not in resultado:
                            resultado[key] = {
                                "Ingrediente": nombre,
                                "Cantidad Total": 0.0,
                                "Unidad": uni if uni else "N/A",
                                "Notas": ""
                            }
                        
                        if cant is None:
                            resultado[key]["Notas"] = "Requiere cálculo manual (dato nulo)"
                        else:
                            resultado[key]["Cantidad Total"] += cant_total_comida
                        
        logger.info("Agregación completada exitosamente con ajustes de ocupación.")
        return {"status": "success", "data": list(resultado.values()), "desglose": desglose}
    except Exception as e:
        logger.error(f"Error en agregación: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    pass
