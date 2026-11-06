"""Genera gráficos nítidos de los nodos y recorridos óptimos en Cusco."""
import os
import matplotlib.pyplot as plt
import networkx as nx

def generate_cusco_route_figure():
    fig, ax = plt.subplots(figsize=(10, 6.5), dpi=300)
    
    # Coordenadas esquemáticas basadas en la topografía del Centro Histórico
    coords = {
        "A": (0.0, 0.0),       # Plaza Mayor
        "B": (-1.3, 0.2),      # Regocijo
        "C": (1.8, -1.8),      # Qorikancha
        "D": (-2.8, -0.6),     # San Francisco
        "E": (-3.8, -2.2),     # San Pedro
        "F": (3.5, -2.8),      # Limacpampa
    }
    
    node_labels = {
        "A": "A: Plaza Mayor\n(3,399 m.s.n.m.)",
        "B": "B: Regocijo\n(Cusipata)",
        "C": "C: Qorikancha\n(Santo Domingo)",
        "D": "D: San Francisco\n(Plaza)",
        "E": "E: Mercado\nSan Pedro",
        "F": "F: Limacpampa\n(Grande)",
    }
    
    G = nx.DiGraph()
    for n, p in coords.items():
        G.add_node(n, pos=p)
        
    edges = [
        ("A", "B", "Espaderos\n+1.5% (45 s)"),
        ("A", "C", "Loreto\n-2.0% (108 s)"),
        ("B", "D", "Garcilaso\n+3.0% (57 s)"),
        ("B", "C", "Almagro\n-1.0% (96 s)"),
        ("C", "F", "Ahuacpinta\n+0.5% (36 s)"),
        ("C", "E", "Matará\n+2.0% (151 s)"),
        ("D", "E", "Santa Clara\n+2.5% (64 s)"),
        ("D", "C", "Marqués\n-2.5% (120 s)"),
        ("E", "F", "Tullumayo\n-1.0% (158 s)"),
    ]
    
    for u, v, label in edges:
        G.add_edge(u, v, label=label)
        
    # Ruta óptima A -> C -> F
    optimal_edges = [("A", "C"), ("C", "F")]
    optimal_nodes = ["A", "C", "F"]
    
    # Dibujar aristas no óptimas
    other_edges = [e for e in G.edges() if e not in optimal_edges]
    nx.draw_networkx_edges(
        G, coords, edgelist=other_edges,
        edge_color="#877d77", width=1.8, alpha=0.6,
        arrowsize=16, arrowstyle="-|>", connectionstyle="arc3,rad=0.08", ax=ax
    )
    
    # Dibujar aristas óptimas destacadas
    nx.draw_networkx_edges(
        G, coords, edgelist=optimal_edges,
        edge_color="#681c32", width=3.8, alpha=0.95,
        arrowsize=22, arrowstyle="-|>", connectionstyle="arc3,rad=0.06", ax=ax
    )
    
    # Dibujar nodos
    other_nodes = [n for n in G.nodes() if n not in optimal_nodes]
    nx.draw_networkx_nodes(
        G, coords, nodelist=other_nodes,
        node_color="#f7f3ea", edgecolors="#53484b", node_size=1800, linewidths=2.0, ax=ax
    )
    nx.draw_networkx_nodes(
        G, coords, nodelist=optimal_nodes,
        node_color="#681c32", edgecolors="#8a6418", node_size=2100, linewidths=2.8, ax=ax
    )
    
    # Etiquetas de nodos
    for n, (x, y) in coords.items():
        color = "#ffffff" if n in optimal_nodes else "#1f1b1c"
        ax.text(x, y, node_labels[n], ha="center", va="center", fontsize=8.5,
                fontweight="bold", color=color, zorder=10)
        
    # Etiquetas de aristas
    edge_labels = {(u, v): d["label"] for u, v, d in G.edges(data=True)}
    for (u, v), label in edge_labels.items():
        is_opt = (u, v) in optimal_edges
        x1, y1 = coords[u]
        x2, y2 = coords[v]
        xm, ym = (x1 + x2) / 2.0, (y1 + y2) / 2.0
        # Ligero desplazamiento
        offset = 0.2 if (x2 > x1) else -0.2
        ax.text(xm, ym + offset, label, fontsize=7.2, ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.2", facecolor="#ffffff" if not is_opt else "#fff8e7",
                          edgecolor="#681c32" if is_opt else "#b8a99a", alpha=0.9, lw=1.0))
        
    ax.set_title("Red Vial y Ruta Óptima en el Centro Histórico de Cusco\n"
                 "Ruta mínima calculada: A (Plaza Mayor) → C (Qorikancha) → F (Limacpampa) | Costo: 144.45 s",
                 fontsize=11.5, fontweight="bold", pad=16, color="#341e25")
    
    # Recuadro informativo
    info_text = (
        "Modelo Topográfico y de Relieve:\n"
        "• Penalización de subida: F_pendiente = 1 + 2.5 × max(0, pendiente/100)\n"
        "• Velocidades nominales: Calle colonial 15 km/h | Avenida 35 km/h\n"
        "• Certificación: Dijkstra (3 colas) y Bellman-Ford idénticos (brecha dual = 0)"
    )
    ax.text(0.02, 0.03, info_text, transform=ax.transAxes, fontsize=8,
            verticalalignment='bottom', bbox=dict(boxstyle='round,pad=0.5', facecolor='#ffffff', edgecolor='#8a6418', lw=1.2))
    
    ax.axis("off")
    plt.tight_layout()
    
    outputs = [
        "latex/figuras/grafo_nodos_rutas_centro.png",
        "web/public/data/grafo_nodos_rutas_centro.png",
        "python/results/figures/grafo_nodos_rutas_centro.png"
    ]
    for out in outputs:
        os.makedirs(os.path.dirname(out), exist_ok=True)
        fig.savefig(out, bbox_inches="tight")
        print(f"Generado exitosamente: {out}")
        
    plt.close(fig)

if __name__ == "__main__":
    generate_cusco_route_figure()
