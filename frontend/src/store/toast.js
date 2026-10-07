import { reactive } from 'vue'

export const toasts = reactive({ list: [] })

let uid = 0
export function toast(message, type = 'ok', ms = 2400) {
  const id = ++uid
  toasts.list.push({ id, message, type })
  setTimeout(() => {
    toasts.list = toasts.list.filter(t => t.id !== id)
  }, ms)
}

export function toastOk(msg) { toast(msg, 'ok') }
export function toastErr(msg) { toast(msg, 'err', 3800) }