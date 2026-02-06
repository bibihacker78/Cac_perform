<script setup>
import { ref, h, inject, onMounted, computed, watch, nextTick } from 'vue';
import { useRoute } from 'vue-router';
import GroupingComponent from '@/components/GroupingComponent.vue';
import EfiComponent from '@/components/EfiComponent.vue';
import router from "@/router";


const axios = inject('axios');
const route = useRoute();

const props = defineProps(['missionId', 'grouping']);

const componentKey = ref('');
const renderComponent = ref();
const infoMission = ref();
const selectBtn = ref(null);              // <- remplace activeStep

// Recuperer l'id mission dans l'URL
const id_mission = window.location.pathname.split('/')[2]

const groupingData = ref(null)
const anneeAuditee = ref(null)

function normalizeYear(value) {
  const year = parseInt(value, 10)
  return Number.isNaN(year) ? null : year
}

const effectiveYear = computed(() => {
  return (
    normalizeYear(anneeAuditee.value) ??
    normalizeYear(route.query?.annee) ??
    normalizeYear(infoMission.value?.annee_auditee?.[0] ?? infoMission.value?.annee_auditee)
  );
});

async function loadGrouping() {
  try {
    const res = await axios.get(`/mission/make_final/${id_mission}`);

    console.log("API DATA 👉", res.data);

    groupingData.value = res.data?.grouping
      ? { grouping: res.data.grouping }
      : null;

    anneeAuditee.value = normalizeYear(
      res.data?.annee_auditee ??
      infoMission.value?.annee_auditee?.[0]
    );
  } catch (err) {
    console.error("Erreur chargement grouping", err);
  }
}

/* === Nouveaux états pour les 3 features === */
const revueAnalytique = ref([]);
const coherenceReport = ref(null);
const selectedYearCoherence = ref(null);
const selectedControlType = ref('arithmetique'); // 'arithmetique' ou 'vraisemblance'
const viewMode = ref('table'); // 'table', 'cards', 'graph', 'compact'
const intangibiliteReport = ref(null);
const classementBilanReport = ref(null);
const etatsFinanciersReport = ref(null);
const materialiteReport = ref(null);
const analyseQuantitativeReport = ref(null);

// Variables pour la détermination du seuil de signification
const listBenchmark = ref([
  {
    id: "ebitda",
    name: "EBITDA",
    balance_value: null,
    factor: null,
    amount_based_on_factor: null,
    performance_materiality: null,
    thresold: null,
    text: "Fourchette de facteur attendue : 3-5 % (peut aller jusqu'à 5 % compte tenu de la taille de l'entité). Consultez le guide de matérialité pour plus de détails."
  },
  {
    id: "expenses",
    name: "Expenses",
    balance_value: null,
    factor: null,
    amount_based_on_factor: null,
    performance_materiality: null,
    thresold: null,
    text: "Fourchette de facteur attendue : 3-5 % (peut aller jusqu'à 5 % compte tenu de la taille de l'entité). Consultez le guide de matérialité pour plus de détails."
  },
  {
    id: "profit_before_tax",
    name: "Profit Before Tax",
    balance_value: null,
    factor: null,
    amount_based_on_factor: null,
    performance_materiality: null,
    thresold: null,
    text: "Fourchette de facteur attendue : 5-10%. Voir le guide de matérialité pour plus de détails."
  },
  {
    id: "revenue",
    name: "Revenue",
    balance_value: null,
    factor: null,
    amount_based_on_factor: null,
    performance_materiality: null,
    thresold: null,
    text: "Fourchette de facteur attendue : 0,8-2 % (peut aller jusqu'à 5 % compte tenu de la taille de l'entité). Consultez le guide de matérialité pour plus de détails."
  },
  {
    id: "total_assets",
    name: "Total Assets",
    balance_value: null,
    factor: null,
    amount_based_on_factor: null,
    performance_materiality: null,
    thresold: null,
    text: "Fourchette de facteur attendue : 1-2%. Consultez le guide de matérialité pour plus de détails."
  }
]);

const listMaterialities = ref([]);
const selectedBench = ref("");
const bench = ref({
  id: "",
  balanceValue: "",
  factor: "",
  amount_based_on_factor: null,
  performance_materiality: null,
  thresold: null,
  text: ""
});

// Champs pour benchmark personnalisé (option 'Autre')
bench.value.custom_label = "";
bench.value.custom_balance = null;

const FACTOR_PERFORMANCE_MATERIALITY = 0.08;
const FACTOR_THRESHOLD = 0.05;
const analyseQualitativeReport = ref(null);
const presentationComptesSignificatifsReport = ref(null);
const revueAnalytiqueFinaleReport = ref(null);
const qualitativeResponses = ref({});
const selectedEfiTab = ref('actif');
const loading = ref(false);
const errorMsg = ref("");
const expandedRows = ref([]);

function hasBalanceValues(item) {
  if (!item || typeof item !== 'object') return false;
  const fields = ['solde_n', 'solde_n1', 'variation'];
  return fields.some((key) => {
    const val = item[key];
    if (val === null || val === undefined || val === '') return false;
    const num = Number(val);
    return !Number.isNaN(num) && num !== 0;
  });
}

function filterByBalanceRows(list) {
  if (!Array.isArray(list)) return [];
  return list.filter(hasBalanceValues);
}

// Variables réactives pour les statistiques
const qualitativeStats = ref({
  significant_accounts: 0,
  non_significant_accounts: 0,
  total_positive_responses: 0,
  average_score: 0
});

// Gestion du tooltip pour les questions
const showQuestionTooltip = ref(false);
const selectedQuestion = ref('');
const selectedQuestionText = ref('');
const tooltipPosition = ref({ x: 0, y: 0 });

/* ================================
   WORKFLOW PAR PHASES (NOUVEAU)
================================ */

// Phases + étapes
const workflowPhases = ref([
  {
    id: 1,
    label: 'Phase 1 – Planification',
    open: true,
    steps: [
      { id: 1, name: "Préparation de l’audit", key: "prep_audit", checked: false, static: true },
      { id: 2, name: "Contrôle interne", key: "controle_interne", checked: false, static: true }
    ]
  },
  {
    id: 2,
    label: 'Phase 2 – Exécution',
    open: true,
    steps: [
      { id: 3, name: "Contrôle de cohérence", key: "coherence"},
      { id: 4, name: "Contrôle d’intangibilité", key: "intang" },
      { id: 5, name: "Calcul des seuils", key: "materialite" },
      { id: 6, name: "Grouping", key: "grouping" },
      { id: 7, name: "États financiers préliminaires", key: "efi" },
      { id: 8, name: "Décision finale des comptes à tester", key: "presentation" }
    ]
  },
  {
    id: 3,
    label: 'Phase 3 – Conclusion',
    open: false,
    steps: [
      { id: 9, name: "Revue analytique finale", key: "revue", checked: false, static: false }
    ]
  }
]);

// Toggle ouverture phase
function togglePhase(phase) {
  phase.open = !phase.open;
}

// Checkbox (phase 1 & 3 uniquement)
function toggleStep(step) {
  step.checked = !step.checked;
}

// Navigation uniquement pour phase 2
function handleStepClick(step) {
  if (step.static) return;
  showComponent(step.key);
}

// Calcul progression
const allSteps = computed(() =>
  workflowPhases.value.flatMap(p => p.steps)
);

const completedSteps = computed(() =>
  allSteps.value.filter(s => s.checked).length
);

const totalSteps = computed(() =>
  allSteps.value.filter(s => s.static).length
);

const progress = computed(() => {
  if (!totalSteps.value) return 0;
  return Math.round((completedSteps.value / totalSteps.value) * 50);
});


const currentStep = ref(1); // Commencer à l'étape 1 (contrôle de cohérence)



onMounted(async () => {
  const result = (await axios.get(`/mission/affichage_infos_mission/${id_mission}`)).data.response;
  infoMission.value = typeof result === 'object' ? result : null;
  console.log("infoooo:", infoMission.value);
});

watch(
  () => infoMission.value,
  (val) => {
    if (!anneeAuditee.value) {
      anneeAuditee.value = normalizeYear(val?.annee_auditee?.[0] ?? val?.annee_auditee);
    }
  },
  { immediate: true }
);

watch(
  () => route.query?.annee,
  (val) => {
    if (!anneeAuditee.value) {
      anneeAuditee.value = normalizeYear(val);
    }
  },
  { immediate: true }
);

/* === Workflow libre - toutes les étapes accessibles === */

function getStepStatusIcon(status) {
  switch (status) {
    case "completed": return "✅";
    case "current": return "🔄";
    case "available": return "📋";
    case "locked": return "🔒";
    default: return "⏳";
  }
}

function getStepButtonClass(step) {
  const baseClass = "px-4 py-3 text-xs font-bold text-white tracking-wide rounded-md transition-all duration-300 flex items-center justify-between";

  switch (step.status) {
    case "completed":
      return `${baseClass} bg-green-600 hover:bg-green-700`;
    case "current":
      return `${baseClass} bg-blue-600 hover:bg-blue-700`;
    case "available":
      return `${baseClass} bg-blue-ycube-1 hover:bg-blue-600`;
    case "locked":
      return `${baseClass} bg-gray-400 cursor-not-allowed opacity-60`;
    default:
      return `${baseClass} bg-blue-ycube-1 hover:bg-blue-600`;
  }
}

/* === Fonctions de chargement des données === */


/* === Fonctions utilitaires === */
function toggleDetail(index) {
  const currentIndex = expandedRows.value.indexOf(index);
  if (currentIndex > -1) {
    expandedRows.value.splice(currentIndex, 1);
  } else {
    expandedRows.value.push(index);
  }
}

/* === Loaders API === */
async function loadRevueAnalytique() {
  loading.value = true; errorMsg.value = "";
  try {
    const { data } = await axios.get(`/mission/revue_analytique/${props.missionId}`);
    revueAnalytique.value = filterByBalanceRows(data.response || []);
  } catch (e) {
    errorMsg.value = "Échec du chargement de la revue analytique.";
    console.error(e);
  } finally {
    loading.value = false;
  }
}

async function loadCoherence() {
  loading.value = true; errorMsg.value = "";
  try {
    console.log("🔍 Tentative de chargement du contrôle de cohérence pour mission:", props.missionId);
    const { data } = await axios.get(`/mission/controle_coherence/${props.missionId}`);
    console.log("📊 Réponse reçue:", data);
    const raw = data?.data || [];

    const formatted = {};
    raw.forEach(item => {
      if (item.annee && item.rapport) {
        formatted[item.annee] = item.rapport;
      }
    });

    coherenceReport.value = formatted;

    console.log("✅ Rapport cohérence formaté:", coherenceReport.value);

    // Marquer l'étape comme complétée si des données sont présentes
    if (coherenceReport.value && Object.keys(coherenceReport.value).length > 0) {
      console.log("✅ Contrôle de cohérence chargé avec succès");
      // Initialiser l'année sélectionnée avec la première année disponible
      const years = Object.keys(coherenceReport.value).sort().reverse();
      if (years.length > 0 && !selectedYearCoherence.value) {
        selectedYearCoherence.value = years[0];
      }
    } else {
      console.log("⚠️ Aucune donnée de contrôle de cohérence trouvée");
    }
  } catch (e) {
    errorMsg.value = `Échec du chargement du contrôle de cohérence: ${e.message}`;
    console.error("❌ Erreur lors du chargement du contrôle de cohérence:", e);
    console.error("📋 Détails de l'erreur:", {
      message: e.message,
      response: e.response?.data,
      status: e.response?.status,
      missionId: props.missionId
    });
  } finally {
    loading.value = false;
  }
}

// Computed pour obtenir les années disponibles dans le rapport de cohérence
const availableYearsCoherence = computed(() => {
  if (!coherenceReport.value || typeof coherenceReport.value !== 'object') {
    return [];
  }
  return Object.keys(coherenceReport.value)
    .filter(key => !isNaN(parseInt(key))) // Filtrer seulement les clés qui sont des années
    .sort((a, b) => parseInt(b) - parseInt(a)); // Tri décroissant
});

// Computed pour obtenir le rapport filtré par année sélectionnée et type de contrôle
const filteredCoherenceReport = computed(() => {
  if (!coherenceReport.value || !selectedYearCoherence.value) {
    return null;
  }
  const yearReport = coherenceReport.value[selectedYearCoherence.value];
  if (!yearReport) {
    return null;
  }

  // Filtrer les erreurs selon le type de contrôle sélectionné
  let filteredErrors = [];
  if (yearReport.erreurs && Array.isArray(yearReport.erreurs)) {
    if (selectedControlType.value === 'arithmetique') {
      // Contrôles arithmétiques : équilibre global et erreurs arithmétiques
      filteredErrors = yearReport.erreurs.filter(e =>
        e.type === 'equilibre' || e.type === 'equilibre_global' || e.type === 'arithmetique'
      );
    } else if (selectedControlType.value === 'vraisemblance') {
      // Contrôles de vraisemblance : signe et comptes non soldés
      filteredErrors = yearReport.erreurs.filter(e =>
        e.type === 'signe' || e.type === 'compte_non_solde'
      );
    }
  }

  // Créer une copie du rapport avec les erreurs filtrées
  const filteredReport = {
    ...yearReport,
    erreurs: filteredErrors
  };

  return {
    [selectedYearCoherence.value]: filteredReport
  };
});

// Computed pour grouper les erreurs par type (pour les graphiques et statistiques)
const errorsByType = computed(() => {
  if (!filteredCoherenceReport.value || !selectedYearCoherence.value) {
    return {};
  }
  const yearReport = filteredCoherenceReport.value[selectedYearCoherence.value];
  if (!yearReport || !yearReport.erreurs) {
    return {};
  }

  const grouped = {};
  yearReport.erreurs.forEach(error => {
    const type = error.type || 'autre';
    if (!grouped[type]) {
      grouped[type] = [];
    }
    grouped[type].push(error);
  });

  return grouped;
});

// Computed pour les statistiques d'erreurs
const errorStats = computed(() => {
  if (!filteredCoherenceReport.value || !selectedYearCoherence.value) {
    return { total: 0, byType: {} };
  }
  const yearReport = filteredCoherenceReport.value[selectedYearCoherence.value];
  if (!yearReport || !yearReport.erreurs) {
    return { total: 0, byType: {} };
  }

  const stats = {
    total: yearReport.erreurs.length,
    byType: {}
  };

  yearReport.erreurs.forEach(error => {
    const type = error.type || 'autre';
    stats.byType[type] = (stats.byType[type] || 0) + 1;
  });

  return stats;
});

async function loadIntangibilite() {
  loading.value = true; errorMsg.value = "";
  try {
    console.log("🔍 Chargement du contrôle d'intangibilité pour mission:", props.missionId);
    const { data } = await axios.get(`/mission/controle_intangibilite/${props.missionId}`);
    console.log("📊 Réponse complète reçue:", data);
    console.log("📊 data.response:", data.response);
    console.log("📊 Type de data.response:", typeof data.response);
    console.log("📊 Clés de data.response:", data.response ? Object.keys(data.response) : "null");
    intangibiliteReport.value = data.response || {};
    console.log("📋 Rapport d'intangibilité:", intangibiliteReport.value);
    console.log("📋 Rapport d'intangibilité (JSON):", JSON.stringify(intangibiliteReport.value, null, 2));
    console.log("📊 Nombre de comptes:", intangibiliteReport.value?.comptes?.length || 0);
    console.log("📊 comptes existe?", 'comptes' in (intangibiliteReport.value || {}));
    console.log("📊 ecarts existe?", 'ecarts' in (intangibiliteReport.value || {}));
    // Marquer l'étape comme complétée si des données sont présentes
    if (intangibiliteReport.value && Object.keys(intangibiliteReport.value).length > 0) {
      console.log("✅ Contrôle d'intangibilité chargé avec succès");
      if (intangibiliteReport.value.comptes && intangibiliteReport.value.comptes.length > 0) {
        console.log(`✅ ${intangibiliteReport.value.comptes.length} comptes trouvés`);
      } else {
        console.warn("⚠️ Aucun compte trouvé dans la réponse");
      }
    }
  } catch (e) {
    errorMsg.value = "Échec du chargement du contrôle d'intangibilité.";
    console.error("❌ Erreur lors du chargement:", e);
    console.error("📋 Détails:", e.response?.data);
  } finally {
    loading.value = false;
  }
}

/* === Navigation === */
function showComponent(type) {
  const subProps = { data: infoMission.value };
  selectBtn.value = type;     // <- ACTIVE LA NOUVELLE SIDEBAR
  componentKey.value = type;  // <- Gère l’affichage composant

  console.log("➡️ Navigation vers composant :", type);

  // 1️⃣ Onglets historiques (Groupement & États financiers)
  if (type === "grouping") {
    renderComponent.value = null;
    loadGrouping();
    return;
  }

  if (type === "efi") {
    loadEtatsFinanciers()
      .then(() => {
        const props = {
          data: etatsFinanciersReport.value || {
            efi: { actif: [], passif: [], pnl: [] },
            annee_auditee:
              infoMission.value?.annee_auditee?.[0] ||
              new Date().getFullYear()
          }
        };

        renderComponent.value = h(EfiComponent, props);
      })
      .catch(() => {
        const emptyProps = {
          data: {
            efi: { actif: [], passif: [], pnl: [] },
            annee_auditee:
              infoMission.value?.annee_auditee?.[0] ||
              new Date().getFullYear()
          }
        };
        renderComponent.value = h(EfiComponent, emptyProps);
      });

    return;
  }

  // 2️⃣ Pour toutes les autres étapes : affichage full-page via v-if
  renderComponent.value = null;

  switch (type) {
    case "coherence":
      loadCoherence();
      break;
    case "intang":
      loadIntangibilite();
      break;
    case "classement":
      loadClassement();
      break;
    case "materialite":
      loadMaterialite();
      break;
    case "presentation":
      loadPresentationComptesSignificatifs();
      break;
    case "synthese":
      loadSynthese();
      break;
    case "revue":
      loadRevueAnalytique();
      break;
  }
}

/* === Nouvelles fonctions de chargement === */
async function loadMaterialite() {
  loading.value = true; errorMsg.value = "";
  try {
    console.log("🔍 Tentative de chargement des données de matérialité pour mission:", props.missionId);

    // Charger les données de matérialité
    const { data } = await axios.get(`/mission/materialite/${props.missionId}`);
    console.log("📊 Réponse reçue:", data);

    if (data.response && data.response.ok) {
      materialiteReport.value = data.response;
      console.log("✅ Données de matérialité chargées avec succès");
    } else {
      errorMsg.value = data.response?.message || "Aucune donnée de matérialité disponible";
      console.log("⚠️ Aucune donnée de matérialité trouvée");
    }

    // Charger les benchmarks
    await loadBenchmarks();

    // Charger la liste des matérialités
    await getListMaterialities();

  } catch (e) {
    errorMsg.value = `Échec du chargement des données de matérialité: ${e.message}`;
    console.error("❌ Erreur lors du chargement des données de matérialité:", e);
    console.error("📋 Détails de l'erreur:", {
      message: e.message,
      response: e.response?.data,
      status: e.response?.status,
      missionId: props.missionId
    });
  } finally {
    loading.value = false;
  }
}

async function loadBenchmarks() {
  try {
    const result = (await axios.get(`/mission/get_benchmarks/${props.missionId}`)).data.response;
    const _keys = Object.keys(result);

    // Remplir la variable listBenchmark avec les benchmarks
    listBenchmark.value.forEach(obj => {
      if (_keys.includes(obj.id)) {
        obj.balance_value = result[obj.id];
      }
    });
    console.log("✅ Benchmarks chargés:", listBenchmark.value);
  } catch (e) {
    console.error("❌ Erreur lors du chargement des benchmarks:", e);
  }
}

async function getListMaterialities() {
  try {
    const materialities = (await axios.get(`/mission/get_materiality/${props.missionId}`)).data.response.materiality;
    console.log("📊 Matérialités chargées:", materialities);
    listMaterialities.value = materialities || [];
  } catch (e) {
    console.error("❌ Erreur lors du chargement des matérialités:", e);
    listMaterialities.value = [];
  }
}

async function selectMaterialityBenchmark(benchmark) {
  loading.value = true; errorMsg.value = "";
  try {
    console.log("🔍 Sélection du benchmark de matérialité:", benchmark);
    const { data } = await axios.put(`/mission/validate_materiality/${props.missionId}`, {
      benchmark: benchmark
    });

    if (data.response) {
      console.log("✅ Benchmark sélectionné avec succès");
      // Recharger les données pour voir la mise à jour
      await loadMaterialite();
    } else {
      errorMsg.value = "Erreur lors de la sélection du benchmark";
    }
  } catch (e) {
    errorMsg.value = `Échec de la sélection du benchmark: ${e.message}`;
    console.error("❌ Erreur lors de la sélection du benchmark:", e);
  } finally {
    loading.value = false;
  }
}

// Fonctions pour la détermination du seuil de signification
watch(selectedBench, (newValue) => {
  bench.value.id = newValue;
  console.log('selectedBench changed ->', newValue);
  // Si 'autre' sélectionné, initialiser les champs custom et vider balanceValue
  if (newValue === 'autre') {
    bench.value.balanceValue = null;
    bench.value.text = '';
    // initialiser valeurs custom si undefined
    if (bench.value.custom_label === undefined) bench.value.custom_label = '';
    if (bench.value.custom_balance === undefined) bench.value.custom_balance = null;
  } else {
    listBenchmark.value.map(obj => {
      if (obj.id === newValue) {
        bench.value.balanceValue = obj.balance_value;
        bench.value.text = obj.text;
      }
    });
  }
  // Recalculer les montants si nécessaire
  updateSelectBenchmark();
});

// Calculer les valeurs dépendantes du facteur saisi
function updateSelectBenchmark() {
  const factor = parseFloat(bench.value.factor);
  // support custom benchmark when selected
  const balance = bench.value.id === 'autre' ? Number(bench.value.custom_balance) : bench.value.balanceValue;
  if (factor && balance) {
    // Calculer la matérialité réelle (peut être négative)
    bench.value.amount_based_on_factor = Math.round((balance * factor) / 100);
    bench.value.performance_materiality = Math.round(bench.value.amount_based_on_factor * FACTOR_PERFORMANCE_MATERIALITY);
    bench.value.thresold = Math.round(bench.value.amount_based_on_factor * FACTOR_THRESHOLD);
  }
}

