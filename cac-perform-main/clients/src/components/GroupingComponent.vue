<script setup>
import { ref, h, onMounted, inject } from 'vue';
import GroupingInitial from './GroupingInitial.vue';
import { useNotyf } from '@/composables/useNotyf';
const notif = useNotyf()
const props = defineProps(['data'])
const axios = inject('axios')
const selectedValue = ref('')
const componentKey = ref('')
const renderComponent = ref()

// Recuperer l'id mission dans l'URL
const id_mission = window.location.pathname.split('/')[2]

onMounted(()=>{
    console.log('📊 GroupingComponent - Données reçues:', props.data)
    // Afficher 'init' par défaut
    if (props.data && props.data.grouping) {
        showComp('init');
    }
})

function showComp(type) {
    let vnode;
    selectedValue.value = type

    if (type === 'init') {
        const subProps = {
            grouping: props.data.grouping,
            annee_auditee: props.data.annee_auditee
        }
        vnode = h(GroupingInitial, subProps)
    }
    renderComponent.value = vnode;
    componentKey.value = type;
}

async function downloadGrouping() {
    const isTelechargeable = props.data.grouping[0]
    if (isTelechargeable.mat_sign) {
        const response = await axios.get(`/mission/download_grouping/${id_mission}`, {responseType:'blob'})
        if (response.data) {
            const url = window.URL.createObjectURL(new Blob([response.data]))
            const link = document.createElement('a')
            link.href = url

            link.setAttribute('download', 'grouping.xlsx')

            document.body.appendChild(link)
            link.click()

            window.URL.revokeObjectURL(url)
        } else {
            console.error('Erreur lors du téléchargement du fichier');
            notif.trigger('Erreur lors du téléchargement du fichier', 'error')
        }
    } else {
        notif.trigger('Impossible de télécharger car le grouping est incomplet', 'error')
    }
}
</script>

<template>
    <div class="h-full w-full flex flex-col space-y-2 overflow-auto">
        <div class="min-h-10 flex space-x-3 px-4 pt-2 items-center">
            <button class="w-[250px] h-8 bg-blue-ycube text-white rounded-md shadow-md" :class="{'bg-green-ycube transition-all ease-in-out duration-300': selectedValue === 'init'}" @click="showComp('init')">Grouping Initial</button>
            <button class="w-[250px] h-8 bg-blue-ycube text-white rounded-md shadow-md" @click="downloadGrouping">Télécharger le grouping</button>
        </div>

        <!--  -->
        <div class="flex-auto flex flex-col overflow-visible">
            <div class="w-full h-full flex flex-col overflow-visible">
                <component :is="renderComponent" :key="componentKey" />
            </div>
        </div>
    </div>
</template>
