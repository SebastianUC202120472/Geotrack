// Motor de escena isométrica 3D para los mapas del sitio público (hero + flota).
// Port fiel de armarEscena/pintarEscena del mockup (landing_extraido/pagina.html,
// líneas 1278-1368). En lugar de guardar estado en `this`, cada llamada trabaja
// sobre el <svg> recibido: la lista de edificios se cachea en el propio nodo SVG
// (svg.__escenaEdif[sufijo]) para que ambas funciones la compartan y se libere al
// desmontar el componente. Los ids del SVG llevan sufijo ('' hero, '2' flota).

// Proyecta plano, edificios y etiquetas según la cámara (th = giro, T = inclinación).
// Input: svg (<svg>), sufijo de ids ('' | '2'), camara {th, T}.
// Devuelve la matriz de proyección {a,b,c,d,e,f} usada (útil para los flashes).
export function pintarEscena(svg, sufijo, camara) {
  const iso = svg.querySelector('#isoPlano' + sufijo);
  const edi = svg.querySelector('#edificios' + sufijo);
  const edif = svg.__escenaEdif && svg.__escenaEdif[sufijo];
  if (!iso || !edi || !edif) return null;
  const th = camara.th, T = camara.T;
  // Matriz isométrica: a/c/b/d giran e inclinan el plano según th y T
  const a = Math.cos(th), c = -Math.sin(th), b = Math.sin(th) * T, d = Math.cos(th) * T;
  const vb = svg.viewBox.baseVal;
  // Centra el plano proyectando sus 4 esquinas y recalculando la traslación e/f
  const esq = [[-18, -18], [778, -18], [-18, 538], [778, 538]];
  const Xs = esq.map(p => a * p[0] + c * p[1]), Ys = esq.map(p => b * p[0] + d * p[1]);
  const e = (vb.width - (Math.max.apply(null, Xs) - Math.min.apply(null, Xs))) / 2 - Math.min.apply(null, Xs);
  const f = (vb.height - (Math.max.apply(null, Ys) - Math.min.apply(null, Ys))) / 2 - Math.min.apply(null, Ys) + 26;
  iso.setAttribute('transform', 'matrix(' + a.toFixed(4) + ' ' + b.toFixed(4) + ' ' + c.toFixed(4) + ' ' + d.toFixed(4) + ' ' + e.toFixed(1) + ' ' + f.toFixed(1) + ')');
  // Vector "arriba" para extruir la altura de cada edificio
  const ux = -Math.sin(th) / T, uy = -Math.cos(th) / T;
  const sv = Math.sin(th) > 0, cv = Math.cos(th) > 0;
  // Ordena de atrás hacia adelante para el pintado correcto (painter's algorithm)
  const orden = edif.slice().sort((p, q) => (Math.sin(th) * (p.x + p.w / 2) + Math.cos(th) * (p.y + p.d / 2)) - (Math.sin(th) * (q.x + q.w / 2) + Math.cos(th) * (q.y + q.d / 2)));
  orden.forEach(bd => {
    const x = bd.x + 7, y = bd.y + 7, w = bd.w - 14, dd = bd.d - 14, h = bd.h;
    const A = [x, y], B = [x + w, y], C = [x + w, y + dd], D = [x, y + dd];
    const up = (p) => [p[0] + h * ux, p[1] + h * uy];
    const lado1 = sv ? [B, C] : [D, A];
    const lado2 = cv ? [C, D] : [A, B];
    const quad = (par) => [par[0], par[1], up(par[1]), up(par[0])].map(q => q[0].toFixed(1) + ',' + q[1].toFixed(1)).join(' ');
    bd.polys[0].setAttribute('points', quad(lado1));
    bd.polys[0].setAttribute('fill', '#b7c9dd');
    bd.polys[1].setAttribute('points', quad(lado2));
    bd.polys[1].setAttribute('fill', '#ccdae9');
    bd.polys[2].setAttribute('points', [up(A), up(B), up(C), up(D)].map(q => q[0].toFixed(1) + ',' + q[1].toFixed(1)).join(' '));
    bd.polys[2].setAttribute('fill', bd.techo);
    edi.appendChild(bd.g);
  });
  // Etiquetas ancladas a coordenadas del plano: data-world="x,y,dy"
  svg.querySelectorAll('text[data-world]').forEach(tx => {
    const w = tx.dataset.world.split(',').map(parseFloat);
    tx.setAttribute('x', (a * w[0] + c * w[1] + e).toFixed(1));
    tx.setAttribute('y', (b * w[0] + d * w[1] + f + (w[2] || 0)).toFixed(1));
  });
  const mat = { a, b, c, d, e, f };
  svg.__escenaMat = svg.__escenaMat || {};
  svg.__escenaMat[sufijo] = mat;
  return mat;
}

