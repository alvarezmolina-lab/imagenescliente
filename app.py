import streamlit as st
import pandas as pd
import requests
import os
import shutil
import zipfile

# --- NUEVA CONFIGURACIÓN DE PÁGINA Y LOGO ---
URL_LOGO = "https://mauiandsons.cl/media/logo/stores/1/logo.png"

# 1. Configurar la pestaña del navegador (Opcional pero recomendado)
st.set_page_config(
    page_title="Organizador Imágenes - Maui", # Título de la pestaña
    page_icon=URL_LOGO,                    # Ícono de la pestaña
    layout="centered"                       # O "wide" para pantalla completa
)

# 2. Diseño de la esquina superior izquierda (Logo + Título)
# Creamos dos columnas: la primera para el logo (estrecha), la segunda para el título (ancha).
col_logo, col_titulo = st.columns([1, 4]) # Proporción 1 a 4

with col_logo:
    # Mostramos el logo. 'width=150' ajusta el tamaño.
    st.image(URL_LOGO, width=150)

with col_titulo:
    # Mostramos el título justo al lado del logo
    st.title("Descargador y Organizador de Imágenes")

st.title("Descarga las imagenes de tus pedidos")
st.write("Sube tu archivo Excel que descargaste desde NuOrder. Cuando este cargado el sistema agrupará las imágenes en carpetas y te entregará un archivo ZIP.")

# 1. Interfaz para subir el archivo
archivo_subido = st.file_uploader("Sube tu plantilla Excel (.xlsx)", type=["xlsx"])

if archivo_subido is not None:
    # 2. Leer el Excel con Pandas
    df = pd.read_excel(archivo_subido)
    st.write("Vista previa de los datos:", df.head(3))
    
    if st.button("Procesar y Descargar Imágenes"):
        carpeta_base = "temp_descargas"
        os.makedirs(carpeta_base, exist_ok=True)
        
        barra_progreso = st.progress(0)
        total_filas = len(df)
        
        # 3. Iterar sobre las filas del DataFrame
        for indice, fila in df.iterrows():
            # Asumiendo que la columna BF se llama 'Pack Name 1' en tu Excel
            nombre_carpeta = str(fila.get('Pack Name 1', f'Carpeta_{indice}'))
            ruta_carpeta = os.path.join(carpeta_base, nombre_carpeta)
            os.makedirs(ruta_carpeta, exist_ok=True)
            
            # Buscar columnas que contengan 'Media URL' (BG, BH, etc.)
            columnas_urls = [col for col in df.columns if 'Media URL' in str(col)]
            
            contador_img = 1
            for col in columnas_urls:
                url = fila[col]
                # Verificar que la celda no esté vacía (Pandas las lee como NaN)
                if pd.notna(url) and str(url).strip() != "":
                    try:
                        respuesta = requests.get(url, stream=True)
                        if respuesta.status_code == 200:
                            nombre_archivo = f"{nombre_carpeta}_{contador_img}.jpg"
                            ruta_archivo = os.path.join(ruta_carpeta, nombre_archivo)
                            
                            with open(ruta_archivo, 'wb') as f:
                                f.write(respuesta.content)
                            contador_img += 1
                    except Exception as e:
                        st.error(f"Error descargando {url}: {e}")
            
            # Actualizar barra de progreso
            barra_progreso.progress((indice + 1) / total_filas)
            
        st.success("¡Imágenes procesadas correctamente!")
        
        # 4. Comprimir la carpeta en un archivo ZIP
        shutil.make_archive("imagenes_empaquetadas", 'zip', carpeta_base)
        
        # 5. Botón de descarga del ZIP
        with open("imagenes_empaquetadas.zip", "rb") as fp:
            st.download_button(
                label="Descargar archivo ZIP con carpetas",
                data=fp,
                file_name="imagenes_organizadas.zip",
                mime="application/zip"
            )
            
        # Limpieza (opcional, para no llenar el servidor)
        shutil.rmtree(carpeta_base)
