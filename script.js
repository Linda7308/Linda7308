const state = {
  score: 0,
  streak: 0,
  completed: 0,
};

const flashcards = [
  {
    question: "Quel est le rôle principal de la membrane plasmique ?",
    answer: "Délimiter la cellule et contrôler les échanges avec le milieu extracellulaire.",
  },
  {
    question: "Pourquoi parle-t-on de mosaïque fluide ?",
    answer: "Parce que les lipides et protéines membranaires sont mobiles dans le plan de la membrane.",
  },
  {
    question: "Quel composant rigidifie la membrane chez les champignons ?",
    answer: "L’ergostérol, qui joue un rôle similaire au cholestérol chez les animaux.",
  },
  {
    question: "Quelle structure fongique assure l’absorption des nutriments ?",
    answer: "Les hyphes, filaments qui augmentent la surface de contact avec le substrat.",
  },
  {
    question: "Quelle est la différence entre paroi et membrane ?",
    answer: "La paroi est rigide et externe, la membrane est souple et semi-perméable.",
  },
];

const quizQuestions = [
  {
    question: "Quelle macromolécule forme la bicouche lipidique ?",
    options: ["Phospholipides", "Cellulose", "Ribosomes", "ADN"],
    answer: 0,
    explanation: "Les phospholipides s’auto-assemblent en bicouche grâce à leur amphiphilie.",
  },
  {
    question: "Quel colorant est souvent utilisé pour observer la paroi fongique ?",
    options: ["Bleu de méthylène", "Rouge Congo", "Safranine", "Lugol"],
    answer: 1,
    explanation: "Le rouge Congo se fixe sur la chitine et met en évidence la paroi.",
  },
  {
    question: "Quelle structure assure la reproduction asexuée chez beaucoup de champignons ?",
    options: ["Les conidies", "Les chloroplastes", "Les chlorophylles", "Les lysosomes"],
    answer: 0,
    explanation: "Les conidies sont des spores asexuées produites au bout des hyphes.",
  },
];

const trueFalseStatements = [
  {
    statement: "La membrane plasmique est uniquement composée de protéines.",
    isTrue: false,
    explanation: "Elle contient surtout des lipides et des protéines.",
  },
  {
    statement: "Les champignons possèdent une paroi riche en chitine.",
    isTrue: true,
    explanation: "La chitine est un polysaccharide majeur de la paroi fongique.",
  },
  {
    statement: "Le transport passif nécessite de l’ATP.",
    isTrue: false,
    explanation: "Le transport passif se fait sans dépense d’énergie.",
  },
];

const challengeItems = [
  { label: "Pompes ioniques", zone: "membrane" },
  { label: "Ergostérol", zone: "membrane" },
  { label: "Hyphes septés", zone: "fungi" },
  { label: "Chitine", zone: "fungi" },
  { label: "Récepteurs membranaires", zone: "membrane" },
  { label: "Conidies", zone: "fungi" },
];

const scoreTotal = document.getElementById("score-total");
const streakTotal = document.getElementById("streak");
const completedTotal = document.getElementById("completed");

const tabs = document.querySelectorAll(".tab");
const panels = document.querySelectorAll(".panel");
const heroButtons = document.querySelectorAll("header .controls button");

const flashcardElement = document.getElementById("flashcard");
const flashcardQuestion = document.getElementById("flashcard-question");
const flashcardAnswer = document.getElementById("flashcard-answer");
const flashcardProgress = document.getElementById("flashcard-progress");
const flashcardPrev = document.getElementById("flashcard-prev");
const flashcardNext = document.getElementById("flashcard-next");
const flashcardFlip = document.getElementById("flashcard-flip");

const quizQuestion = document.getElementById("quiz-question");
const quizOptions = document.getElementById("quiz-options");
const quizFeedback = document.getElementById("quiz-feedback");
const quizValidate = document.getElementById("quiz-validate");
const quizSkip = document.getElementById("quiz-skip");

const tfQuestion = document.getElementById("tf-question");
const tfFeedback = document.getElementById("tf-feedback");
const tfTrue = document.getElementById("tf-true");
const tfFalse = document.getElementById("tf-false");

const challengeList = document.getElementById("challenge-items");
const challengeReset = document.getElementById("challenge-reset");
const challengeFeedback = document.getElementById("challenge-feedback");
const dropzones = document.querySelectorAll(".dropzone");

let flashcardIndex = 0;
let quizIndex = 0;
let tfIndex = 0;
let selectedQuiz = null;

const updateStats = () => {
  scoreTotal.textContent = state.score;
  streakTotal.textContent = state.streak;
  completedTotal.textContent = state.completed;
};

const addPoints = (points) => {
  state.score += points;
  state.streak += 1;
  updateStats();
};

const resetStreak = () => {
  state.streak = 0;
  updateStats();
};

const markCompleted = () => {
  state.completed += 1;
  updateStats();
};

const switchSection = (sectionId) => {
  tabs.forEach((tab) => tab.classList.toggle("active", tab.dataset.section === sectionId));
  panels.forEach((panel) => panel.classList.toggle("active", panel.id === sectionId));
};

heroButtons.forEach((button) => {
  button.addEventListener("click", () => switchSection(button.dataset.section));
});

