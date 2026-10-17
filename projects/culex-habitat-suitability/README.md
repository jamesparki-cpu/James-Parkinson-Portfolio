# Culex nigripalpus habitat suitability, Florida

My MSc dissertation project. I built weekly habitat-suitability models for *Culex nigripalpus*, a mosquito vector of St. Louis encephalitis and West Nile virus, across Florida. The models combine mosquito observation records with satellite-derived climate, vegetation and land-cover data, and are validated against simple reference forecasts so their skill can be judged honestly.

**Code:** [jamesparki-cpu/MSc-Code](https://github.com/jamesparki-cpu/MSc-Code)

## What it does

- **Data extraction** through Google Earth Engine: Daymet daily climate, MODIS vegetation and water indices (EVI, NDWI) and NLCD land cover, assigned to a regular grid. Observation records come from field and citizen-science sources, with sampling effort and absences handled explicitly.
- **Feature engineering**: weekly aggregation of presence and absence, lagged climate features, and seasonal and land-cover predictors stored as Parquet tables.
- **Models**: XGBoost, random forest and MaxEnt (with both standard and target-group background sampling).
- **Validation**: block cross-validation under spatial and spatiotemporal hold-out schemes. Every model is scored against constant-prevalence, climatology and persistence baselines using ROC-AUC, PR-AUC, the Brier skill score and the Boyce index, with block-bootstrap 95% confidence intervals and nested isotonic calibration.
- **Interpretation**: SHAP attribution by predictor group, with collinearity checks before reading importances.
- **Outputs**: weekly statewide suitability maps, a held-out 2018 validation, and 2025 nowcast maps.

## Key finding

Under spatiotemporal cross-validation the tree models reach a ROC-AUC of about 0.85, but when whole regions are held out (spatial cross-validation) this falls to about 0.66 for XGBoost and random forest. The models learn the timing of mosquito activity well but transfer much less reliably to places they have not seen. Measuring that gap, rather than reporting only the flattering score, was a central part of the project.

## Tools

Python, pandas, NumPy, scikit-learn, XGBoost, elapid (MaxEnt), SHAP, SciPy, Google Earth Engine (`earthengine-api`, `geemap`), PyArrow, Matplotlib.
