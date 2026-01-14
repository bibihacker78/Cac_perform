
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as apiLogin } from '../api.js'
import axios from 'axios'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userRole = ref(localStorage.getItem('userRole') || '')
  const user = ref(JSON.parse(localStorage.getItem('user')) || null)

  const isLoading = ref(false)
  const isAuthenticated = computed(() => !!token.value)

  async function login(credentials) {
    isLoading.value = true
    try {
      // Utilise la fonction login de api.js
      const response = await apiLogin(credentials)
      if (response.data.access_token) {
        token.value = response.data.access_token
        user.value = response.data.user
        userRole.value = response.data.user.role

        localStorage.setItem('token', token.value)
        localStorage.setItem('userRole', userRole.value)
        localStorage.setItem('user', JSON.stringify(user.value))
        isLoading.value = false
        return true
      }
    } catch (error) {
      console.error('Erreur de connexion:', error)
      isLoading.value = false
      return false
    }
    isLoading.value = false
    return false
  }

    // ✅ Méthode initialize définie
  const initialize = async () => {
    try {
      // Récupérer le token depuis localStorage
      const savedToken = localStorage.getItem('token')
      const savedUser = localStorage.getItem('user')
      
      if (savedToken && savedUser) {
        token.value = savedToken
        user.value = JSON.parse(savedUser)
        isAuthenticated.value = true
        
        // Optionnel : Vérifier la validité du token
        await validateToken()
      }
    } catch (error) {
      console.error('Erreur lors de l\'initialisation:', error)
      logout() // Nettoyer en cas d'erreur
    }
  }
    const validateToken = async () => {
    try {
      const response = await fetch('/api/validate-token', {
        headers: { 'Authorization': `Bearer ${token.value}` }
      })
      
      if (!response.ok) {
        logout()
        return false
      }
      
      return true
    } catch (error) {
      console.error('Erreur validation token:', error)
      logout()
      return false
    }
  }

  // Fonction de déconnexion
  function logout() {
    token.value = ''
    user.value = null
    userRole.value = ''

    // Supprimer du localStorage
    localStorage.removeItem('token')
    localStorage.removeItem('userRole')
    localStorage.removeItem('user')
    // Supprimer l'en-tête d'autorisation
    delete axios.defaults.headers.common['Authorization']
  }
  

  return {
    token,
    user,
    userRole,
    isAuthenticated,
    isLoading,
    initialize, 
    validateToken,
    login,
    logout,
  }
})
