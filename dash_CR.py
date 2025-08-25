import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Registro de Compras",
    page_icon="🛒",
    layout="wide"
)

# Función para verificar stock bajo
def verificar_stock_bajo(df_maestro, umbral=5):
    """
    Verifica productos con stock bajo y retorna alertas
    """
    stock_bajo = df_maestro[df_maestro['Cantidad sobrante'] <= umbral]
    return stock_bajo

# Función para ordenar tallas
def ordenar_tallas(tallas):
    """
    Ordena las tallas según el orden especificado: XS, S, M, L, XL, 2XL, 3XL, 4XL, 5XL
    """
    orden_tallas = ['XS', 'S', 'M', 'L', 'XL', '2XL', '3XL', '4XL', '5XL']
    tallas_ordenadas = []
    
    for talla_orden in orden_tallas:
        if talla_orden in tallas:
            tallas_ordenadas.append(talla_orden)
    
    # Agregar tallas que no están en el orden predefinido al final
    for talla in tallas:
        if talla not in tallas_ordenadas:
            tallas_ordenadas.append(talla)
    
    return tallas_ordenadas

# Función para cargar datos de ventas
def cargar_datos_ventas():
    """
    Carga todos los archivos de ventas para generar estadísticas
    """
    archivos_ventas = []
    datos_ventas = []
    
    # Buscar todos los archivos de ventas (formato fecha.xlsx)
    for archivo in os.listdir("."):
        if archivo.endswith(".xlsx") and archivo != "CR_Control.xlsx":
            try:
                # Verificar si es un archivo de ventas válido
                df_temp = pd.read_excel(archivo)
                if 'Fecha' in df_temp.columns and 'Ganancia' in df_temp.columns:
                    df_temp['Archivo'] = archivo
                    datos_ventas.append(df_temp)
            except:
                continue
    
    if datos_ventas:
        return pd.concat(datos_ventas, ignore_index=True)
    else:
        return pd.DataFrame()

