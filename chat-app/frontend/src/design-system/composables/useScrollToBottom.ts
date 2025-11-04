import { ref, nextTick } from 'vue';

export function useScrollToBottom() {
  const containerRef = ref<HTMLElement | null>(null);

  async function scrollToBottom(smooth = true) {
    await nextTick();
    if (containerRef.value) {
      containerRef.value.scrollTo({
        top: containerRef.value.scrollHeight,
        behavior: smooth ? 'smooth' : 'auto',
      });
    }
  }

  return {
    containerRef,
    scrollToBottom,
  };
}