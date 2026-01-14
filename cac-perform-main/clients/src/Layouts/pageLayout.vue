<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Header from '@/components/Header.vue'

const route = useRoute()

// Affiche le Header si la route définit `meta.showHeader === true`
// Sinon, par défaut on affiche le header sur la page 'home'.
const showHeader = computed(() => {
    return (route.meta && route.meta.showHeader) ?? (route.name === 'home')
})
</script>

<template>
  <div class="h-screen w-full flex flex-col bg-[#f5f7fa]">
      
      <!-- HEADER -->
      <Header v-if="showHeader" class="shadow-sm bg-white" />

      <!-- CONTENU -->
      <div class="flex-1 flex overflow-hidden">
        <slot />
      </div>

  </div>
</template>


<style scoped>

</style>