# Función para generar dashboard de estadísticas
def mostrar_dashboard_estadisticas():
    """
    Muestra dashboard con estadísticas de ventas
    """
    st.markdown("# 📊 Dashboard de Estadísticas de Ventas")
    st.markdown("---")
    
    # Cargar datos de ventas
    df_ventas = cargar_datos_ventas()
    df_maestro = cargar_archivo_maestro()
    
    if df_ventas.empty:
        st.info("📝 No hay datos de ventas disponibles para mostrar estadísticas.")
        return
    
    # Convertir fecha a datetime
    df_ventas['Fecha'] = pd.to_datetime(df_ventas['Fecha'])
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        ganancia_total = df_ventas['Ganancia'].sum()
        st.metric("💰 Ganancia Total", f"${ganancia_total:,.2f}")
    
    with col2:
        productos_vendidos = df_ventas['Cantidad Vendida'].sum()
        st.metric("📦 Productos Vendidos", f"{productos_vendidos:,}")
    
    with col3:
        ventas_unicas = len(df_ventas['Archivo'].unique())
        st.metric("🛒 Ventas Realizadas", f"{ventas_unicas:,}")
    
    with col4:
        if not df_ventas.empty:
            promedio_venta = df_ventas.groupby('Archivo')['Ganancia'].sum().mean()
            st.metric("📈 Promedio por Venta", f"${promedio_venta:,.2f}")
    
    st.markdown("---")
    
    # Gráficos en dos columnas
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🏆 Productos Más Vendidos")
        
        # Agrupar por producto y talla
        ventas_por_producto_talla = df_ventas.groupby(['Producto', 'Talla']).agg({
            'Cantidad Vendida': 'sum',
            'Ganancia': 'sum'
        }).reset_index()
        
        # Crear columna combinada para mejor visualización
        ventas_por_producto_talla['Producto_Talla'] = ventas_por_producto_talla['Producto'] + ' (Talla ' + ventas_por_producto_talla['Talla'].astype(str) + ')'
        
        # Ordenar por cantidad vendida
        ventas_por_producto_talla = ventas_por_producto_talla.sort_values('Cantidad Vendida', ascending=True)
        
        # Tomar top 10
        top_productos = ventas_por_producto_talla.tail(10)
        
        if not top_productos.empty:
            fig_productos = px.bar(
                top_productos,
                x='Cantidad Vendida',
                y='Producto_Talla',
                orientation='h',
                title="Top 10 Productos/Tallas Más Vendidos",
                labels={'Cantidad Vendida': 'Unidades Vendidas', 'Producto_Talla': 'Producto (Talla)'},
                color='Cantidad Vendida',
                color_continuous_scale='Blues'
            )
            fig_productos.update_layout(height=500)
            st.plotly_chart(fig_productos, use_container_width=True)
        else:
            st.info("No hay datos suficientes para mostrar productos más vendidos")
    
    with col2:
        st.markdown("### 💵 Ganancias por Producto")
        
        # Ganancias por producto (sin talla)
        ganancias_por_producto = df_ventas.groupby('Producto')['Ganancia'].sum().reset_index()
        ganancias_por_producto = ganancias_por_producto.sort_values('Ganancia', ascending=False)
        
        if not ganancias_por_producto.empty:
            fig_ganancias = px.pie(
                ganancias_por_producto,
                values='Ganancia',
                names='Producto',
                title="Distribución de Ganancias por Producto"
            )
            fig_ganancias.update_traces(textposition='inside', textinfo='percent+label')
            fig_ganancias.update_layout(height=500)
            st.plotly_chart(fig_ganancias, use_container_width=True)
        else:
            st.info("No hay datos suficientes para mostrar ganancias por producto")
    
    # Tabla detallada de ganancias
    st.markdown("### 📋 Detalle de Ganancias por Producto")
    
    # Crear tabla resumen
    resumen_productos = df_ventas.groupby('Producto').agg({
        'Cantidad Vendida': 'sum',
        'Ganancia': 'sum',
        'Costo': 'mean'  # Promedio del costo
    }).reset_index()
    
    resumen_productos['Ganancia por Unidad'] = resumen_productos['Ganancia'] / resumen_productos['Cantidad Vendida']
    resumen_productos = resumen_productos.sort_values('Ganancia', ascending=False)
    
    # Formatear para mostrar
    resumen_display = resumen_productos.copy()
    resumen_display['Ganancia'] = resumen_display['Ganancia'].apply(lambda x: f"${x:,.2f}")
    resumen_display['Costo'] = resumen_display['Costo'].apply(lambda x: f"${x:,.2f}")
    resumen_display['Ganancia por Unidad'] = resumen_display['Ganancia por Unidad'].apply(lambda x: f"${x:,.2f}")
    
    st.dataframe(
        resumen_display,
        column_config={
            "Producto": "Producto",
            "Cantidad Vendida": st.column_config.NumberColumn("Unidades Vendidas", format="%d"),
            "Ganancia": "Ganancia Total",
            "Costo": "Costo Promedio",
            "Ganancia por Unidad": "Ganancia por Unidad"
        },
        use_container_width=True
    )
    
    # Gráfico de ventas por fecha (separado más)
    st.markdown("---")
    st.markdown("### 📅 Ventas por Fecha")
    
    ventas_por_fecha = df_ventas.groupby('Fecha').agg({
        'Ganancia': 'sum',
        'Cantidad Vendida': 'sum'
    }).reset_index()
    
    if not ventas_por_fecha.empty:
        # Gráfico de ganancias
        st.markdown("#### 💰 Ganancias por Fecha")
        fig_ganancias = px.line(
            ventas_por_fecha,
            x='Fecha',
            y='Ganancia',
            title='Evolución de Ganancias por Fecha',
            markers=True,
            line_shape='linear'
        )
        fig_ganancias.update_traces(line=dict(color='green', width=3))
        fig_ganancias.update_layout(height=400)
        st.plotly_chart(fig_ganancias, use_container_width=True)
        
        st.markdown("---")
        
        # Gráfico de unidades vendidas
        st.markdown("#### 📦 Unidades Vendidas por Fecha")
        fig_unidades = px.line(
            ventas_por_fecha,
            x='Fecha',
            y='Cantidad Vendida',
            title='Evolución de Unidades Vendidas por Fecha',
            markers=True,
            line_shape='linear'
        )
        fig_unidades.update_traces(line=dict(color='blue', width=3))
        fig_unidades.update_layout(height=400)
        st.plotly_chart(fig_unidades, use_container_width=True)

# Función para cargar el archivo maestro
def cargar_archivo_maestro():
    """
    Carga el archivo maestro de control de inventario
    """
    try:
        df = pd.read_excel("CR_Control.xlsx")
        return df
    except FileNotFoundError:
        st.error("No se encontró el archivo CR_Control.xlsx")
        return None
    except Exception as e:
        st.error(f"Error al cargar el archivo: {str(e)}")
        return None

