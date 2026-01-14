<script setup>
import { onMounted } from 'vue';

const props = defineProps(['efiActif', 'annee_auditee'])

// Formatte un montant avec séparateurs de milliers (locale fr-FR).
// Accepte des nombres ou des chaînes numériques. Retourne chaîne vide pour null/undefined.
function formatAmount(value) {
  if (value === null || value === undefined || value === '') return ''

  // Normaliser les chaînes (supprimer espaces, remplacer virgules par point)
  const normalized = typeof value === 'string' ? value.replace(/\s+/g, '').replace(/,/g, '.') : value
  const num = Number(normalized)
  if (Number.isNaN(num)) return value

  // Affiche sans décimales si entier, sinon jusqu'à 2 décimales
  const opts = Number.isInteger(num)
    ? { maximumFractionDigits: 0 }
    : { minimumFractionDigits: 2, maximumFractionDigits: 2 }

  return num.toLocaleString('fr-FR', opts)
}

onMounted(() => {
  console.log('📊 ActifComponent - Données reçues:');
  console.log('  - efiActif:', props.efiActif);
  console.log('  - annee_auditee:', props.annee_auditee);
  console.log('  - Type efiActif:', typeof props.efiActif);
  console.log('  - Est un tableau?', Array.isArray(props.efiActif));
  console.log('  - Longueur:', props.efiActif?.length);
  if (props.efiActif && props.efiActif.length > 0) {
    console.log('  - Premier élément:', props.efiActif[0]);
  }
})
</script>

<template>
  <!-- Tableau grouping principal -->
  <h3 class="pt-5 pb-1 pl-0 text-xl font-semibold uppercase tracking-wider">Bilan Actif</h3>
  <div class="overflow-hidden rounded-xl shadow-xl bg-white border border-gray-100">
    <table class="min-w-full divide-y divide-gray-200">
      <thead class="bg-gradient-to-r from-blue-ycube to-blue-ycube-3">
        <tr>
          <th class="px-6 py-4 text-left text-xs font-semibold text-white uppercase tracking-wider" colspan="2"></th>
          <th class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider" colspan="3">
            EXERCICE AU 31/12/{{ props.annee_auditee }}</th>
          <th class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider">EXERCICE AU
            31/12/{{ parseInt(props.annee_auditee) - 1 }}</th>
        </tr>
        <tr>
          <th class="px-6 py-4 text-left text-xs font-semibold text-white uppercase tracking-wider">REF</th>
          <th class="px-6 py-4 text-left text-xs font-semibold text-white uppercase tracking-wider">Intitulé</th>
          <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">BRUT</th>
          <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">AMORT et DEPREC
          </th>
          <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">NET</th>
          <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">NET</th>
        </tr>
      </thead>
      <tbody class="bg-white divide-y divide-gray-200">
        <tr v-if="!props.efiActif || props.efiActif.length === 0">
          <td colspan="6" class="px-6 py-4 text-center text-gray-500">
            <div class="text-sm">Aucune donnée disponible</div>
            <div class="text-xs mt-1">efiActif: {{ props.efiActif ? 'défini' : 'non défini' }} | Longueur: {{
              props.efiActif?.length || 0 }}</div>
          </td>
        </tr>
        <tr v-for="data, index in props.efiActif" :key="index" :class="[
          data.ref === 'BZ' ? 'bg-gradient-to-r from-blue-100 to-indigo-100 border-t-2 border-blue-500 font-bold' : 'hover:bg-gradient-to-r hover:from-blue-50 hover:to-indigo-50',
          'transition-all duration-300 group transform hover:scale-[1.01] hover:shadow-md'
        ]">
          <td class="px-6 py-4 whitespace-nowrap">
            <div :class="[
              'text-sm font-mono',
              data.ref === 'BZ' ? 'font-extrabold text-blue-900' : 'font-bold text-gray-900 group-hover:text-blue-700'
            ]">{{ data.ref }}</div>
          </td>
          <td class="px-6 py-4">
            <div :class="[
              'text-sm max-w-xs truncate',
              data.ref === 'BZ' ? 'font-bold text-blue-900' : 'text-gray-900 group-hover:text-blue-700'
            ]" :title="data.libelle">{{ data.libelle }}</div>
          </td>
          <td class="px-6 py-4 whitespace-nowrap text-right">
            <div :class="[
              'text-sm font-mono',
              data.ref === 'BZ' ? 'font-bold text-blue-900' : 'text-gray-900 group-hover:text-blue-700'
            ]">{{ formatAmount(data.brut_solde_n) }}</div>
          </td>
          <td class="px-6 py-4 whitespace-nowrap text-right">
            <div :class="[
              'text-sm font-mono',
              data.ref === 'BZ' ? 'font-bold text-blue-900' : 'text-gray-900 group-hover:text-blue-700'
            ]">{{ formatAmount(data.amor_solde_n) }}</div>
          </td>
          <td class="px-6 py-4 whitespace-nowrap text-right">
            <div :class="[
              'text-sm font-mono',
              data.ref === 'BZ' ? 'font-extrabold text-blue-900' : 'font-semibold text-gray-900 group-hover:text-blue-700'
            ]">{{ formatAmount(data.net_solde_n) }}</div>
          </td>
          <td class="px-6 py-4 whitespace-nowrap text-right">
            <div :class="[
              'text-sm font-mono',
              data.ref === 'BZ' ? 'font-bold text-blue-900' : 'text-gray-900 group-hover:text-blue-700'
            ]">{{ formatAmount(data.net_solde_n1) }}</div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
