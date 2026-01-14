<script setup>
import { ref, inject, onMounted } from 'vue';
const props = defineProps(['grouping', 'annee_auditee'])
const axios = inject('axios')

const isSignificant = ref(false);
const groupings = ref([])
const expandedRows = ref(new Set())
// Recuperer l'id mission dans l'URL
const id_mission = window.location.pathname.split('/')[2]

onMounted(async()=>{
    groupings.value = props.grouping;
    console.log('📊 GroupingInitial - Données reçues:', groupings.value);
    console.log('  - Nombre de groupes:', groupings.value?.length || 0);
    if (groupings.value && groupings.value.length > 0) {
        const groupes_avec_comptes = groupings.value.filter(g => hasComptes(g));
        console.log('  - Groupes avec comptes:', groupes_avec_comptes.length);
        console.log('  - Exemple de groupe:', groupings.value[0]);
        if (groupings.value[0]) {
            console.log('  - Premier groupe a des comptes?', hasComptes(groupings.value[0]));
            console.log('  - Comptes du premier groupe:', groupings.value[0].comptes || groupings.value[0].comptes_detaille || []);
        }
    }
    await showSignificantGrouping();
})

async function showSignificantGrouping() {
    const result = await axios.get(`/mission/make_final/${id_mission}`)
    console.log(result)
    const verifyResult = result.data.grouping[0]
    if (verifyResult.mat_sign) {
        isSignificant.value = true
        groupings.value = result.data.grouping

    }
}

function toggleRow(index) {
    if (expandedRows.value.has(index)) {
        expandedRows.value.delete(index)
    } else {
        expandedRows.value.add(index)
        // Faire défiler vers la ligne expandée après un court délai pour permettre au DOM de se mettre à jour
        setTimeout(() => {
            // Trouver la ligne du tableau correspondant à l'index
            const rowElement = document.querySelector(`[data-row-index="${index}"]`)
            if (rowElement) {
                // Faire défiler vers la ligne en la centrant dans la vue
                rowElement.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'center',
                    inline: 'nearest'
                })
            }
        }, 100)
    }
}

function hasComptes(data) {
    // Vérifier si le groupe a des comptes détaillés (comptes ou comptes_detaille)
    const comptes = data.comptes || data.comptes_detaille || []
    return Array.isArray(comptes) && comptes.length > 0
}
</script>