# Función para actualizar el archivo maestro
def actualizar_archivo_maestro(compras_realizadas):
    """
    Actualiza el archivo maestro con las compras realizadas
    """
    try:
        df_maestro = pd.read_excel("CR_Control.xlsx")
        
        for compra in compras_realizadas:
            # Buscar el producto en el archivo maestro
            mask = (df_maestro['Producto'] == compra['Producto']) & \
                   (df_maestro['Talla'] == compra['Talla'])
            
            if mask.any():
                # Actualizar cantidad vendida
                df_maestro.loc[mask, 'Cantidad vendida'] += compra['Cantidad']
                
                # Actualizar ganancia (Cantidad vendida * Costo)
                df_maestro.loc[mask, 'Ganancia'] = \
                    df_maestro.loc[mask, 'Cantidad vendida'] * df_maestro.loc[mask, 'Costo']
                
                # Actualizar cantidad sobrante (Cantidad inicial - Cantidad vendida)
                df_maestro.loc[mask, 'Cantidad sobrante'] = \
                    df_maestro.loc[mask, 'Cantidad inicial'] - df_maestro.loc[mask, 'Cantidad vendida']
        
        # Guardar el archivo actualizado
        df_maestro.to_excel("CR_Control.xlsx", index=False)
        return True
        
    except Exception as e:
        st.error(f"Error al actualizar el archivo maestro: {str(e)}")
        return False

# Función para generar nombre único de archivo
def generar_nombre_archivo():
    """
    Genera un nombre único para el archivo de compra basado en la fecha
    """
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    nombre_base = f"{fecha_hoy}.xlsx"
    
    if not os.path.exists(nombre_base):
        return nombre_base
    
    contador = 1
    while True:
        nombre_archivo = f"{fecha_hoy}_{contador}.xlsx"
        if not os.path.exists(nombre_archivo):
            return nombre_archivo
        contador += 1

# Función para guardar compra en Excel
def guardar_compra_excel(compras_realizadas):
    """
    Guarda la compra realizada en un archivo Excel
    """
    try:
        # Crear DataFrame con las compras
        df_compra = pd.DataFrame(compras_realizadas)
        df_compra['Fecha'] = datetime.now().strftime("%Y-%m-%d")
        
        # Reordenar columnas según especificación
        columnas_orden = ['Producto', 'SKU', 'Talla', 'Cantidad Vendida', 'Costo', 'Ganancia', 'Fecha']
        df_compra = df_compra[columnas_orden]
        
        # Generar nombre único y guardar
        nombre_archivo = generar_nombre_archivo()
        df_compra.to_excel(nombre_archivo, index=False)
        
        return nombre_archivo
        
    except Exception as e:
        st.error(f"Error al guardar la compra: {str(e)}")
        return None

# Inicializar estados de sesión
if 'estado' not in st.session_state:
    st.session_state.estado = 'inicio'
if 'carrito' not in st.session_state:
    st.session_state.carrito = []
if 'producto_seleccionado' not in st.session_state:
    st.session_state.producto_seleccionado = None
if 'talla_seleccionada' not in st.session_state:
    st.session_state.talla_seleccionada = None
if 'mostrar_dashboard' not in st.session_state:
    st.session_state.mostrar_dashboard = False

