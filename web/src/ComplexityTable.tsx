export default function ComplexityTable() {
  return <section className="section-space" id="complejidad">
    <h2>Complejidad de las alternativas</h2>
    <p>V = vértices, E = aristas, n = elementos de la cola. Se separa el núcleo de la reconstrucción de caminos.</p>
    <div className="table-scroll"><table><caption>Operaciones de las colas de prioridad</caption>
      <thead><tr><th>Cola</th><th>Insertar</th><th>Extraer mínimo</th><th>Disminuir clave</th><th>Tipo de cota</th></tr></thead>
      <tbody>
        <tr><th scope="row">Binaria</th><td>O(log n)</td><td>O(log n)</td><td>O(log n)</td><td>Peor caso</td></tr>
        <tr><th scope="row">4-aria</th><td>O(log₄ n)</td><td>O(4 log₄ n)</td><td>O(log₄ n)</td><td>Peor caso; d = 4 constante</td></tr>
        <tr><th scope="row">Fibonacci</th><td>O(1)</td><td>O(log n)</td><td>O(1)</td><td>Amortizada; una operación aislada puede costar O(n)</td></tr>
      </tbody>
    </table></div>
    <div className="table-scroll"><table><caption>Núcleo algorítmico, sin traza ni todos los caminos</caption>
      <thead><tr><th>Alternativa</th><th>Tiempo</th><th>Espacio auxiliar</th><th>Operación dominante</th></tr></thead>
      <tbody>
        <tr><th scope="row">Dijkstra binario / 4-ario</th><td>O((V + E) log V), peor caso</td><td>O(V)</td><td>Extracciones y disminuciones de clave</td></tr>
        <tr><th scope="row">Dijkstra Fibonacci</th><td>O(E + V log V), amortizado</td><td>O(V)</td><td>Relajaciones y consolidación</td></tr>
        <tr><th scope="row">A* consistente</th><td>Misma cota que Dijkstra según la cola</td><td>O(V)</td><td>Relajaciones y evaluación de h</td></tr>
        <tr><th scope="row">Dijkstra con arreglo (referencia)</th><td>O(V² + E), peor caso</td><td>O(V)</td><td>Búsqueda lineal del mínimo</td></tr>
        <tr><th scope="row">Bellman-Ford (referencia)</th><td>O(VE), peor caso</td><td>O(V)</td><td>Pasadas sobre todas las aristas</td></tr>
      </tbody>
    </table></div>
    <p>El grafo ocupa O(V + E). Validar y calibrar la heurística cuesta O(V + E); si h = 0, A* no obtiene una ventaja heurística. No se afirma una cota promedio sin un modelo probabilístico.</p>
    <p className="fineprint">Opciones adicionales: reconstruir todos los caminos puede requerir O(V²) de tiempo y espacio; guardar la traza completa añade O(V² log V + E) de tiempo y O(V² + E) de espacio en el peor caso. El benchmark desactiva ambas opciones.</p>
  </section>
}
