import { useEffect, useState } from 'react'
import { fmt } from './format'

export type DeliveryReport = {
  schema_version: number; generated_at_utc: string
  git: { head: string; branch: string; dirty: boolean; github_head: string | null; github_checked_at: string | null }
  tests: { python: { passed: number; failed: number; skipped: number; seconds: number; modules: { name: string; passed: number; failed: number; skipped: number }[] };
    web: { passed: number; failed: number; total: number } }
  pilot: { generated_at_utc: string; protocol: Record<string, unknown>; environment: Record<string, string>;
    rows: { profile: string; nodes: number; edges: number; queue: string; median_us: number; q1_us: number; q3_us: number; sample_count: number; instance_seeds: number[] }[] }
  contributors: { name: string; count: number }[]
  commits: { hash: string; date: string; author: string; subject: string }[]
}
const repository = 'https://github.com/frankich99/PROYECTO_Algoritmos-Avanzados-UNSAAC'
const requirements = [
  ['Implementación funcional', '6 y 7', 'Dijkstra con tres colas y A*', 'entrega-integracion'],
  ['Pruebas automatizadas', '8', 'Casos normales, límite, adversos y semillas', 'entrega-pruebas'],
  ['Integración', '7 y 8', 'Generar, validar, resolver y contrastar', 'entrega-integracion'],
  ['Análisis de complejidad', '6', 'Peor caso, amortización y memoria', 'entrega-complejidad'],
  ['Experimentos preliminares', '9, 10 y 11', 'Protocolo, piloto y límites', 'entrega-piloto'],
  ['Documentación técnica', '7 y 14', 'Instalación y reproducción', 'entrega-documentacion'],
  ['Bitácora actualizada', '14', 'Fechas, autores y commits', 'entrega-bitacora'],
]