# Función principal de la aplicación
def main():
    # Cargar datos maestros
    df_maestro = cargar_archivo_maestro()
    if df_maestro is not None:
        # Agregar botones de navegación en sidebar
        st.sidebar.markdown("### 🧭 Navegación")
        
        if st.sidebar.button("🛒 Sistema de Ventas", use_container_width=True):
            st.session_state.mostrar_dashboard = False
            st.session_state.estado = 'inicio'
            st.rerun()
        
        if st.sidebar.button("📊 Dashboard Estadísticas", use_container_width=True):
            st.session_state.mostrar_dashboard = True
            st.rerun()
    
    # Mostrar dashboard o sistema de ventas
    if st.session_state.get('mostrar_dashboard', False):
        mostrar_dashboard_estadisticas()
        return
    
    # Sistema de ventas original
    st.title("🛒 Sistema de Registro de Compras")
    st.markdown("---")
    
    if df_maestro is None:
        st.stop()
    
    # Pantalla de inicio
    if st.session_state.estado == 'inicio':
        st.markdown("### Bienvenido al Sistema de Registro de Compras")
        st.markdown("Presiona el botón para comenzar una nueva compra")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🛍️ Generar Nueva Compra", use_container_width=True, type="primary"):
                st.session_state.estado = 'seleccionar_producto'
                st.rerun()
    
    # Pantalla de selección de producto
    elif st.session_state.estado == 'seleccionar_producto':
        st.markdown("### Seleccionar Producto")
        
        # Obtener productos únicos
        productos_disponibles = df_maestro['Producto'].unique()
        
        # Mostrar productos en una grilla
        cols = st.columns(3)
        for i, producto in enumerate(productos_disponibles):
            with cols[i % 3]:
                if st.button(f"📦 {producto}", key=f"prod_{i}", use_container_width=True):
                    st.session_state.producto_seleccionado = producto
                    st.session_state.estado = 'seleccionar_talla'
                    st.rerun()
        
        # Botón para volver al carrito si hay artículos
        if st.session_state.carrito:
            st.markdown("---")
            if st.button("🛒 Ver Carrito", type="secondary"):
                st.session_state.estado = 'carrito'
                st.rerun()
    
    # Pantalla de selección de talla
    elif st.session_state.estado == 'seleccionar_talla':
        st.markdown(f"### Seleccionar Talla para: {st.session_state.producto_seleccionado}")
        
        # Filtrar tallas disponibles para el producto seleccionado
        tallas_disponibles = df_maestro[
            df_maestro['Producto'] == st.session_state.producto_seleccionado
        ]['Talla'].unique()
        
        # Ordenar tallas según el orden especificado
        tallas_ordenadas = ordenar_tallas(tallas_disponibles)
        
        # Mostrar información del producto
        producto_info = df_maestro[df_maestro['Producto'] == st.session_state.producto_seleccionado]
        
        st.markdown("#### Información del Producto:")
        for _, row in producto_info.iterrows():
            # Determinar color del expander según stock
            stock = row['Cantidad sobrante']
            if stock == 0:
                titulo = f"🔴 Talla {row['Talla']} - AGOTADO"
            elif stock <= 5:
                titulo = f"🟡 Talla {row['Talla']} - STOCK BAJO: {stock} unidades"
            else:
                titulo = f"🟢 Talla {row['Talla']} - Disponible: {stock} unidades"
            
            with st.expander(titulo):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**SKU:** {row['SKU']}")
                    st.write(f"**Costo:** ${row['Costo']:,.2f}")
                with col2:
                    st.write(f"**Cantidad inicial:** {row['Cantidad inicial']}")
                    st.write(f"**Cantidad vendida:** {row['Cantidad vendida']}")
        
        # Selección de talla con orden específico
        st.markdown("#### Seleccionar Talla:")
        cols = st.columns(len(tallas_ordenadas))
        for i, talla in enumerate(tallas_ordenadas):
            with cols[i]:
                # Verificar stock para esta talla
                stock_talla = df_maestro[
                    (df_maestro['Producto'] == st.session_state.producto_seleccionado) &
                    (df_maestro['Talla'] == talla)
                ]['Cantidad sobrante'].iloc[0]
                
                button_disabled = stock_talla == 0
                button_text = f"Talla {talla}" if not button_disabled else f"Talla {talla} (Agotado)"
                
                if st.button(button_text, key=f"talla_{i}", use_container_width=True, disabled=button_disabled):
                    st.session_state.talla_seleccionada = talla
                    st.session_state.estado = 'confirmar_articulo'
                    st.rerun()
        
        # Botón para regresar
        st.markdown("---")
        if st.button("⬅️ Regresar a Productos"):
            st.session_state.estado = 'seleccionar_producto'
            st.rerun()
    
    # Pantalla de confirmación de artículo
    elif st.session_state.estado == 'confirmar_articulo':
        st.markdown("### Confirmar Artículo")
        
        # Obtener información del artículo seleccionado
        articulo_info = df_maestro[
            (df_maestro['Producto'] == st.session_state.producto_seleccionado) &
            (df_maestro['Talla'] == st.session_state.talla_seleccionada)
        ].iloc[0]
        
        # Mostrar información del artículo
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"""
            **Producto:** {articulo_info['Producto']}
            **SKU:** {articulo_info['SKU']}
            **Talla:** {articulo_info['Talla']}
            """)
        
        with col2:
            st.success(f"""
            **Costo:** ${articulo_info['Costo']:,.2f}
            **Disponible:** {articulo_info['Cantidad sobrante']} unidades
            """)
        
        # Seleccionar cantidad
        cantidad_maxima = int(articulo_info['Cantidad sobrante'])
        if cantidad_maxima > 0:
            cantidad = st.number_input(
                "Cantidad a comprar:",
                min_value=1,
                max_value=cantidad_maxima,
                value=1,
                step=1
            )
            
            st.markdown("---")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("➕ Agregar Artículo a la Compra", type="primary", use_container_width=True):
                    # Agregar al carrito
                    nuevo_articulo = {
                        'Producto': articulo_info['Producto'],
                        'SKU': articulo_info['SKU'],
                        'Talla': articulo_info['Talla'],
                        'Cantidad': cantidad,
                        'Cantidad Vendida': cantidad,  # Para el archivo de compra
                        'Costo': articulo_info['Costo'],
                        'Ganancia': cantidad * articulo_info['Costo']
                    }
                    st.session_state.carrito.append(nuevo_articulo)
                    st.session_state.estado = 'carrito'
                    st.success(f"✅ {cantidad} unidad(es) agregada(s) al carrito")
                    st.rerun()
            
            with col2:
                if st.button("⬅️ Cambiar Selección", use_container_width=True):
                    st.session_state.estado = 'seleccionar_producto'
                    st.rerun()
        else:
            st.error("❌ No hay stock disponible para este artículo")
            if st.button("⬅️ Seleccionar Otro Producto"):
                st.session_state.estado = 'seleccionar_producto'
                st.rerun()
    
    # Pantalla del carrito
    elif st.session_state.estado == 'carrito':
        st.markdown("### 🛒 Carrito de Compras")
        
        if st.session_state.carrito:
            # Mostrar artículos en el carrito
            total_compra = 0
            
            for i, articulo in enumerate(st.session_state.carrito):
                with st.expander(f"Artículo {i+1}: {articulo['Producto']} - Talla {articulo['Talla']}", expanded=True):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.write(f"**SKU:** {articulo['SKU']}")
                        st.write(f"**Cantidad:** {articulo['Cantidad']}")
                    with col2:
                        st.write(f"**Precio unitario:** ${articulo['Costo']:,.2f}")
                        st.write(f"**Subtotal:** ${articulo['Ganancia']:,.2f}")
                    with col3:
                        if st.button(f"🗑️ Eliminar", key=f"eliminar_{i}"):
                            st.session_state.carrito.pop(i)
                            st.rerun()
                
                total_compra += articulo['Ganancia']
            
            # Mostrar total
            st.markdown("---")
            st.markdown(f"### 💰 Total de la Compra: ${total_compra:,.2f}")
            
            # Botones de acción
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("➕ Agregar Más Artículos", use_container_width=True):
                    st.session_state.estado = 'seleccionar_producto'
                    st.rerun()
            
            with col2:
                if st.button("✅ Finalizar Compra", type="primary", use_container_width=True):
                    st.session_state.estado = 'finalizar_compra'
                    st.rerun()
            
            with col3:
                if st.button("🗑️ Vaciar Carrito", use_container_width=True):
                    st.session_state.carrito = []
                    st.rerun()
        
        else:
            st.info("El carrito está vacío")
            if st.button("➕ Agregar Artículos"):
                st.session_state.estado = 'seleccionar_producto'
                st.rerun()
    
    # Pantalla de finalización de compra
    elif st.session_state.estado == 'finalizar_compra':
        st.markdown("### ✅ Finalizar Compra")
        
        if st.session_state.carrito:
            # Mostrar resumen final
            st.markdown("#### Resumen de la Compra:")
            
            df_resumen = pd.DataFrame(st.session_state.carrito)
            df_resumen_display = df_resumen[['Producto', 'Talla', 'Cantidad', 'Costo', 'Ganancia']].copy()
            df_resumen_display['Costo'] = df_resumen_display['Costo'].apply(lambda x: f"${x:,.2f}")
            df_resumen_display['Ganancia'] = df_resumen_display['Ganancia'].apply(lambda x: f"${x:,.2f}")
            
            st.dataframe(df_resumen_display, use_container_width=True)
            
            total_final = sum(articulo['Ganancia'] for articulo in st.session_state.carrito)
            st.markdown(f"### 💰 **Total Final: ${total_final:,.2f}**")
            
            st.markdown("---")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("💾 Confirmar y Guardar Compra", type="primary", use_container_width=True):
                    # Guardar compra en Excel
                    nombre_archivo = guardar_compra_excel(st.session_state.carrito)
                    
                    if nombre_archivo:
                        # Actualizar archivo maestro
                        if actualizar_archivo_maestro(st.session_state.carrito):
                            st.success(f"✅ Compra guardada exitosamente en: {nombre_archivo}")
                            st.success("✅ Archivo maestro actualizado correctamente")
                            
                            # Limpiar carrito y regresar al inicio
                            st.session_state.carrito = []
                            st.session_state.estado = 'inicio'
                            st.balloons()
                            
                            # Botón para nueva compra
                            if st.button("🛍️ Nueva Compra"):
                                st.rerun()
                        else:
                            st.error("❌ Error al actualizar el archivo maestro")
                    else:
                        st.error("❌ Error al guardar la compra")
            
            with col2:
                if st.button("⬅️ Regresar al Carrito", use_container_width=True):
                    st.session_state.estado = 'carrito'
                    st.rerun()

# Ejecutar la aplicación
if __name__ == "__main__":
    main()