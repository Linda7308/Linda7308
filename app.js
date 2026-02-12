const steps = [
  {
    title: "Stériliser le matériel",
    details: "Passage de la verrerie/milieu en autoclave pour éviter toute contamination.",
    suggestedMinutes: 20,
  },
  {
    title: "Préparer le milieu nutritif",
    details: "Dissoudre le milieu, chauffer et homogénéiser sur agitateur.",
    suggestedMinutes: 15,
  },
  {
    title: "Travailler sous hotte",
    details: "Verser le milieu dans les boîtes de Petri en conditions aseptiques.",
    suggestedMinutes: 12,
  },
  {
    title: "Étiqueter les boîtes",
    details: "Ajouter date, échantillon et code de lot pour la traçabilité.",
    suggestedMinutes: 8,
  },
  {
    title: "Incuber",
    details: "Placer les boîtes à la température définie jusqu'à croissance visible.",
    suggestedMinutes: 1440,
  },
  {
    title: "Observer et mesurer",
    details: "Compter les colonies / contrôler les résultats puis faire la pesée si nécessaire.",
    suggestedMinutes: 20,
  },
];

const summaryList = document.getElementById("summary-list");
const stepsList = document.getElementById("steps-list");
const progressLabel = document.getElementById("progress-label");
const progress = document.getElementById("progress");
const resetBtn = document.getElementById("reset-btn");
const currentStep = document.getElementById("current-step");
const timerDisplay = document.getElementById("timer-display");
const startTimerBtn = document.getElementById("start-timer");
const pauseTimerBtn = document.getElementById("pause-timer");
const resetTimerBtn = document.getElementById("reset-timer");

let selectedStepIndex = null;
let elapsedSeconds = 0;
let timerId = null;

function formatDuration(mins) {
  if (mins >= 60) {
    const hours = Math.floor(mins / 60);
    const remaining = mins % 60;
    return `${hours}h${remaining ? ` ${remaining}min` : ""}`;
  }
  return `${mins} min`;
}

function formatClock(totalSeconds) {
  const m = String(Math.floor(totalSeconds / 60)).padStart(2, "0");
  const s = String(totalSeconds % 60).padStart(2, "0");
  return `${m}:${s}`;
}

function loadState() {
  const raw = localStorage.getItem("labProtocolState");
  if (!raw) return steps.map(() => false);
  try {
    const parsed = JSON.parse(raw);
    return steps.map((_, idx) => Boolean(parsed[idx]));
  } catch {
    return steps.map(() => false);
  }
}

let done = loadState();

function saveState() {
  localStorage.setItem("labProtocolState", JSON.stringify(done));
}

function renderSummary() {
  summaryList.innerHTML = "";
  steps.forEach((step, i) => {
    const li = document.createElement("li");
    li.textContent = `${i + 1}. ${step.title} (${formatDuration(step.suggestedMinutes)})`;
    summaryList.appendChild(li);
  });
}

function setSelectedStep(index) {
  selectedStepIndex = index;
  const step = steps[index];
  currentStep.textContent = `Étape en cours : ${index + 1}. ${step.title} (durée conseillée: ${formatDuration(step.suggestedMinutes)})`;
  elapsedSeconds = 0;
  timerDisplay.textContent = formatClock(elapsedSeconds);
  if (timerId) {
    clearInterval(timerId);
    timerId = null;
  }
}

function renderChecklist() {
  stepsList.innerHTML = "";

  done.forEach((isDone, index) => {
    const step = steps[index];

    const item = document.createElement("li");
    item.className = `step${isDone ? " done" : ""}`;

    const top = document.createElement("div");
    top.className = "step-top";

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = isDone;
    checkbox.addEventListener("change", () => {
      done[index] = checkbox.checked;
      saveState();
      renderChecklist();
    });

    const label = document.createElement("strong");
    label.textContent = `${index + 1}. ${step.title}`;

    const selectBtn = document.createElement("button");
    selectBtn.className = "secondary";
    selectBtn.textContent = "Sélectionner";
    selectBtn.addEventListener("click", () => setSelectedStep(index));

    top.append(checkbox, label, selectBtn);

    const details = document.createElement("small");
    details.textContent = `${step.details} | Durée conseillée: ${formatDuration(step.suggestedMinutes)}`;

    item.append(top, details);
    stepsList.appendChild(item);
  });

  const doneCount = done.filter(Boolean).length;
  progress.value = (doneCount / steps.length) * 100;
  progressLabel.textContent = `${doneCount} / ${steps.length} étape(s) terminée(s)`;
}

startTimerBtn.addEventListener("click", () => {
  if (selectedStepIndex === null || timerId) return;
  timerId = setInterval(() => {
    elapsedSeconds += 1;
    timerDisplay.textContent = formatClock(elapsedSeconds);
  }, 1000);
});

pauseTimerBtn.addEventListener("click", () => {
  if (!timerId) return;
  clearInterval(timerId);
  timerId = null;
});

resetTimerBtn.addEventListener("click", () => {
  elapsedSeconds = 0;
  timerDisplay.textContent = formatClock(elapsedSeconds);
});

resetBtn.addEventListener("click", () => {
  done = steps.map(() => false);
  saveState();
  renderChecklist();
});

renderSummary();
renderChecklist();