// Crea el estado de cámara, construye los edificios 3D y conecta el arrastre de vista.
// Input: svg (<svg>), sufijo de ids ('' hero | '2' flota), repintar (callback opcional
// que se dispara tras cada giro; por defecto vuelve a pintar la escena).
// Devuelve { camara, limpiar }: camara {th, T} mutable y limpiar() que desconecta
// TODOS los listeners y borra los edificios generados.
export function armarEscena(svg, sufijo, repintar) {
  const edi = svg.querySelector('#edificios' + sufijo);
  // Cámara inicial: la flota ('2') arranca con más giro/inclinación que el hero
  const camara = sufijo === '2' ? { th: Math.PI / 3.4, T: 0.6 } : { th: Math.PI / 4, T: 0.55 };
  const volverAPintar = repintar || (() => pintarEscena(svg, sufijo, camara));
  if (!edi) return { camara, limpiar: () => {} };

  // Genera un edificio (3 caras) por cada manzana no-parque, alturas fijas del mockup
  edi.innerHTML = '';
  const NS = 'http://www.w3.org/2000/svg';
  const alturas = sufijo === '2' ? [30, 42, 24, 38, 48, 28, 36] : [46, 64, 38, 58, 72, 42, 54];
  const edif = Array.from(svg.querySelectorAll('#manzanas' + sufijo + ' rect')).map(rc => ({
    x: +rc.getAttribute('x'), y: +rc.getAttribute('y'),
    w: +rc.getAttribute('width'), d: +rc.getAttribute('height'),
    park: rc.getAttribute('fill') === '#d8ecdc'
  })).filter(b => !b.park).map((b, i) => {
    const g = document.createElementNS(NS, 'g');
    const polys = [0, 1, 2].map(() => {
      const p = document.createElementNS(NS, 'polygon');
      p.setAttribute('stroke', 'rgba(15,43,74,.1)');
      p.setAttribute('stroke-width', '1');
      g.appendChild(p);
      return p;
    });
    edi.appendChild(g);
    return Object.assign({}, b, { h: alturas[i % alturas.length], techo: i % 3 === 0 ? '#e9f1f9' : '#dfeaf5', g, polys });
  });
  svg.__escenaEdif = svg.__escenaEdif || {};
  svg.__escenaEdif[sufijo] = edif;

  // Arrastre de cámara: girar (th) e inclinar (T) la vista con pointer events
  let arrastrando = false, camX = 0, camY = 0;
  const onDown = (e) => {
    // No robar el arrastre si se está tocando la camioneta del hero
    if (e.target.closest && e.target.closest('#vanMapa')) return;
    arrastrando = true; svg.style.cursor = 'grabbing';
    camX = e.clientX; camY = e.clientY;
    svg.setPointerCapture(e.pointerId);
    e.preventDefault();
  };
  const onMove = (e) => {
    if (!arrastrando) return;
    camara.th += (e.clientX - camX) * 0.008;
    camara.T = Math.max(0.3, Math.min(0.9, camara.T + (e.clientY - camY) * 0.0032));
    camX = e.clientX; camY = e.clientY;
    volverAPintar();
  };
  const finCam = () => { arrastrando = false; svg.style.cursor = 'grab'; };
  svg.addEventListener('pointerdown', onDown);
  svg.addEventListener('pointermove', onMove);
  svg.addEventListener('pointerup', finCam);
  svg.addEventListener('pointercancel', finCam);

  // Pinta la escena una vez con la cámara inicial
  pintarEscena(svg, sufijo, camara);

  // Desconecta todos los listeners y libera los edificios cacheados
  const limpiar = () => {
    svg.removeEventListener('pointerdown', onDown);
    svg.removeEventListener('pointermove', onMove);
    svg.removeEventListener('pointerup', finCam);
    svg.removeEventListener('pointercancel', finCam);
    if (svg.__escenaEdif) delete svg.__escenaEdif[sufijo];
    if (svg.__escenaMat) delete svg.__escenaMat[sufijo];
  };

  return { camara, limpiar };
}
