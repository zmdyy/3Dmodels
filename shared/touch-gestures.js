/* Unified two-finger navigation for custom 3D camera controllers.
 * One finger remains owned by the model (orbit / pick / drag).
 * Two fingers are reserved for camera zoom + pan; after the gesture, lift
 * both fingers before starting another one-finger action to avoid jumps.
 */
(function (root) {
  'use strict';
  const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

  function attach(element, options = {}) {
    if (!element || !element.addEventListener) throw new TypeError('TouchGestures.attach requires an element');
    const points = new Map();
    const oldTouchAction = element.style.touchAction;
    let mode = 'single';
    let previous = null;
    let dispatchingCancel = false;
    let disposed = false;
    element.style.touchAction = 'none';

    function metrics() {
      const a = [...points.values()];
      if (a.length < 2) return null;
      return {
        x: (a[0].x + a[1].x) / 2,
        y: (a[0].y + a[1].y) / 2,
        distance: Math.max(1, Math.hypot(a[0].x - a[1].x, a[0].y - a[1].y))
      };
    }
    function suppress(event) {
      if (event.cancelable) event.preventDefault();
      event.stopImmediatePropagation();
    }
    function cancelFirstPointer() {
      const first = points.entries().next().value;
      if (!first) return;
      const [pointerId, p] = first;
      try {
        dispatchingCancel = true;
        element.dispatchEvent(new PointerEvent('pointercancel', {
          bubbles: true, cancelable: false, pointerId, pointerType: 'touch',
          isPrimary: true, clientX: p.x, clientY: p.y, buttons: 0
        }));
      } finally {
        dispatchingCancel = false;
      }
    }
    function onDown(event) {
      if (dispatchingCancel || event.pointerType !== 'touch') return;
      points.set(event.pointerId, { x: event.clientX, y: event.clientY });
      if (points.size === 2 && mode === 'single') {
        cancelFirstPointer();
        mode = 'gesture';
        previous = metrics();
        try { element.setPointerCapture(event.pointerId); } catch (_) {}
        if (options.onStart) options.onStart();
        suppress(event);
      } else if (points.size > 2) {
        mode = 'locked';
        suppress(event);
      }
    }
    function onMove(event) {
      if (dispatchingCancel || event.pointerType !== 'touch' || !points.has(event.pointerId)) return;
      if (mode === 'gesture' || mode === 'locked') {
        suppress(event);
        const p = points.get(event.pointerId);
        points.set(event.pointerId, { x: event.clientX, y: event.clientY });
        if (mode !== 'gesture' || points.size < 2) return;
        const next = metrics();
        if (previous && next && options.onGesture) {
          const rawScale = previous.distance / next.distance;
          options.onGesture({
            scale: clamp(rawScale, 0.65, 1.55),
            dx: next.x - previous.x,
            dy: next.y - previous.y,
            centerX: next.x,
            centerY: next.y,
            distance: next.distance
          });
        }
        previous = next;
        return;
      }
      points.set(event.pointerId, { x: event.clientX, y: event.clientY });
    }
    function onEnd(event) {
      if (dispatchingCancel || event.pointerType !== 'touch' || !points.has(event.pointerId)) return;
      if (mode === 'gesture' || mode === 'locked') suppress(event);
      points.delete(event.pointerId);
      if (points.size === 0) {
        const wasGesture = mode !== 'single';
        mode = 'single';
        previous = null;
        if (wasGesture && options.onEnd) options.onEnd();
      } else if (mode === 'gesture') {
        // Do not reinterpret the remaining finger as a fresh orbit / part drag.
        // Lift all fingers, then begin a new one-finger action.
        mode = 'locked';
        previous = null;
      }
    }
    const listeners = [
      ['pointerdown', onDown], ['pointermove', onMove],
      ['pointerup', onEnd], ['pointercancel', onEnd], ['lostpointercapture', onEnd]
    ];
    for (const [type, handler] of listeners) {
      element.addEventListener(type, handler, { capture: true, passive: false });
    }

    return {
      dispose() {
        if (disposed) return;
        disposed = true;
        for (const [type, handler] of listeners) element.removeEventListener(type, handler, true);
        points.clear();
        element.style.touchAction = oldTouchAction;
      }
    };
  }

  function pan(camera, target, element, dx, dy) {
    if (!camera || !target || !element || !camera.position || !target.addScaledVector) return;
    if (camera.updateMatrixWorld) camera.updateMatrixWorld();
    const height = Math.max(1, element.clientHeight || element.getBoundingClientRect().height);
    const scale = camera.isOrthographicCamera
      ? (camera.top - camera.bottom) / Math.max(1e-6, camera.zoom || 1) / height
      : 2 * camera.position.distanceTo(target) * Math.tan((camera.fov || 50) * Math.PI / 360) / height;
    const right = target.clone().setFromMatrixColumn(camera.matrixWorld, 0);
    const up = target.clone().setFromMatrixColumn(camera.matrixWorld, 1);
    target.addScaledVector(right, -dx * scale).addScaledVector(up, dy * scale);
  }

  root.TouchGestures = { attach, pan };
})(typeof window === 'undefined' ? globalThis : window);
