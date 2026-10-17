# James Parkinson: Data Science Portfolio

Projects in machine learning, geospatial modelling, deep learning and databases, from my MSc in Data Science and Artificial Intelligence at the University of Liverpool. Each folder under `projects/` is self-contained, with its own README covering the problem, method, results and how to run it.

Projects marked **team** were completed with Ewan Moorcroft and Joshua Huzzard, with the work shared evenly across the three of us.

## Geospatial machine learning

| Project | Summary |
|---|---|
| [Culex habitat suitability, Florida](projects/culex-habitat-suitability) | MSc dissertation. Weekly mosquito habitat-suitability models from satellite climate, vegetation and land-cover data (Google Earth Engine), using XGBoost, random forest and MaxEnt, validated with spatial block cross-validation against reference forecasts. |

## Machine learning and deep learning

| Project | Summary |
|---|---|
| [Chest X-ray classification](projects/chest-xray-classification) **team** | Three-class lung X-ray classification with a custom CNN, ResNet-18 and RegNet. Fine-tuned ResNet-18 reached 0.938 macro F1 on held-out data. |
| [Neural text chunking](projects/neural-chunking) **team** | BiLSTM and Transformer sequence taggers for shallow parsing with 17 BIO tags. The BiLSTM reached 0.943 token accuracy and 0.929 MCC. |
| [Patient diagnosis classification](projects/patient-diagnosis-classification) **team** | Four classifiers compared in a leakage-safe scikit-learn pipeline with stratified cross-validation, plus a critical look at a suspiciously perfect score. |

## Reinforcement learning and search

| Project | Summary |
|---|---|
| [LunarLander Double DQN](projects/lunar-lander-dqn) **team** | Double DQN with experience replay in PyTorch, averaging 284 reward in greedy evaluation (200 counts as solved). |
| [Multi-armed bandits](projects/multi-armed-bandits) **team** | ε-greedy vs UCB across 5, 10 and 20 arms over 2,000 runs. |
| [Chess agent](projects/chess-alpha-beta) **team** | Minimax with alpha-beta pruning and move ordering; won 50 of 50 games against a random baseline. Runnable script. |

## Databases and SQL

| Project | Summary |
|---|---|
| [Relational database and SQL queries](projects/sql-database) | Schema plus seven queries, including relational division, anti-joins and `> ANY`. Runs locally with a self-checking test script. |
| [Database design](projects/database-design) | EER model with specialisations, mapped to a tested SQL logical schema, plus relational algebra queries. |

## Tools

Python (pandas, NumPy, scikit-learn, XGBoost, PyTorch, Matplotlib), SQL (MariaDB/MySQL, DuckDB), Google Earth Engine, Gymnasium, Git.

## Data

Datasets supplied for university modules are not redistributed here. Each project README says where the notebook expects its data.

## Licence

See [LICENSE](LICENSE). The code may be viewed and run for professional evaluation, but not reused in other work.
