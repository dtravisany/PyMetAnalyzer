import json
import toml
import csv
import os
from pathlib import Path
from subprocess import run, PIPE
from datetime import datetime, timedelta
import pandas as pd

class NCBI_Data:
    def __init__(self, config_file=".secrets/config.toml", genome_folder="genomes"):
        """
        Inicializa la instancia de NCBI_Data.
        :param config_file: Ruta al archivo de configuración TOML.
        :param genome_folder: Ruta a la carpeta donde se almacenarán los genomas descargados.
        """
        self.config = toml.load(Path(__file__).parent / config_file)
        self.api_key = self.config['ncbi']['api_key']
        self.genome_folder = Path(genome_folder)

    def ejecutar_comando_datasets(self, comando):
        """
        Ejecuta un comando de la herramienta datasets y devuelve la salida.
        :param comando: Comando de datasets a ejecutar.
        :return: Salida del comando como string.
        """
        cmd = f"{comando} --api-key {self.api_key}"
        result = run(cmd, shell=True, stdout=PIPE, text=True)
        return result.stdout

    def obtener_resumen_genomas_bacterias(self, archivo_tsv='bacterial.tsv', forzar_descarga=False):
        """
        Obtiene un resumen de los genomas de bacterias en formato TSV.
        :param archivo_tsv: Nombre del archivo TSV donde se almacenan los datos.
        :param forzar_descarga: Si es True, fuerza la descarga de datos nuevos.
        :return: DataFrame de genomas en formato TSV.
        """
        if not os.path.exists(archivo_tsv) or self.archivo_desactualizado(archivo_tsv) or forzar_descarga:
            comando = f"datasets summary genome taxon Bacteria --mag exclude --reference --api-key {self.api_key}"
            datos_json = self.ejecutar_comando_datasets(comando)
            with open('bacterial.json', 'w') as file:
                file.write(datos_json)

            # Transformar JSON a TSV utilizando dataformat
            comando_tsv = f"dataformat tsv genome --inputfile bacterial.json > {archivo_tsv}"
            self.ejecutar_comando(comando_tsv)

        return pd.read_csv(archivo_tsv, sep='\t')

    def ejecutar_comando(self, comando):
        """
        Ejecuta un comando en la terminal y devuelve la salida.
        :param comando: Comando a ejecutar.
        :return: Salida del comando como string.
        """
        result = run(comando, shell=True, stdout=PIPE, text=True)
        return result.stdout

    def archivo_desactualizado(self, archivo, dias=30):
        """
        Verifica si un archivo está desactualizado.
        :param archivo: Ruta del archivo.
        :param dias: Cantidad de días para considerar un archivo desactualizado.
        :return: True si el archivo está desactualizado, de lo contrario False.
        """
        ultima_modificacion = datetime.fromtimestamp(os.path.getmtime(archivo))
        return datetime.now() - ultima_modificacion > timedelta(days=dias)

    def filtrar_genomas(self, genomas, nivel_ensamblaje='Full', cobertura_minima=0):
        """
        Filtra los genomas según el nivel de ensamblaje y la cobertura mínima.
        :param genomas: Lista de genomas a filtrar.
        :param nivel_ensamblaje: Nivel de ensamblaje requerido.
        :param cobertura_minima: Cobertura mínima requerida para incluir el genoma.
        :return: Lista de genomas filtrados.
        """
        genomas_filtrados = []
        for g in genomas:
            cobertura_str = g['assembly_stats'].get('genome_coverage', '0').rstrip('x')
            cobertura = float(cobertura_str) if cobertura_str else 0
            if g['assembly_info']['assembly_level'] == nivel_ensamblaje and cobertura >= cobertura_minima:
                genomas_filtrados.append(g)
        return genomas_filtrados

    def seleccionar_un_genoma_por_especie(self, genomas):
        """
        Selecciona un genoma por especie basándose en la completitud y la fecha de lanzamiento.
        :param genomas: Lista de genomas a procesar.
        :return: Lista de genomas seleccionados.
        """
        genomas_por_especie = {}
        for genoma in genomas:
            especie = genoma['organism']['organism_name']
            fecha_lanzamiento = datetime.strptime(genoma['assembly_info']['release_date'], '%Y-%m-%d')
            completitud = genoma['checkm_info'].get('completeness', 0)
            calidad_ensamblaje = genoma['assembly_info']['assembly_level']

            if especie not in genomas_por_especie or \
               (completitud > genomas_por_especie[especie]['completitud'] or
                (completitud == genomas_por_especie[especie]['completitud'] and 
                 fecha_lanzamiento > genomas_por_especie[especie]['fecha_lanzamiento']) or
                (completitud == genomas_por_especie[especie]['completitud'] and 
                 fecha_lanzamiento == genomas_por_especie[especie]['fecha_lanzamiento'] and 
                 calidad_ensamblaje > genomas_por_especie[especie]['calidad_ensamblaje'])):
                genomas_por_especie[especie] = {'genoma': genoma, 'completitud': completitud, 
                                                'fecha_lanzamiento': fecha_lanzamiento, 
                                                'calidad_ensamblaje': calidad_ensamblaje}

        return [info['genoma'] for info in genomas_por_especie.values()]

    def descargar_genomas(self, genomas_seleccionados, directorio_destino="descargas_genomas"):
        """
        Descarga genomas seleccionados en el directorio especificado.
        :param genomas_seleccionados: Lista de genomas a descargar.
        :param directorio_destino: Directorio de destino para las descargas.
        """
        self.genome_folder.mkdir(parents=True, exist_ok=True)
        for genoma in genomas_seleccionados:
            # Asegurarse de que la clave 'accession' está presente en el diccionario.
            if  'accession' in genoma:
                accession = genoma['accession']
                comando = f"datasets download genome accession {accession} --filename {self.genome_folder}/{accession}.zip --api-key {self.api_key}"
                self.ejecutar_comando_datasets(comando)
            else:
                print(f"Genoma sin 'accession': {genoma}")


   # def extraer_accession_organismo(self, archivo_salida='keydata_bacterial.csv'):
   #     """
   #     Extrae los accessions y organismos de los genomas presentes en bacterial.json y los guarda en un CSV más simple.
   #     :param archivo_salida: Nombre del archivo CSV de salida.
   #     """
   #     df = pd.

# Ejemplo de uso del módulo
ncbi_data_manager = NCBI_Data()
#genomas = ncbi_data_manager.obtener_resumen_genomas_bacterias(forzar_descarga=False)
#genomas_filtrados = ncbi_data_manager.filtrar_genomas(genomas)
#genomas_por_especie = ncbi_data_manager.seleccionar_un_genoma_por_especie(genomas_filtrados)
#ncbi_data_manager.descargar_genomas(genomas_por_especie)
#ncbi_data_manager.extraer_accession_organismo()

genomas = ncbi_data_manager.obtener_resumen_genomas_bacterias(forzar_descarga=False)
