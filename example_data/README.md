# Exemple de test (étape 6)

## 1) Générer une image synthétique

```bash
python example_data/generate_synthetic_gel.py
```

## 2) Lancer l'analyse

```bash
python main.py \
  --image example_data/synthetic_gel.png \
  --output-dir outputs \
  --gel-type agarose \
  --ladder-lane 1 \
  --ladder-sizes 10000,8000,6000,5000,4000,3000,2000,1500,1000,700,500
```

## 3) Résultats attendus

- `outputs/report.json`
- `outputs/report.txt`
- `outputs/annotated_gel.png`

Si `numpy`/`opencv-python` ne sont pas installés, la commande échouera avec un message de dépendances manquantes.