// Calculer seuil de signification et enregistrer dans la BD
async function validerSeuil() {
  loading.value = true; errorMsg.value = "";
  try {
    updateSelectBenchmark();

    const field = {
      benchmark: bench.value.id,
      materiality: bench.value.amount_based_on_factor,
      performance_materiality: bench.value.performance_materiality,
      trivial_misstatements: bench.value.thresold,
      factor: bench.value.factor
    };

    // If user provided a custom benchmark, include its label and balance
    if (bench.value.id === 'autre') {
      field.custom_benchmark_label = bench.value.custom_label;
      field.custom_balance_value = bench.value.custom_balance;
    }

    console.log("🔍 Validation du seuil:", field);
    const result = (await axios.put(`/mission/save_materiality/${props.missionId}`, field)).data.response;
    console.log("📊 Résultat:", result);

    if (result === 1) {
      console.log("✅ Seuil enregistré avec succès");
      // Recharger la liste des matérialités
      await getListMaterialities();
      // Réinitialiser le formulaire
      selectedBench.value = "";
      bench.value = {
        id: "",
        balanceValue: "",
        factor: "",
        amount_based_on_factor: null,
        performance_materiality: null,
        thresold: null,
        text: "",
        custom_label: "",
        custom_balance: null
      };
    } else {
      errorMsg.value = "Veuillez réessayer";
    }
  } catch (e) {
    errorMsg.value = `Échec de la validation du seuil: ${e.message}`;
    console.error("❌ Erreur lors de la validation du seuil:", e);
  } finally {
    loading.value = false;
  }
}

async function applySeuil(benchmark) {
  loading.value = true;
  errorMsg.value = "";

  try {
    console.log("🔍 Application du seuil:", benchmark);

    const field = { benchmark };
    const response = await axios.put(
      `/mission/validate_materiality/${props.missionId}`,
      field
    );

    // ✅ validate_materiality OK
    if (response.status === 200) {

      const res = await axios.put(
        `/mission/quantitative_analysis/${props.missionId}`
      );

      console.log("✅ Seuil appliqué au grouping");
      console.log("📊 Lignes modifiées:", res.data.response);

      // même si 0 → ce n’est PAS une erreur
      errorMsg.value = "";

    } else {
      errorMsg.value = "Impossible de valider le seuil de matérialité";
    }

  } catch (e) {
    errorMsg.value = `Erreur lors de l'application du seuil`;
    console.error("❌ Erreur:", e);
  } finally {
    loading.value = false;
  }
}


async function loadQuantitatif() {
  loading.value = true; errorMsg.value = "";
  try {
    const { data } = await axios.get(`/mission/analyse_quantitative/${props.missionId}`);
    analyseQuantitativeReport.value = data.response ?? data ?? {};
    if (analyseQuantitativeReport.value?.analyse) {
      analyseQuantitativeReport.value.analyse = filterByBalanceRows(analyseQuantitativeReport.value.analyse);
    }
    console.log("loadQuantitatiffff:", analyseQuantitativeReport.value);
    
  } catch (e) {
    errorMsg.value = "Échec du chargement de l'analyse quantitative.";
    console.error(e);
  } finally {
    loading.value = false;
  }
}

async function loadQualitatif() {
  loading.value = true; errorMsg.value = "";
  try {
    const { data } = await axios.get(`/mission/analyse_qualitative/${props.missionId}`);
    analyseQualitativeReport.value = data.response ?? data ?? {};
    if (analyseQualitativeReport.value?.analyse) {
      analyseQualitativeReport.value.analyse = filterByBalanceRows(analyseQualitativeReport.value.analyse);
    }
    console.log("loadQualitatiiiiif:", analyseQualitativeReport.value);
    // Initialiser les réponses (même si vides)
    if (analyseQualitativeReport.value && analyseQualitativeReport.value.analyse) {
      const responses = {};
      analyseQualitativeReport.value.analyse.forEach(item => {
        responses[item.compte] = {};
        // Initialiser toutes les questions Q1-Q8
        for (let q = 1; q <= 8; q++) {
          const questionId = `Q${q}`;
          responses[item.compte][questionId] = item.responses_detail.find(r => r.question_id === questionId)?.response || false;
        }
      });
      qualitativeResponses.value = responses;

      // Recalculer tous les statuts avec les réponses chargées
      analyseQualitativeReport.value.analyse.forEach(item => {
        updateQualitativeStatus(item.compte);
      });

      // Initialiser les statistiques si elles n'existent pas
      if (!analyseQualitativeReport.value.statistics) {
        analyseQualitativeReport.value.statistics = {
          significant_accounts: 0,
          non_significant_accounts: 0,
          total_positive_responses: 0,
          average_score: 0
        };
      }

      // Recalculer les statistiques globales
      await updateQualitativeStatistics();
    }

    // Marquer l'étape comme complétée si des données sont présentes
    if (analyseQualitativeReport.value && analyseQualitativeReport.value.ok) {
      console.log("✅ Analyse qualitative chargée avec succès");
    }
  } catch (e) {
    errorMsg.value = "Échec du chargement de l'analyse qualitative.";
    console.error("❌ Erreur lors du chargement de l'analyse qualitative:", e);
  } finally {
    loading.value = false;
  }
}

async function loadSynthese() {
  loading.value = true; errorMsg.value = "";
  try {
    const { data } = await axios.get(`/mission/synthese_significatifs/${props.missionId}`);
    // Traiter les données de synthèse
    console.log("Données de synthèse:", data);
  } catch (e) {
    errorMsg.value = "Échec du chargement de la synthèse.";
    console.error(e);
  } finally {
    loading.value = false;
  }
}

async function loadClassement() {
  loading.value = true; errorMsg.value = "";
  try {
    const { data } = await axios.get(`/mission/classement_bilan/${props.missionId}`);
    classementBilanReport.value = data.response || {};

    // Forcer la réinitialisation des filtres au chargement
    resetFilters();

    // Marquer l'étape comme complétée si des données sont présentes
    if (classementBilanReport.value && classementBilanReport.value.ok) {
      console.log("✅ Classement du bilan chargé avec succès");
    }
  } catch (e) {
    errorMsg.value = "Échec du chargement du classement.";
    console.error(e);
  } finally {
    loading.value = false;
  }
}

async function loadEtatsFinanciers() {
  loading.value = true; errorMsg.value = "";
  try {
    const { data } = await axios.get(`/mission/etats_financiers_preliminaires/${props.missionId}`);
    etatsFinanciersReport.value = data.response || {};
    const rawYear = etatsFinanciersReport.value?.annee_auditee;
    let normalizedYear = normalizeYear(rawYear);
    if (normalizedYear !== null && normalizedYear < 100) {
      normalizedYear = null;
    }
    etatsFinanciersReport.value.annee_auditee =
      normalizedYear ?? effectiveYear.value ?? etatsFinanciersReport.value?.annee_auditee;
    console.log('📊 loadEtatsFinanciers - Données chargées:', etatsFinanciersReport.value);
    console.log('  - Type:', typeof etatsFinanciersReport.value);
    console.log('  - efi existe?', etatsFinanciersReport.value?.efi ? 'oui' : 'non');
    console.log('  - actif existe?', etatsFinanciersReport.value?.efi?.actif ? 'oui' : 'non');
    console.log('  - actif longueur:', etatsFinanciersReport.value?.efi?.actif?.length || 0);
    console.log('  - passif existe?', etatsFinanciersReport.value?.efi?.passif ? 'oui' : 'non');
    console.log('  - passif longueur:', etatsFinanciersReport.value?.efi?.passif?.length || 0);
    console.log('  - annee_auditee:', etatsFinanciersReport.value?.annee_auditee);
    if (etatsFinanciersReport.value?.efi?.actif && etatsFinanciersReport.value.efi.actif.length > 0) {
      console.log('  - Premier élément actif:', etatsFinanciersReport.value.efi.actif[0]);
    }
    if (etatsFinanciersReport.value?.efi?.passif && etatsFinanciersReport.value.efi.passif.length > 0) {
      console.log('  - Premier élément passif:', etatsFinanciersReport.value.efi.passif[0]);
      console.log('  - Toutes les refs passif reçues:', etatsFinanciersReport.value.efi.passif.map(x => x.ref));
      console.log('  - Nombre attendu: 28 lignes');
      console.log('  - Nombre reçu:', etatsFinanciersReport.value.efi.passif.length);
    }
  } catch (e) {
    errorMsg.value = "Échec du chargement des états financiers.";
    console.error('❌ Erreur loadEtatsFinanciers:', e);
    console.error('❌ Détails:', e.response?.data);
  } finally {
    loading.value = false;
  }
}

async function loadAnalyseQuantitative() {
  return await loadQuantitatif();
}

async function loadAnalyseQualitative() {
  return await loadQualitatif();
}

function back() {
  router.go(-1);
}

// Variables réactives pour les filtres et la recherche du tableau "Variation des comptes par rubrique"
const searchQuery = ref('');
const natureFilter = ref('');
const variationFilter = ref('');
const sortField = ref('');
const sortDirection = ref('asc');

// Fonctions pour les fonctionnalités UX avancées du tableau
function sortBy(field) {
  if (sortField.value === field) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortField.value = field
    sortDirection.value = 'asc'
  }
}

function resetFilters() {
  searchQuery.value = '';
  natureFilter.value = '';
  variationFilter.value = '';
  sortField.value = '';
  sortDirection.value = 'asc';
}

async function reloadClassement() {
  resetFilters();
  await loadClassement();
}

// Computed pour les données filtrées et triées
const filteredData = computed(() => {
  if (!classementBilanReport.value?.classement) return []

  let data = [...classementBilanReport.value.classement]

  // Filtrage par recherche
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    data = data.filter(item =>
      item.compte.toLowerCase().includes(query) ||
      item.libelle.toLowerCase().includes(query)
    )
  }

  // Filtrage par nature
  if (natureFilter.value) {
    data = data.filter(item => item.nature === natureFilter.value)
  }

  // Filtrage par variation
  if (variationFilter.value) {
    switch (variationFilter.value) {
      case 'positive':
        data = data.filter(item => item.variation_percent > 0)
        break
      case 'negative':
        data = data.filter(item => item.variation_percent < 0)
        break
      case 'high':
        data = data.filter(item => Math.abs(item.variation_percent) > 20)
        break
    }
  }

  // Tri
  if (sortField.value) {
    data.sort((a, b) => {
      let aVal = a[sortField.value]
      let bVal = b[sortField.value]

      // Gestion des types
      if (typeof aVal === 'string') {
        aVal = aVal.toLowerCase()
        bVal = bVal.toLowerCase()
      }

      if (sortDirection.value === 'asc') {
        return aVal > bVal ? 1 : -1
      } else {
        return aVal < bVal ? 1 : -1
      }
    })
  }

  return data
})

// Fonctions pour l'analyse qualitative
async function handleQualitativeResponse(compte, questionId, checked) {
  if (!qualitativeResponses.value[compte]) {
    qualitativeResponses.value[compte] = {};
  }
  qualitativeResponses.value[compte][questionId] = checked;

  // Recalculer le statut en temps réel
  await updateQualitativeStatus(compte);
}

// Fonction pour calculer le statut en temps réel
async function updateQualitativeStatus(compte) {
  if (!analyseQualitativeReport.value || !analyseQualitativeReport.value.analyse) return;

  const item = analyseQualitativeReport.value.analyse.find(i => i.compte === compte);
  if (!item) return;

  // Compter les réponses positives (cochées)
  const responses = qualitativeResponses.value[compte] || {};
  let positiveResponses = 0;
  let totalQuestions = 0;

  for (let q = 1; q <= 8; q++) {
    const questionId = `Q${q}`;
    totalQuestions++;
    if (responses[questionId]) {
      positiveResponses++;
    }
  }

  // Calculer le score qualitatif (pourcentage de réponses positives)
  const qualitativeScore = totalQuestions > 0 ? (positiveResponses / totalQuestions) * 100 : 0;

  // Déterminer le statut basé sur le score (3 niveaux de risque)
  let status, isSignificant;
  if (qualitativeScore >= 50) {
    // Risque élevé : ≥ 50% de réponses positives
    status = "À tester";
    isSignificant = true;
  } else if (qualitativeScore >= 25) {
    // Risque modéré : 25-49% de réponses positives
    status = "Ne pas tester";
    isSignificant = false;
  } else {
    // Risque faible : < 25% de réponses positives
    status = "Ne pas tester";
    isSignificant = false;
  }

  // Mettre à jour l'objet item
  item.qualitative_score = qualitativeScore;
  item.status = status;
  item.is_qualitatively_significant = isSignificant;

  // Recalculer les statistiques globales
  await updateQualitativeStatistics();
}

// Fonction pour recalculer les statistiques globales
async function updateQualitativeStatistics() {
  if (!analyseQualitativeReport.value || !analyseQualitativeReport.value.analyse) {
    return;
  }

  const analyse = analyseQualitativeReport.value.analyse;
  let significantAccounts = 0;
  let nonSignificantAccounts = 0;
  let totalPositiveResponses = 0;
  let totalScore = 0;
  let totalAccounts = analyse.length;

  analyse.forEach(item => {
    // Compter les comptes significatifs
    if (item.is_qualitatively_significant) {
      significantAccounts++;
    } else {
      nonSignificantAccounts++;
    }

    // Compter les réponses positives
    const responses = qualitativeResponses.value[item.compte] || {};
    for (let q = 1; q <= 8; q++) {
      if (responses[`Q${q}`]) {
        totalPositiveResponses++;
      }
    }

    // Ajouter au score total
    totalScore += item.qualitative_score || 0;
  });

  // Mettre à jour les variables réactives
  qualitativeStats.value = {
    significant_accounts: significantAccounts,
    non_significant_accounts: nonSignificantAccounts,
    total_positive_responses: totalPositiveResponses,
    average_score: totalAccounts > 0 ? totalScore / totalAccounts : 0
  };

  // Mettre à jour aussi l'objet original pour la compatibilité
  if (!analyseQualitativeReport.value.statistics) {
    analyseQualitativeReport.value.statistics = {};
  }

  analyseQualitativeReport.value.statistics.significant_accounts = significantAccounts;
  analyseQualitativeReport.value.statistics.non_significant_accounts = nonSignificantAccounts;
  analyseQualitativeReport.value.statistics.total_positive_responses = totalPositiveResponses;
  analyseQualitativeReport.value.statistics.average_score = qualitativeStats.value.average_score;

}

async function saveQualitativeResponses() {
  loading.value = true;
  errorMsg.value = "";


  try {
    // Utiliser directement l'endpoint qui fonctionne (qualitative_analysis)
    const listGrouping = [];
    for (const [compte, responses] of Object.entries(qualitativeResponses.value)) {
      for (const [questionId, significant] of Object.entries(responses)) {
        const questionNumber = parseInt(questionId.replace('Q', ''));
        listGrouping.push({
          compte: compte,
          question: questionNumber,
          significant: significant
        });
      }
    }

    const payload = { listGrouping };
    const response = await axios.put(`/mission/qualitative_analysis/${props.missionId}`, payload);
    const data = response.data;

    if (data.response && data.response.ok) {
      // Recharger l'analyse après sauvegarde
      await loadAnalyseQualitative();

      // Recharger aussi la présentation des comptes significatifs si elle existe
      if (presentationComptesSignificatifsReport.value) {
        // Recharger d'abord les données de variation (étape 3) car elles sont utilisées dans la présentation
        await loadClassement();
        // Puis recharger la présentation
        await loadPresentationComptesSignificatifs();
      }

      errorMsg.value = "";
    } else {
      errorMsg.value = data.response?.message || "Erreur lors de la sauvegarde";
    }
  } catch (e) {
    errorMsg.value = `Échec de la sauvegarde des réponses: ${e.response?.data?.message || e.message}`;
  } finally {
    loading.value = false;
  }
}

async function initQualitativeResponses() {
  loading.value = true;
  try {
    const { data } = await axios.post(`/mission/init_qualitative_responses/${props.missionId}`);

    if (data.response.ok) {
      // Recharger l'analyse après initialisation
      await loadAnalyseQualitative();
      errorMsg.value = "";
    } else {
      errorMsg.value = data.response.message || "Erreur lors de l'initialisation";
    }
  } catch (e) {
    errorMsg.value = "Échec de l'initialisation des réponses.";
    console.error(e);
  } finally {
    loading.value = false;
  }
}

async function loadPresentationComptesSignificatifs() {
  loading.value = true; errorMsg.value = "";
  try {
    const { data } = await axios.get(`/mission/presentation_comptes_significatifs/${props.missionId}`);
    presentationComptesSignificatifsReport.value = data.response || {};
    if (presentationComptesSignificatifsReport.value?.presentation) {
      presentationComptesSignificatifsReport.value.presentation =
        filterByBalanceRows(presentationComptesSignificatifsReport.value.presentation);
    }
  } catch (e) {
    errorMsg.value = "Échec du chargement de la présentation des comptes significatifs.";
    console.error(e);
  } finally {
    loading.value = false;
  }
}

async function loadRevueAnalytiqueFinale() {
  loading.value = true; errorMsg.value = "";
  try {
    const { data } = await axios.get(`/mission/revue_analytique_finale/${props.missionId}`);
    revueAnalytiqueFinaleReport.value = data.response || {};
    if (revueAnalytiqueFinaleReport.value?.revue) {
      revueAnalytiqueFinaleReport.value.revue =
        filterByBalanceRows(revueAnalytiqueFinaleReport.value.revue);
    }
  } catch (e) {
    errorMsg.value = "Échec du chargement de la revue analytique finale.";
    console.error(e);
  } finally {
    loading.value = false;
  }
}


// Questions qualitatives Q1-Q8
const qualitativeQuestions = ref([
  "Volume d'activité, complexité et homogénéité des transactions enregistrées, existence de transactions significatives inhabituelles ou anormales dans le COTABD",
  "Changements identifiés dans le COTABD et détermination si un ou de nouveaux risque(s) sont apparus du fait de changement au sein de l'entité ou de son environnement (économique, légal, réglementaire, normatif ou méthodes comptables)",
  "Sensibilité de l'entité aux anomalies issues de fraudes (Si oui, le risque est obligatoirement Significant)",
  "Niveau de complexité des normes, règles, méthodes comptables, notes annexes, estimations ou jugements liées aux comptes ou aux notes annexes",
  "Exposition du COTABD à des pertes (charges ou dépréciations)",
  "Probabilité que des passifs éventuels significatifs (procès, contentieux, litiges etc…) puissent être issus des transactions enregistrées dans le COTABD",
  "Existence de transactions avec des parties liées dans le COTABD",
  "Niveau de contrôle interne et fiabilité des systèmes d'information liés aux comptes"
]);


// Fonction pour afficher une question au clic
function showQuestion(questionNumber, event) {
  selectedQuestion.value = `Q${questionNumber}`;
  selectedQuestionText.value = qualitativeQuestions.value[questionNumber - 1];

  // Positionner le tooltip près du clic
  const rect = event.target.getBoundingClientRect();
  tooltipPosition.value = {
    x: rect.left + rect.width / 2,
    y: rect.bottom + 10
  };

  showQuestionTooltip.value = true;
}

// Fonction pour fermer le tooltip
function hideQuestionTooltip() {
  showQuestionTooltip.value = false;
  selectedQuestion.value = '';
  selectedQuestionText.value = '';
}

function getRiskLevelClass(riskLevel) {
  switch (riskLevel) {
    case "Très élevé": return "bg-red-100 text-red-800 border-red-200";
    case "Élevé": return "bg-orange-100 text-orange-800 border-orange-200";
    case "Modéré": return "bg-yellow-100 text-yellow-800 border-yellow-200";
    case "Faible": return "bg-green-100 text-green-800 border-green-200";
    case "À déterminer": return "bg-purple-100 text-purple-800 border-purple-200";
    case "Non évalué": return "bg-gray-100 text-gray-800 border-gray-200";
    default: return "bg-gray-100 text-gray-800 border-gray-200";
  }
}

function getStatusClass(finalStatus) {
  if (finalStatus.includes("À tester")) {
    return "bg-red-100 text-red-800 border-red-200";
  } else {
    return "bg-green-100 text-green-800 border-green-200";
  }
}

function getSignificativiteClass(significativiteStatus) {
  if (significativiteStatus.includes("Significatif")) {
    return "bg-red-100 text-red-800 border-red-200";
  } else {
    return "bg-green-100 text-green-800 border-green-200";
  }
}

function getPrioriteClass(priorite) {
  switch (priorite) {
    case "Haute": return "bg-red-100 text-red-800 border-red-200";
    case "Moyenne": return "bg-orange-100 text-orange-800 border-orange-200";
    case "Faible": return "bg-green-100 text-green-800 border-green-200";
    default: return "bg-gray-100 text-gray-800 border-gray-200";
  }
}

function getValidationStatusClass(validationStatus) {
  switch (validationStatus) {
    case "Validation obligatoire": return "bg-red-100 text-red-800 border-red-200";
    case "Validation recommandée": return "bg-orange-100 text-orange-800 border-orange-200";
    case "Validation optionnelle": return "bg-yellow-100 text-yellow-800 border-yellow-200";
    case "Validation non requise": return "bg-green-100 text-green-800 border-green-200";
    default: return "bg-gray-100 text-gray-800 border-gray-200";
  }
}

function handleCommentaireChange(compte, newComment) {
  if (revueAnalytiqueFinaleReport.value && revueAnalytiqueFinaleReport.value.revue) {
    const item = revueAnalytiqueFinaleReport.value.revue.find(r => r.compte === compte);
    if (item) {
      item.commentaire_perso = newComment;
    }
  }
}

function handleValidationChange(compte, isValidated) {
  if (revueAnalytiqueFinaleReport.value && revueAnalytiqueFinaleReport.value.revue) {
    const item = revueAnalytiqueFinaleReport.value.revue.find(r => r.compte === compte);
    if (item) {
      item.is_validated = isValidated;
    }
  }
}

async function saveRevueAnalytique() {
  if (!revueAnalytiqueFinaleReport.value || !revueAnalytiqueFinaleReport.value.revue) {
    errorMsg.value = "Aucune donnée de revue analytique à sauvegarder.";
    return;
  }

  loading.value = true;
  try {
    const { data } = await axios.put(`/mission/save_revue_analytique/${props.missionId}`, {
      revue_data: revueAnalytiqueFinaleReport.value.revue
    });

    if (data.response.ok) {
      errorMsg.value = "";
      // Recharger les données pour mettre à jour les statistiques
      await loadRevueAnalytiqueFinale();
    } else {
      errorMsg.value = data.response.message || "Erreur lors de la sauvegarde";
    }
  } catch (e) {
    errorMsg.value = "Échec de la sauvegarde de la revue analytique.";
    console.error(e);
  } finally {
    loading.value = false;
  }
}


