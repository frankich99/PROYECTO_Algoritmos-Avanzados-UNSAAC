import math
import os
from PIL import Image, ImageDraw, ImageFilter

def create_cusco_icon(size=1024):
    # Crear imagen base en alta resolución (1024x1024) con canal alfa
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 1. Fondo: Squircle redondeado imperial (Granate UNSAAC con sutil degradado)
    margin = int(size * 0.04)
    radius = int(size * 0.22)
    box = [margin, margin, size - margin, size - margin]
    
    # Dibujar sombra suave de base
    shadow_offset = int(size * 0.02)
    shadow_box = [margin, margin + shadow_offset, size - margin, size - margin + shadow_offset]
    draw.rounded_rectangle(shadow_box, radius=radius, fill=(0, 0, 0, 75))
    
    # Fondo granate institucional
    maroon_bg = (104, 28, 50, 255) # #681C32
    draw.rounded_rectangle(box, radius=radius, fill=maroon_bg)
    
    # Borde dorado imperial
    gold_border = (200, 160, 80, 255) # #C8A050
    draw.rounded_rectangle(box, radius=radius, outline=gold_border, width=int(size * 0.022))

    # Centro de la imagen
    cx, cy = size / 2.0, size / 2.0
    scale = size * 0.40 # Escala de la Chakana

    # 2. Geometría de la Chakana (Cruz Andina escalonada)
    # Definimos los vértices de una Chakana proporcional de 12 esquinas escalonadas
    # Cada cuadrante tiene 3 escalones
    step = scale / 3.0
    half_w = scale
    
    # Dibujamos una cruz escalonada simétrica
    chakana_points = [
        # Superior (Norte)
        (cx - step/2, cy - half_w),
        (cx + step/2, cy - half_w),
        (cx + step/2, cy - 2*step),
        (cx + step, cy - 2*step),
        (cx + step, cy - step),
        # Este (Derecha)
        (cx + 2*step, cy - step),
        (cx + 2*step, cy - step/2),
        (cx + half_w, cy - step/2),
        (cx + half_w, cy + step/2),
        (cx + 2*step, cy + step/2),
        (cx + 2*step, cy + step),
        (cx + step, cy + step),
        (cx + step, cy + 2*step),
        # Sur (Inferior)
        (cx + step/2, cy + 2*step),
        (cx + step/2, cy + half_w),
        (cx - step/2, cy + half_w),
        (cx - step/2, cy + 2*step),
        (cx - step, cy + 2*step),
        (cx - step, cy + step),
        # Oeste (Izquierda)
        (cx - 2*step, cy + step),
        (cx - 2*step, cy + step/2),
        (cx - half_w, cy + step/2),
        (cx - half_w, cy - step/2),
        (cx - 2*step, cy - step/2),
        (cx - 2*step, cy - step),
        (cx - step, cy - step),
        (cx - step, cy - 2*step),
        (cx - step/2, cy - 2*step)
    ]
    
    # Relleno de la Chakana en granate oscuro con textura
    dark_maroon = (75, 18, 35, 255)
    draw.polygon(chakana_points, fill=dark_maroon, outline=gold_border)
    draw.line(chakana_points + [chakana_points[0]], fill=gold_border, width=int(size * 0.012))
    
    # 3. Red de Grafo y Ruta Óptima superpuesta (Nodos y Aristas viales de Cusco)
    # Nodos principales situados en los centros de los cuadrantes y en los ejes
    network_nodes = [
        (cx, cy - 1.8 * step), # Norte
        (cx + 1.8 * step, cy), # Este
        (cx, cy + 1.8 * step), # Sur
        (cx - 1.8 * step, cy), # Oeste
        (cx + 1.2 * step, cy - 1.2 * step), # NE
        (cx + 1.2 * step, cy + 1.2 * step), # SE
        (cx - 1.2 * step, cy + 1.2 * step), # SO
        (cx - 1.2 * step, cy - 1.2 * step), # NO
        (cx, cy) # Centro (Plaza Mayor / Qosqo)
    ]
    
    # Aristas de fondo (red vial)
    bg_edges = [
        (network_nodes[3], network_nodes[7]),
        (network_nodes[7], network_nodes[0]),
        (network_nodes[0], network_nodes[4]),
        (network_nodes[4], network_nodes[1]),
        (network_nodes[1], network_nodes[5]),
        (network_nodes[5], network_nodes[2]),
        (network_nodes[2], network_nodes[6]),
        (network_nodes[6], network_nodes[3]),
        (network_nodes[3], network_nodes[8]),
        (network_nodes[7], network_nodes[8]),
        (network_nodes[5], network_nodes[8]),
        (network_nodes[6], network_nodes[8])
    ]
    
    for u, v in bg_edges:
        draw.line([u, v], fill=(138, 100, 24, 180), width=int(size * 0.010))
        
    # Ruta Mínima Resaltada (camino dorado brillante desde Oeste hasta Este pasando por Centro)
    optimal_path = [
        network_nodes[3], # Origen (Oeste)
        network_nodes[7], # NO
        network_nodes[8], # Centro (Plaza Mayor de Cusco)
        network_nodes[4], # NE
        network_nodes[1]  # Destino (Este)
    ]
    
    gold_highlight = (245, 205, 95, 255)
    for i in range(len(optimal_path) - 1):
        u = optimal_path[i]
        v = optimal_path[i+1]
        draw.line([u, v], fill=gold_highlight, width=int(size * 0.024))
        
    # Dibujar vértices (nodos)
    for idx, (nx, ny) in enumerate(network_nodes):
        is_path = (nx, ny) in optimal_path
        is_endpoint = (nx, ny) in (optimal_path[0], optimal_path[-1])
        is_center = idx == 8
        
        node_r = int(size * 0.038) if (is_endpoint or is_center) else int(size * 0.024)
        node_box = [nx - node_r, ny - node_r, nx + node_r, ny + node_r]
        
        if is_center:
            # Centro solar (Inti / Qosqo)
            draw.ellipse(node_box, fill=(255, 220, 100, 255), outline=(75, 18, 35, 255), width=int(size * 0.008))
            inner_r = node_r * 0.5
            draw.ellipse([nx - inner_r, ny - inner_r, nx + inner_r, ny + inner_r], fill=maroon_bg)
        elif is_endpoint:
            draw.ellipse(node_box, fill=(255, 240, 180, 255), outline=maroon_bg, width=int(size * 0.008))
        elif is_path:
            draw.ellipse(node_box, fill=(230, 185, 75, 255), outline=maroon_bg, width=int(size * 0.006))
        else:
            draw.ellipse(node_box, fill=(180, 140, 60, 220), outline=dark_maroon, width=int(size * 0.005))
            
    # Pequeño sol central en el corazón de la Chakana
    sun_r = int(size * 0.012)
    draw.ellipse([cx - sun_r, cy - sun_r, cx + sun_r, cy + sun_r], fill=(255, 230, 130, 255))
    
    return img

def main():
    icon_master = create_cusco_icon(1024)
    
    # Directorio de assets móvil
    os.makedirs("mobile/assets/icon", exist_ok=True)
    icon_master.resize((512, 512), Image.Resampling.LANCZOS).save("mobile/assets/icon/app_icon.png")
    print("Guardado mobile/assets/icon/app_icon.png (512x512)")
    
    # Directorios mipmap de Android
    densities = {
        "mipmap-mdpi": 48,
        "mipmap-hdpi": 72,
        "mipmap-xhdpi": 96,
        "mipmap-xxhdpi": 144,
        "mipmap-xxxhdpi": 192
    }
    
    for folder, dim in densities.items():
        out_dir = os.path.join("mobile/android/app/src/main/res", folder)
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "ic_launcher.png")
        resized = icon_master.resize((dim, dim), Image.Resampling.LANCZOS)
        resized.save(out_path)
        print(f"Guardado {out_path} ({dim}x{dim})")

if __name__ == "__main__":
    main()