<template>
    <!-- Tableau grouping principal -->
    <h3 class="pt-5 pb-1 pl-0 text-xl font-semibold uppercase tracking-wider">Tableau des clients CAC</h3>
    <div class="overflow-auto rounded-xl shadow-xl bg-white border border-gray-100 max-h-[calc(100vh-200px)]">
        <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gradient-to-r from-blue-ycube via-blue-ycube-1 to-blue-ycube-3">
                <tr>
                    <th class="px-4 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider w-12"></th>
                    <th class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider">#</th>
                    <th class="px-6 py-4 text-left text-xs font-semibold text-white uppercase tracking-wider">Intitulé</th>
                    <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">{{ props.annee_auditee }}</th>
                    <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">{{ parseInt(props.annee_auditee) - 1 }}</th>
                    <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">Variation</th>
                    <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">Variation %</th>
                    <th v-if="isSignificant" class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider">Quantitatif</th>
                    <th v-if="isSignificant" class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider">Qualitatif</th>
                    <th v-if="isSignificant" class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider">Significativité</th>
                </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
                <template v-for="(data, index) in groupings" :key="index">
                    <tr :data-row-index="index" class="hover:bg-gradient-to-r hover:from-blue-50 hover:to-indigo-50 transition-all duration-300 group transform hover:scale-[1.01] hover:shadow-md">
                        <td class="px-4 py-4 whitespace-nowrap text-center">
                            <button 
                                v-if="hasComptes(data)" 
                                @click="toggleRow(index)" 
                                class="p-1 rounded-md hover:bg-blue-100 transition-colors duration-200"
                                :title="expandedRows.has(index) ? 'Réduire' : 'Voir le détail'"
                            >
                                <svg 
                                    class="w-5 h-5 text-blue-600 transition-transform duration-200" 
                                    :class="{ 'rotate-90': expandedRows.has(index) }"
                                    fill="none" 
                                    stroke="currentColor" 
                                    viewBox="0 0 24 24"
                                >
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
                                </svg>
                            </button>
                            <span v-else class="w-5 h-5 inline-block"></span>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-center">
                            <div class="flex items-center justify-center">
                                <div class="flex-shrink-0 h-8 w-8  rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform duration-200">
                                    <span class="text-xs font-extrabold text-black">{{ data.compte }}</span>
                                </div>
                            </div>
                        </td>
                        <td class="px-6 py-4">
                            <div class="text-sm text-gray-900 max-w-xs truncate group-hover:text-blue-700 transition-colors duration-200" :title="data.libelle">{{ data.libelle }}</div>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-right">
                            <div class="text-sm font-mono text-gray-900 group-hover:text-blue-700 transition-colors duration-200">{{ data.solde_n.toLocaleString() }}</div>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-right">
                            <div class="text-sm font-mono text-gray-900 group-hover:text-blue-700 transition-colors duration-200">{{ data.solde_n1.toLocaleString() }}</div>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-right">
                            <div class="flex items-center justify-end">
                                <div class="text-sm font-mono font-semibold transform group-hover:scale-105 transition-all duration-200" :class="data.variation >= 0 ? 'text-emerald-600' : 'text-red-600'">
                                    {{ data.variation.toLocaleString() }}
                                </div>
                                <div class="ml-2 w-2 h-2 rounded-full" :class="data.variation >= 0 ? 'bg-emerald-500' : 'bg-red-500'"></div>
                            </div>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-right">
                            <div class="flex items-center justify-end">
                                <div class="text-sm font-mono font-semibold transform group-hover:scale-105 transition-all duration-200" :class="data.variation_percent >= 0 ? 'text-emerald-600' : 'text-red-600'">
                                    {{ Number.isInteger(data.variation_percent) ? data.variation_percent : data.variation_percent.toFixed(2) }}%
                                </div>
                                <svg v-if="Math.abs(data.variation_percent) > 20" class="w-4 h-4 ml-1 text-orange-500 animate-pulse" fill="currentColor" viewBox="0 0 20 20">
                                    <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
                                </svg>
                            </div>
                        </td>
                        <td v-if="isSignificant" class="px-6 py-4 whitespace-nowrap text-center">
                            <span class="inline-flex px-3 py-1 rounded-full text-xs font-medium shadow-sm transform group-hover:scale-105 transition-all duration-200" 
                                  :class="data.materiality ? 'bg-gradient-to-r from-emerald-100 to-emerald-200 text-emerald-800 border border-emerald-300' : 'bg-gradient-to-r from-gray-100 to-gray-200 text-gray-800 border border-gray-300'">
                                <span class="w-2 h-2 rounded-full mr-2" :class="data.materiality ? 'bg-emerald-500' : 'bg-gray-500'"></span>
                                {{ data.materiality ? 'Oui' : 'Non' }}
                            </span>
                        </td>
                        <td v-if="isSignificant" class="px-6 py-4 whitespace-nowrap text-center">
                            <span class="inline-flex px-3 py-1 rounded-full text-xs font-medium shadow-sm transform group-hover:scale-105 transition-all duration-200" 
                                  :class="data.significant ? 'bg-gradient-to-r from-blue-100 to-blue-200 text-blue-800 border border-blue-300' : 'bg-gradient-to-r from-gray-100 to-gray-200 text-gray-800 border border-gray-300'">
                                <span class="w-2 h-2 rounded-full mr-2" :class="data.significant ? 'bg-blue-500' : 'bg-gray-500'"></span>
                                {{ data.significant ? 'Oui' : 'Non' }}
                            </span>
                        </td>
                        <td v-if="isSignificant" class="px-6 py-4 whitespace-nowrap text-center">
                            <span class="inline-flex px-3 py-1 rounded-full text-xs font-medium shadow-sm transform group-hover:scale-105 transition-all duration-200" 
                                  :class="data.mat_sign ? 'bg-gradient-to-r from-red-100 to-red-200 text-red-800 border border-red-300' : 'bg-gradient-to-r from-emerald-100 to-emerald-200 text-emerald-800 border border-emerald-300'">
                                <span class="w-2 h-2 rounded-full mr-2" :class="data.mat_sign ? 'bg-red-500' : 'bg-emerald-500'"></span>
                                {{ data.mat_sign ? 'Significatif' : 'Non significatif' }}
                            </span>
                        </td>
                    </tr>
                    <!-- Ligne expandable avec le détail des comptes -->
                    <tr v-if="expandedRows.has(index) && hasComptes(data)">
                        <td colspan="100%" class="px-6 py-4 bg-gray-50">
                            <div class="border-l-4 border-blue-500 pl-4">
                                <div class="flex items-center mb-3">
                                    <svg class="w-5 h-5 text-blue-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                                    </svg>
                                    <h4 class="text-sm font-semibold text-gray-900">Détail des comptes du groupe {{ data.compte }}</h4>
                                    <span class="ml-2 text-xs text-gray-500">({{ (data.comptes || data.comptes_detaille || []).length }} compte(s))</span>
                                </div>
                                
                                <div class="overflow-hidden rounded-lg border border-gray-200 bg-white">
                                    <table class="min-w-full divide-y divide-gray-200">
                                        <thead class="bg-gray-50">
                                            <tr>
                                                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Compte</th>
                                                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Libellé</th>
                                                <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">{{ props.annee_auditee }}</th>
                                                <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">{{ parseInt(props.annee_auditee) - 1 }}</th>
                                                <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Variation</th>
                                            </tr>
                                        </thead>
                                        <tbody class="bg-white divide-y divide-gray-200">
                                            <tr v-for="(compte, cIndex) in (data.comptes || data.comptes_detaille || [])" :key="cIndex" class="hover:bg-gray-50 transition-colors duration-150">
                                                <td class="px-4 py-3 whitespace-nowrap text-sm font-mono font-medium text-gray-900">{{ compte.numero_compte }}</td>
                                                <td class="px-4 py-3 text-sm text-gray-900 max-w-xs truncate" :title="compte.libelle">{{ compte.libelle }}</td>
                                                <td class="px-4 py-3 whitespace-nowrap text-sm font-mono text-gray-900 text-right">{{ (compte.solde_n || 0).toLocaleString() }}</td>
                                                <td class="px-4 py-3 whitespace-nowrap text-sm font-mono text-gray-900 text-right">{{ (compte.solde_n1 || 0).toLocaleString() }}</td>
                                                <td class="px-4 py-3 whitespace-nowrap text-sm font-mono font-semibold text-right" :class="(compte.variation || 0) >= 0 ? 'text-emerald-600' : 'text-red-600'">
                                                    {{ (compte.variation || 0).toLocaleString() }}
                                                </td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </td>
                    </tr>
                </template>
            </tbody>
        </table>
    </div>
</template>
