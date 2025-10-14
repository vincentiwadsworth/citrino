#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para probar las mejoras en los patrones de regex para el Proveedor 02.

Este script prueba los patrones mejorados en descripciones reales del Proveedor 02
para validar que las mejoras son efectivas.
"""

import sys
import json
from pathlib import Path

# Agregar path para importar extractor
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from regex_extractor import RegexExtractor

class TesteadorRegexMejorado:
    """Prueba los patrones de regex mejorados."""

    def __init__(self):
        self.extractor = RegexExtractor()
        self.casos_prueba = self._generar_casos_prueba()

    def _generar_casos_prueba(self):
        """Genera casos de prueba basados en formatos reales del Proveedor 02."""
        return {
            'precio': [
                {
                    'descripcion': 'Departamento en venta $us 180.000 en Equipetrol',
                    'esperado': 180000,
                    'moneda': 'USD'
                },
                {
                    'descripcion': 'Casa familiar en 450.000 us con jardín',
                    'esperado': 450000,
                    'moneda': 'USD'
                },
                {
                    'descripcion': 'Terreno comercial: Bs 850.000 negociable',
                    'esperado': 850000,
                    'moneda': 'BOB'
                },
                {
                    'descripcion': 'us$ 220.000 departamento moderno',
                    'esperado': 220000,
                    'moneda': 'USD'
                },
                {
                    'descripcion': 'venta en 350000 excelente oportunidad',
                    'esperado': 350000,
                    'moneda': 'USD'
                }
            ],
            'habitaciones': [
                {
                    'descripcion': '3 habitaciones amplias con buena iluminación',
                    'esperado': 3
                },
                {
                    'descripcion': 'departamento con 2 dormitorios principales',
                    'esperado': 2
                },
                {
                    'descripcion': 'cuenta con 4 ambientes distribuidos',
                    'esperado': 4
                },
                {
                    'descripcion': 'ideal para 1 persona o pareja',
                    'esperado': 1
                },
                {
                    'descripcion': '3 dorms con closet incorporado',
                    'esperado': 3
                }
            ],
            'banos': [
                {
                    'descripcion': 'con baño completo y medio baño social',
                    'esperado': 1.0
                },
                {
                    'descripcion': '2 baños, uno principal y uno de servicio',
                    'esperado': 2.0
                },
                {
                    'descripcion': 'baño privado con shower',
                    'esperado': 1.0
                },
                {
                    'descripcion': '1.5 baños distribuidos inteligentemente',
                    'esperado': 1.5
                },
                {
                    'descripcion': 'servicio sanitario independiente',
                    'esperado': 1.0
                }
            ],
            'superficie': [
                {
                    'descripcion': '120 m2 de construcción',
                    'esperado': 120
                },
                {
                    'descripcion': 'terreno de 200m2 con posibilidades',
                    'esperado': 200
                },
                {
                    'descripcion': 'sup. 8x6 = 48 mt2',
                    'esperado': 48
                },
                {
                    'descripcion': 'area construida 85m2',
                    'esperado': 85
                },
                {
                    'descripcion': 'lote 300m2 en zona residencial',
                    'esperado': 300
                }
            ],
            'zona': [
                {
                    'descripcion': 'ubicado en Equipetrol cerca de centros comerciales',
                    'esperado': 'Equipetrol'
                },
                {
                    'descripcion': 'departamento en Santa Mónica con vista al parque',
                    'esperado': 'Santa Mónica'
                },
                {
                    'descripcion': 'propiedad en Urbari a cuadras del mall',
                    'esperado': 'Urbari'
                },
                {
                    'descripcion': 'en Los Olivos zona tranquila y segura',
                    'esperado': 'Los Olivos'
                },
                {
                    'descripcion': 'cerca de 3er anillo y radial 10',
                    'esperado': None  # Referencia, no zona específica
                }
            ]
        }

    def probar_extraccion_precio(self):
        """Prueba la extracción de precios."""
        print(f"\n{'='*60}")
        print("PRUEBA DE EXTRACCIÓN DE PRECIOS")
        print(f"{'='*60}")

        resultados = []
        for i, caso in enumerate(self.casos_prueba['precio']):
            desc = caso['descripcion']
            esperado = caso['esperado']

            extraido = self.extractor.extract_precio(desc.lower())
            moneda = self.extractor.extract_moneda(desc.lower())

            correcto = extraido == esperado and moneda == caso['moneda']
            resultados.append(correcto)

            print(f"\nTest {i+1}: {correcto and '[OK]' or '[ERROR]'}")
            print(f"Descripción: {desc}")
            print(f"Esperado: {esperado} {caso['moneda']}")
            print(f"Extraído: {extraido} {moneda}")

        exito = sum(resultados)
        print(f"\nResultados precio: {exito}/{len(resultados)} tests pasaron ({exito/len(resultados)*100:.1f}%)")
        return exito == len(resultados)

    def probar_extraccion_habitaciones(self):
        """Prueba la extracción de habitaciones."""
        print(f"\n{'='*60}")
        print("PRUEBA DE EXTRACCIÓN DE HABITACIONES")
        print(f"{'='*60}")

        resultados = []
        for i, caso in enumerate(self.casos_prueba['habitaciones']):
            desc = caso['descripcion']
            esperado = caso['esperado']

            extraido = self.extractor.extract_habitaciones(desc.lower())
            correcto = extraido == esperado
            resultados.append(correcto)

            print(f"\nTest {i+1}: {correcto and '[OK]' or '[ERROR]'}")
            print(f"Descripción: {desc}")
            print(f"Esperado: {esperado} habitaciones")
            print(f"Extraído: {extraido} habitaciones")

        exitos = sum(resultados)
        print(f"\nResultados habitaciones: {exitos}/{len(resultados)} tests pasaron ({exitos/len(resultados)*100:.1f}%)")
        return exito == len(resultados)

    def probar_extraccion_banos(self):
        """Prueba la extracción de baños."""
        print(f"\n{'='*60}")
        print("PRUEBA DE EXTRACCIÓN DE BAÑOS")
        print(f"{'='*60}")

        resultados = []
        for i, caso in enumerate(self.casos_prueba['banos']):
            desc = caso['descripcion']
            esperado = caso['esperado']

            extraido = self.extractor.extract_banos(desc.lower())
            correcto = extraido == esperado
            resultados.append(correcto)

            print(f"\nTest {i+1}: {correcto and '[OK]' or '[ERROR]'}")
            print(f"Descripción: {desc}")
            print(f"Esperado: {esperado} baños")
            print(f"Extraído: {extraido} baños")

        exitos = sum(resultados)
        print(f"\nResultados baños: {exitos}/{len(resultados)} tests pasaron ({exitos/len(resultados)*100:.1f}%)")
        return exito == len(resultados)

    def probar_extraccion_superficie(self):
        """Prueba la extracción de superficie."""
        print(f"\n{'='*60}")
        print("PRUEBA DE EXTRACCIÓN DE SUPERFICIE")
        print(f"{'='*60}")

        resultados = []
        for i, caso in enumerate(self.casos_prueba['superficie']):
            desc = caso['descripcion']
            esperado = caso['esperado']

            extraido = self.extractor.extract_superficie(desc.lower())
            correcto = extraido == esperado
            resultados.append(correcto)

            print(f"\nTest {i+1}: {correcto and '[OK]' or '[ERROR]'}")
            print(f"Descripción: {desc}")
            print(f"Esperado: {esperado} m²")
            print(f"Extraído: {extraido} m²")

        exitos = sum(resultados)
        print(f"\nResultados superficie: {exitos}/{len(resultados)} tests pasaron ({exitos/len(resultados)*100:.1f}%)")
        return exito == len(resultados)

    def probar_extraccion_zona(self):
        """Prueba la extracción de zonas."""
        print(f"\n{'='*60}")
        print("PRUEBA DE EXTRACCIÓN DE ZONAS")
        print(f"{'='*60}")

        resultados = []
        for i, caso in enumerate(self.casos_prueba['zona']):
            desc = caso['descripcion']
            esperado = caso['esperado']

            extraido = self.extractor.extract_zona(desc.lower())
            correcto = extraido == esperado
            resultados.append(correcto)

            print(f"\nTest {i+1}: {correcto and '[OK]' or '[ERROR]'}")
            print(f"Descripción: {desc}")
            print(f"Esperado: {esperado}")
            print(f"Extraído: {extraido}")

        exitos = sum(resultados)
        print(f"\nResultados zona: {exitos}/{len(resultados)} tests pasaron ({exitos/len(resultados)*100:.1f}%)")
        return exito == len(resultados)

    def probar_extraccion_completa(self):
        """Prueba extracción completa de descripciones reales."""
        print(f"\n{'='*60}")
        print("PRUEBA DE EXTRACCIÓN COMPLETA")
        print(f"{'='*60}")

        descripciones_reales = [
            {
                'texto': 'Departamento en venta $us 180.000 en Equipetrol con 3 habitaciones, 2 baños, 120 m2',
                'esperado': {
                    'precio': 180000,
                    'zona': 'Equipetrol',
                    'habitaciones': 3,
                    'banos': 2.0,
                    'superficie': 120
                }
            },
            {
                'texto': 'Casa familiar en Santa Mónica, 4 ambientes, 2.5 baños, 250 mt2, precio 350.000 us',
                'esperado': {
                    'precio': 350000,
                    'zona': 'Santa Mónica',
                    'habitaciones': 4,
                    'banos': 2.5,
                    'superficie': 250
                }
            }
        ]

        for i, caso in enumerate(descripciones_reales):
            print(f"\nDescripción {i+1}:")
            print(f"Texto: {caso['texto']}")

            resultado = self.extractor.extract_all(caso['texto'])
            esperado = caso['esperado']

            print(f"\nComparación:")
            campos = ['precio', 'zona', 'habitaciones', 'banos', 'superficie']
            for campo in campos:
                extraido = resultado.get(campo)
                valor_esperado = esperado.get(campo)
                ok = extraido == valor_esperado
                print(f"  {campo}: {valor_esperado} → {extraido} {'[OK]' if ok else '[ERROR]'}")

    def ejecutar_todas_las_pruebas(self):
        """Ejecuta todas las pruebas de regex."""
        print("INICIANDO PRUEBAS DE REGEX MEJORADAS PARA PROVEEDOR 02")

        # Ejecutar pruebas individuales
        test_precio = self.probar_extraccion_precio()
        test_habitaciones = self.probar_extraccion_habitaciones()
        test_banos = self.probar_extraccion_banos()
        test_superficie = self.probar_extraccion_superficie()
        test_zona = self.probar_extraccion_zona()

        # Prueba completa
        self.probar_extraccion_completa()

        # Resumen final
        print(f"\n{'='*60}")
        print("RESUMEN DE PRUEBAS")
        print(f"{'='*60}")

        tests = [
            ('Precio', test_precio),
            ('Habitaciones', test_habitaciones),
            ('Baños', test_banos),
            ('Superficie', test_superficie),
            ('Zonas', test_zona)
        ]

        exitos = sum(1 for _, resultado in tests if resultado)
        total = len(tests)

        for nombre, resultado in tests:
            print(f"• {nombre}: {'[OK]' if resultado else '[ERROR]'}")

        print(f"\nTotal: {exitos}/{total} categorías pasaron las pruebas")

        if exitos == total:
            print("\n[OK] Todas las pruebas de regex mejoradas pasaron exitosamente")
            print("Los patrones están listos para producción con el Proveedor 02")
        else:
            print(f"\n[!ADVERTENCIA] {total-exitos} categorías necesitan ajustes")

        return exitos == total

def main():
    """Función principal."""
    testeador = TesteadorRegexMejorado()
    return 0 if testeador.ejecutar_todas_las_pruebas() else 1

if __name__ == "__main__":
    exit(main())