<script setup>
import { computed } from 'vue'
import router from '@/router'

const hasToken = computed(() => typeof localStorage !== 'undefined' && !!localStorage.getItem('token'))

function logout() {
  localStorage.removeItem('token')
  router.push('/connexion')
}
</script>

<template>
  <RouterView />
</template>