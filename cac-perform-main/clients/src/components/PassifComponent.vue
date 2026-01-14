<script setup>
import { onMounted } from 'vue';

const props = defineProps(['efiPassif', 'annee_auditee'])

function formatNumber(value) {
  if (value === null || value === undefined || value === '') return '';
  const num = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(num)) return '';
  return new Intl.NumberFormat('fr-FR', { minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(num);
}

onMounted(() => {
  console.log('📊 PassifComponent - Données reçues:');
  console.log('  - efiPassif:', props.efiPassif);
  console.log('  - annee_auditee:', props.annee_auditee);
  console.log('  - Type efiPassif:', typeof props.efiPassif);
  console.log('  - Est un tableau?', Array.isArray(props.efiPassif));
  console.log('  - Longueur:', props.efiPassif?.length);
  if (props.efiPassif && props.efiPassif.length > 0) {
    console.log('  - Premier élément:', props.efiPassif[0]);
    console.log('  - Toutes les refs:', props.efiPassif.map(x => x.ref));
    console.log('  - Refs manquantes (si < 28):', props.efiPassif.length < 28 ? 'OUI' : 'NON');
    console.log('  - Nombre attendu: 28 lignes');
    console.log('  - Nombre reçu:', props.efiPassif.length);
  }
  
  // Vérifier combien de lignes <tr> sont rendues dans le DOM
  setTimeout(() => {
    const tbody = document.querySelector('tbody');
    if (tbody) {
      const rows = tbody.querySelectorAll('tr');
      console.log('📊 PassifComponent - Lignes <tr> dans le DOM:', rows.length);
      console.log('  - Toutes les refs dans le DOM:', Array.from(rows).map(row => {
        const refCell = row.querySelector('td:first-child');
        return refCell ? refCell.textContent.trim() : 'N/A';
      }));
    }
  }, 100);
})
</script>

<template>
    <!-- Tableau grouping principal -->
    <h3 class="pt-5 pb-1 pl-0 text-xl font-semibold uppercase tracking-wider">Bilan Passif</h3>
    <div class="rounded-xl shadow-xl bg-white border border-gray-100 overflow-x-auto overflow-y-visible">
        <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gradient-to-r from-blue-ycube to-blue-ycube-3">
                <tr>
                    <th class="px-6 py-4 text-left text-xs font-semibold text-white uppercase tracking-wider" colspan="3"></th>
                    <th class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider">EXERCICE AU 31/12/{{ props.annee_auditee }}</th>
                    <th class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider">EXERCICE AU 31/12/{{ parseInt(props.annee_auditee) - 1 }}</th>
                </tr>
                <tr>
                    <th class="px-6 py-4 text-left text-xs font-semibold text-white uppercase tracking-wider">REF</th>
                    <th class="px-6 py-4 text-left text-xs font-semibold text-white uppercase tracking-wider">PASSIF</th>
                    <th class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider">Note</th>
                    <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">NET</th>
                    <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">NET</th>
                </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
                <tr v-if="!props.efiPassif || props.efiPassif.length === 0">
                    <td colspan="5" class="px-6 py-4 text-center text-gray-500">
                        <div class="text-sm">Aucune donnée disponible</div>
                        <div class="text-xs mt-1">efiPassif: {{ props.efiPassif ? 'défini' : 'non défini' }} | Longueur: {{ props.efiPassif?.length || 0 }}</div>
                    </td>
                </tr>
                <tr v-for="data,index in props.efiPassif" :key="`passif-${index}-${data.ref}`" 
                    :class="[
                      ['CP', 'DD', 'DF', 'DP', 'DT', 'DZ'].includes(data.ref) 
                        ? 'bg-gradient-to-r from-blue-100 to-indigo-100 border-t-2 border-blue-500 font-bold' 
                        : 'hover:bg-gradient-to-r hover:from-blue-50 hover:to-indigo-50',
                      'transition-all duration-300 group transform hover:scale-[1.01] hover:shadow-md'
                    ]">
                    <td class="px-6 py-4 whitespace-nowrap">
                        <div :class="[
                          'text-sm font-mono',
                          ['CP', 'DD', 'DF', 'DP', 'DT', 'DZ'].includes(data.ref) 
                            ? 'font-extrabold text-blue-900' 
                            : 'font-bold text-gray-900 group-hover:text-blue-700'
                        ]">{{ data.ref }}</div>
                    </td>
                    <td class="px-6 py-4">
                        <div :class="[
                          'text-sm max-w-xs',
                          ['CP', 'DD', 'DF', 'DP', 'DT', 'DZ'].includes(data.ref) 
                            ? 'font-bold text-blue-900' 
                            : 'text-gray-900 group-hover:text-blue-700'
                        ]" :title="data.libelle">{{ data.libelle }}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-center">
                        <div :class="[
                          'text-sm',
                          ['CP', 'DD', 'DF', 'DP', 'DT', 'DZ'].includes(data.ref) 
                            ? 'font-bold text-blue-900' 
                            : 'text-gray-600'
                        ]">{{ data.note || '' }}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-right">
                        <div :class="[
                          'text-sm font-mono',
                          ['CP', 'DD', 'DF', 'DP', 'DT', 'DZ'].includes(data.ref) 
                            ? 'font-extrabold text-blue-900' 
                            : 'font-semibold text-gray-900 group-hover:text-blue-700'
                        ]">{{ formatNumber(data.net_solde_n) }}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-right">
                        <div :class="[
                          'text-sm font-mono',
                          ['CP', 'DD', 'DF', 'DP', 'DT', 'DZ'].includes(data.ref) 
                            ? 'font-bold text-blue-900' 
                            : 'text-gray-900 group-hover:text-blue-700'
                        ]">{{ formatNumber(data.net_solde_n1) }}</div>
                    </td>
                </tr>
            </tbody>
        </table>
    </div>
</template>
