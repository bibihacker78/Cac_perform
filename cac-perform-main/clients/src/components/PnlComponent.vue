<script setup>
import { onMounted } from 'vue';

const props = defineProps(['efiPnl', 'annee_auditee'])

function formatNumber(value) {
  if (value === null || value === undefined || value === '') return '';
  const num = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(num)) return '';
  return new Intl.NumberFormat('fr-FR', { minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(num);
}

onMounted(() => {
  console.log('📊 PnlComponent - Données reçues:');
  console.log('  - efiPnl:', props.efiPnl);
  console.log('  - annee_auditee:', props.annee_auditee);
  console.log('  - Longueur:', props.efiPnl?.length);
})
</script>

<template>
    <!-- Tableau grouping principal -->
    <h3 class="pt-5 pb-1 pl-0 text-xl font-semibold uppercase tracking-wider">Compte de résultat</h3>
    <div class="rounded-xl shadow-xl bg-white border border-gray-100 overflow-x-auto overflow-y-visible">
        <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gradient-to-r from-blue-ycube to-blue-ycube-3">
                <tr>
                    <th class="px-6 py-4 text-left text-xs font-semibold text-white uppercase tracking-wider" colspan="2"></th>
                    <th class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider">EXERCICE AU 31/12/{{ props.annee_auditee }}</th>
                    <th class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider">EXERCICE AU 31/12/{{ parseInt(props.annee_auditee) - 1 }}</th>
                </tr>
                <tr>
                    <th class="px-6 py-4 text-left text-xs font-semibold text-white uppercase tracking-wider">REF</th>
                    <th class="px-6 py-4 text-left text-xs font-semibold text-white uppercase tracking-wider">Intitulé</th>
                    <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">NET</th>
                    <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">NET</th>
                </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
                <tr v-if="!props.efiPnl || props.efiPnl.length === 0">
                    <td colspan="4" class="px-6 py-4 text-center text-gray-500">
                        <div class="text-sm">Aucune donnée disponible</div>
                        <div class="text-xs mt-1">efiPnl: {{ props.efiPnl ? 'défini' : 'non défini' }} | Longueur: {{ props.efiPnl?.length || 0 }}</div>
                    </td>
                </tr>
                <tr v-for="data,index in props.efiPnl" :key="`pnl-${index}-${data.ref}`" 
                    :class="[
                      'hover:bg-gradient-to-r hover:from-blue-50 hover:to-indigo-50',
                      'transition-all duration-300 group transform hover:scale-[1.01] hover:shadow-md'
                    ]">
                    <td class="px-6 py-4 whitespace-nowrap">
                        <div class="text-sm font-mono font-bold text-gray-900 group-hover:text-blue-700">{{ data.ref }}</div>
                    </td>
                    <td class="px-6 py-4">
                        <div class="text-sm text-gray-900 max-w-xs truncate group-hover:text-blue-700" :title="data.libelle">{{ data.libelle }}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-right">
                        <div class="text-sm font-mono font-semibold text-gray-900 group-hover:text-blue-700">{{ formatNumber(data.net_solde_n) }}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-right">
                        <div class="text-sm font-mono text-gray-900 group-hover:text-blue-700">{{ formatNumber(data.net_solde_n1) }}</div>
                    </td>
                </tr>
            </tbody>
        </table>
    </div>
</template>
