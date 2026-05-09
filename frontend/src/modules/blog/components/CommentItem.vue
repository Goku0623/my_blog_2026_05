<template>
  <div
    :class="[
      'flex gap-3 sm:gap-4 transition-colors',
      isReply
        ? 'pl-3 sm:pl-4 py-3 border-l-2 border-[var(--brand)]/30'
        : 'p-4 sm:p-5 hover:bg-[var(--bg-soft)]/40',
    ]"
  >
    <UAvatar :name="comment.guest_name" :size="isReply ? 32 : 40" />
    <div class="flex-1 min-w-0">
      <div class="flex flex-wrap items-center gap-x-2 gap-y-1 mb-1.5">
        <a
          v-if="comment.guest_website"
          :href="comment.guest_website"
          target="_blank"
          rel="noopener noreferrer"
          class="text-sm font-semibold text-[var(--text)] hover:text-[var(--brand)] transition-colors"
        >{{ comment.guest_name }}</a>
        <span v-else class="text-sm font-semibold text-[var(--text)]">{{ comment.guest_name }}</span>

        <span v-if="isAi" class="inline-flex items-center gap-0.5 text-[10px] font-medium px-1.5 py-0.5 rounded-md bg-gradient-to-r from-[var(--brand)] to-[var(--accent)] text-white">
          AI
        </span>

        <span class="text-xs text-[var(--text-muted)]">·</span>
        <span class="text-xs text-[var(--text-muted)]">{{ formatFriendlyTime(comment.created_at) }}</span>
      </div>

      <div
        class="prose prose-sm max-w-none dark:prose-invert text-[var(--text-soft)] leading-relaxed"
        v-html="renderedContent"
      />

      <div class="mt-2 flex items-center gap-3">
        <button
          class="inline-flex items-center gap-1 text-xs text-[var(--text-muted)] hover:text-[var(--brand)] transition-colors"
          @click="$emit('reply', comment)"
        >
          <Reply class="size-3.5" /> 回复
        </button>
      </div>

      <div
        v-if="comment.replies && comment.replies.length > 0 && !isReply"
        class="mt-3 space-y-1 ml-1"
      >
        <CommentItem
          v-for="reply in comment.replies"
          :key="reply.id"
          :comment="reply"
          :is-reply="true"
          @reply="$emit('reply', $event)"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { type Comment } from '@/api/comments'
import { formatFriendlyTime } from '@/utils/time'
import { useMarkdown } from '@/composables/useMarkdown'
import { Reply } from 'lucide-vue-next'
import { UAvatar } from '@/ui'

const props = defineProps<{ comment: Comment; isReply?: boolean }>()

defineEmits<{ (e: 'reply', comment: Comment): void }>()

const { render } = useMarkdown()
const renderedContent = computed(() => render(props.comment.content))

const isAi = computed(() => {
  const token = props.comment.guest?.guest_token?.toLowerCase()
  const name = props.comment.guest_name || ''
  return token === 'ai-assistant' || name.includes('AI助手') || name.includes('AI助手Bot')
})
</script>
