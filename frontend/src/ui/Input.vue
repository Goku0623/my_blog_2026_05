<template>
  <div :class="['flex items-center', sizeCls, wrapperCls]">
    <span v-if="$slots.prefix || prefixIcon" class="mr-2 flex shrink-0 text-[var(--text-muted)]">
      <slot name="prefix">
        <component :is="prefixIcon" v-if="prefixIcon" class="size-4" />
      </slot>
    </span>
    <input
      v-if="type !== 'textarea'"
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :readonly="readonly"
      :maxlength="maxlength"
      class="w-full bg-transparent outline-none placeholder:text-[var(--text-muted)] disabled:cursor-not-allowed"
      @input="onInput"
      @keydown="$emit('keydown', $event)"
      @keyup="$emit('keyup', $event)"
      @focus="$emit('focus', $event)"
      @blur="$emit('blur', $event)"
    />
    <textarea
      v-else
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :readonly="readonly"
      :rows="rows"
      :maxlength="maxlength"
      class="w-full bg-transparent outline-none placeholder:text-[var(--text-muted)] resize-none disabled:cursor-not-allowed"
      @input="onInput"
      @keydown="$emit('keydown', $event)"
      @keyup="$emit('keyup', $event)"
      @focus="$emit('focus', $event)"
      @blur="$emit('blur', $event)"
    />
    <span v-if="$slots.suffix" class="ml-2 flex shrink-0 text-[var(--text-muted)]">
      <slot name="suffix" />
    </span>
    <span
      v-else-if="showCount && maxlength"
      class="ml-2 shrink-0 text-xs text-[var(--text-muted)]"
    >
      {{ String(modelValue ?? '').length }}/{{ maxlength }}
    </span>
  </div>
</template>

<script setup lang="ts">
import { computed, type Component } from 'vue'

interface Props {
  modelValue?: string | number
  type?: 'text' | 'password' | 'email' | 'number' | 'search' | 'url' | 'date' | 'time' | 'datetime-local' | 'textarea'
  placeholder?: string
  disabled?: boolean
  readonly?: boolean
  size?: 'sm' | 'md' | 'lg'
  prefixIcon?: Component
  rows?: number
  maxlength?: number
  showCount?: boolean
  status?: 'default' | 'error'
}

const props = withDefaults(defineProps<Props>(), {
  type: 'text',
  size: 'md',
  rows: 3,
  status: 'default',
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'keydown', ev: KeyboardEvent): void
  (e: 'keyup', ev: KeyboardEvent): void
  (e: 'focus', ev: FocusEvent): void
  (e: 'blur', ev: FocusEvent): void
}>()

const onInput = (ev: Event) => {
  const target = ev.target as HTMLInputElement | HTMLTextAreaElement
  emit('update:modelValue', target.value)
}

const sizeCls = computed(() => {
  if (props.type === 'textarea') return 'px-3 py-2 text-sm'
  switch (props.size) {
    case 'sm':
      return 'h-8 px-2.5 text-sm'
    case 'lg':
      return 'h-12 px-4 text-base'
    default:
      return 'h-10 px-3 text-sm'
  }
})

const wrapperCls = computed(() => {
  const base = [
    'rounded-lg border bg-[var(--surface)] text-[var(--text)] transition-shadow',
    'focus-within:ring-2 focus-within:ring-[var(--brand)]/30',
  ]
  if (props.disabled) {
    base.push('bg-[var(--bg-muted)] cursor-not-allowed')
  }
  if (props.status === 'error') {
    base.push('border-[var(--danger)] focus-within:ring-[var(--danger)]/25')
  } else {
    base.push('border-[var(--border-strong)] focus-within:border-[var(--brand)]')
  }
  return base.join(' ')
})
</script>
