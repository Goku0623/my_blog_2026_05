<template>
  <div class="relative inline-flex w-full">
    <select
      :value="modelValue"
      :disabled="disabled"
      :class="[
        'w-full appearance-none rounded-lg border bg-[var(--surface)] text-[var(--text)] pl-3 pr-9 outline-none transition',
        'border-[var(--border-strong)] focus:border-[var(--brand)] focus:ring-2 focus:ring-[var(--brand)]/30',
        sizeCls,
        disabled && 'bg-[var(--bg-muted)] cursor-not-allowed',
      ]"
      @change="onChange"
    >
      <option v-if="placeholder" value="" disabled>{{ placeholder }}</option>
      <option
        v-for="opt in normalizedOptions"
        :key="String(opt.value)"
        :value="opt.value"
      >{{ opt.label }}</option>
    </select>
    <ChevronDown class="absolute right-3 top-1/2 -translate-y-1/2 size-4 text-[var(--text-muted)] pointer-events-none" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ChevronDown } from 'lucide-vue-next'

type OptionLike = string | number | { label: string; value: string | number }

interface Props {
  modelValue?: string | number
  options: OptionLike[]
  placeholder?: string
  disabled?: boolean
  size?: 'sm' | 'md' | 'lg'
}

const props = withDefaults(defineProps<Props>(), { size: 'md' })
const emit = defineEmits<{ (e: 'update:modelValue', v: string | number): void; (e: 'change', v: string | number): void }>()

const normalizedOptions = computed(() =>
  props.options.map((o) => (typeof o === 'object' ? o : { label: String(o), value: o }))
)

const sizeCls = computed(() => {
  switch (props.size) {
    case 'sm': return 'h-8 text-sm'
    case 'lg': return 'h-12 text-base'
    default: return 'h-10 text-sm'
  }
})

const onChange = (e: Event) => {
  const v = (e.target as HTMLSelectElement).value
  emit('update:modelValue', v)
  emit('change', v)
}
</script>
