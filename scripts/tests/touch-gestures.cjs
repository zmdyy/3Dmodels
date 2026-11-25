const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

class FakePointerEvent extends Event {
  constructor(type, init = {}) {
    const { bubbles, cancelable, ...props } = init;
    super(type, { bubbles: !!bubbles, cancelable: !!cancelable });
    Object.assign(this, props);
    this.immediateStopped = false;
  }
  stopImmediatePropagation() { this.immediateStopped = true; super.stopImmediatePropagation(); }
}

const listeners = new Map();
const element = {
  style: { touchAction: 'pan-y' },
  clientHeight: 400,
  addEventListener(type, fn, options) {
    const list = listeners.get(type) || [];
    list.push({ fn, capture: !!(options && options.capture) });
    listeners.set(type, list);
  },
  removeEventListener(type, fn) {
    listeners.set(type, (listeners.get(type) || []).filter(x => x.fn !== fn));
  },
  setPointerCapture() {},
  dispatchEvent(event) {
    const ordered = [...(listeners.get(event.type) || [])].sort((a, b) => Number(b.capture) - Number(a.capture));
    for (const item of ordered) {
      item.fn.call(this, event);
      if (event.immediateStopped) break;
    }
    return !event.defaultPrevented;
  }
};

const context = {
  PointerEvent: FakePointerEvent,
  window: null,
  globalThis: null,
  Map, Math, TypeError
};
context.window = context;
context.globalThis = context;
vm.runInNewContext(fs.readFileSync(require.resolve('../../shared/touch-gestures.js'), 'utf8'), context);

const log = [];
element.addEventListener('pointerdown', e => log.push('model-down-' + e.pointerId));
element.addEventListener('pointercancel', e => log.push('model-cancel-' + e.pointerId));
element.addEventListener('pointermove', e => log.push('model-move-' + e.pointerId));
element.addEventListener('pointerup', e => log.push('model-up-' + e.pointerId));

const navigation = context.TouchGestures.attach(element, {
  onStart: () => log.push('gesture-start'),
  onGesture: g => log.push({ scale: g.scale, dx: g.dx, dy: g.dy }),
  onEnd: () => log.push('gesture-end')
});

const send = (type, init) => element.dispatchEvent(new FakePointerEvent(type, {
  bubbles: true, cancelable: true, pointerType: 'touch', ...init
}));

send('pointerdown', { pointerId: 1, clientX: 100, clientY: 100, button: 0 });
send('pointerdown', { pointerId: 2, clientX: 200, clientY: 100, button: 0 });
send('pointermove', { pointerId: 1, clientX: 80, clientY: 100 });
send('pointermove', { pointerId: 2, clientX: 230, clientY: 130 });
send('pointerup', { pointerId: 2, clientX: 230, clientY: 130 });
send('pointerup', { pointerId: 1, clientX: 80, clientY: 100 });

assert(log.includes('model-down-1'), 'first finger must still reach the model');
assert(log.includes('model-cancel-1'), 'second finger must cancel the original one-finger action');
assert(!log.includes('model-down-2'), 'second finger must be reserved for camera gestures');
assert(!log.includes('model-move-1') && !log.includes('model-move-2'), 'two-finger moves must not reach the model drag handler');
assert(log.some(x => typeof x === 'object' && x.dx !== 0 && x.dy !== 0), 'two-finger centroid movement must pan');
assert(log.some(x => typeof x === 'object' && x.scale < 1), 'pinch-out must zoom in');
assert(log.includes('gesture-end'), 'gesture end must be reported');
assert.equal(element.style.touchAction, 'none', 'touch scrolling must be disabled on the 3D surface');

const camera = {
  position: { x: 0, y: 0, z: 10 },
  matrixWorld: { elements: [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1] },
  fov: 50,
  updateMatrixWorld() {}
};
const arrayTarget = [0, 0, 0];
context.TouchGestures.pan(camera, arrayTarget, element, 10, 10);
assert(arrayTarget[0] < 0 && arrayTarget[1] > 0, 'pan helper must support array camera targets');
class Vec3 {
  constructor(x=0,y=0,z=0){this.x=x;this.y=y;this.z=z;}
  clone(){return new Vec3();}
  setFromMatrixColumn(matrix,index){const i=index*4;this.x=matrix.elements[i];this.y=matrix.elements[i+1];this.z=matrix.elements[i+2];return this;}
  addScaledVector(v,s){this.x+=v.x*s;this.y+=v.y*s;this.z+=v.z*s;return this;}
}
const vectorTarget = new Vec3();
context.TouchGestures.pan(camera, vectorTarget, element, 10, 10);
assert(vectorTarget.x < 0 && vectorTarget.y > 0, 'pan helper must support Vector3-like camera targets');
navigation.dispose();
assert.equal(element.style.touchAction, 'pan-y', 'dispose must restore the original touch-action style');

console.log('touch-gestures: passed');