export default function EvidencePage({ onMethod }: { onMethod: () => void }) {
  const [report, setReport] = useState<DeliveryReport | null>(null)
  const [error, setError] = useState('')
  const [attempt, setAttempt] = useState(0)
  const [author, setAuthor] = useState('')
  const [allCommits, setAllCommits] = useState(false)
  useEffect(() => {
    const controller = new AbortController()
    setReport(null); setError('')
    fetch('./data/delivery_evidence.json', { signal: controller.signal }).then(async response => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      const value = await response.json() as DeliveryReport
      if (value.schema_version !== 1 || !value.tests?.python?.modules || !value.pilot?.rows || !value.commits || !value.git?.head)
        throw new Error('Formato de evidencia no válido')
      if (!controller.signal.aborted) setReport(value)
    }).catch(reason => { if (!controller.signal.aborted) setError(reason instanceof Error ? reason.message : 'Error de lectura') })
    return () => controller.abort()
  }, [attempt])
  const normalizeAuthor = (name: string) => name === 'Grupo 5 - Algoritmos Avanzados' ? 'ramaFRANKI' : name
  const allContributors = report?.contributors.map(c => ({ name: normalizeAuthor(c.name), count: c.count })) ?? []
  const contributors = allContributors.reduce((acc, curr) => {
    const existing = acc.find(c => c.name === curr.name)
    if (existing) existing.count += curr.count
    else acc.push({ ...curr })
    return acc
  }, [] as typeof allContributors)

  const rawCommits = report?.commits.map(c => ({ ...c, author: normalizeAuthor(c.author) })) ?? []
  const entries = rawCommits.filter(commit => !author || commit.author === author)
  const leaders = new Map<string, NonNullable<DeliveryReport['pilot']['rows'][number]>>()
  for (const row of report?.pilot.rows ?? []) {
    const key = `${row.profile}-${row.nodes}`
    if (!leaders.has(key) || row.median_us < leaders.get(key)!.median_us) leaders.set(key, row)
  }
  return <div className="reading-page delivery-page">
    <h1>Segunda entrega: evidencias</h1>
    <p className="page-intro">Del requisito a la prueba: implementación, integración, mediciones y aportes del grupo. Este registro técnico no sustituye la evaluación ni la defensa individual.</p>
    <div className="delivery-downloads"><a href="./data/segunda_entrega.md" download>Guía de reproducción</a><a href="./data/bitacora_github.md" download>Bitácora GitHub</a><a href="./data/delivery_evidence.json" download>Evidencias JSON</a><a href="./data/informe_final_unsaac.pdf" download>Informe PDF guardado</a></div>
    <div className="table-scroll"><table className="requirements-table"><caption>Organización según los productos de la segunda entrega</caption><thead><tr><th>Producto</th><th>Secciones del informe</th><th>Evidencia</th></tr></thead>
      <tbody>{requirements.map(([product, sections, evidence, id]) => <tr key={product}><th scope="row"><a href={`#${id}`}>{product}</a></th><td>{sections}</td><td>{evidence}</td></tr>)}</tbody></table></div>
    {!report && !error && <p role="status">Cargando el registro de pruebas y el piloto…</p>}
    {error && <div className="error" role="alert"><p>No se pudo cargar la evidencia: {error}. No se muestran conteos sin verificar.</p><button type="button" onClick={() => setAttempt(n => n + 1)}>Reintentar lectura</button></div>}
    {report && <>
      <p className="evidence-stamp">Registro generado: {report.generated_at_utc}. Base Git: <a href={`${repository}/commit/${report.git.head}`}>{report.git.head.slice(0, 7)}</a> ({report.git.branch}). {report.git.dirty ? 'Incluye cambios locales sin publicar.' : 'Árbol limpio al generar.'}</p>
      <section className="section-space" id="entrega-pruebas"><h2>Pruebas automatizadas ejecutadas</h2>
        <p><strong>Python: {report.tests.python.passed} aprobadas</strong>, {report.tests.python.failed} fallidas y {report.tests.python.skipped} omitidas, en {fmt(report.tests.python.seconds, 2)} s. <strong>Web: {report.tests.web.passed} aprobadas</strong> de {report.tests.web.total}, {report.tests.web.failed} fallidas.</p>
        <p className="fineprint">Son resultados de una ejecución guardada, no un porcentaje de cobertura de líneas ni una garantía formal de ausencia de errores.</p>
        <ul className="evidence-list"><li>Normales: costos conocidos, operaciones de colas y ruta A → B → C de costo 6.</li><li>Límite: cola vacía, origen igual a destino, empates, peso cero y nodos inalcanzables.</li><li>Adversos: pesos negativos, NaN, infinito, IDs inválidos, certificados alterados y JSON mal formado.</li><li>Reproducibles: colas contra heapq, Dijkstra contra Bellman-Ford y NetworkX, y grafos pequeños contra enumeración exhaustiva con semillas 0, 1, 7, 42 y 12345.</li></ul>
        <details><summary>Ver resultados por módulo Python</summary><div className="table-scroll"><table><thead><tr><th>Módulo</th><th>Aprobadas</th><th>Fallidas</th><th>Omitidas</th></tr></thead><tbody>{report.tests.python.modules.map(module => <tr key={module.name}><th scope="row">{module.name}</th><td>{module.passed}</td><td>{module.failed}</td><td>{module.skipped}</td></tr>)}</tbody></table></div></details>
      </section>
      <section className="section-space" id="entrega-integracion"><h2>Flujo integrado y verificación</h2>
        <ol className="evidence-list"><li>Cargar JSON / CSV / TXT o generar una red con semilla.</li><li>Validar IDs, pesos, coordenadas y límites de tamaño.</li><li>Ejecutar Dijkstra con tres colas y A* sobre la misma instancia.</li><li>Contrastar costos y caminos con referencias independientes.</li><li>Registrar muestras, semillas, entorno y contadores; exportar JSON y construir tablas.</li></ol>
        <p>Las pruebas HTTP repiten este flujo con cuatro generadores y semillas 0, 42 y 12345. El benchmark verifica contra NetworkX antes de medir; esa verificación queda fuera del cronómetro.</p>
      </section>
      <section className="section-space" id="entrega-complejidad"><h2>Complejidad y operaciones dominantes</h2><p>La comparación distingue cotas de peor caso y amortizadas, costo de la cola, memoria del grafo, reconstrucción y trazas.</p><button type="button" onClick={onMethod}>Ver análisis de complejidad y modelo</button></section>
      <section className="section-space" id="entrega-piloto"><h2>Diseño experimental y piloto actual</h2>
        <dl className="protocol-list"><div><dt>Instancias</dt><dd>Dispersas: V = 30 y 100, E ≈ 4V. Densas: V = 30 y 60, E ≈ 0,08V(V−1). Dos semillas por tamaño.</dd></div><div><dt>Repeticiones</dt><dd>5 por instancia y cola, 2 calentamientos; tres colas. 120 tiempos en total.</dd></div><div><dt>Medición</dt><dd>perf_counter_ns, GC desactivado durante cada muestra, orden de colas barajado con semilla. Solo núcleo: sin I/O, validación, trazas ni reconstrucción.</dd></div><div><dt>Variables controladas</dt><dd>Grafo, pesos, origen, semillas, intérprete y máquina. Sin llamadas a proveedores durante la medición.</dd></div><div><dt>Métricas</dt><dd>Microsegundos, mediana, Q1/Q3, operaciones, V/E y semillas. No se midieron caché ni memoria máxima.</dd></div><div><dt>Entorno</dt><dd>Python {report.pilot.environment.python}; {report.pilot.environment.platform}. Medido {report.pilot.generated_at_utc}.</dd></div></dl>
        <div className="table-scroll"><table><caption>Resultados del piloto de revisión, separados del banco histórico</caption><thead><tr><th>Perfil</th><th>V / E</th><th>Cola</th><th>Mediana (µs)</th><th>Q1 / Q3 (µs)</th><th>Muestras</th></tr></thead><tbody>{report.pilot.rows.map(row => <tr key={`${row.profile}-${row.nodes}-${row.queue}`}><td>{row.profile === 'sparse' ? 'Disperso' : 'Denso'}</td><td>{row.nodes} / {row.edges}</td><td>{row.queue}</td><td>{fmt(row.median_us, 2)}</td><td>{fmt(row.q1_us, 2)} / {fmt(row.q3_us, 2)}</td><td>{row.sample_count}</td></tr>)}</tbody></table></div>
        <p>Las cotas predicen más trabajo al crecer V y E. En estas escalas pequeñas, las constantes y la implementación pueden dominar. Una mediana menor aquí no acredita una ventaja universal ni significación estadística.</p>
        <ul className="evidence-list">{[...leaders.values()].map(row => <li key={`${row.profile}-${row.nodes}`}>En el perfil {row.profile === 'sparse' ? 'disperso' : 'denso'} con {row.nodes} vértices y {row.edges} aristas, {row.queue} tiene la menor mediana observada: {fmt(row.median_us, 2)} µs. Es una comparación descriptiva de esta ejecución.</li>)}</ul>
        <p><a href="./data/delivery_pilot.json" download>Descargar muestras crudas y protocolo del piloto</a></p>
        <details><summary>Consultar gráficos históricos</summary><p>Banco canónico de 1350 tiempos y piloto histórico de 18 tiempos; no se mezclan con este piloto.</p><img className="evidence-img" src="./data/benchmark_canonico.png" alt="Medianas e IQR del banco histórico, no del piloto actual" loading="lazy" /></details>
      </section>
      <section className="section-space" id="entrega-documentacion"><h2>Documentación y pendientes</h2><p>La guía descargable describe instalación, módulos, parámetros, formatos, pruebas y almacenamiento. El PDF es el informe guardado: esta revisión web no implica que el PDF haya sido recompilado.</p><ul className="evidence-list"><li>Local: FastAPI sirve la web compilada y todos los algoritmos.</li><li>Pages sin API: snapshots y mediciones guardadas. No produce nuevos benchmarks ni datos de proveedores.</li><li>Pendientes de acreditación: instalación en una máquina limpia, bitácoras individuales de aprendizaje, presentación y defensa. Las mediciones de rendimiento no son bitácoras de dedicación.</li></ul></section>
      <section className="section-space" id="entrega-bitacora"><h2>Bitácora de aportes en GitHub</h2>
        <p>Autoría del commit por rama y desarrollador. Los commits de «ramaFRANKI» registran el avance integrado del repositorio.</p>
        <p className="fineprint">{report.git.github_head ? `GitHub consultado ${report.git.github_checked_at}; HEAD remoto ${report.git.github_head.slice(0, 7)}.` : 'Sin comprobación remota guardada; el historial proviene del Git local.'}</p>
        <label className="author-filter">Filtrar por autor<select value={author} onChange={event => { setAuthor(event.target.value); setAllCommits(false) }}><option value="">Todos los autores</option>{contributors.map(contributor => <option key={contributor.name} value={contributor.name}>{contributor.name} ({contributor.count})</option>)}</select></label>
        <div className="table-scroll"><table><caption>Commits alcanzables desde la rama al generar el registro</caption><thead><tr><th>Fecha del autor</th><th>Autor</th><th>Cambio registrado</th><th>Commit</th></tr></thead><tbody>{entries.slice(0, allCommits ? undefined : 12).map(commit => <tr key={commit.hash}><td>{commit.date.slice(0, 10)}</td><td>{commit.author}</td><td>{commit.subject}</td><td><a href={`${repository}/commit/${commit.hash}`}>{commit.hash.slice(0, 7)}</a></td></tr>)}</tbody></table></div>
        {entries.length > 12 && <button type="button" onClick={() => setAllCommits(value => !value)}>{allCommits ? 'Mostrar solo recientes' : `Ver los ${entries.length} commits`}</button>}
        {!entries.length && <p className="empty-state">No hay commits para este filtro.</p>}
      </section>
    </>}
  </div>
}
