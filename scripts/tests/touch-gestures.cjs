const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

class FakePointerEvent extends Event {
  constructor(type, init = {}) {
    super(type, { bubbles: !!init.bubbles, cancelable: !!init.cancelable });
    Object.assign(this, init);
  }
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
    for (const item of [...(listeners.get(event.type) || [])]) {
      item.fn.call(this, event);
      if (event.cancelBubble) break;
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

context.TouchGestures.attach(element, {
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

console.log('touch-gestures: passed');
