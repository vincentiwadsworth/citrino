#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demostración del sistema de retroalimentación en tiempo real.

Este script muestra cómo funciona el sistema de feedback procesando
un lote pequeño de 10 propiedades.
"""

import time
import os
from procesamiento_con_feedback import ProcesadorConFeedback

def demo_feedback():
    """
    Demostración del sistema de feedback con un lote pequeño.
    """
    print("DEMOSTRACIÓN DEL SISTEMA DE FEEDBACK")
    print("=" * 50)
    print("Procesando 10 propiedades con retroalimentación detallada")
    print()

    # Crear procesador con feedback
    procesador = ProcesadorConFeedback(
        batch_size=10,  # Lote pequeño para demo
        enable_llm=True
    )

    try:
        # Procesar lote pequeño
        propiedades = procesador.procesar_archivos_por_bloque(
            max_archivos=1,      # Solo primer archivo
            max_propiedades=10   # Solo 10 propiedades
        )

        print(f"\nDEMO COMPLETADA: {len(propiedades)} propiedades procesadas")

        # Mostrar archivos generados
        print("\nARCHIVOS GENERADOS:")
        feedback_file = "data/feedback_procesamiento.json"
        log_file = "data/procesamiento_detailed.log"

        if os.path.exists(feedback_file):
            print(f"✓ Feedback JSON: {feedback_file}")
        if os.path.exists(log_file):
            print(f"✓ Log detallado: {log_file}")

        print("\nPara ver el feedback detallado, abre el archivo JSON generado.")

    except Exception as e:
        print(f"Error en demo: {e}")

if __name__ == "__main__":
    demo_feedback()