function exportToCsv(data, filename) {
  // Pour la revue analytique, formater les données avec les commentaires
  let csvContent;
  if (filename === 'revue_analytique') {
    const headers = ['Compte', 'Libellé', 'N', 'N-1', 'Δ', 'Δ %', 'Commentaire Auto', 'Commentaire Perso'];
    const rows = data.map(row => [
      row.numero_compte,
      row.libelle,
      row.solde_n,
      row.solde_n1,
      row.delta_abs,
      (row.delta_pct * 100).toFixed(1) + '%',
      row.commentaire_auto || '',
      row.commentaire_perso || ''
    ]);
    csvContent = [headers, ...rows].map(row => row.join(',')).join('\n');
  } else if (filename === 'classement_bilan') {
    const headers = ['Compte', 'Libellé', 'Nature', 'N', 'N-1', 'Variation', 'Variation %'];
    const rows = data.map(row => [
      row.compte,
      row.libelle,
      row.nature,
      row.solde_n,
      row.solde_n1,
      row.variation,
      row.variation_percent.toFixed(1) + '%'
    ]);
    csvContent = [headers, ...rows].map(row => row.join(',')).join('\n');
  } else if (filename.startsWith('etats_financiers_')) {
    const type = filename.split('_')[2]; // actif, passif, ou pnl
    let headers, rows;

    if (type === 'actif') {
      headers = ['REF', 'Libellé', 'BRUT N', 'AMORT N', 'NET N', 'NET N-1'];
      rows = data.map(row => [
        row.ref,
        row.libelle,
        row.brut_solde_n || 0,
        row.amor_solde_n || 0,
        row.net_solde_n || 0,
        row.net_solde_n1 || 0
      ]);
    } else {
      headers = ['REF', 'Libellé', 'NET N', 'NET N-1'];
      rows = data.map(row => [
        row.ref,
        row.libelle,
        row.net_solde_n || 0,
        row.net_solde_n1 || 0
      ]);
    }
    csvContent = [headers, ...rows].map(row => row.join(',')).join('\n');
  } else if (filename === 'analyse_quantitative') {
    const headers = ['Compte', 'Libellé', 'Solde N', 'Solde N-1', 'Variation', 'Seuil Matérialité', 'Pourcentage', 'Statut'];
    const rows = data.map(row => [
      row.compte,
      row.libelle,
      row.solde_n,
      row.solde_n1,
      row.variation,
      row.materiality_threshold,
      row.percentage_of_threshold.toFixed(1) + '%',
      row.status
    ]);
    csvContent = [headers, ...rows].map(row => row.join(',')).join('\n');
  } else if (filename === 'analyse_qualitative') {
    const headers = ['Compte', 'Libellé', 'Solde N', 'Solde N-1', 'Variation', 'Score Qualitatif', 'Réponses Positives', 'Statut'];
    const rows = data.map(row => [
      row.compte,
      row.libelle,
      row.solde_n,
      row.solde_n1,
      row.variation,
      row.qualitative_score.toFixed(1) + '%',
      row.positive_responses + '/' + row.total_questions,
      row.status
    ]);
    csvContent = [headers, ...rows].map(row => row.join(',')).join('\n');
  } else if (filename === 'synthese_comptes_significatifs') {
    const headers = ['Compte', 'Libellé', 'Solde N', 'Solde N-1', 'Variation', 'Significatif Quantitatif', 'Significatif Qualitatif', 'Statut Final', 'Niveau de Risque', 'Recommandation'];
    const rows = data.map(row => [
      row.compte,
      row.libelle,
      row.solde_n,
      row.solde_n1,
      row.variation,
      row.is_quantitatively_significant ? 'Oui' : 'Non',
      row.is_qualitatively_significant ? 'Oui' : 'Non',
      row.final_status,
      row.risk_level,
      row.recommendation
    ]);
    csvContent = [headers, ...rows].map(row => row.join(',')).join('\n');
  } else if (filename === 'presentation_comptes_significatifs') {
    const headers = ['Compte', 'Libellé', 'Solde N', 'Solde N-1', 'Variation', 'Variation %', 'Significatif Quantitatif', 'Significatif Qualitatif', 'Statut Significativité', 'Recommandation Audit'];
    const rows = data.map(row => [
      row.compte,
      row.libelle,
      row.solde_n,
      row.solde_n1,
      row.variation,
      row.variation_percent.toFixed(1) + '%',
      row.is_quantitatively_significant ? 'Oui' : 'Non',
      row.is_qualitatively_significant ? 'Oui' : 'Non',
      row.significativite_status,
      row.recommandation_audit
    ]);
    csvContent = [headers, ...rows].map(row => row.join(',')).join('\n');
  } else if (filename === 'revue_analytique_finale') {
    const headers = ['Compte', 'Libellé', 'Solde N', 'Solde N-1', 'Variation', 'Variation %', 'Statut Final', 'Niveau de Risque', 'Statut Validation', 'Validé', 'Commentaire Auto', 'Commentaire Perso'];
    const rows = data.map(row => [
      row.compte,
      row.libelle,
      row.solde_n,
      row.solde_n1,
      row.variation,
      row.variation_percent.toFixed(1) + '%',
      row.final_status,
      row.risk_level,
      row.validation_status,
      row.is_validated ? 'Oui' : 'Non',
      row.commentaire_auto,
      row.commentaire_perso
    ]);
    csvContent = [headers, ...rows].map(row => row.join(',')).join('\n');
  } else {
    csvContent = data.map(row => Object.values(row).join(',')).join('\n');
  }

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${filename}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/* === Utilitaires === */
function getTypeLabel(type) {
  const typeLabels = {
    'equilibre': 'Équilibre Global',
    'equilibre_global': 'Équilibre Global',
    'identite': 'Erreur d\'Identité',
    'identite_compte': 'Cohérence des Données',
    'signe': 'Anomalie de Sens',
    'signe_incoherent': 'Signe Incohérent',
    'arithmetique': 'Erreur Arithmétique',
    'completude': 'Complétude/Exhaustivité',
    'compte_non_solde': 'Compte Non Soldé'
  };
  return typeLabels[type] || type || 'Autre';
}

// Fonctions pour extraire les informations des erreurs arithmétiques
function extractLibelle(message) {
  if (!message) return '';
  const match = message.match(/Libellé\s*:\s*(.+?)(?:\n|$)/);
  return match ? match[1].trim() : '';
}

function extractEcart(message) {
  if (!message) return '';
  // Chercher "🔴 ÉCART DÉTECTÉ : X FCFA"
  const match = message.match(/ÉCART DÉTECTÉ\s*:\s*([\d\s,]+)\s*FCFA/i);
  if (match) return match[1].trim().replace(/\s/g, ' ') + ' FCFA';

  // Fallback: chercher "• Écart : X FCFA"
  const match2 = message.match(/•\s*Écart\s*:\s*([\d\s,]+)\s*FCFA/i);
  return match2 ? match2[1].trim().replace(/\s/g, ' ') + ' FCFA' : '';
}

function extractSoldeOuverture(message) {
  if (!message) return 'N/A';
  // Chercher "• Solde d'ouverture : X FCFA (Débit initial Y - Crédit initial Z)"
  const match = message.match(/•\s*Solde d'ouverture\s*:\s*([\d\s,]+)\s*FCFA\s*\(Débit initial\s*([\d\s,]+)\s*-\s*Crédit initial\s*([\d\s,]+)\)/i);
  if (match) {
    return `${match[1].trim().replace(/\s/g, ' ')} FCFA (Débit ${match[2].trim().replace(/\s/g, ' ')} - Crédit ${match[3].trim().replace(/\s/g, ' ')})`;
  }

  // Fallback simple
  const match2 = message.match(/Solde d'ouverture\s*:\s*([\d\s,]+)\s*FCFA/i);
  return match2 ? match2[1].trim().replace(/\s/g, ' ') + ' FCFA' : 'N/A';
}

function extractMouvements(message) {
  if (!message) return 'N/A';
  // Chercher "• Mouvements : Débit X | Crédit Y | Net Z FCFA"
  const match = message.match(/•\s*Mouvements\s*:\s*Débit\s*([\d\s,]+)\s*\|\s*Crédit\s*([\d\s,]+)\s*\|\s*Net\s*([\d\s,]+)\s*FCFA/i);
  if (match) {
    return `Débit ${match[1].trim().replace(/\s/g, ' ')} | Crédit ${match[2].trim().replace(/\s/g, ' ')} | Net ${match[3].trim().replace(/\s/g, ' ')} FCFA`;
  }
  return 'N/A';
}

function extractSoldeAttendu(message) {
  if (!message) return 'N/A';
  // Chercher "• Solde attendu : X FCFA"
  const match = message.match(/•\s*Solde attendu\s*:\s*([\d\s,]+)\s*FCFA/i);
  return match ? match[1].trim().replace(/\s/g, ' ') + ' FCFA' : 'N/A';
}

function extractSoldeReel(message) {
  if (!message) return 'N/A';
  // Chercher "• Solde réel : X FCFA"
  const match = message.match(/•\s*Solde réel\s*:\s*([\d\s,]+)\s*FCFA/i);
  if (match) return match[1].trim().replace(/\s/g, ' ') + ' FCFA';

  // Fallback: chercher dans "• Solde de clôture : X FCFA (Débit fin Y - Crédit fin Z)"
  const match2 = message.match(/•\s*Solde de clôture\s*:\s*([\d\s,]+)\s*FCFA\s*\(Débit fin\s*([\d\s,]+)\s*-\s*Crédit fin\s*([\d\s,]+)\)/i);
  if (match2) {
    return `${match2[1].trim().replace(/\s/g, ' ')} FCFA (Débit ${match2[2].trim().replace(/\s/g, ' ')} - Crédit ${match2[3].trim().replace(/\s/g, ' ')})`;
  }
  return 'N/A';
}

function extractJustification(message) {
  if (!message) return '';
  // Chercher "Justification : ..."
  const match = message.match(/Justification\s*:\s*(.+?)(?:\n\n|$)/s);
  return match ? match[1].trim() : '';
}

function getBilanMessage(yearReport) {
  if (!yearReport.erreurs || yearReport.erreurs.length === 0) {
    return '✅ Aucune anomalie détectée';
  }

  // Compter les types d'erreurs
  const errorCounts = yearReport.erreurs.reduce((acc, error) => {
    acc[error.type] = (acc[error.type] || 0) + 1;
    return acc;
  }, {});

  // Construire le message détaillé
  const messages = [];

  const equilibreCount = (errorCounts.equilibre || 0) + (errorCounts.equilibre_global || 0);
  if (equilibreCount > 0) {
    messages.push(`${equilibreCount} déséquilibre(s) global`);
  }

  const identiteCount = (errorCounts.identite || 0) + (errorCounts.identite_compte || 0);
  if (identiteCount > 0) {
    messages.push(`${identiteCount} incohérence(s) de données`);
  }

  const arithmetiqueCount = errorCounts.arithmetique || 0;
  if (arithmetiqueCount > 0) {
    messages.push(`${arithmetiqueCount} erreur(s) arithmétique(s)`);
  }

  const signeCount = (errorCounts.signe || 0) + (errorCounts.signe_incoherent || 0);
  if (signeCount > 0) {
    messages.push(`${signeCount} anomalie(s) de sens`);
  }

  const completudeCount = errorCounts.completude || 0;
  if (completudeCount > 0) {
    messages.push(`${completudeCount} erreur(s) de complétude`);
  }

  const comptesNonSoldesCount = errorCounts.compte_non_solde || 0;
  if (comptesNonSoldesCount > 0) {
    messages.push(`${comptesNonSoldesCount} compte(s) non soldé(s)`);
  }

  if (messages.length > 0) {
    return `Anomalies détectées : ${messages.join(', ')}`;
  }

  return '✅ Aucune anomalie détectée';
}

function getDetailedMessage(yearReport) {
  if (!yearReport.erreurs || yearReport.erreurs.length === 0) {
    return 'Tous les contrôles sont passés avec succès';
  }

  // Chercher l'erreur d'équilibre (nouveau ou ancien format)
  const equilibreError = yearReport.erreurs.find(e => e.type === 'equilibre' || e.type === 'equilibre_global');

  if (equilibreError && equilibreError.message) {
    // Si le message contient déjà les informations, on l'utilise directement
    return equilibreError.message;
  }

  // Pour les autres erreurs
  const otherErrors = yearReport.erreurs.filter(e => e.type !== 'equilibre' && e.type !== 'equilibre_global');
  if (otherErrors.length > 0) {
    const compteList = otherErrors.map(e => e.numero_compte || 'N/A').filter(c => c !== '-').join(', ');
    if (compteList) {
      return `${otherErrors.length} compte(s) présentent des incohérences : ${compteList}. 
            Vérifiez les soldes initiaux, mouvements et finaux de ces comptes.`;
    } else {
      // Si les messages sont disponibles, les utiliser
      return otherErrors.map(e => e.message || `Erreur ${e.type} pour le compte ${e.numero_compte || 'N/A'}`).join('\n');
    }
  }

  return 'Vérifiez la cohérence des données comptables';
}

// Formatage des montants en français avec espaces insécables
function formatAmount(value) {
  const n = Number(value || 0);
  return new Intl.NumberFormat('fr-FR').format(n);
}

</script>



<template>
  <div class="flex w-full overflow-hidden">
    <!-- Sidebar -->
    <!-- SIDEBAR ÉTAPES -->
<!-- SIDEBAR WORKFLOW PAR PHASES -->
<div class="min-w-[320px] bg-blue-ycube text-white flex flex-col px-5 py-6 shadow-xl">

  <!-- Bouton retour -->
  <button
    class="mb-4 px-4 py-2 rounded-lg bg-white/20 hover:bg-white/30 font-semibold flex items-center gap-2 transition"
    @click="back">
    <i class="fa-solid fa-arrow-left"></i> Retour
  </button>

  <!-- Progression globale -->
  <div class="mb-6 bg-blue-ycube-1 rounded-xl p-4 shadow-inner">
    <h3 class="text-sm font-bold mb-3">Progression de l’audit</h3>

    <div class="w-full bg-white/20 rounded-full h-2 overflow-hidden">
      <div
        class="bg-green-400 h-2 transition-all duration-500"
        :style="{ width: progress + '%' }">
      </div>
    </div>

    <p class="text-xs mt-2 opacity-90">
      {{ completedSteps }} / 9 étapes validées
    </p>
  </div>

  <!-- PHASES -->
  <div class="flex flex-col gap-4 overflow-y-auto pr-1">

    <div
      v-for="phase in workflowPhases"
      :key="phase.id"
      class="rounded-xl bg-white/10"
    >

      <!-- HEADER PHASE -->
      <button
        class="w-full flex items-center justify-between px-4 py-3 text-sm font-bold hover:bg-white/20 transition rounded-t-xl"
        @click="togglePhase(phase)"
      >
        <span>{{ phase.label }}</span>
        <i
          class="fa-solid transition-transform duration-300"
          :class="phase.open ? 'fa-chevron-up' : 'fa-chevron-down'"
        ></i>
      </button>

      <!-- ÉTAPES -->
      <div v-if="phase.open" class="flex flex-col gap-2 px-3 pb-3">

        <div
          v-for="step in phase.steps"
          :key="step.id"
          :class="[
            'rounded-lg px-3 py-2 flex items-start gap-3 transition',
            step.static ? 'bg-blue-ycube-1' : 'bg-white/10 hover:bg-white/20 cursor-pointer'
          ]"
          @click="handleStepClick(step)"
        >

          <!-- CHECKBOX (Phase 1 & 3) -->
          <input
            v-if="step.static"
            type="checkbox"
            class="mt-1 accent-green-500 cursor-pointer"
            v-model="step.checked"
            @click.stop
          />

          <!-- DOT (Phase 2) -->
          <span v-else class="text-white/60 mt-1">•</span>

          <!-- TEXTE -->
          <div class="flex flex-col">
            <span class="font-semibold text-sm">
              {{ step.name }}
            </span>
            <span class="text-xs text-white/60">
              Étape {{ step.id }}
            </span>
          </div>

        </div>

      </div>
    </div>

  </div>
</div>



    <!-- Main Body -->
    <div class="flex-auto flex overflow-auto p-4">
      <!-- Rendu historique par composant -->
      <component :is="renderComponent" :key="componentKey" v-if="renderComponent" />

      <!-- Nouveaux rendus inline -->
      <div v-else class="w-full">
        <!-- Bandeau état -->
        <div v-if="loading" class="text-sm text-gray-600 mb-3">Chargement…</div>
        <div v-if="errorMsg" class="text-sm text-red-600 mb-3">{{ errorMsg }}</div>

        <!-- Revue analytique -->
        <div v-if="componentKey === 'revue'">
          <h2 class="text-xl font-semibold mb-3">Revue analytique</h2>
          <div v-if="revueAnalytique.length === 0 && !loading" class="text-sm text-gray-600">Aucune donnée.</div>
          <button v-if="revueAnalytique.length" @click="exportToCsv(revueAnalytique, 'revue_analytique')"
            class="mb-3 px-4 py-2 bg-green-ycube text-white rounded-md shadow-md">Télécharger (CSV)</button>
          <div class="overflow-x-auto rounded-xl shadow-xl bg-white border border-gray-100"
            v-if="revueAnalytique.length">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gradient-to-r from-blue-ycube  to-blue-ycube-3">
                <tr>
                  <th class="px-6 py-4 text-left text-xs font-semibold text-white uppercase tracking-wider">Compte</th>
                  <th class="px-6 py-4 text-left text-xs font-semibold text-white uppercase tracking-wider">Libellé</th>
                  <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">N</th>
                  <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">N-1</th>
                  <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">Δ</th>
                  <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">Δ %</th>
                  <th class="px-6 py-4 text-left text-xs font-semibold text-white uppercase tracking-wider">Commentaire
                    Auto</th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr v-for="r in revueAnalytique" :key="r.numero_compte"
                  class="hover:bg-gradient-to-r hover:from-blue-50 hover:to-indigo-50 transition-all duration-300 group transform hover:scale-[1.01] hover:shadow-md">
                  <td class="px-6 py-4 whitespace-nowrap">
                    <div class="flex items-center">
                      <div
                        class="flex-shrink-0 h-8 w-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center mr-3 group-hover:scale-110 transition-transform duration-200">
                        <span class="text-xs font-bold text-white">{{ r.numero_compte.charAt(0) }}</span>
                      </div>
                      <div
                        class="text-sm font-mono font-bold text-gray-900 group-hover:text-blue-700 transition-colors duration-200">
                        {{ r.numero_compte }}</div>
                    </div>
                  </td>
                  <td class="px-6 py-4">
                    <div
                      class="text-sm text-gray-900 max-w-xs truncate group-hover:text-blue-700 transition-colors duration-200"
                      :title="r.libelle">{{ r.libelle }}</div>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-right">
                    <div
                      class="text-sm font-mono text-gray-900 group-hover:text-blue-700 transition-colors duration-200">
                      {{ formatAmount(r.solde_n) }}</div>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-right">
                    <div
                      class="text-sm font-mono text-gray-900 group-hover:text-blue-700 transition-colors duration-200">
                      {{ formatAmount(r.solde_n1) }}</div>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-right">
                    <div class="flex items-center justify-end">
                      <div
                        class="text-sm font-mono font-semibold transform group-hover:scale-105 transition-all duration-200"
                        :class="r.delta_abs >= 0 ? 'text-emerald-600' : 'text-red-600'">
                        {{ formatAmount(r.delta_abs) }}
                      </div>
                      <div class="ml-2 w-2 h-2 rounded-full"
                        :class="r.delta_abs >= 0 ? 'bg-emerald-500' : 'bg-red-500'"></div>
                    </div>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-right">
                    <div class="flex items-center justify-end">
                      <div
                        class="text-sm font-mono font-semibold transform group-hover:scale-105 transition-all duration-200"
                        :class="Math.abs(r.delta_pct * 100) > 20 ? 'text-red-600' : 'text-gray-600'">
                        {{ (r.delta_pct * 100).toFixed(1) }}%
                      </div>
                      <svg v-if="Math.abs(r.delta_pct * 100) > 20" class="w-4 h-4 ml-1 text-red-500 animate-pulse"
                        fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd"
                          d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                          clip-rule="evenodd"></path>
                      </svg>
                    </div>
                  </td>
                  <td class="px-6 py-4">
                    <div
                      class="text-sm text-gray-900 max-w-xs truncate group-hover:text-blue-700 transition-colors duration-200"
                      :title="r.commentaire_auto || '-'">{{ r.commentaire_auto || '-' }}</div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Contrôle de cohérence -->
        <div v-if="componentKey === 'coherence'">
          <div class="flex justify-between items-center mb-3">
            <h2 class="text-xl font-semibold">Contrôle de cohérence</h2>
          </div>

          <!-- Boutons de sélection du type de contrôle -->
          <div v-if="coherenceReport" class="mb-4 flex flex-wrap gap-3 items-center">
            <div class="flex gap-3">
              <button @click="selectedControlType = 'arithmetique'" :class="selectedControlType === 'arithmetique'
                ? 'bg-blue-ycube text-white shadow-lg ring-2 ring-blue-ycube-2'
                : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'"
                class="px-6 py-3 rounded-lg font-semibold text-sm transition-all duration-200 flex items-center gap-2">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z">
                  </path>
                </svg>
                Contrôle Arithmétique
              </button>
              <button @click="selectedControlType = 'vraisemblance'" :class="selectedControlType === 'vraisemblance'
                ? 'bg-blue-ycube text-white shadow-lg ring-2 ring-blue-ycube-2'
                : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'"
                class="px-6 py-3 rounded-lg font-semibold text-sm transition-all duration-200 flex items-center gap-2">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                Contrôle de Vraisemblance
              </button>
            </div>
          </div>

          <div v-if="!coherenceReport && !loading" class="text-sm text-gray-600">Aucune donnée.</div>

          <!-- Sélecteur d'année -->
          <div v-if="coherenceReport && availableYearsCoherence.length > 0" class="mb-4 flex items-center gap-4">
            <label class="text-sm font-medium text-gray-700">Sélectionner l'année :</label>
            <select v-model="selectedYearCoherence"
              class="px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-ycube-2 focus:border-blue-ycube bg-white text-gray-900 font-medium">
              <option v-for="year in availableYearsCoherence" :key="year" :value="year">
                {{ year }}
              </option>
            </select>
            <button v-if="coherenceReport" @click="exportToCsv(coherenceReport, 'controle_coherence')"
              class="px-4 py-2 bg-green-ycube-2 text-white rounded-md shadow-md hover:bg-green-ycube transition-colors duration-200">
              Télécharger (CSV)
            </button>
          </div>

          <!-- Avertissements de matérialité négative -->
          <div v-if="coherenceReport?.materiality_warnings?.length > 0"
            class="mb-4 p-4 bg-red-50 border-l-4 border-red-400 rounded-md">
            <h3 class="text-lg font-semibold text-red-800 mb-2">⚠️ Avertissements de Matérialité</h3>
            <div class="space-y-2">
              <div v-for="warning in coherenceReport.materiality_warnings" :key="warning.benchmark"
                class="p-3 bg-red-100 border border-red-300 rounded-md">
                <div class="font-semibold text-red-800">{{ warning.message }}</div>
                <div class="text-sm text-red-700 mt-1">
                  <div>Benchmark: {{ warning.benchmark }}</div>
                  <div>Matérialité: {{ warning.materiality?.toLocaleString() }}</div>
                  <div>Matérialité de performance: {{ warning.performance_materiality?.toLocaleString() }}</div>
                  <div>Erreurs triviales: {{ warning.trivial_misstatements?.toLocaleString() }}</div>
                </div>
              </div>
            </div>
          </div>

          <div v-if="filteredCoherenceReport && selectedYearCoherence" class="space-y-4">
            <template v-for="(yearReport, annee) in filteredCoherenceReport" :key="annee">
              <!-- Résumé de l'année -->
              <div class="bg-white rounded-lg p-4 border border-blue-200 mb-4">
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-4">
                    <div
                      class="flex-shrink-0 h-12 w-12 bg-gradient-to-br from-blue-ycube-3 to-blue-ycube rounded-lg flex items-center justify-center shadow-md">
                      <span class="text-lg font-bold text-white">{{ annee }}</span>
                    </div>
                    <div>
                      <h3 class="text-lg font-semibold text-gray-900">
                        {{ selectedControlType === 'arithmetique' ? 'Contrôles Arithmétiques' : 'Contrôles de Vraisemblance' }} - Année {{ annee }}
                      </h3>
                      <p class="text-sm text-gray-600 mt-1">
                        <span v-if="selectedControlType === 'arithmetique'" class="inline-flex items-center gap-2 mr-4">
                          <span class="w-2 h-2 rounded-full"
                            :class="yearReport.equilibre_global ? 'bg-emerald-500' : 'bg-red-500'"></span>
                          Équilibre: {{ yearReport.equilibre_global ? 'OK' : 'Déséquilibré' }}
                          <span v-if="!yearReport.equilibre_global && yearReport.ecart_equilibre !== undefined"
                            class="ml-2 px-2 py-1 bg-red-100 text-red-800 rounded-md font-bold border border-red-300">
                            Écart: {{ formatAmount(yearReport.ecart_equilibre) }} FCFA
                          </span>
                        </span>
                        <span v-if="yearReport.erreurs" class="inline-flex items-center gap-2">
                          <span class="w-2 h-2 rounded-full"
                            :class="yearReport.erreurs.length > 0 ? 'bg-orange-500' : 'bg-emerald-500'"></span>
                          {{ yearReport.erreurs.length || 0 }} erreur(s) détectée(s)
                        </span>
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Explication de la vérification de l'équilibre (si contrôle arithmétique) -->
              <div v-if="selectedControlType === 'arithmetique' && yearReport.verification_equilibre"
                :class="yearReport.equilibre_global ? 'mb-4 bg-emerald-50 border-l-4 border-emerald-400 rounded-md p-4' : 'mb-4 bg-red-50 border-l-4 border-red-400 rounded-md p-4'">
                <div class="flex items-start">
                  <div class="flex-shrink-0">
                    <svg v-if="yearReport.equilibre_global" class="h-6 w-6 text-emerald-500" fill="none"
                      stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                    <svg v-else class="h-6 w-6 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                  </div>
                  <div class="ml-3 flex-1">
                    <h3
                      :class="yearReport.equilibre_global ? 'text-sm font-semibold text-emerald-800 mb-2' : 'text-sm font-semibold text-red-800 mb-2'">
                      <span v-if="yearReport.equilibre_global">✅</span>
                      <span v-else>🔴</span>
                      Premier Contrôle Arithmétique : Vérification de l'Équilibre
                    </h3>
                    <div
                      :class="yearReport.equilibre_global ? 'text-sm text-emerald-700 space-y-2' : 'text-sm text-red-700 space-y-2'">
                      <p><strong>Résultats exacts de la vérification :</strong></p>
                      <div class="mt-3 grid grid-cols-2 gap-4 text-sm font-mono">
                        <div class="bg-white p-2 rounded border">
                          <span class="font-semibold text-gray-700">Total des débits :</span>
                          <span class="ml-2 font-bold text-blue-700">{{
                            formatAmount(yearReport.verification_equilibre.total_debits) }} FCFA</span>
                        </div>
                        <div class="bg-white p-2 rounded border">
                          <span class="font-semibold text-gray-700">Total des crédits :</span>
                          <span class="ml-2 font-bold text-green-700">{{
                            formatAmount(yearReport.verification_equilibre.total_credits) }} FCFA</span>
                        </div>
                        <div
                          v-if="!yearReport.equilibre_global && yearReport.verification_equilibre.ecart !== undefined"
                          class="bg-white p-2 rounded border col-span-2">
                          <span class="font-semibold text-gray-700">Écart détecté :</span>
                          <span class="ml-2 font-bold text-red-700">{{
                            formatAmount(yearReport.verification_equilibre.ecart) }} FCFA</span>
                        </div>
                        <div class="col-span-2 text-xs text-gray-600">
                          <span class="font-semibold">Nombre de comptes analysés :</span>
                          <span class="ml-2">{{ yearReport.verification_equilibre.nb_comptes_analyses }}</span>
                        </div>
                      </div>
                      <div class="mt-3 p-2 rounded text-xs"
                        :class="yearReport.equilibre_global ? 'bg-emerald-100' : 'bg-red-100'">
                        <p><strong>Explication :</strong> {{ yearReport.verification_equilibre.explication }}</p>
                      </div>
                      <div class="mt-2 p-2 bg-gray-100 rounded text-xs">
                        <strong>Comment vérifier manuellement :</strong> Additionnez toutes les valeurs de la colonne
                        "Débit fin" de tous les comptes, puis additionnez toutes les valeurs de la colonne "Crédit fin".
                        Les deux totaux doivent être identiques.
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Explication de la vérification de la formule (si contrôle arithmétique) -->
              <div v-if="selectedControlType === 'arithmetique' && yearReport.verification_formule"
                :class="yearReport.verification_formule.statut === 'OK' ? 'mb-4 bg-emerald-50 border-l-4 border-emerald-400 rounded-md p-4' : 'mb-4 bg-amber-50 border-l-4 border-amber-400 rounded-md p-4'">
                <div class="flex items-start">
                  <div class="flex-shrink-0">
                    <svg v-if="yearReport.verification_formule.statut === 'OK'" class="h-6 w-6 text-emerald-500"
                      fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                    <svg v-else class="h-6 w-6 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z">
                      </path>
                    </svg>
                  </div>
                  <div class="ml-3 flex-1">
                    <h3
                      :class="yearReport.verification_formule.statut === 'OK' ? 'text-sm font-semibold text-emerald-800 mb-2' : 'text-sm font-semibold text-amber-800 mb-2'">
                      {{ yearReport.verification_formule.statut === 'OK' ? '✅' : '⚠️' }} Second Contrôle Arithmétique :
                      Vérification de la Formule
                    </h3>
                    <div
                      :class="yearReport.verification_formule.statut === 'OK' ? 'text-sm text-emerald-700 space-y-2' : 'text-sm text-amber-700 space-y-2'">
                      <p><strong>Formule vérifiée :</strong> Solde de clôture = Solde d'ouverture + Mouvements de
                        période</p>
                      <p class="ml-4">{{ yearReport.verification_formule.explication }}</p>
                      <div class="mt-3 grid grid-cols-3 gap-4 text-xs">
                        <div class="bg-white p-2 rounded border">
                          <span class="font-semibold">Comptes vérifiés :</span>
                          <span class="ml-2 font-bold">{{ yearReport.verification_formule.nb_comptes_verifies }}</span>
                        </div>
                        <div class="bg-white p-2 rounded border">
                          <span class="font-semibold">Formule respectée :</span>
                          <span class="ml-2 font-bold text-emerald-600">{{ yearReport.verification_formule.nb_comptes_ok
                          }}</span>
                        </div>
                        <div class="bg-white p-2 rounded border"
                          :class="yearReport.verification_formule.nb_comptes_erreur > 0 ? 'border-red-300 bg-red-50' : ''">
                          <span class="font-semibold">Formule non respectée :</span>
                          <span class="ml-2 font-bold text-red-600">{{ yearReport.verification_formule.nb_comptes_erreur
                          }}</span>
                        </div>
                      </div>
                      <div
                        v-if="yearReport.verification_formule.statut === 'ERREUR' && yearReport.verification_formule.nb_comptes_erreur > 0"
                        class="mt-3 p-3 bg-red-50 border border-red-200 rounded text-xs">
                        <p class="font-semibold text-red-800 mb-1">⚠️ Attention : Des erreurs ont été détectées</p>
                        <p class="text-red-700">Les comptes avec des erreurs de formule sont listés dans le tableau
                          ci-dessous. Chaque erreur indique l'écart exact entre le solde de clôture attendu et le solde
                          réel, ainsi que les détails des calculs.</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Structure complète du contrôle de vraisemblance -->
              <div
                v-if="selectedControlType === 'vraisemblance' && yearReport.verification_vraisemblance && yearReport.verification_vraisemblance.structure"
                class="space-y-6 mb-6">

                <!-- Résumé explicatif -->
                <div class="bg-white border-l-4 border-blue-ycube rounded-lg p-6 shadow-md">
                  <h2 class="text-xl font-bold text-blue-ycube mb-4 flex items-center gap-2">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z">
                      </path>
                    </svg>
                    Contrôle de Vraisemblance - Guide Complet
                  </h2>

                  <div class="space-y-4">
                    <div>
                      <h3 class="text-lg font-semibold text-blue-ycube mb-2">Objectif</h3>
                      <p class="text-blue-900">{{ yearReport.verification_vraisemblance.structure.resume.objectif }}</p>
                    </div>

                    <div>
                      <h3 class="text-lg font-semibold text-blue-ycube mb-2">Principes Généraux</h3>
                      <ul class="list-disc list-inside space-y-1 text-blue-900">
                        <li
                          v-for="(principe, index) in yearReport.verification_vraisemblance.structure.resume.principes_generaux"
                          :key="index">
                          {{ principe }}
                        </li>
                      </ul>
                    </div>
                  </div>
                </div>

                <!-- Tableau par classe (1 à 7) -->
                <div class="bg-white rounded-lg shadow-lg border border-gray-200 overflow-hidden">
                  <div class="bg-gradient-to-r from-blue-ycube to-blue-ycube-3 p-4">
                    <h2 class="text-xl font-bold text-white">Tableau par Classe de Comptes (1 à 7)</h2>
                  </div>

                  <div class="overflow-x-auto">
                    <table class="min-w-full divide-y divide-gray-200">
                      <thead class="bg-gray-50">
                        <tr>
                          <th class="px-4 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                            Classe</th>
                          <th class="px-4 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                            Nature des Comptes</th>
                          <th class="px-4 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">Sens
                            Normal du Solde</th>
                          <th class="px-4 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                            Exceptions et Cas Particuliers</th>
                          <th class="px-4 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                            Anomalies Détectées dans cette Balance</th>
                        </tr>
                      </thead>
                      <tbody class="bg-white divide-y divide-gray-200">
                        <tr v-for="classe in yearReport.verification_vraisemblance.structure.tableau_classes"
                          :key="classe.classe" class="hover:bg-gray-50">
                          <td class="px-4 py-4 whitespace-nowrap">
                            <div class="flex items-center">
                              <span
                                class="inline-flex items-center justify-center w-10 h-10 rounded-full bg-indigo-100 text-indigo-800 font-bold text-lg">
                                {{ classe.classe }}
                              </span>
                              <span class="ml-2 font-semibold text-gray-900">Classe {{ classe.classe }} - {{ classe.nom
                              }}</span>
                            </div>
                          </td>
                          <td class="px-4 py-4 text-sm text-gray-700">{{ classe.nature }}</td>
                          <td class="px-4 py-4 whitespace-nowrap">
                            <span class="px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full"
                              :class="classe.sens_normal === 'CRÉDITEUR' ? 'bg-gray-500 text-white' : 'bg-gray-200 text-gray-800'">
                              {{ classe.sens_normal }}
                            </span>
                          </td>
                          <td class="px-4 py-4 text-sm text-gray-700">
                            <ul class="list-disc list-inside space-y-1">
                              <li v-for="(exception, idx) in classe.exceptions" :key="idx" class="text-xs">{{ exception
                              }}</li>
                            </ul>
                          </td>
                          <td class="px-4 py-4 text-sm text-gray-700">
                            <div v-if="classe.anomalies_detectees && classe.anomalies_detectees.length > 0"
                              class="space-y-3">
                              <div v-for="(anomalie, idx) in classe.anomalies_detectees" :key="idx"
                                class="bg-red-50 border-l-4 border-red-500 p-3 rounded-lg shadow-sm">
                                <div class="flex items-start gap-2 mb-2">
                                  <svg class="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" fill="none"
                                    stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                      d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z">
                                    </path>
                                  </svg>
                                  <div class="flex-1">
                                    <div class="font-bold text-red-900 mb-1 text-sm">
                                      Compte {{ anomalie.compte }}
                                    </div>
                                    <div class="text-red-800 text-xs leading-relaxed whitespace-pre-line">
                                      {{ anomalie.message }}
                                    </div>
                                  </div>
                                </div>
                              </div>
                            </div>
                            <div v-else
                              class="text-xs text-emerald-700 bg-emerald-50 p-3 rounded-lg border border-emerald-200 flex items-center gap-2">
                              <svg class="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor"
                                viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                              </svg>
                              <span class="font-medium">Aucune anomalie détectée pour cette classe</span>
                            </div>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>

                <!-- Tableau des comptes à solder -->
                <div class="bg-white rounded-lg shadow-lg border border-gray-200 overflow-hidden">
                  <div class="bg-gradient-to-r from-red-500 to-orange-600 p-4">
                    <h2 class="text-xl font-bold text-white">Comptes à Solder Obligatoirement</h2>
                  </div>

                  <div class="overflow-x-auto">
                    <table class="min-w-full divide-y divide-gray-200">
                      <thead class="bg-gray-50">
                        <tr>
                          <th class="px-4 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                            Numéro du Compte</th>
                          <th class="px-4 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                            Libellé</th>
                          <th class="px-4 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                            Moment du Solde</th>
                          <th class="px-4 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                            Gravité si Non Soldé</th>
                          <th class="px-4 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                            Raison</th>
                        </tr>
                      </thead>
                      <tbody class="bg-white divide-y divide-gray-200">
                        <tr v-for="(compte, index) in yearReport.verification_vraisemblance.structure.comptes_a_solder"
                          :key="index" class="hover:bg-gray-50">
                          <td class="px-4 py-4 whitespace-nowrap">
                            <div class="flex flex-col">
                              <span
                                class="font-mono font-bold text-lg text-blue-900 bg-blue-50 px-3 py-1 rounded-md border border-blue-200">
                                {{ compte.numero.length === 1 ? `Classe ${compte.numero}` : compte.numero }}
                              </span>
                              <span v-if="compte.numero === '6' || compte.numero === '7'"
                                class="text-xs text-gray-600 mt-1 italic">(Tous les comptes de cette classe)</span>
                            </div>
                          </td>
                          <td class="px-4 py-4 text-sm text-gray-700 font-medium">{{ compte.libelle }}</td>
                          <td class="px-4 py-4 text-sm text-gray-700">{{ compte.moment }}</td>
                          <td class="px-4 py-4 whitespace-nowrap">
                            <span class="px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full" :class="compte.gravite === 'CRITIQUE' ? 'bg-red-100 text-red-800' :
                              compte.gravite === 'MOYENNE' ? 'bg-yellow-100 text-yellow-800' :
                                'bg-gray-100 text-gray-800'">
                              {{ compte.gravite }}
                            </span>
                          </td>
                          <td class="px-4 py-4 text-sm text-gray-700">{{ compte.raison }}</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>

              <!-- Affichage conditionnel selon le mode sélectionné -->

              <!-- VUE TABLEAU (mode par défaut) - Masqué pour le contrôle de vraisemblance -->
              <div
                v-if="viewMode === 'table' && selectedControlType !== 'vraisemblance' && yearReport.erreurs && yearReport.erreurs.length > 0"
                class="overflow-hidden rounded-xl shadow-xl bg-white border border-gray-100">
                <table class="min-w-full divide-y divide-gray-200">
                  <thead class="bg-gradient-to-r from-blue-ycube to-blue-ycube-3">
                    <tr>
                      <th class="px-6 py-4 text-left text-xs font-semibold text-white uppercase tracking-wider">Type
                        d'erreur</th>
                      <th class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider">Compte
                      </th>
                      <th class="px-6 py-4 text-left text-xs font-semibold text-white uppercase tracking-wider">Détails
                      </th>
                    </tr>
                  </thead>
                  <tbody class="bg-white divide-y divide-gray-200">
                    <tr v-for="(e, i) in yearReport.erreurs" :key="`${annee}-${i}`"
                      class="hover:bg-gradient-to-r hover:from-blue-50 hover:to-indigo-50 transition-all duration-200 group">
                      <td class="px-6 py-4 whitespace-nowrap">
                        <span
                          class="inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium shadow-sm transition-all duration-200"
                          :class="e.type === 'equilibre' ? 'bg-red-100 text-red-800 border border-red-300' :
                            e.type === 'identite' ? 'bg-orange-100 text-orange-800 border border-orange-300' :
                              e.type === 'signe' ? 'bg-yellow-100 text-yellow-800 border border-yellow-300' :
                                e.type === 'arithmetique' ? 'bg-pink-100 text-pink-800 border border-pink-300' :
                                  e.type === 'completude' ? 'bg-purple-100 text-purple-800 border border-purple-300' :
                                    e.type === 'compte_non_solde' ? (e.gravite === 'CRITIQUE' ? 'bg-red-200 text-red-900 border-2 border-red-500' : 'bg-amber-100 text-amber-800 border border-amber-300') :
                                      'bg-gray-100 text-gray-800 border border-gray-300'">
                          <span class="w-2 h-2 rounded-full mr-2" :class="e.type === 'equilibre' ? 'bg-red-500' :
                            e.type === 'identite' ? 'bg-orange-500' :
                              e.type === 'signe' ? 'bg-yellow-500' :
                                e.type === 'arithmetique' ? 'bg-pink-500' :
                                  e.type === 'completude' ? 'bg-purple-500' :
                                    e.type === 'compte_non_solde' ? (e.gravite === 'CRITIQUE' ? 'bg-red-600 animate-pulse' : 'bg-amber-500') :
                                      'bg-gray-500'"></span>
                          {{ getTypeLabel(e.type) }}
                          <span v-if="e.gravite === 'CRITIQUE'" class="ml-2 text-xs font-bold uppercase">⚠️
                            CRITIQUE</span>
                        </span>
                      </td>
                      <td class="px-6 py-4 whitespace-nowrap text-center">
                        <div v-if="e.numero_compte && e.numero_compte !== '-'"
                          class="inline-flex items-center px-3 py-1.5 bg-blue-50 rounded-md border border-blue-200 font-mono font-semibold text-blue-900 text-sm">
                          {{ e.numero_compte }}
                        </div>
                        <span v-else class="text-gray-400 text-sm">-</span>
                      </td>
                      <td class="px-6 py-4">
                        <!-- Affichage structuré pour les erreurs arithmétiques -->
                        <div v-if="e.type === 'arithmetique'" class="space-y-3">
                          <!-- En-tête avec compte et libellé -->
                          <div class="bg-gradient-to-r from-pink-50 to-rose-50 p-3 rounded-lg border border-pink-200">
                            <div class="flex items-center justify-between mb-2">
                              <div class="flex items-center gap-2">
                                <span class="text-xs font-semibold text-pink-800 uppercase">Compte</span>
                                <span class="font-mono font-bold text-pink-900">{{ e.numero_compte }}</span>
                              </div>
                              <span
                                class="text-xs px-2 py-1 bg-red-100 text-red-800 rounded-md font-bold border border-red-300">
                                🔴 Erreur détectée
                              </span>
                            </div>
                            <div v-if="extractLibelle(e.message)" class="text-sm text-gray-700 font-medium">
                              {{ extractLibelle(e.message) }}
                            </div>
                          </div>

                          <!-- Écart détecté -->
                          <div class="bg-red-50 p-3 rounded-lg border-l-4 border-red-500">
                            <div class="flex items-center gap-2 mb-1">
                              <span class="text-sm font-bold text-red-800">Écart détecté :</span>
                              <span class="text-lg font-bold text-red-900">{{ extractEcart(e.message) }}</span>
                            </div>
                            <p class="text-xs text-red-700 mt-1">{{ extractJustification(e.message) }}</p>
                          </div>

                          <!-- Détails des valeurs -->
                          <div class="grid grid-cols-2 gap-3">
                            <!-- Solde d'ouverture -->
                            <div class="bg-blue-50 p-3 rounded-lg border border-blue-200">
                              <div class="text-xs font-semibold text-blue-800 mb-1">Solde d'ouverture</div>
                              <div class="text-sm font-mono text-blue-900">{{ extractSoldeOuverture(e.message) }}</div>
                            </div>

                            <!-- Mouvements -->
                            <div class="bg-purple-50 p-3 rounded-lg border border-purple-200">
                              <div class="text-xs font-semibold text-purple-800 mb-1">Mouvements de période</div>
                              <div class="text-sm font-mono text-purple-900">{{ extractMouvements(e.message) }}</div>
                            </div>

                            <!-- Solde attendu -->
                            <div class="bg-emerald-50 p-3 rounded-lg border border-emerald-200">
                              <div class="text-xs font-semibold text-emerald-800 mb-1">Solde attendu</div>
                              <div class="text-sm font-mono text-emerald-900 font-bold">{{
                                extractSoldeAttendu(e.message) }}</div>
                            </div>

                            <!-- Solde réel -->
                            <div class="bg-amber-50 p-3 rounded-lg border border-amber-200">
                              <div class="text-xs font-semibold text-amber-800 mb-1">Solde réel</div>
                              <div class="text-sm font-mono text-amber-900 font-bold">{{ extractSoldeReel(e.message) }}
                              </div>
                            </div>
                          </div>

                          <!-- Formule -->
                          <div class="bg-gray-50 p-3 rounded-lg border border-gray-200">
                            <div class="text-xs font-semibold text-gray-700 mb-1">Formule vérifiée</div>
                            <div class="text-sm font-mono text-gray-800">
                              Solde de clôture = Solde d'ouverture + Mouvements de période
                            </div>
                          </div>
                        </div>

                        <!-- Affichage standard pour les autres types d'erreurs -->
                        <div v-else class="text-sm text-gray-700 leading-relaxed whitespace-pre-line"
                          :title="e.message || 'Aucun message'">
                          {{ e.message || 'Aucun message disponible' }}
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>

                <!-- Résumé final avec statut -->
                <div class="px-6 py-4 border-t-2 border-gray-200 bg-gray-50">
                  <div class="flex items-center justify-between">
                    <div class="flex items-center gap-4">
                      <div class="flex items-center gap-2">
                        <svg class="w-6 h-6 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z">
                          </path>
                        </svg>
                        <span class="text-base font-semibold text-red-700">⚠️ Anomalies détectées</span>
                      </div>
                      <div class="text-sm text-gray-600">
                        <span class="font-medium">{{ yearReport.erreurs.length }}</span> erreur(s) trouvée(s)
                      </div>
                    </div>
                    <div class="flex items-center gap-6" v-if="yearReport.totaux">
                      <template v-if="selectedControlType === 'arithmetique'">
                        <div class="text-sm">
                          <span class="text-gray-600">Équilibre:</span>
                          <span class="ml-2 font-semibold"
                            :class="yearReport.equilibre_global ? 'text-emerald-600' : 'text-red-600'">
                            {{ yearReport.equilibre_global ? '✅ OK' : '❌ Déséquilibré' }}
                          </span>
                        </div>
                        <div class="text-sm">
                          <span class="text-gray-600">Erreurs arithmétiques:</span>
                          <span class="ml-2 font-semibold text-pink-600">{{ yearReport.totaux.nb_erreurs_arithmetique ||
                            0 }}</span>
                        </div>
                      </template>
                      <template v-else-if="selectedControlType === 'vraisemblance'">
                        <div class="text-sm">
                          <span class="text-gray-600">Erreurs de signe:</span>
                          <span class="ml-2 font-semibold text-yellow-600">{{ yearReport.totaux.nb_erreurs_signe || 0
                          }}</span>
                        </div>
                        <div class="text-sm">
                          <span class="text-gray-600">Comptes non soldés:</span>
                          <span class="ml-2 font-semibold text-red-600">{{ yearReport.totaux.nb_erreurs_comptes_soldes
                            || 0 }}</span>
                        </div>
                      </template>
                    </div>
                  </div>
                </div>
              </div>

              <!-- VUE CARTES - Masquée pour le contrôle de vraisemblance -->
              <div
                v-else-if="viewMode === 'cards' && selectedControlType !== 'vraisemblance' && yearReport.erreurs && yearReport.erreurs.length > 0"
                class="space-y-4">
                <!-- Résumé statistique -->
                <div class="bg-gradient-to-r from-gray-50 to-gray-100 rounded-lg p-4 border border-gray-200">
                  <div class="flex items-center justify-between flex-wrap gap-4">
                    <div class="flex items-center gap-4">
                      <div class="flex items-center gap-2">
                        <svg class="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z">
                          </path>
                        </svg>
                        <span class="text-sm font-semibold text-gray-700">{{ yearReport.erreurs.length }} erreur(s)
                          détectée(s)</span>
                      </div>
                    </div>
                    <div class="flex items-center gap-6 text-xs" v-if="yearReport.totaux">
                      <template v-if="selectedControlType === 'arithmetique'">
                        <span class="text-gray-600">Équilibre: <span
                            :class="yearReport.equilibre_global ? 'text-emerald-600' : 'text-red-600'"
                            class="font-semibold">{{ yearReport.equilibre_global ? '✅ OK' : '❌ Déséquilibré'
                            }}</span></span>
                        <span class="text-gray-600">Erreurs arithmétiques: <span class="font-semibold text-pink-600">{{
                          yearReport.totaux.nb_erreurs_arithmetique || 0 }}</span></span>
                      </template>
                      <template v-else-if="selectedControlType === 'vraisemblance'">
                        <span class="text-gray-600">Erreurs de signe: <span class="font-semibold text-yellow-600">{{
                          yearReport.totaux.nb_erreurs_signe || 0 }}</span></span>
                        <span class="text-gray-600">Comptes non soldés: <span class="font-semibold text-red-600">{{
                          yearReport.totaux.nb_erreurs_comptes_soldes || 0 }}</span></span>
                      </template>
                    </div>
                  </div>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  <div v-for="(e, i) in yearReport.erreurs" :key="`${annee}-${i}`"
                    class="bg-white rounded-lg shadow-md border-l-4 p-5 hover:shadow-lg transition-shadow duration-200"
                    :class="e.type === 'equilibre' ? 'border-red-500' :
                      e.type === 'identite' ? 'border-orange-500' :
                        e.type === 'signe' ? 'border-yellow-500' :
                          e.type === 'arithmetique' ? 'border-pink-500' :
                            e.type === 'compte_non_solde' ? (e.gravite === 'CRITIQUE' ? 'border-red-600' : 'border-amber-500') :
                              'border-gray-500'">
                    <div class="flex items-start justify-between mb-3">
                      <div class="flex items-center gap-2">
                        <span class="w-3 h-3 rounded-full" :class="e.type === 'equilibre' ? 'bg-red-500' :
                          e.type === 'identite' ? 'bg-orange-500' :
                            e.type === 'signe' ? 'bg-yellow-500' :
                              e.type === 'arithmetique' ? 'bg-pink-500' :
                                e.type === 'compte_non_solde' ? (e.gravite === 'CRITIQUE' ? 'bg-red-600 animate-pulse' : 'bg-amber-500') :
                                  'bg-gray-500'"></span>
                        <h4 class="font-semibold text-gray-900">{{ getTypeLabel(e.type) }}</h4>
                      </div>
                      <span v-if="e.gravite === 'CRITIQUE'" class="text-xs font-bold text-red-600 uppercase">⚠️
                        CRITIQUE</span>
                    </div>
                    <div v-if="e.numero_compte && e.numero_compte !== '-'" class="mb-3">
                      <span class="text-xs text-gray-500">Compte :</span>
                      <span class="ml-2 px-2 py-1 bg-blue-50 rounded font-mono text-sm font-semibold text-blue-900">
                        {{ e.numero_compte }}
                      </span>
                    </div>

                    <!-- Affichage structuré pour les erreurs arithmétiques -->
                    <div v-if="e.type === 'arithmetique'" class="space-y-2">
                      <div class="bg-red-50 p-2 rounded border-l-3 border-red-500">
                        <div class="text-xs font-bold text-red-800">Écart : {{ extractEcart(e.message) }}</div>
                      </div>
                      <div class="grid grid-cols-2 gap-2 text-xs">
                        <div class="bg-blue-50 p-2 rounded">
                          <div class="font-semibold text-blue-800">Solde d'ouverture</div>
                          <div class="text-blue-900 font-mono">{{ extractSoldeOuverture(e.message) }}</div>
                        </div>
                        <div class="bg-purple-50 p-2 rounded">
                          <div class="font-semibold text-purple-800">Mouvements</div>
                          <div class="text-purple-900 font-mono text-xs">{{ extractMouvements(e.message) }}</div>
                        </div>
                        <div class="bg-emerald-50 p-2 rounded">
                          <div class="font-semibold text-emerald-800">Solde attendu</div>
                          <div class="text-emerald-900 font-mono font-bold">{{ extractSoldeAttendu(e.message) }}</div>
                        </div>
                        <div class="bg-amber-50 p-2 rounded">
                          <div class="font-semibold text-amber-800">Solde réel</div>
                          <div class="text-amber-900 font-mono font-bold">{{ extractSoldeReel(e.message) }}</div>
                        </div>
                      </div>
                    </div>

                    <!-- Affichage standard pour les autres types -->
                    <div v-else class="text-sm text-gray-700 leading-relaxed whitespace-pre-line line-clamp-4">
                      {{ e.message || 'Aucun message disponible' }}
                    </div>
                  </div>
                </div>
              </div>

              <!-- VUE GRAPHIQUE - Masquée pour le contrôle de vraisemblance -->
              <div
                v-else-if="viewMode === 'graph' && selectedControlType !== 'vraisemblance' && yearReport.erreurs && yearReport.erreurs.length > 0"
                class="space-y-6">
                <!-- Résumé statistique -->
                <div class="bg-gradient-to-r from-gray-50 to-gray-100 rounded-lg p-4 border border-gray-200">
                  <div class="flex items-center justify-between flex-wrap gap-4">
                    <div class="flex items-center gap-4">
                      <div class="flex items-center gap-2">
                        <svg class="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z">
                          </path>
                        </svg>
                        <span class="text-sm font-semibold text-gray-700">{{ yearReport.erreurs.length }} erreur(s)
                          détectée(s)</span>
                      </div>
                    </div>
                    <div class="flex items-center gap-6 text-xs" v-if="yearReport.totaux">
                      <template v-if="selectedControlType === 'arithmetique'">
                        <span class="text-gray-600">Équilibre: <span
                            :class="yearReport.equilibre_global ? 'text-emerald-600' : 'text-red-600'"
                            class="font-semibold">{{ yearReport.equilibre_global ? '✅ OK' : '❌ Déséquilibré'
                            }}</span></span>
                        <span class="text-gray-600">Erreurs arithmétiques: <span class="font-semibold text-pink-600">{{
                          yearReport.totaux.nb_erreurs_arithmetique || 0 }}</span></span>
                      </template>
                      <template v-else-if="selectedControlType === 'vraisemblance'">
                        <span class="text-gray-600">Erreurs de signe: <span class="font-semibold text-yellow-600">{{
                          yearReport.totaux.nb_erreurs_signe || 0 }}</span></span>
                        <span class="text-gray-600">Comptes non soldés: <span class="font-semibold text-red-600">{{
                          yearReport.totaux.nb_erreurs_comptes_soldes || 0 }}</span></span>
                      </template>
                    </div>
                  </div>
                </div>

                <!-- Graphique en barres par type d'erreur -->
                <div class="bg-white rounded-xl shadow-lg border border-gray-200 p-6">
                  <h3 class="text-lg font-semibold text-gray-900 mb-4">Répartition des erreurs par type</h3>
                  <div class="space-y-4">
                    <div v-for="(errors, type) in errorsByType" :key="type" class="flex items-center gap-4">
                      <div class="w-32 text-sm font-medium text-gray-700">{{ getTypeLabel(type) }}</div>
                      <div class="flex-1 bg-gray-200 rounded-full h-8 relative overflow-hidden">
                        <div class="h-full rounded-full flex items-center justify-end pr-2 transition-all duration-500"
                          :class="type === 'equilibre' ? 'bg-red-500' :
                            type === 'identite' ? 'bg-orange-500' :
                              type === 'signe' ? 'bg-yellow-500' :
                                type === 'arithmetique' ? 'bg-pink-500' :
                                  type === 'compte_non_solde' ? 'bg-amber-500' :
                                    'bg-gray-500'"
                          :style="{ width: `${(errors.length / yearReport.erreurs.length) * 100}%` }">
                          <span class="text-xs font-semibold text-white">{{ errors.length }}</span>
                        </div>
                      </div>
                      <div class="w-16 text-right text-sm font-semibold text-gray-700">
                        {{ Math.round((errors.length / yearReport.erreurs.length) * 100) }}%
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Liste des erreurs groupées par type -->
                <div v-for="(errors, type) in errorsByType" :key="type"
                  class="bg-white rounded-xl shadow-lg border border-gray-200 p-6">
                  <h4 class="text-md font-semibold text-gray-900 mb-4 flex items-center gap-2">
                    <span class="w-3 h-3 rounded-full" :class="type === 'equilibre' ? 'bg-red-500' :
                      type === 'identite' ? 'bg-orange-500' :
                        type === 'signe' ? 'bg-yellow-500' :
                          type === 'arithmetique' ? 'bg-pink-500' :
                            type === 'compte_non_solde' ? 'bg-amber-500' :
                              'bg-gray-500'"></span>
                    {{ getTypeLabel(type) }} ({{ errors.length }})
                  </h4>
                  <div class="space-y-3">
                    <div v-for="(e, i) in errors" :key="`${type}-${i}`"
                      class="p-4 bg-gray-50 rounded-lg border border-gray-200">
                      <div class="flex items-center justify-between mb-2">
                        <span v-if="e.numero_compte && e.numero_compte !== '-'"
                          class="px-3 py-1 bg-blue-50 rounded font-mono text-sm font-semibold text-blue-900">
                          {{ e.numero_compte }}
                        </span>
                        <span v-else class="text-gray-400 text-sm">-</span>
                        <span v-if="e.gravite === 'CRITIQUE'" class="text-xs font-bold text-red-600 uppercase">⚠️
                          CRITIQUE</span>
                      </div>

                      <!-- Affichage structuré pour les erreurs arithmétiques -->
                      <div v-if="e.type === 'arithmetique'" class="space-y-2">
                        <div class="bg-red-50 p-2 rounded border-l-3 border-red-500">
                          <div class="text-xs font-bold text-red-800">Écart : {{ extractEcart(e.message) }}</div>
                        </div>
                        <div class="grid grid-cols-2 gap-2 text-xs">
                          <div class="bg-blue-50 p-2 rounded">
                            <div class="font-semibold text-blue-800">Solde d'ouverture</div>
                            <div class="text-blue-900 font-mono">{{ extractSoldeOuverture(e.message) }}</div>
                          </div>
                          <div class="bg-purple-50 p-2 rounded">
                            <div class="font-semibold text-purple-800">Mouvements</div>
                            <div class="text-purple-900 font-mono text-xs">{{ extractMouvements(e.message) }}</div>
                          </div>
                          <div class="bg-emerald-50 p-2 rounded">
                            <div class="font-semibold text-emerald-800">Solde attendu</div>
                            <div class="text-emerald-900 font-mono font-bold">{{ extractSoldeAttendu(e.message) }}</div>
                          </div>
                          <div class="bg-amber-50 p-2 rounded">
                            <div class="font-semibold text-amber-800">Solde réel</div>
                            <div class="text-amber-900 font-mono font-bold">{{ extractSoldeReel(e.message) }}</div>
                          </div>
                        </div>
                      </div>

                      <!-- Affichage standard pour les autres types -->
                      <div v-else class="text-sm text-gray-700 leading-relaxed whitespace-pre-line">
                        {{ e.message || 'Aucun message disponible' }}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- VUE COMPACTE - Masquée pour le contrôle de vraisemblance -->
              <div
                v-else-if="viewMode === 'compact' && selectedControlType !== 'vraisemblance' && yearReport.erreurs && yearReport.erreurs.length > 0"
                class="space-y-3">
                <!-- Résumé statistique compact -->
                <div
                  class="bg-gray-50 rounded-lg p-3 border border-gray-200 flex items-center justify-between flex-wrap gap-2 text-xs">
                  <span class="font-semibold text-gray-700">{{ yearReport.erreurs.length }} erreur(s)</span>
                  <div class="flex items-center gap-4" v-if="yearReport.totaux">
                    <template v-if="selectedControlType === 'arithmetique'">
                      <span>Équilibre: <span :class="yearReport.equilibre_global ? 'text-emerald-600' : 'text-red-600'"
                          class="font-semibold">{{ yearReport.equilibre_global ? 'OK' : 'Déséquilibré' }}</span></span>
                      <span>Arithmétique: <span class="font-semibold text-pink-600">{{
                        yearReport.totaux.nb_erreurs_arithmetique || 0 }}</span></span>
                    </template>
                    <template v-else-if="selectedControlType === 'vraisemblance'">
                      <span>Signe: <span class="font-semibold text-yellow-600">{{ yearReport.totaux.nb_erreurs_signe ||
                        0 }}</span></span>
                      <span>Non soldés: <span class="font-semibold text-red-600">{{
                        yearReport.totaux.nb_erreurs_comptes_soldes || 0 }}</span></span>
                    </template>
                  </div>
                </div>

                <div class="space-y-2">
                  <div v-for="(e, i) in yearReport.erreurs" :key="`${annee}-${i}`"
                    class="flex items-start gap-3 p-3 bg-white rounded-lg border border-gray-200 hover:border-blue-300 hover:shadow-md transition-all">
                    <span class="w-2 h-2 rounded-full mt-2 flex-shrink-0" :class="e.type === 'equilibre' ? 'bg-red-500' :
                      e.type === 'identite' ? 'bg-orange-500' :
                        e.type === 'signe' ? 'bg-yellow-500' :
                          e.type === 'arithmetique' ? 'bg-pink-500' :
                            e.type === 'compte_non_solde' ? (e.gravite === 'CRITIQUE' ? 'bg-red-600 animate-pulse' : 'bg-amber-500') :
                              'bg-gray-500'"></span>
                    <div class="flex-1 min-w-0">
                      <div class="flex items-center gap-2 mb-1">
                        <span class="text-sm font-semibold text-gray-900">{{ getTypeLabel(e.type) }}</span>
                        <span v-if="e.numero_compte && e.numero_compte !== '-'"
                          class="px-2 py-0.5 bg-blue-50 rounded font-mono text-xs font-semibold text-blue-900">
                          {{ e.numero_compte }}
                        </span>
                        <span v-if="e.gravite === 'CRITIQUE'" class="text-xs font-bold text-red-600 uppercase">⚠️
                          CRITIQUE</span>
                      </div>

                      <!-- Affichage structuré pour les erreurs arithmétiques -->
                      <div v-if="e.type === 'arithmetique'" class="space-y-1.5 text-xs">
                        <div class="bg-red-50 p-1.5 rounded border-l-2 border-red-500">
                          <span class="font-bold text-red-800">Écart : {{ extractEcart(e.message) }}</span>
                        </div>
                        <div class="grid grid-cols-2 gap-1.5">
                          <div class="bg-blue-50 p-1.5 rounded">
                            <div class="font-semibold text-blue-800 text-[10px]">Solde d'ouverture</div>
                            <div class="text-blue-900 font-mono text-[10px]">{{ extractSoldeOuverture(e.message) }}
                            </div>
                          </div>
                          <div class="bg-emerald-50 p-1.5 rounded">
                            <div class="font-semibold text-emerald-800 text-[10px]">Solde attendu</div>
                            <div class="text-emerald-900 font-mono font-bold text-[10px]">{{
                              extractSoldeAttendu(e.message) }}</div>
                          </div>
                          <div class="bg-amber-50 p-1.5 rounded">
                            <div class="font-semibold text-amber-800 text-[10px]">Solde réel</div>
                            <div class="text-amber-900 font-mono font-bold text-[10px]">{{ extractSoldeReel(e.message)
                            }}</div>
                          </div>
                          <div class="bg-purple-50 p-1.5 rounded">
                            <div class="font-semibold text-purple-800 text-[10px]">Mouvements</div>
                            <div class="text-purple-900 font-mono text-[10px]">{{ extractMouvements(e.message) }}</div>
                          </div>
                        </div>
                      </div>

                      <!-- Affichage standard pour les autres types -->
                      <div v-else class="text-xs text-gray-600 line-clamp-2">
                        {{ e.message || 'Aucun message disponible' }}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Message si aucune erreur - Masqué pour le contrôle de vraisemblance -->
              <div v-else-if="selectedControlType !== 'vraisemblance'"
                class="bg-emerald-50 border border-emerald-200 rounded-lg p-6 text-center">
                <div class="flex items-center justify-center gap-3">
                  <svg class="w-8 h-8 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                  </svg>
                  <div>
                    <h3 class="text-lg font-semibold text-emerald-800">Aucune erreur détectée</h3>
                    <p class="text-sm text-emerald-700 mt-1">
                      Tous les {{ selectedControlType === 'arithmetique' ? 'contrôles arithmétiques' : 'contrôles de vraisemblance' }}
                      sont passés avec succès pour l'année {{ annee }}
                    </p>
                  </div>
                </div>
              </div>
            </template>
          </div>
        </div>

        <!-- Contrôle d'intangibilité -->
        <div v-if="componentKey === 'intang'">
          <div class="flex justify-between items-center mb-3">
            <h2 class="text-xl font-semibold">Contrôle d'intangibilité</h2>
          </div>
          <div v-if="!intangibiliteReport && !loading" class="text-sm text-gray-600">Aucune donnée.</div>
          <div v-else-if="intangibiliteReport?.message && !intangibiliteReport.ok"
            class="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
            <div class="text-sm text-red-700 font-semibold mb-2">⚠️ Erreur du contrôle d'intangibilité</div>
            <div class="text-sm text-red-600">{{ intangibiliteReport.message }}</div>
            <div v-if="intangibiliteReport.periodes" class="text-xs text-gray-500 mt-2">
              Périodes : N = {{ intangibiliteReport.periodes.N }}, N-1 = {{ intangibiliteReport.periodes['N-1'] }}
            </div>
          </div>
          <div v-else-if="intangibiliteReport && intangibiliteReport.ok !== undefined">
            <div class="text-sm mb-3" :class="intangibiliteReport.ok ? 'text-green-700' : 'text-red-700'">
              {{ intangibiliteReport.ok ? '✅ Aucun écart relevé' : `⚠️ ${intangibiliteReport.ecarts_count || 0} écart(s)
              détecté(s) sur ${intangibiliteReport.total_comptes || 0} compte(s)` }}
            </div>
            <div v-if="intangibiliteReport.periodes" class="text-xl text-blue-ycube mb-3">
              Périodes analysées : N = {{ intangibiliteReport.periodes.N }}, N-1 = {{
                intangibiliteReport.periodes['N-1'] }}
            </div>
            <button v-if="intangibiliteReport && intangibiliteReport.comptes && intangibiliteReport.comptes.length > 0"
              @click="exportToCsv(intangibiliteReport.comptes, 'controle_intangibilite')"
              class="mb-3 px-4 py-2 bg-green-ycube text-white rounded-md shadow-md">Télécharger (CSV)</button>

            <!-- Afficher un message si le rapport existe mais n'a pas de comptes -->
            <div
              v-if="intangibiliteReport && intangibiliteReport.comptes !== undefined && intangibiliteReport.comptes.length === 0"
              class="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
              <div class="text-sm text-yellow-700 font-semibold mb-2">⚠️ Aucun compte trouvé</div>
              <div class="text-sm text-yellow-600">{{ intangibiliteReport.message || "Aucun compte n'a été trouvé dans les balances pour le contrôle d'intangibilité." }}</div>
            </div>

            <div
              v-else-if="intangibiliteReport && intangibiliteReport.comptes && intangibiliteReport.comptes.length > 0"
              class="overflow-hidden rounded-xl shadow-xl bg-white border border-gray-100">
              <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gradient-to-r from-blue-ycube  to-blue-ycube-3">
                  <tr>
                    <th class="px-6 py-4 text-left text-xs font-semibold text-white uppercase tracking-wider">Compte
                    </th>
                    <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">Bilan
                      ouverture
                      (N)</th>
                    <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">Bilan
                      clôture
                      (N-1)</th>
                    <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">Écarts
                    </th>
                    <th class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider">Statut
                    </th>
                    <th class="px-6 py-4 text-left text-xs font-semibold text-white uppercase tracking-wider">
                      Explications probables</th>
                    <th class="px-6 py-4 text-left text-xs font-semibold text-white uppercase tracking-wider">Conclusion
                      audit
                    </th>
                  </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                  <tr v-for="(e, i) in intangibiliteReport.comptes" :key="i"
                    class="hover:bg-gradient-to-r hover:from-blue-50 hover:to-indigo-50 transition-all duration-300 group transform hover:scale-[1.01] hover:shadow-md"
                    :class="e.status === 'ok' ? 'bg-green-50' : e.status === 'ecart' ? 'bg-red-50' : e.status === 'nouveau' ? 'bg-blue-50' : e.status === 'supprime' ? 'bg-yellow-50' : ''">
                    <td class="px-6 py-4 whitespace-nowrap">
                      <div class="flex items-center">
                        <div
                          class="flex-shrink-0 h-8 w-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center mr-3 group-hover:scale-110 transition-transform duration-200">
                          <span class="text-xs font-bold text-white">{{ e.numero_compte.charAt(0) }}</span>
                        </div>
                        <div
                          class="text-sm font-mono font-bold text-gray-900 group-hover:text-blue-700 transition-colors duration-200">
                          {{ e.numero_compte }}</div>
                      </div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-right">
                      <div
                        class="text-sm font-mono text-gray-900 group-hover:text-blue-700 transition-colors duration-200">
                        {{
                          formatAmount(e.ouverture_n) }}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-right">
                      <div
                        class="text-sm font-mono text-gray-900 group-hover:text-blue-700 transition-colors duration-200">
                        {{ e.cloture_n1 !== null ? formatAmount(e.cloture_n1) : 'N/A' }}
                      </div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-right">
                      <div
                        class="text-sm font-mono font-semibold transform group-hover:scale-105 transition-all duration-200"
                        :class="e.ecart >= 0 ? 'text-emerald-600' : 'text-red-600'">
                        {{ formatAmount(e.ecart) }}
                      </div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-center">
                      <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium" :class="e.status === 'ok' ? 'bg-green-100 text-green-800' :
                        e.status === 'ecart' ? 'bg-red-100 text-red-800' :
                          e.status === 'nouveau' ? 'bg-blue-100 text-blue-800' :
                            e.status === 'supprime' ? 'bg-yellow-100 text-yellow-800' : 'bg-gray-100 text-gray-800'">
                        {{ e.status === 'ok' ? '✓ OK' :
                          e.status === 'ecart' ? '⚠ Écart' :
                            e.status === 'nouveau' ? '🆕 Nouveau' :
                              e.status === 'supprime' ? '🗑 Supprimé' : '?' }}
                      </span>
                    </td>
                    <td class="px-6 py-4">
                      <div v-if="e.justification && e.justification !== '-'" class="max-w-sm">
                        <div
                          class="bg-blue-50 border border-blue-200 rounded-lg p-3 group-hover:bg-blue-100 transition-colors duration-200">
                          <div class="flex items-start space-x-2">
                            <div class="flex-shrink-0">
                              <svg class="w-4 h-4 text-blue-600 mt-0.5" fill="none" stroke="currentColor"
                                viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z">
                                </path>
                              </svg>
                            </div>
                            <div class="flex-1 min-w-0">
                              <p class="text-sm text-gray-700 leading-relaxed">{{ e.justification }}</p>
                            </div>
                          </div>
                        </div>
                      </div>
                      <div v-else class="text-sm text-gray-500 italic">Aucune justification</div>
                    </td>
                    <td class="px-6 py-4">
                      <div v-if="e.conclusion_audit && e.conclusion_audit !== '-'" class="max-w-sm">
                        <div
                          class="bg-emerald-50 border border-emerald-200 rounded-lg p-3 group-hover:bg-emerald-100 transition-colors duration-200">
                          <div class="flex items-start space-x-2">
                            <div class="flex-shrink-0">
                              <svg class="w-4 h-4 text-emerald-600 mt-0.5" fill="none" stroke="currentColor"
                                viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                              </svg>
                            </div>
                            <div class="flex-1 min-w-0">
                              <p class="text-xs font-medium text-emerald-800 mb-1">Conclusion Audit</p>
                              <p class="text-sm text-gray-700 leading-relaxed">{{ e.conclusion_audit }}</p>
                            </div>
                          </div>
                        </div>
                      </div>
                      <div v-else class="text-sm text-gray-500 italic">Aucune conclusion</div>
                    </td>
                  </tr>
                </tbody>
              </table>
              <div class="text-xs text-gray-500 mt-2 ml-1">Astuce : survolez une ligne pour la mettre en évidence,
                utilisez Tab
                pour naviguer.</div>
            </div>
            <div v-else-if="intangibiliteReport && !intangibiliteReport.comptes"
              class="overflow-hidden rounded-xl shadow-xl bg-white border border-gray-100">
              <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gradient-to-r from-indigo-600 via-blue-600 to-cyan-600">
                  <tr>
                    <th class="px-6 py-4 text-left text-xs font-semibold text-white uppercase tracking-wider">Compte
                    </th>
                    <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">Bilan
                      ouverture
                      (N)</th>
                    <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">Bilan
                      clôture
                      (N-1)</th>
                    <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">Écarts
                    </th>
                    <th class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider">Statut
                    </th>
                    <th class="px-6 py-4 text-left text-xs font-semibold text-white uppercase tracking-wider">
                      Justification</th>
                    <th class="px-6 py-4 text-left text-xs font-semibold text-white uppercase tracking-wider">Conclusion
                      audit
                    </th>
                  </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                  <tr class="hover:bg-gradient-to-r hover:from-gray-50 hover:to-gray-100 transition-all duration-300">
                    <td colspan="7" class="px-6 py-8 text-center">
                      <div class="flex flex-col items-center space-y-3">
                        <div class="flex-shrink-0">
                          <svg class="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                              d="M9.172 16.172a4 4 0 015.656 0M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z">
                            </path>
                          </svg>
                        </div>
                        <div class="text-center">
                          <h3 class="text-lg font-semibold text-gray-800 mb-2">Aucun compte trouvé</h3>
                          <p class="text-sm text-gray-600">Aucun compte n'a été trouvé pour le contrôle d'intangibilité.
                            Vérifiez que les balances N et N-1 sont bien importées.</p>
                        </div>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- Étape 3: Variation des comptes par rubrique -->
        <div v-if="componentKey === 'classement'">
          <div class="flex justify-between items-center mb-3">
            <h2 class="text-xl font-semibold">Variation des comptes par rubrique</h2>
            <button @click="reloadClassement"
              class="px-4 py-2 bg-gray-ycube text-white rounded-md shadow-md hover:bg-blue-700 transition-colors">
              Recharger
            </button>
          </div>

          <div v-if="!classementBilanReport && !loading" class="text-sm text-gray-600">Aucune donnée.</div>
          <div v-else-if="classementBilanReport?.message" class="text-sm text-red-700 mb-3">
            {{ classementBilanReport.message }}
          </div>



          <div v-if="classementBilanReport && classementBilanReport.ok" class="space-y-4">
            <!-- Informations générales -->
            <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 class="text-lg font-semibold text-blue-800 mb-2">Variation des comptes par rubrique</h3>
              <p class="text-blue-700 text-sm mb-2">{{ classementBilanReport.message }}</p>
              <p class="text-blue-600 text-xs">Référentiel: {{ classementBilanReport.referentiel || 'syscohada' }}</p>

            </div>

            <!-- Bouton d'export -->
            <button v-if="classementBilanReport.classement && classementBilanReport.classement.length"
              @click="exportToCsv(classementBilanReport.classement, 'classement_bilan')"
              class="mb-3 px-4 py-2 bg-green-ycube text-white rounded-md shadow-md hover:bg-green-600 transition-colors">
              Télécharger (CSV)
            </button>

            <!-- Barre d'outils du tableau -->
            <div v-if="classementBilanReport.classement && classementBilanReport.classement.length"
              class="mb-6 bg-white rounded-xl shadow-sm border border-gray-200 p-4">
              <div class="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
                <!-- Recherche -->
                <div class="relative flex-1 max-w-md">
                  <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <svg class="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                    </svg>
                  </div>
                  <input v-model="searchQuery" type="text" placeholder="Rechercher par compte ou libellé..."
                    class="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-sm transition-all duration-200">
                </div>

                <!-- Filtres -->
                <div class="flex gap-2">
                  <select v-model="natureFilter"
                    class="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200">
                    <option value="">Toutes les natures</option>
                    <option value="bilan">Bilan</option>
                    <option value="pnl">Résultat (PNL)</option>
                  </select>

                  <select v-model="variationFilter"
                    class="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200">
                    <option value="">Toutes les variations</option>
                    <option value="positive">Variations positives</option>
                    <option value="negative">Variations négatives</option>
                    <option value="high">Variations importantes (>20%)</option>
                  </select>
                </div>

                <!-- Statistiques -->
                <div class="text-sm text-gray-600">
                  <span class="font-medium">{{ filteredData.length }}</span> résultats sur <span class="font-medium">{{
                    classementBilanReport.classement.length }}</span>
                </div>

                <!-- Bouton réinitialiser les filtres -->
                <button v-if="searchQuery || natureFilter || variationFilter" @click="resetFilters"
                  class="px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-lg hover:bg-gray-200 transition-colors duration-200">
                  Réinitialiser
                </button>
              </div>
            </div>

            <!-- Tableau de classement -->
            <div v-if="classementBilanReport.classement && classementBilanReport.classement.length"
              class="overflow-hidden rounded-xl shadow-xl bg-white border border-gray-100">
              <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gradient-to-r from-blue-ycube  to-blue-ycube-3">
                  <tr>
                    <th
                      class="px-6 py-4 text-left text-xs font-semibold text-white uppercase tracking-wider cursor-pointer hover:bg-blue-700 transition-colors duration-200"
                      @click="sortBy('compte')">
                      <div class="flex items-center space-x-1">
                        <span>Compte</span>
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4"></path>
                        </svg>
                      </div>
                    </th>
                    <th
                      class="px-6 py-4 text-left text-xs font-semibold text-white uppercase tracking-wider cursor-pointer hover:bg-blue-700 transition-colors duration-200"
                      @click="sortBy('libelle')">
                      <div class="flex items-center space-x-1">
                        <span>Libellé</span>
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4"></path>
                        </svg>
                      </div>
                    </th>
                    <th
                      class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider cursor-pointer hover:bg-blue-700 transition-colors duration-200"
                      @click="sortBy('nature')">
                      <div class="flex items-center justify-center space-x-1">
                        <span>Nature</span>
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4"></path>
                        </svg>
                      </div>
                    </th>
                    <th
                      class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider cursor-pointer hover:bg-blue-700 transition-colors duration-200"
                      @click="sortBy('solde_n')">
                      <div class="flex items-center justify-end space-x-1">
                        <span>N</span>
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4"></path>
                        </svg>
                      </div>
                    </th>
                    <th
                      class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider cursor-pointer hover:bg-blue-700 transition-colors duration-200"
                      @click="sortBy('solde_n1')">
                      <div class="flex items-center justify-end space-x-1">
                        <span>N-1</span>
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4"></path>
                        </svg>
                      </div>
                    </th>
                    <th
                      class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider cursor-pointer hover:bg-blue-700 transition-colors duration-200"
                      @click="sortBy('variation')">
                      <div class="flex items-center justify-end space-x-1">
                        <span>Variation</span>
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4"></path>
                        </svg>
                      </div>
                    </th>
                    <th
                      class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider cursor-pointer hover:bg-blue-700 transition-colors duration-200"
                      @click="sortBy('variation_percent')">
                      <div class="flex items-center justify-center space-x-1">
                        <span>Variation %</span>
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4"></path>
                        </svg>
                      </div>
                    </th>
                    <th class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider">Actions
                    </th>
                  </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                  <template v-for="(item, index) in filteredData" :key="index">
                    <!-- Ligne principale -->
                    <tr
                      class="hover:bg-gradient-to-r hover:from-blue-50 hover:to-indigo-50 transition-all duration-300 group transform hover:scale-[1.01] hover:shadow-md">
                      <td class="px-6 py-4 whitespace-nowrap">
                        <div class="flex items-center">
                          <div
                            class="flex-shrink-0 h-8 w-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center mr-3 group-hover:scale-110 transition-transform duration-200">
                            <span class="text-xs font-bold text-white">{{ item.compte.charAt(0) }}</span>
                          </div>
                          <div
                            class="text-sm font-mono font-bold text-gray-900 group-hover:text-blue-700 transition-colors duration-200">
                            {{ item.compte }}</div>
                        </div>
                      </td>
                      <td class="px-6 py-4">
                        <div
                          class="text-sm text-gray-900 max-w-xs truncate group-hover:text-blue-700 transition-colors duration-200"
                          :title="item.libelle">{{ item.libelle }}</div>
                      </td>
                      <td class="px-6 py-4 whitespace-nowrap text-center">
                        <span
                          class="inline-flex px-3 py-1 rounded-full text-xs font-medium shadow-sm transform group-hover:scale-105 transition-all duration-200"
                          :class="item.nature === 'bilan' ? 'bg-gradient-to-r from-blue-100 to-blue-200 text-blue-800 border border-blue-300' : 'bg-gradient-to-r from-emerald-100 to-emerald-200 text-emerald-800 border border-emerald-300'">
                          <span class="w-2 h-2 rounded-full mr-2"
                            :class="item.nature === 'bilan' ? 'bg-blue-500' : 'bg-emerald-500'"></span>
                          {{ item.nature }}
                        </span>
                      </td>
                      <td class="px-6 py-4 whitespace-nowrap text-right">
                        <div
                          class="text-sm font-mono text-gray-900 group-hover:text-blue-700 transition-colors duration-200">
                          {{ formatAmount(item.solde_n) }}</div>
                      </td>
                      <td class="px-6 py-4 whitespace-nowrap text-right">
                        <div
                          class="text-sm font-mono text-gray-900 group-hover:text-blue-700 transition-colors duration-200">
                          {{ formatAmount(item.solde_n1) }}</div>
                      </td>
                      <td class="px-6 py-4 whitespace-nowrap text-right">
                        <div class="flex items-center justify-end">
                          <div
                            class="text-sm font-mono font-semibold transform group-hover:scale-105 transition-all duration-200"
                            :class="item.variation >= 0 ? 'text-emerald-600' : 'text-red-600'">
                            {{ formatAmount(item.variation) }}
                          </div>
                          <div class="ml-2 w-2 h-2 rounded-full"
                            :class="item.variation >= 0 ? 'bg-emerald-500' : 'bg-red-500'"></div>
                        </div>
                      </td>
                      <td class=" px-6 py-4 whitespace-nowrap text-center">
                        <div class="flex items-center justify-center">
                          <div
                            class="text-sm font-mono font-semibold transform group-hover:scale-105 transition-all duration-200"
                            :class="item.variation_percent >= 0 ? 'text-emerald-600' : 'text-red-600'">
                            {{ item.variation_percent.toFixed(1) }}%
                          </div>
                          <svg v-if="Math.abs(item.variation_percent) > 20"
                            class="w-4 h-4 ml-1 text-orange-500 animate-pulse" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd"
                              d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                              clip-rule="evenodd"></path>
                          </svg>
                        </div>
                      </td>
                      <td class="px-6 py-4 whitespace-nowrap text-center">
                        <button @click="toggleDetail(index)"
                          class="inline-flex items-center px-4 py-2 border border-transparent text-xs font-medium rounded-lg transition-all duration-300 transform hover:scale-105 hover:shadow-lg"
                          :class="expandedRows.includes(index)
                            ? 'bg-gradient-to-r from-red-100 to-red-200 text-red-700 hover:from-red-200 hover:to-red-300 border border-red-300'
                            : 'bg-gradient-to-r from-blue-100 to-blue-200 text-blue-700 hover:from-blue-200 hover:to-blue-300 border border-blue-300'">
                          <svg class="w-4 h-4 mr-2 transition-transform duration-300"
                            :class="expandedRows.includes(index) ? 'rotate-180' : 'rotate-0'" fill="none"
                            stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7">
                            </path>
                          </svg>
                          {{ expandedRows.includes(index) ? 'Masquer' : 'Détails' }}
                        </button>
                      </td>
                    </tr>

                    <!-- Ligne de détail -->
                    <tr v-if="expandedRows.includes(index)" class="bg-gradient-to-r from-gray-50 to-gray-100">
                      <td colspan="8" class="px-6 py-6">
                        <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                          <div class="flex items-center mb-4">
                            <div class="flex-shrink-0">
                              <svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z">
                                </path>
                              </svg>
                            </div>
                            <div class="ml-3">
                              <h4 class="text-lg font-semibold text-gray-900">Détail des comptes</h4>
                              <p class="text-sm text-gray-600">{{ item.libelle }}</p>
                            </div>
                          </div>


                          <div v-if="item.comptes_detaille && item.comptes_detaille.length"
                            class="overflow-hidden rounded-lg border border-gray-200">
                            <table class="min-w-full divide-y divide-gray-200">
                              <thead class="bg-gray-50">
                                <tr>
                                  <th
                                    class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Compte</th>
                                  <th
                                    class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Libellé</th>
                                  <th
                                    class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    N</th>
                                  <th
                                    class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    N-1</th>
                                  <th
                                    class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Variation</th>
                                </tr>
                              </thead>
                              <tbody class="bg-white divide-y divide-gray-200">
                                <tr v-for="(compte, cIndex) in item.comptes_detaille" :key="cIndex"
                                  class="hover:bg-gray-50 transition-colors duration-150">
                                  <td class="px-4 py-3 whitespace-nowrap text-sm font-mono font-medium text-gray-900">{{
                                    compte.numero_compte }}</td>
                                  <td class="px-4 py-3 text-sm text-gray-900 max-w-xs truncate" :title="compte.libelle">
                                    {{ compte.libelle }}</td>
                                  <td class="px-4 py-3 whitespace-nowrap text-sm font-mono text-gray-900 text-right">{{
                                    compte.solde_n.toLocaleString() }}</td>
                                  <td class="px-4 py-3 whitespace-nowrap text-sm font-mono text-gray-900 text-right">{{
                                    formatAmount(compte.solde_n) }}</td>
                                  <td class="px-4 py-3 whitespace-nowrap text-sm font-mono text-gray-900 text-right">{{
                                    compte.solde_n1.toLocaleString() }}</td>
                                  <td class="px-4 py-3 whitespace-nowrap text-sm font-mono text-gray-900 text-right">{{
                                    formatAmount(compte.solde_n1) }}</td>
                                  <td class="px-4 py-3 whitespace-nowrap text-sm font-mono font-semibold text-right"
                                    :class="compte.variation >= 0 ? 'text-emerald-600' : 'text-red-600'">
                                    {{ formatAmount(compte.variation) }}
                                  </td>
                                </tr>
                              </tbody>
                            </table>
                          </div>
                          <div v-else class="text-gray-500 text-sm">Aucun compte détaillé</div>
                        </div>
                      </td>
                    </tr>
                  </template>
                </tbody>
              </table>

              <!-- Pagination -->
              <div v-if="filteredData.length > 10"
                class="bg-white px-6 py-4 border-t border-gray-200 flex items-center justify-between">
                <div class="flex items-center text-sm text-gray-700">
                  <span>Affichage de 1 à {{ Math.min(10, filteredData.length) }} sur {{ filteredData.length }}
                    résultats</span>
                </div>
                <div class="flex items-center space-x-2">
                  <button
                    class="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors duration-200">
                    Précédent
                  </button>
                  <button
                    class="px-3 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-lg hover:bg-blue-700 transition-colors duration-200">
                    1
                  </button>
                  <button
                    class="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors duration-200">
                    2
                  </button>
                  <button
                    class="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors duration-200">
                    Suivant
                  </button>
                </div>
              </div>

              <!-- Message si aucun résultat -->
              <div v-if="filteredData.length === 0" class="text-center py-12">
                <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M9.172 16.172a4 4 0 015.656 0M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z">
                  </path>
                </svg>
                <h3 class="mt-2 text-sm font-medium text-gray-900">Aucun résultat trouvé</h3>
                <p class="mt-1 text-sm text-gray-500">Essayez de modifier vos critères de recherche ou de filtrage.</p>
                <div v-if="searchQuery || natureFilter || variationFilter" class="mt-4">
                  <button @click="resetFilters"
                    class="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors duration-200">
                    🔄 Réinitialiser les filtres
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Étape 4: Grouping -->
        <div v-if="componentKey === 'grouping'">
          <div class="flex justify-between items-center mb-3">
            <h2 class="text-xl font-semibold">Grouping</h2>
          </div>

          <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
            <h3 class="text-lg font-semibold text-blue-800 mb-2">Regroupement des comptes</h3>
            <p class="text-blue-700 text-sm">Cette étape permet de regrouper les comptes selon leur nature et leur
              fonction.</p>
          </div>

          <!-- Utilisation du composant GroupingComponent existant -->
          <div class="space-y-4">
            <GroupingComponent
              v-if="groupingData"
              :data="groupingData"
              :annee_auditee="effectiveYear ?? ''"
            />

            <div v-else class="text-sm text-gray-600">
              <p>Le composant de grouping sera chargé ici.</p>
              <p class="mt-2 text-xs text-gray-500">
                Cette étape utilise le composant GroupingComponent existant pour l'analyse des regroupements de comptes.
              </p>
            </div>
          </div>
        </div>

        

        <!-- Étape 6: Calcul matérialités -->
        <div v-if="componentKey === 'materialite'">
          <div class="flex justify-between items-center mb-3">
            <h2 class="text-xl font-semibold">Calcul des matérialités</h2>
          </div>

          <!-- Message d'erreur -->
          <div v-if="errorMsg" class="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
            <div class="text-red-700 text-sm">{{ errorMsg }}</div>
          </div>

          <!-- État de chargement -->
          <div v-if="loading" class="text-center py-8">
            <div class="text-gray-600">Chargement des données de matérialité...</div>
          </div>

          <!-- Aucune donnée -->
          <div v-else-if="!materialiteReport && !loading" class="text-center py-8">
            <div class="text-gray-600 mb-4">Aucune donnée de matérialité disponible.</div>
            <button @click="loadMaterialite" class="btn-primary btn-large text-white" :disabled="loading">
              🔄 Charger les données de matérialité
            </button>
          </div>

          <!-- Données de matérialité -->
          <div v-else-if="materialiteReport && materialiteReport.ok" class="space-y-6">
            <!-- Section: Détermination du seuil de signification -->
            <div class="bg-gray-100 border border-blue-200 rounded-lg p-4">
              <h3 class="text-lg font-semibold text-blue-ycube mb-4 flex items-center">
                Détermination du seuil de signification
              </h3>

              <!-- Calcul du seuil de signification -->
              <div class="bg-white border border-gray-200 rounded-lg p-4 mb-4">
                <h4 class="text-base font-semibold text-gray-800 mb-3">Calcul du seuil</h4>
                <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
                  <div>
                    <label class="block text-sm font-semibold text-gray-700 mb-1">Choisir benchmark</label>
                    <select v-model="selectedBench"
                      class="w-full px-3 py-2 border-2 border-blue-500 rounded-md focus:outline-none focus:border-blue-600">
                      <option value="" disabled>Aucun benchmark choisi</option>
                      <option value="autre">Autre</option>
                      <option v-for="bench in listBenchmark" :key="bench.id" :value="bench.id">{{ bench.name }}</option>
                    </select>
                  </div>

                  <div>
                    <label class="block text-sm font-semibold text-gray-700 mb-1">Benchmark Balance</label>
                    <div v-if="selectedBench === 'autre'" class="space-y-2">
                      <input v-model="bench.custom_label" type="text" placeholder="Nom du benchmark..."
                        class="w-full px-3 py-2 border-2 border-gray-300 rounded-md" />
                      <input v-model.number="bench.custom_balance" type="number" placeholder="Valeur du benchmark"
                        class="w-full px-3 py-2 border-2 border-gray-300 rounded-md" @input="updateSelectBenchmark" />
                    </div>
                    <div v-else class="px-3 py-2 border-2 border-gray-300 rounded-md bg-gray-50">
                      {{ bench.balanceValue ? formatAmount(bench.balanceValue) : 'Aucun benchmark choisi' }}
                    </div>
                    <div v-if="bench.amount_based_on_factor && bench.amount_based_on_factor < 0"
                      class="mt-1 text-xs text-red-600 font-semibold">
                      ⚠️ ATTENTION: Seuil de matérialité négatif !
                    </div>
                  </div>

                  <div>
                    <label class="block text-sm font-semibold text-gray-700 mb-1">Facteur (%)</label>
                    <input v-model="bench.factor" @input="updateSelectBenchmark"
                      class="w-full px-3 py-2 border-2 border-blue-500 rounded-md focus:outline-none focus:border-blue-600"
                      type="number" step="0.1" placeholder="Saisir facteur...">
                    <div v-if="bench.text" class="mt-1 text-xs text-gray-600">
                      <i class="fas fa-info-circle mr-1"></i>{{ bench.text }}
                    </div>
                  </div>

                  <div>
                    <label class="block text-sm font-semibold text-gray-700 mb-1">Commantaire</label>
                    <input
                      class="w-full px-3 py-2 border-2 border-blue-500 rounded-md focus:outline-none focus:border-blue-600"
                      type="text" placeholder="Entrez un commentaire...">
                  </div>

                  <div class="mt-6">
                    <button @click="validerSeuil"
                      class="w-full btn-primary text-white px-3 py-2 rounded-md font-semibold"
                      :disabled="!selectedBench || !bench.factor || (selectedBench === 'autre' && (!bench.custom_label || !bench.custom_balance))">
                      ✅ Valider
                    </button>
                  </div>
                </div>
              </div>

              <!-- Liste des seuils de signification calculés -->
              <div class="bg-white border border-gray-200 rounded-lg p-4">
                <h4 class="text-base font-semibold text-gray-800 mb-3">Liste des seuils de signification</h4>
                <div class="overflow-auto">
                  <table class="min-w-full table w-full border-collapse border border-gray-300">
                    <thead class="font-bold text-left bg-blue-ycube text-white text-xs">
                      <tr>
                        <th class="w-[5%] border-2 border-gray-300 p-2">#</th>
                        <th class="w-[20%] border-2 border-gray-300 p-2">Benchmark</th>
                        <th class="w-[15%] border-2 border-gray-300 p-2">Facteur</th>
                        <th class="w-[20%] border-2 border-gray-300 p-2">Seuil de matérialité</th>
                        <th class="w-[20%] border-2 border-gray-300 p-2">Performance de matérialité</th>
                        <th class="w-[20%] border-2 border-gray-300 p-2">Seuil pour les inexactitudes manifestement
                          insignifiantes</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(mat, index) in listMaterialities" :key="index" class="border-t h-12 text-sm"
                        :class="index % 2 === 0 ? 'bg-gray-50' : 'bg-white'">
                        <td class="border-2 border-gray-300 p-2 text-center">{{ index + 1 }}</td>
                        <td class="border-2 border-gray-300 p-2 font-semibold">
                          {{ mat.benchmark }}
                          <div v-if="mat.warning" class="text-xs text-orange-600 mt-1">{{ mat.warning }}</div>
                        </td>
                        <td class="border-2 border-gray-300 p-2">{{ mat.factor }}</td>
                        <td class="border-2 border-gray-300 p-2 font-mono"
                          :class="mat.materiality < 0 ? 'text-red-600' : 'text-green-600'">{{
                            mat.materiality?.toLocaleString()
                          }}</td>
                        <td class="border-2 border-gray-300 p-2 font-mono"
                          :class="mat.performance_materiality < 0 ? 'text-red-600' : 'text-blue-600'">{{
                            mat.performance_materiality?.toLocaleString() }}</td>
                        <td class="border-2 border-gray-300 p-2 font-mono"
                          :class="mat.trivial_misstatements < 0 ? 'text-red-600' : 'text-orange-600'">{{
                            mat.trivial_misstatements?.toLocaleString() }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            <!-- Section: Application au grouping -->
            <div v-if="listMaterialities.length > 0" class="bg-gray-100 border border-gray-200 rounded-lg p-4">
              <h3 class="text-lg font-semibold text-green-800 mb-4 flex items-center">
                Application au grouping
              </h3>
              <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div v-for="mat in listMaterialities" :key="mat.benchmark"
                  class="bg-white border border-green-200 rounded-lg p-4">
                  <div class="flex justify-between items-center mb-2">
                    <h4 class="font-semibold text-gray-800">{{ mat.benchmark }}</h4>
                    <button @click="applySeuil(mat.benchmark)" class="btn-success btn-small text-white">
                      Appliquer
                    </button>
                  </div>
                  <div class="text-sm text-gray-600 space-y-1">
                    <div><strong>Matérialité:</strong> {{ mat.materiality?.toLocaleString() }}</div>
                    <div><strong>Performance:</strong> {{ mat.performance_materiality?.toLocaleString() }}</div>
                    <div><strong>Triviales:</strong> {{ mat.trivial_misstatements?.toLocaleString() }}</div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Boutons d'action -->
            <div class="flex gap-4 flex-wrap justify-center">
              <button v-if="listMaterialities.length > 0" @click="exportToCsv(listMaterialities, 'materialite')"
                class="btn-success btn-standard text-white">
                Télécharger (CSV)
              </button>
              <button @click="loadMaterialite" class="btn-primary btn-standard text-white" :disabled="loading">
                Actualiser
              </button>
            </div>

            <!-- Légende -->
            <div class="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <h4 class="text-sm font-semibold text-gray-800 mb-2">Légende des benchmarks :</h4>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs text-gray-600">
                <div><strong>profit_before_tax :</strong> Bénéfice avant impôt (5-10%)</div>
                <div><strong>ebitda :</strong> Excédent brut d'exploitation (3-5%)</div>
                <div><strong>revenue :</strong> Chiffre d'affaires (0.8-2%)</div>
                <div><strong>total_assets :</strong> Total des actifs (1-2%)</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Étape 7: Identification comptes matériels (quantitatif) -->
        <div v-if="componentKey === 'quantitatif'">
          <div class="flex justify-between items-center mb-3">
            <h2 class="text-xl font-semibold">Identification comptes matériels (quantitatif)</h2>
          </div>

          <div v-if="!analyseQuantitativeReport && !loading" class="text-sm text-gray-600">Aucune donnée.</div>
          <div v-else-if="analyseQuantitativeReport?.message" class="text-sm text-red-700 mb-3">
            {{ analyseQuantitativeReport.message }}
          </div>

          <div v-if="analyseQuantitativeReport && analyseQuantitativeReport.ok" class="space-y-4">
            <!-- Informations générales -->
            <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 class="text-lg font-semibold text-blue-800 mb-2">Analyse quantitative des comptes</h3>
              <p class="text-blue-700 text-sm mb-2">{{ analyseQuantitativeReport.message }}</p>
              <div v-if="analyseQuantitativeReport.statistics" class="grid grid-cols-2 md:grid-cols-4 gap-4 mt-3">
                <div class="bg-white p-3 rounded border">
                  <div class="text-xs text-gray-600">Seuil de matérialité</div>
                  <div class="text-lg font-bold text-blue-600">{{
                    analyseQuantitativeReport.statistics.materiality_threshold.toLocaleString() }} FCFA</div>
                </div>
                <div class="bg-white p-3 rounded border">
                  <div class="text-xs text-gray-600">Comptes significatifs</div>
                  <div class="text-lg font-bold text-green-600">{{
                    analyseQuantitativeReport.statistics.significant_accounts }}
                  </div>
                </div>
                <div class="bg-white p-3 rounded border">
                  <div class="text-xs text-gray-600">Comptes non significatifs</div>
                  <div class="text-lg font-bold text-gray-600">{{
                    analyseQuantitativeReport.statistics.non_significant_accounts
                  }}</div>
                </div>
                <div class="bg-white p-3 rounded border">
                  <div class="text-xs text-gray-600">Total significatif</div>
                  <div class="text-lg font-bold text-purple-600">{{
                    analyseQuantitativeReport.statistics.total_significant_amount.toLocaleString() }} FCFA</div>
                </div>
              </div>
            </div>

            <!-- Bouton d'export -->
            <button v-if="analyseQuantitativeReport.analyse && analyseQuantitativeReport.analyse.length"
              @click="exportToCsv(analyseQuantitativeReport.analyse, 'analyse_quantitative')"
              class="mb-3 px-4 py-2 bg-green-ycube-2 text-white rounded-md shadow-md hover:bg-green-700 transition-colors">
              Télécharger (CSV)
            </button>

            <!-- Tableau d'analyse quantitative -->
            <div v-if="analyseQuantitativeReport.analyse && analyseQuantitativeReport.analyse.length"
              class="overflow-hidden rounded-xl shadow-xl bg-white border border-gray-100">
              <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gradient-to-r from-blue-ycube to-blue-ycube-3">
                  <tr>
                    <th class="px-6 py-4 text-left text-xs font-semibold text-white uppercase tracking-wider">Compte
                    </th>
                    <th class="px-6 py-4 text-left text-xs font-semibold text-white uppercase tracking-wider">Libellé
                    </th>
                    <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">Solde N
                    </th>
                    <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">Solde N-1
                    </th>
                    <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">Variation
                    </th>
                    <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">% du
                      Seuil</th>
                    <th class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider">Statut
                    </th>
                  </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                  <tr v-for="(item, index) in analyseQuantitativeReport.analyse" :key="index"
                    class="hover:bg-gradient-to-r hover:from-blue-50 hover:to-indigo-50 transition-all duration-300 group transform hover:scale-[1.01] hover:shadow-md">
                    <td class="px-6 py-4 whitespace-nowrap">
                      <div class="flex items-center">
                        <div
                          class="flex-shrink-0 h-8 w-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center mr-3 group-hover:scale-110 transition-transform duration-200">
                          <span class="text-xs font-bold text-white">{{ item.compte.charAt(0) }}</span>
                        </div>
                        <div
                          class="text-sm font-mono font-bold text-gray-900 group-hover:text-blue-700 transition-colors duration-200">
                          {{ item.compte }}</div>
                      </div>
                    </td>
                    <td class="px-6 py-4">
                      <div
                        class="text-sm text-gray-900 max-w-xs truncate group-hover:text-blue-700 transition-colors duration-200"
                        :title="item.libelle">{{ item.libelle }}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-right">
                      <div
                        class="text-sm font-mono text-gray-900 group-hover:text-blue-700 transition-colors duration-200">
                        {{
                          formatAmount(item.solde_n) }}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-right">
                      <div
                        class="text-sm font-mono text-gray-900 group-hover:text-blue-700 transition-colors duration-200">
                        {{
                          formatAmount(item.solde_n1) }}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-right">
                      <div class="flex items-center justify-end">
                        <div
                          class="text-sm font-mono font-semibold transform group-hover:scale-105 transition-all duration-200"
                          :class="item.variation >= 0 ? 'text-emerald-600' : 'text-red-600'">
                          {{ formatAmount(item.variation) }}
                        </div>
                        <div class="ml-2 w-2 h-2 rounded-full"
                          :class="item.variation >= 0 ? 'bg-emerald-500' : 'bg-red-500'">
                        </div>
                      </div>
                    </td>
                    <td class=" px-6 py-4 whitespace-nowrap text-right">
                      <div class="flex items-center justify-end">
                        <div
                          class="text-sm font-mono font-semibold transform group-hover:scale-105 transition-all duration-200"
                          :class="item.percentage_of_threshold >= 100 ? 'text-red-600' : item.percentage_of_threshold >= 50 ? 'text-orange-600' : 'text-emerald-600'">
                          {{ item.percentage_of_threshold.toFixed(1) }}%
                        </div>
                        <svg v-if="item.percentage_of_threshold >= 100" class="w-4 h-4 ml-1 text-red-500 animate-pulse"
                          fill="currentColor" viewBox="0 0 20 20">
                          <path fill-rule="evenodd"
                            d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                            clip-rule="evenodd"></path>
                        </svg>
                      </div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-center">
                      <span
                        class="inline-flex px-3 py-1 rounded-full text-xs font-medium shadow-sm transform group-hover:scale-105 transition-all duration-200"
                        :class="item.is_significant ? 'bg-gradient-to-r from-red-100 to-red-200 text-red-800 border border-red-300' : 'bg-gradient-to-r from-emerald-100 to-emerald-200 text-emerald-800 border border-emerald-300'">
                        <span class="w-2 h-2 rounded-full mr-2"
                          :class="item.is_significant ? 'bg-red-500' : 'bg-emerald-500'"></span>
                        {{ item.status }}
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Résumé des résultats -->
            <div v-if="analyseQuantitativeReport.statistics" class="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <h4 class="text-lg font-semibold text-gray-800 mb-3">Résumé de l'analyse quantitative</h4>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h5 class="font-semibold text-green-800 mb-2">✅ Comptes à tester ({{
                    analyseQuantitativeReport.statistics.significant_accounts }})</h5>
                  <p class="text-sm text-gray-700">
                    Ces comptes dépassent le seuil de matérialité de {{
                      analyseQuantitativeReport.statistics.materiality_threshold.toLocaleString() }} FCFA
                    et représentent un montant total de {{
                      analyseQuantitativeReport.statistics.total_significant_amount.toLocaleString() }} FCFA.
                  </p>
                </div>
                <div>
                  <h5 class="font-semibold text-gray-800 mb-2">ℹ️ Comptes ne pas tester ({{
                    analyseQuantitativeReport.statistics.non_significant_accounts }})</h5>
                  <p class="text-sm text-gray-700">
                    Ces comptes sont en dessous du seuil de matérialité et ne nécessitent pas de tests d'audit
                    approfondis.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Étape 8: Identification comptes matériels (qualitatif) -->
        <div v-if="componentKey === 'qualitatif'">
          <div class="flex justify-between items-center mb-3">
            <h2 class="text-xl font-semibold">Identification comptes</h2>
          </div>

          <div v-if="!analyseQualitativeReport && !loading" class="text-justifypy-8">
            <div class="text-gray-600 mb-4">Aucune donnée d'analyse qualitative disponible.</div>
            <button @click="initQualitativeResponses"
              class="px-6 py-3 bg-blue-600 text-white rounded-md shadow-md hover:bg-blue-700 transition-colors"
              :disabled="loading">
              🚀 Initialiser l'analyse qualitative
            </button>
          </div>
          <div v-else-if="analyseQualitativeReport?.message && !analyseQualitativeReport.ok"
            class="text-sm text-red-700 mb-3">
            {{ analyseQualitativeReport.message }}
          </div>

          <div v-if="analyseQualitativeReport && analyseQualitativeReport.ok" class="space-y-4">
            <!-- Informations générales -->
            <div class="bg-gray-100 border border-blue-200 rounded-lg p-4">
              <h3 class="text-lg font-semibold text-blue-ycube mb-2">Analyse qualitative des comptes</h3>
              <p class="text-blue-700 text-sm mb-2">{{ analyseQualitativeReport.message }}</p>
              <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mt-3">
                <div class="bg-white p-3 rounded border">
                  <div class="text-xs text-gray-600">Comptes significatifs</div>
                  <div class="text-lg font-bold text-green-600">{{ qualitativeStats.significant_accounts }}</div>
                </div>
                <div class="bg-white p-3 rounded border">
                  <div class="text-xs text-gray-600">Comptes non significatifs</div>
                  <div class="text-lg font-bold text-gray-600">{{ qualitativeStats.non_significant_accounts }}</div>
                </div>
                <div class="bg-white p-3 rounded border">
                  <div class="text-xs text-gray-600">Réponses positives</div>
                  <div class="text-lg font-bold text-purple-600">{{ qualitativeStats.total_positive_responses }}</div>
                </div>
                <!--
                  <div class="bg-white p-3 rounded border">
                    <div class="text-xs text-gray-600">Score moyen</div>
                    <div class="text-lg font-bold text-blue-600">{{ qualitativeStats.average_score.toFixed(1) }}%</div>
                  </div>
                -->
              </div>
            </div>

            <!-- Boutons d'action -->
            <div class="flex gap-3 flex-wrap">
              <button v-if="analyseQualitativeReport.analyse && analyseQualitativeReport.analyse.length"
                @click="exportToCsv(analyseQualitativeReport.analyse, 'analyse_qualitative')"
                class="px-4 py-2 bg-green-ycube-2 text-white rounded-md shadow-md hover:bg-green-700 transition-colors">
                Télécharger (CSV)
              </button>
              <button @click="saveQualitativeResponses"
                class="px-4 py-2 bg-blue-ycube-3 text-white rounded-md shadow-md hover:bg-blue-ycube transition-colors"
                :disabled="loading">
                Sauvegarder les réponses
              </button>
              <button @click="initQualitativeResponses"
                class="px-4 py-2 bg-gray-ycube-1 text-white rounded-md shadow-md hover:bg-orange-700 transition-colors"
                :disabled="loading">
                Réinitialiser
              </button>
            </div>

            <!-- Tableau des questionnaires Q1-Q8 -->
            <div v-if="analyseQualitativeReport.analyse && analyseQualitativeReport.analyse.length"
              class="overflow-hidden rounded-xl shadow-xl bg-white border border-gray-100">
              <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gradient-to-r from-blue-ycube  to-blue-ycube-3">
                  <tr>
                    <th class="px-6 py-4 text-left text-xs font-semibold text-white uppercase tracking-wider">Compte
                    </th>
                    <th class="px-6 py-4 text-left text-xs font-semibold text-white uppercase tracking-wider">Libellé
                    </th>
                    <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">Solde N
                    </th>
                    <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">Score
                    </th>
                    <th
                      class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider cursor-pointer hover:bg-blue-700 transition-colors"
                      @click="showQuestion(1, $event)" title="Cliquer pour voir la question complète">Q1</th>
                    <th
                      class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider cursor-pointer hover:bg-blue-700 transition-colors"
                      @click="showQuestion(2, $event)" title="Cliquer pour voir la question complète">Q2</th>
                    <th
                      class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider cursor-pointer hover:bg-blue-700 transition-colors"
                      @click="showQuestion(3, $event)" title="Cliquer pour voir la question complète">Q3</th>
                    <th
                      class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider cursor-pointer hover:bg-blue-700 transition-colors"
                      @click="showQuestion(4, $event)" title="Cliquer pour voir la question complète">Q4</th>
                    <th
                      class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider cursor-pointer hover:bg-blue-700 transition-colors"
                      @click="showQuestion(5, $event)" title="Cliquer pour voir la question complète">Q5</th>
                    <th
                      class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider cursor-pointer hover:bg-blue-700 transition-colors"
                      @click="showQuestion(6, $event)" title="Cliquer pour voir la question complète">Q6</th>
                    <th
                      class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider cursor-pointer hover:bg-blue-700 transition-colors"
                      @click="showQuestion(7, $event)" title="Cliquer pour voir la question complète">Q7</th>
                    <th
                      class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider cursor-pointer hover:bg-blue-700 transition-colors"
                      @click="showQuestion(8, $event)" title="Cliquer pour voir la question complète">Q8</th>
                    <th class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider">Statut
                    </th>
                  </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                  <tr v-for="(item, index) in analyseQualitativeReport.analyse" :key="index"
                    class="hover:bg-gradient-to-r hover:from-blue-50 hover:to-indigo-50 transition-all duration-300 group transform hover:scale-[1.01] hover:shadow-md">
                    <td class="px-6 py-4 whitespace-nowrap">
                      <div class="flex items-center">
                        <div
                          class="flex-shrink-0 h-8 w-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center mr-3 group-hover:scale-110 transition-transform duration-200">
                          <span class="text-xs font-bold text-white">{{ item.compte.charAt(0) }}</span>
                        </div>
                        <div
                          class="text-sm font-mono font-bold text-gray-900 group-hover:text-blue-700 transition-colors duration-200">
                          {{ item.compte }}</div>
                      </div>
                    </td>
                    <td class="px-6 py-4">
                      <div
                        class="text-sm text-gray-900 max-w-xs truncate group-hover:text-blue-700 transition-colors duration-200"
                        :title="item.libelle">{{ item.libelle }}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-right">
                      <div
                        class="text-sm font-mono text-gray-900 group-hover:text-blue-700 transition-colors duration-200">
                        {{
                          item.solde_n.toLocaleString() }}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-right">
                      <div class="flex items-center justify-end">
                        <div
                          class="text-sm font-mono font-semibold transform group-hover:scale-105 transition-all duration-200"
                          :class="item.qualitative_score >= 50 ? 'text-red-600' : item.qualitative_score >= 25 ? 'text-orange-600' : 'text-emerald-600'">
                          {{ item.qualitative_score.toFixed(1) }}%
                        </div>
                        <svg v-if="item.qualitative_score >= 50" class="w-4 h-4 ml-1 text-red-500 animate-pulse"
                          fill="currentColor" viewBox="0 0 20 20">
                          <path fill-rule="evenodd"
                            d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                            clip-rule="evenodd"></path>
                        </svg>
                      </div>
                    </td>
                    <td v-for="q in 8" :key="q" class="px-6 py-4 whitespace-nowrap text-center">
                      <input type="checkbox" :checked="qualitativeResponses[item.compte]?.[`Q${q}`] || false"
                        @change="(e) => handleQualitativeResponse(item.compte, `Q${q}`, e.target.checked)"
                        class="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 transform group-hover:scale-110 transition-all duration-200" />
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-center">
                      <span
                        class="inline-flex px-3 py-1 rounded-full text-xs font-medium shadow-sm transform group-hover:scale-105 transition-all duration-200"
                        :class="item.is_qualitatively_significant ? 'bg-gradient-to-r from-red-100 to-red-200 text-red-800 border border-red-300' : 'bg-gradient-to-r from-emerald-100 to-emerald-200 text-emerald-800 border border-emerald-300'">
                        <span class="w-2 h-2 rounded-full mr-2"
                          :class="item.is_qualitatively_significant ? 'bg-red-500' : 'bg-emerald-500'"></span>
                        {{ item.status }}
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>


          </div>
        </div>

        <!-- Étape 9: Présentation des comptes significatifs -->
        <div v-if="componentKey === 'presentation'">
          <div class="flex justify-between items-center mb-3">
            <h2 class="text-xl font-semibold">Présentation des comptes significatifs</h2>
          </div>

          <div v-if="!presentationComptesSignificatifsReport && !loading" class="text-justifypy-8">
            <div class="text-gray-600 mb-4">Aucune présentation disponible. Assurez-vous d'avoir effectué les analyses
              quantitative et qualitative (étapes 7 et 8).</div>
            <button @click="loadPresentationComptesSignificatifs"
              class="px-6 py-3 bg-blue-600 text-white rounded-md shadow-md hover:bg-blue-700 transition-colors"
              :disabled="loading">
              🔄 Générer la présentation
            </button>
          </div>

          <!-- Bouton de rechargement si la présentation existe déjà -->
          <div v-else-if="presentationComptesSignificatifsReport && presentationComptesSignificatifsReport.ok"
            class="mb-4">
            <button @click="async () => { await loadClassement(); await loadPresentationComptesSignificatifs(); }"
              class="px-4 py-2 bg-gray-ycube-1 text-white rounded-md shadow-md hover:bg-orange-600 transition-colors"
              :disabled="loading">
              Actualiser la présentation
            </button>
            <span class="ml-3 text-sm text-gray-600">Cliquez pour actualiser après avoir modifié les analyses
              qualitative ou
              quantitative</span>
          </div>
          <div v-else-if="presentationComptesSignificatifsReport?.message && !presentationComptesSignificatifsReport.ok"
            class="text-sm text-red-700 mb-3">
            {{ presentationComptesSignificatifsReport.message }}
          </div>

          <div v-if="presentationComptesSignificatifsReport && presentationComptesSignificatifsReport.ok"
            class="space-y-4">
            <!-- Informations générales -->
            <div class="bg-gray-ycube border border-blue-200 rounded-lg p-4">
              <h3 class="text-lg font-semibold text-blue-ycube mb-2">Présentation des comptes significatifs basée sur
                les
                analyses quantitative et qualitative</h3>
              <p class="text-blue-ycube-3 text-sm mb-2">{{ presentationComptesSignificatifsReport.message }}</p>
              <div v-if="presentationComptesSignificatifsReport.statistics"
                class="grid grid-cols-2 md:grid-cols-4 gap-4 mt-3">
                <div class="bg-white p-3 rounded border">
                  <div class="text-xs text-gray-600">Comptes significatifs</div>
                  <div class="text-lg font-bold text-red-600">{{
                    presentationComptesSignificatifsReport.statistics.significant_accounts }}</div>
                </div>
                <div class="bg-white p-3 rounded border">
                  <div class="text-xs text-gray-600">Comptes non significatifs</div>
                  <div class="text-lg font-bold text-green-600">{{
                    presentationComptesSignificatifsReport.statistics.non_significant_accounts }}</div>
                </div>
                <!--
                <div class="bg-white p-3 rounded border">
                  <div class="text-xs text-gray-600">Priorité haute</div>
                  <div class="text-lg font-bold text-orange-600">{{
                    presentationComptesSignificatifsReport.statistics.high_priority_accounts }}</div>
                </div> -->
                <!--
                <div class="bg-white p-3 rounded border">
                  <div class="text-xs text-gray-600">Montant significatif</div>
                  <div class="text-lg font-bold text-purple-600">{{
                    presentationComptesSignificatifsReport.statistics.total_significant_amount.toLocaleString() }} FCFA
                  </div>
                </div>
                -->
              </div>
            </div>

            <!-- Bouton d'export -->
            <button
              v-if="presentationComptesSignificatifsReport.presentation && presentationComptesSignificatifsReport.presentation.length"
              @click="exportToCsv(presentationComptesSignificatifsReport.presentation, 'presentation_comptes_significatifs')"
              class="mb-3 px-4 py-2 bg-green-600 text-white rounded-md shadow-md hover:bg-green-700 transition-colors">
              Télécharger (CSV)
            </button>

            <!-- Tableau de présentation -->
            <div
              v-if="presentationComptesSignificatifsReport.presentation && presentationComptesSignificatifsReport.presentation.length"
              class="overflow-x-auto rounded-xl shadow-xl bg-white border border-gray-100">
              <table class="min-w-full divide-y divide-gray-200 overflow-auto">
                <thead class="bg-gradient-to-r from-blue-ycube  to-blue-ycube-3">
                  <tr>
                    <th class="px-6 py-4 text-left text-xs font-semibold text-white uppercase tracking-wider">Compte
                    </th>
                    <th class="px-6 py-4 text-left text-xs font-semibold text-white uppercase tracking-wider">Libellé
                    </th>
                    <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">Solde N
                    </th>
                    <th class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider">
                      Quantitatif</th>
                    <th class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider">
                      Qualitatif</th>
                    <th class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider">
                      Significativité
                    </th>
                    <th class="px-6 py-4 text-left text-xs font-semibold text-white uppercase tracking-wider">
                      Recommandation
                    </th>
                  </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                  <tr v-for="(item, index) in presentationComptesSignificatifsReport.presentation" :key="index"
                    class="hover:bg-gradient-to-r hover:from-blue-50 hover:to-indigo-50 transition-all duration-300 group transform hover:scale-[1.01] hover:shadow-md">
                    <td class="px-6 py-4 whitespace-nowrap">
                      <div class="flex items-center">
                        <div
                          class="flex-shrink-0 h-8 w-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center mr-3 group-hover:scale-110 transition-transform duration-200">
                          <span class="text-xs font-bold text-white">{{ item.compte.charAt(0) }}</span>
                        </div>
                        <div
                          class="text-sm font-mono font-bold text-gray-900 group-hover:text-blue-700 transition-colors duration-200">
                          {{ item.compte }}</div>
                      </div>
                    </td>
                    <td class="px-6 py-4">
                      <div
                        class="text-sm text-gray-900 max-w-xs truncate group-hover:text-blue-700 transition-colors duration-200"
                        :title="item.libelle">{{ item.libelle }}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-right">
                      <div
                        class="text-sm font-mono text-gray-900 group-hover:text-blue-700 transition-colors duration-200">
                        {{
                          item.solde_n.toLocaleString() }}</div>
                    </td>
                    <!--   <td class="px-6 py-4 whitespace-nowrap text-right">
                      <div class="flex items-center justify-end">
                        <div
                          class="text-sm font-mono font-semibold transform group-hover:scale-105 transition-all duration-200"
                          :class="Math.abs(item.variation_percent) > 20 ? 'text-red-600' : 'text-gray-600'">
                          {{ item.variation_percent.toFixed(1) }}%
                        </div>
                        <svg v-if="Math.abs(item.variation_percent) > 20"
                          class="w-4 h-4 ml-1 text-red-500 animate-pulse" fill="currentColor" viewBox="0 0 20 20">
                          <path fill-rule="evenodd"
                            d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                            clip-rule="evenodd"></path>
                        </svg>
                      </div>
                    </td> -->
                    <td class="px-6 py-4 whitespace-nowrap text-center">
                      <span
                        class="inline-flex px-3 py-1 rounded-full text-xs font-medium shadow-sm transform group-hover:scale-105 transition-all duration-200"
                        :class="item.is_quantitatively_significant ? 'bg-gradient-to-r from-blue-100 to-blue-200 text-blue-800 border border-blue-300' : 'bg-gradient-to-r from-slate-100 to-slate-200 text-slate-800 border border-slate-300'">
                        <span class="w-2 h-2 rounded-full mr-2"
                          :class="item.is_quantitatively_significant ? 'bg-blue-500' : 'bg-slate-500'"></span>
                        {{ item.is_quantitatively_significant ? 'Oui' : 'Non' }}
                      </span>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-center">
                      <span
                        class="inline-flex px-3 py-1 rounded-full text-xs font-medium shadow-sm transform group-hover:scale-105 transition-all duration-200"
                        :class="item.is_qualitatively_significant ? 'bg-gradient-to-r from-blue-100 to-blue-200 text-blue-800 border border-blue-300' : 'bg-gradient-to-r from-slate-100 to-slate-200 text-slate-800 border border-slate-300'">
                        <span class="w-2 h-2 rounded-full mr-2"
                          :class="item.is_qualitatively_significant ? 'bg-blue-500' : 'bg-slate-500'"></span>
                        {{ item.is_qualitatively_significant ? 'Oui' : 'Non' }}
                      </span>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-center">
                      <span
                        class="inline-flex px-3 py-1 rounded-full text-xs font-medium shadow-sm transform group-hover:scale-105 transition-all duration-200"
                        :class="getSignificativiteClass(item.significativite_status)">
                        <span class="w-2 h-2 rounded-full mr-2"
                          :class="item.significativite_status === 'Significatif' ? 'bg-red-500' : 'bg-emerald-500'"></span>
                        {{ item.significativite_status }}
                      </span>
                    </td>
                    <td class="px-6 py-4">
                      <div
                        class="text-sm text-gray-900 max-w-xs truncate group-hover:text-blue-700 transition-colors duration-200"
                        :title="item.recommandation_audit">{{ item.recommandation_audit }}</div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Résumé des priorités -->
            <div v-if="presentationComptesSignificatifsReport.statistics"
              class="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <h4 class="text-lg font-semibold text-gray-800 mb-3">Résumé des priorités d'audit</h4>
              <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <h5 class="font-semibold text-red-800 mb-2">🔴 Priorité Haute ({{
                    presentationComptesSignificatifsReport.statistics.high_priority_accounts }})</h5>
                  <p class="text-sm text-gray-700">
                    Comptes significatifs à la fois quantitativement et qualitativement.
                    Tests d'audit approfondis obligatoires.
                  </p>
                </div>
                <div>
                  <h5 class="font-semibold text-orange-800 mb-2">🟠 Priorité Moyenne ({{
                    presentationComptesSignificatifsReport.statistics.significant_accounts -
                    presentationComptesSignificatifsReport.statistics.high_priority_accounts }})</h5>
                  <p class="text-sm text-gray-700">
                    Comptes significatifs soit quantitativement soit qualitativement.
                    Tests d'audit substantiels recommandés.
                  </p>
                </div>
                <div>
                  <h5 class="font-semibold text-green-800 mb-2">🟢 Priorité Faible ({{
                    presentationComptesSignificatifsReport.statistics.non_significant_accounts }})</h5>
                  <p class="text-sm text-gray-700">
                    Comptes non significatifs dans les deux analyses.
                    Tests d'audit minimaux ou aucun test.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Étape 10: Revue analytique -->
        <div v-if="componentKey === 'revue'">
          <div class="flex justify-between items-center mb-3">
            <h2 class="text-xl font-semibold">Revue analytique finale</h2>
          </div>

          <div v-if="!revueAnalytiqueFinaleReport && !loading" class="text-justifypy-8">
            <div class="text-gray-600 mb-4">Aucune revue analytique disponible. Assurez-vous d'avoir effectué toutes les
              étapes
              précédentes.</div>
            <button @click="loadRevueAnalytiqueFinale"
              class="px-6 py-3 btn-primary text-white rounded-md shadow-md hover:bg-blue-700 transition-colors"
              :disabled="loading">
              Générer la revue analytique
            </button>
          </div>
          <div v-else-if="revueAnalytiqueFinaleReport?.message && !revueAnalytiqueFinaleReport.ok"
            class="text-sm text-red-700 mb-3">
            {{ revueAnalytiqueFinaleReport.message }}
          </div>

          <div v-if="revueAnalytiqueFinaleReport && revueAnalytiqueFinaleReport.ok" class="space-y-4">
            <!-- Informations générales -->
            <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 class="text-lg font-semibold text-blue-800 mb-2">Revue analytique finale pour validation globale de
                l'audit
              </h3>
              <p class="text-blue-700 text-sm mb-2">{{ revueAnalytiqueFinaleReport.message }}</p>

              <!-- Analyses disponibles -->
              <div
                v-if="revueAnalytiqueFinaleReport.analyses_disponibles && revueAnalytiqueFinaleReport.analyses_disponibles.length"
                class="mt-3">
                <div class="text-sm text-blue-600 font-semibold mb-2">Analyses intégrées :</div>
                <div class="flex gap-2 flex-wrap">
                  <span v-for="analyse in revueAnalytiqueFinaleReport.analyses_disponibles" :key="analyse"
                    class="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs font-semibold">
                    ✅ {{ analyse }}
                  </span>
                </div>
              </div>
              <div v-else class="mt-3">
                <div class="text-sm text-orange-600 font-semibold mb-2">Mode évaluation basique :</div>
                <div class="text-xs text-orange-700">
                  Aucune analyse avancée disponible. La revue est basée sur les données de grouping.
                  <br>Pour une analyse complète, exécutez d'abord les étapes 7, 8 et 9.
                </div>
              </div>
              <div v-if="revueAnalytiqueFinaleReport.statistics" class="grid grid-cols-2 md:grid-cols-4 gap-4 mt-3">
                <div class="bg-white p-3 rounded border">
                  <div class="text-xs text-gray-600">Comptes à valider</div>
                  <div class="text-lg font-bold text-orange-600">{{
                    revueAnalytiqueFinaleReport.statistics.accounts_to_validate
                  }}</div>
                </div>
                <div class="bg-white p-3 rounded border">
                  <div class="text-xs text-gray-600">Comptes validés</div>
                  <div class="text-lg font-bold text-green-600">{{
                    revueAnalytiqueFinaleReport.statistics.accounts_validated }}
                  </div>
                </div>
                <div class="bg-white p-3 rounded border">
                  <div class="text-xs text-gray-600">En attente</div>
                  <div class="text-lg font-bold text-red-600">{{ revueAnalytiqueFinaleReport.statistics.accounts_pending
                  }}
                  </div>
                </div>
                <div class="bg-white p-3 rounded border">
                  <div class="text-xs text-gray-600">Progression</div>
                  <div class="text-lg font-bold text-blue-600">{{
                    revueAnalytiqueFinaleReport.statistics.validation_percentage.toFixed(1) }}%</div>
                </div>
              </div>
            </div>

            <!-- Statut de l'audit -->
            <div v-if="revueAnalytiqueFinaleReport.statistics" class="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <h4 class="text-lg font-semibold text-gray-800 mb-3">Statut de l'audit</h4>
              <div class="flex items-center gap-3">
                <div class="text-2xl">
                  {{ revueAnalytiqueFinaleReport.statistics.audit_status === 'Validé' ? '✅' : '🔄' }}
                </div>
                <div>
                  <div class="text-lg font-semibold"
                    :class="revueAnalytiqueFinaleReport.statistics.audit_status === 'Validé' ? 'text-green-800' : 'text-orange-800'">
                    {{ revueAnalytiqueFinaleReport.statistics.audit_status }}
                  </div>
                  <div class="text-sm text-gray-600">
                    {{ revueAnalytiqueFinaleReport.statistics.audit_status === 'Validé' ? 'Tous les comptes significatifs ont été validés' : 'Validation en cours' }}
                  </div>
                </div>
              </div>
            </div>

            <!-- Boutons d'action -->
            <div class="flex gap-3 flex-wrap">
              <button v-if="revueAnalytiqueFinaleReport.revue && revueAnalytiqueFinaleReport.revue.length"
                @click="exportToCsv(revueAnalytiqueFinaleReport.revue, 'revue_analytique_finale')"
                class="px-4 py-2 bg-green-600 text-white rounded-md shadow-md hover:bg-green-700 transition-colors">
                📊 Télécharger (CSV)
              </button>
              <button @click="saveRevueAnalytique"
                class="px-4 py-2 bg-blue-600 text-white rounded-md shadow-md hover:bg-blue-700 transition-colors"
                :disabled="loading">
                💾 Sauvegarder les modifications
              </button>
            </div>

            <!-- Tableau de revue analytique -->
            <div v-if="revueAnalytiqueFinaleReport.revue && revueAnalytiqueFinaleReport.revue.length"
              class="overflow-x-auto rounded-xl shadow-xl bg-white border border-gray-100">
              <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gradient-to-r from-indigo-600 via-blue-600 to-cyan-600">
                  <tr>
                    <th class="px-6 py-4 text-left text-xs font-semibold text-white uppercase tracking-wider">Compte
                    </th>
                    <th class="px-6 py-4 text-left text-xs font-semibold text-white uppercase tracking-wider">Libellé
                    </th>
                    <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">N</th>
                    <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">N-1</th>
                    <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">Δ</th>
                    <th class="px-6 py-4 text-right text-xs font-semibold text-white uppercase tracking-wider">Δ %</th>
                    <th class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider">Statut
                    </th>
                    <th class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider">Risque
                    </th>
                    <th class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider">
                      Validation</th>
                    <th class="px-6 py-4 text-center text-xs font-semibold text-white uppercase tracking-wider">Validé
                    </th>
                    <th class="px-6 py-4 text-left text-xs font-semibold text-white uppercase tracking-wider">
                      Commentaire Auto
                    </th>
                    <th class="px-6 py-4 text-left text-xs font-semibold text-white uppercase tracking-wider">
                      Commentaire Perso
                    </th>
                  </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                  <tr v-for="(item, index) in revueAnalytiqueFinaleReport.revue" :key="index"
                    class="hover:bg-gradient-to-r hover:from-blue-50 hover:to-indigo-50 transition-all duration-300 group transform hover:scale-[1.01] hover:shadow-md">
                    <td class="px-6 py-4 whitespace-nowrap">
                      <div class="flex items-center">
                        <div
                          class="flex-shrink-0 h-8 w-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center mr-3 group-hover:scale-110 transition-transform duration-200">
                          <span class="text-xs font-bold text-white">{{ item.compte.charAt(0) }}</span>
                        </div>
                        <div
                          class="text-sm font-mono font-bold text-gray-900 group-hover:text-blue-700 transition-colors duration-200">
                          {{ item.compte }}</div>
                      </div>
                    </td>
                    <td class="px-6 py-4">
                      <div
                        class="text-sm text-gray-900 max-w-xs truncate group-hover:text-blue-700 transition-colors duration-200"
                        :title="item.libelle">{{ item.libelle }}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-right">
                      <div
                        class="text-sm font-mono text-gray-900 group-hover:text-blue-700 transition-colors duration-200">
                        {{
                          item.solde_n.toLocaleString() }}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-right">
                      <div
                        class="text-sm font-mono text-gray-900 group-hover:text-blue-700 transition-colors duration-200">
                        {{
                          item.solde_n1.toLocaleString() }}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-right">
                      <div class="flex items-center justify-end">
                        <div
                          class="text-sm font-mono font-semibold transform group-hover:scale-105 transition-all duration-200"
                          :class="item.variation >= 0 ? 'text-emerald-600' : 'text-red-600'">
                          {{ item.variation.toLocaleString() }}
                        </div>
                        <div class="ml-2 w-2 h-2 rounded-full"
                          :class="item.variation >= 0 ? 'bg-emerald-500' : 'bg-red-500'">
                        </div>
                      </div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-right">
                      <div class="flex items-center justify-end">
                        <div
                          class="text-sm font-mono font-semibold transform group-hover:scale-105 transition-all duration-200"
                          :class="Math.abs(item.variation_percent) > 20 ? 'text-red-600' : 'text-gray-600'">
                          {{ item.variation_percent.toFixed(1) }}%
                        </div>
                        <svg v-if="Math.abs(item.variation_percent) > 20"
                          class="w-4 h-4 ml-1 text-red-500 animate-pulse" fill="currentColor" viewBox="0 0 20 20">
                          <path fill-rule="evenodd"
                            d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                            clip-rule="evenodd"></path>
                        </svg>
                      </div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-center">
                      <span
                        class="inline-flex px-3 py-1 rounded-full text-xs font-medium shadow-sm transform group-hover:scale-105 transition-all duration-200"
                        :class="getStatusClass(item.final_status)">
                        <span class="w-2 h-2 rounded-full mr-2"
                          :class="item.final_status === 'Significatif' ? 'bg-red-500' : 'bg-emerald-500'"></span>
                        {{ item.final_status }}
                      </span>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-center">
                      <span
                        class="inline-flex px-3 py-1 rounded-full text-xs font-medium shadow-sm transform group-hover:scale-105 transition-all duration-200"
                        :class="getRiskLevelClass(item.risk_level)">
                        <span class="w-2 h-2 rounded-full mr-2"
                          :class="item.risk_level === 'Élevé' ? 'bg-red-500' : item.risk_level === 'Moyen' ? 'bg-orange-500' : 'bg-emerald-500'"></span>
                        {{ item.risk_level }}
                      </span>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-center">
                      <span
                        class="inline-flex px-3 py-1 rounded-full text-xs font-medium shadow-sm transform group-hover:scale-105 transition-all duration-200"
                        :class="getValidationStatusClass(item.validation_status)">
                        <span class="w-2 h-2 rounded-full mr-2"
                          :class="item.validation_status === 'Validé' ? 'bg-emerald-500' : 'bg-orange-500'"></span>
                        {{ item.validation_status }}
                      </span>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-center">
                      <input type="checkbox" :checked="item.is_validated"
                        @change="(e) => handleValidationChange(item.compte, e.target.checked)"
                        class="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 transform group-hover:scale-110 transition-all duration-200" />
                    </td>
                    <td class="px-6 py-4">
                      <div
                        class="text-sm text-gray-900 max-w-xs truncate group-hover:text-blue-700 transition-colors duration-200"
                        :title="item.commentaire_auto">{{ item.commentaire_auto }}</div>
                    </td>
                    <td class="px-6 py-4">
                      <textarea :value="item.commentaire_perso"
                        @input="(e) => handleCommentaireChange(item.compte, e.target.value)"
                        class="w-full p-2 text-xs border border-gray-300 rounded resize-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200"
                        rows="2" placeholder="Commentaire personnel..."></textarea>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Résumé de validation -->
            <div v-if="revueAnalytiqueFinaleReport.statistics" class="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <h4 class="text-lg font-semibold text-gray-800 mb-3">Résumé de validation</h4>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h5 class="font-semibold text-orange-800 mb-2">📋 Comptes à valider ({{
                    revueAnalytiqueFinaleReport.statistics.accounts_to_validate }})</h5>
                  <p class="text-sm text-gray-700">
                    Ces comptes nécessitent une validation par l'auditeur pour finaliser l'audit.
                    Progression : {{ revueAnalytiqueFinaleReport.statistics.validation_percentage.toFixed(1) }}%
                  </p>
                </div>
                <div>
                  <h5 class="font-semibold text-green-800 mb-2">✅ Comptes validés ({{
                    revueAnalytiqueFinaleReport.statistics.accounts_validated }})</h5>
                  <p class="text-sm text-gray-700">
                    Ces comptes ont été validés par l'auditeur et peuvent être considérés comme finalisés.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Tooltip pour afficher les questions -->
    <div v-if="showQuestionTooltip" class="fixed z-50 bg-white border border-gray-300 rounded-lg shadow-lg p-4 max-w-md"
      :style="{
        left: tooltipPosition.x + 'px',
        top: tooltipPosition.y + 'px',
        transform: 'translateX(-50%)'
      }" @click.stop>
      <div class="flex justify-between items-start mb-2">
        <h4 class="text-lg font-bold text-blue-800">{{ selectedQuestion }}</h4>
        <button @click="hideQuestionTooltip" class="text-gray-500 hover:text-gray-700 text-xl font-bold ml-2">
          ×
        </button>
      </div>
      <div class="bg-blue-50 border-l-4 border-blue-400 p-3 rounded">
        <p class="text-sm text-gray-700 leading-relaxed">{{ selectedQuestionText }}</p>
      </div>
    </div>

    <!-- Overlay pour fermer le tooltip en cliquant ailleurs -->
    <div v-if="showQuestionTooltip" class="fixed inset-0 z-40" @click="hideQuestionTooltip"></div>

  </div>
</template>