tabs.forEach((tab) => {
  tab.addEventListener("click", () => switchSection(tab.dataset.section));
});

const loadFlashcard = () => {
  const card = flashcards[flashcardIndex];
  flashcardQuestion.textContent = card.question;
  flashcardAnswer.textContent = card.answer;
  flashcardProgress.textContent = `Carte ${flashcardIndex + 1} / ${flashcards.length}`;
  flashcardElement.classList.remove("flipped");
};

flashcardFlip.addEventListener("click", () => {
  flashcardElement.classList.toggle("flipped");
});

flashcardNext.addEventListener("click", () => {
  flashcardIndex = (flashcardIndex + 1) % flashcards.length;
  loadFlashcard();
  addPoints(2);
});

flashcardPrev.addEventListener("click", () => {
  flashcardIndex = (flashcardIndex - 1 + flashcards.length) % flashcards.length;
  loadFlashcard();
});

const loadQuiz = () => {
  const quiz = quizQuestions[quizIndex];
  quizQuestion.textContent = quiz.question;
  quizOptions.innerHTML = "";
  selectedQuiz = null;
  quizFeedback.textContent = "";

  quiz.options.forEach((option, index) => {
    const button = document.createElement("button");
    button.className = "quiz-option";
    button.textContent = option;
    button.addEventListener("click", () => {
      selectedQuiz = index;
      document.querySelectorAll(".quiz-option").forEach((opt) => opt.classList.remove("selected"));
      button.classList.add("selected");
    });
    quizOptions.appendChild(button);
  });
};

quizValidate.addEventListener("click", () => {
  if (selectedQuiz === null) {
    quizFeedback.textContent = "Choisis une réponse avant de valider.";
    quizFeedback.style.color = "#b45309";
    return;
  }

  const quiz = quizQuestions[quizIndex];
  if (selectedQuiz === quiz.answer) {
    quizFeedback.textContent = `✅ Bonne réponse ! ${quiz.explanation}`;
    quizFeedback.style.color = "#15803d";
    addPoints(5);
  } else {
    quizFeedback.textContent = `❌ Pas tout à fait. ${quiz.explanation}`;
    quizFeedback.style.color = "#b91c1c";
    resetStreak();
  }

  quizIndex = (quizIndex + 1) % quizQuestions.length;
  markCompleted();
  setTimeout(loadQuiz, 900);
});

quizSkip.addEventListener("click", () => {
  quizIndex = (quizIndex + 1) % quizQuestions.length;
  resetStreak();
  loadQuiz();
});

const loadTrueFalse = () => {
  const item = trueFalseStatements[tfIndex];
  tfQuestion.textContent = item.statement;
  tfFeedback.textContent = "";
};

const handleTrueFalse = (value) => {
  const item = trueFalseStatements[tfIndex];
  if (value === item.isTrue) {
    tfFeedback.textContent = `✅ Exact ! ${item.explanation}`;
    tfFeedback.style.color = "#15803d";
    addPoints(3);
  } else {
    tfFeedback.textContent = `❌ Oups. ${item.explanation}`;
    tfFeedback.style.color = "#b91c1c";
    resetStreak();
  }
  tfIndex = (tfIndex + 1) % trueFalseStatements.length;
  markCompleted();
  setTimeout(loadTrueFalse, 900);
};

tfTrue.addEventListener("click", () => handleTrueFalse(true));
tfFalse.addEventListener("click", () => handleTrueFalse(false));

const shuffleArray = (array) => array.sort(() => Math.random() - 0.5);

const loadChallenge = () => {
  challengeList.innerHTML = "";
  challengeFeedback.textContent = "";
  shuffleArray([...challengeItems]).forEach((item) => {
    const card = document.createElement("div");
    card.className = "challenge-item";
    card.textContent = item.label;
    card.draggable = true;
    card.dataset.zone = item.zone;

    card.addEventListener("dragstart", (event) => {
      event.dataTransfer.setData("text/plain", item.zone);
      event.dataTransfer.setData("text/label", item.label);
    });

    challengeList.appendChild(card);
  });
};

dropzones.forEach((zone) => {
  zone.addEventListener("dragover", (event) => {
    event.preventDefault();
    zone.classList.add("over");
  });

  zone.addEventListener("dragleave", () => {
    zone.classList.remove("over");
  });

  zone.addEventListener("drop", (event) => {
    event.preventDefault();
    zone.classList.remove("over");

    const expectedZone = event.dataTransfer.getData("text/plain");
    const label = event.dataTransfer.getData("text/label");
    const item = [...challengeList.children].find((child) => child.textContent === label);

    if (expectedZone === zone.dataset.zone && item) {
      zone.appendChild(item);
      item.draggable = false;
      item.style.cursor = "default";
      addPoints(4);
      if (challengeList.children.length === 0) {
        challengeFeedback.textContent = "🎉 Bravo, défi réussi !";
        challengeFeedback.style.color = "#15803d";
        markCompleted();
      }
    } else {
      challengeFeedback.textContent = "❌ Pas la bonne catégorie. Réessaie !";
      challengeFeedback.style.color = "#b91c1c";
      resetStreak();
    }
  });
});

challengeReset.addEventListener("click", () => {
  loadChallenge();
});

loadFlashcard();
loadQuiz();
loadTrueFalse();
loadChallenge();
updateStats();
