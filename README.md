# GLOOME: Gain Loss Mapping Engine
A high-performance bioinformatics tool for analyzing gene gain and loss events, and the co-evolution of
presence-absence patterns, along a phylogeny.

GLOOME provides evolutionary analysis of presence and absence profiles (phyletic patterns). These patterns are assumed
to result from gain and loss dynamics along a phylogenetic tree. Examples of characters represented by phyletic patterns
include:

* Restriction sites
* Gene families
* Introns
* Indels

The primary purpose of GLOOME is to infer branch-specific and site-specific gain and loss events, and to analyze the
co-evolution of presence-absence patterns (CoPAP). For every branch and every site, GLOOME computes the exact posterior
probability of a gain (0 → 1) and of a loss (1 → 0) under a continuous-time two-state model with gamma-distributed
rate variation among sites.

### Features
* **Gain and loss inference**: exact posterior probabilities of gain and loss events per branch and per site
* **Ancestral reconstruction** of presence/absence at every internal node
* **Posterior rate estimation** per character (site)
* **CoPAP analysis** (co-evolution of presence-absence patterns), with p-values from a simulation-based null
  distribution and Benjamini-Hochberg q-values
* **Parameter optimization** of π1 (frequency of presence), the gamma α parameter and a branch-length scaling coefficient,
  or of every branch length separately (see [Per-branch branch lengths](#per-branch-branch-lengths))
* **Parsimony and homoplasy scores** per character (parsimony score, minimum steps, homoplasy, consistency index)
* **Tree rooting** by MAD, MVR, midpoint or outgroup (trees that are already rooted are kept as they are)
* **Plots of the data**: phylogenetic distance matrix, sequence identity matrix and binary mapping of the
  presence/absence patterns (see [Plots](#plots)), alongside the CoPAP correlation plots
* **Interactive tree** on the results page, with a single-position view (state at every node, gain/loss on every
  branch) and export of the current view as a PNG (see [Results page](#results-page))
* **Large datasets**: outputs that would be too large are capped or drawn in a compact form, and every such case is
  explained in a note (see [Notes on capped outputs](#notes-on-capped-outputs))
* **High-performance computing** powered by NumPy vectorization

### Project structure

```text
gloome
├── app                                     # Flask webserver
│   ├── static
│   │   ├── css
│   │   │   └── main.css
│   │   └── js
│   │       └── main.js                     # interactive tree and result tables
│   ├── templates
│   │   ├── 404.html
│   │   ├── base.html
│   │   ├── base_newick_tools.html
│   │   ├── citing_and_credits.html
│   │   ├── documentation.html
│   │   ├── gallery.html
│   │   ├── index.html
│   │   ├── overview.html
│   │   ├── read_json_response.html
│   │   ├── source_code.html
│   │   ├── table.html
│   │   └── under_construction.html
│   ├── __init__.py                         # routes
│   ├── app.py
│   ├── config.py
│   ├── flask_config.py
│   └── http_utils.py
├── gloome                                  # computational engine and command-line interface
│   ├── data
│   │   └── initial_data                    # example inputs
│   │       ├── tree
│   │       │   ├── newickTree0.tree
│   │       │   ├── newickTree1.tree
│   │       │   ├── newickTree2.tree
│   │       │   ├── newickTree3.tree
│   │       │   ├── newickTree4.tree
│   │       │   ├── newickTree5.tree
│   │       │   ├── newickTree6.tree
│   │       │   ├── newickTree7.tree
│   │       │   ├── newickTree8.tree
│   │       │   ├── newickTree9.tree
│   │       │   ├── newickTree10.tree
│   │       │   └── newickTree11.tree
│   │       └── msa
│   │           ├── patternMSA0.msa
│   │           ├── patternMSA1.msa
│   │           ├── patternMSA2.msa
│   │           ├── patternMSA3.msa
│   │           ├── patternMSA4.msa
│   │           ├── patternMSA5.msa
│   │           ├── patternMSA6.msa
│   │           ├── patternMSA7.msa
│   │           ├── patternMSA8.msa
│   │           ├── patternMSA9.msa
│   │           ├── patternMSA10.msa
│   │           └── patternMSA11.msa
│   ├── services
│   │   ├── __init__.py
│   │   ├── design_functions.py
│   │   └── service_functions.py
│   ├── tree
│   │   ├── __init__.py
│   │   ├── node.py
│   │   ├── npencoder.py
│   │   ├── pairs.py                        # CoPAP site-pair statistics (null distribution, p/q-values)
│   │   └── tree.py
│   ├── __init__.py
│   ├── __main__.py
│   ├── config.py
│   ├── consts.py
│   └── utils.py
├── logs
├── mail
│   ├── __init__.py
│   └── mail.py
├── results
│   ├── out
│   └── in
├── scheduler
│   ├── __init__.py
│   ├── runs_automatic_daily_cleaning.py
│   ├── runs_automatic_daily_job.py
│   └── runs_automatic_report_sending.py
├── tests
│   ├── __init__.py
│   ├── correlation_test.py
│   ├── pairs_test.py
│   └── time_test.py
├── Pipfile
├── README.md
└── requirements.txt
```

This manual covers input formats, command-line usage, the webserver, and how to interpret the results.

## Input

* **MSA** (`--msa_file`): phyletic patterns in FASTA format. Each sequence is a 0/1 string
  (`1` = presence, `0` = absence, `?` = missing data). All sequences must have the same length, and sequence names
  must match the leaf names of the tree.
* **Tree** (`--tree_file`): a phylogenetic tree in Newick format with branch lengths. Bootstrap values are removed
  automatically. A tree that is already rooted (its root has two children) is kept as it is. An unrooted tree (three
  or more children at the root) is rooted with the selected `--rooting_method`.

Example:

```text
>A
11101010111000101011111011111
>B1
...
```

```text
(A:0.1,((E:0.1,(F1:0.1,F2:0.1):0.2):0.2,((D1:1.1,D2:0.1):0.12,((B1:0.1,B2:0.1):0.2,C:0.1):0.2):0.2):0.2);
```

## Installation

GLOOME is available on [PyPI](https://pypi.org/project/gloome/) and requires Python 3.9 or later:

```bash
pip install gloome
```

This installs all required dependencies and the `gloome` command.

## Command-line usage

```bash
gloome --msa_file patterns.fasta --tree_file tree.nwk --out_dir results
```

`python -m gloome` works as well.

Results are written to `<out_dir>/<process_id>/`. If `--process_id` is not given, one is generated.

#### Required parameters

```text
    --msa_file <type=str>
        Path to the MSA in FASTA format. Input must be a 0/1 binary matrix
        ('1' for presence, '0' for absence, and '?' for missing data).

    --tree_file <type=str>
        Path to the tree in Newick format.
```

#### Optional parameters

```text
    --out_dir <type=str>
        Output directory.

    --process_id <type=str>
        Process ID (name of the result subdirectory). Generated automatically if omitted.

    --with_internal_nodes <type=int>
        Write internal node names into the output Newick tree (0/1). Default is 1.

    --rooting_method <type=str>
        Tree rooting method. Possible options: ('mad', 'mvr', 'midpoint', 'outgroup').
        mad - Minimal Ancestor Deviation
        mvr - Minimum Variance Rooting
        midpoint - Midpoint Rooting
        outgroup - Outgroup Rooting
        Used only for unrooted trees; a rooted tree is kept as it is. Default is 'midpoint'.

    --leaf <type=str>
        Leaf to use as the outgroup when --rooting_method is 'outgroup'. Default is ''.
```

Model parameters:

```text
    --pi_1 <type=float>
        π1, the stationary frequency of presence (state '1'), between 0.001 and 0.999. Default is 0.5.

    --alpha <type=float>
        Shape parameter α of the gamma distribution of rates among sites, between 0.1 and 20. Default is 0.5.

    --categories_quantity <type=int>
        Number of discrete gamma rate categories, between 1 and 16. Default is 4.

    --coefficient_bl <type=float>
        Scaling coefficient applied to all branch lengths, between 0.1 and 10. Default is 1.0.

    --branch_length_min_bound <type=float>
        Minimum branch length, between 0.0001 and 1. Default is 0.0001.

    --branch_length_max_bound <type=float>
        Maximum branch length, between 1.0 and 2.0. Default is 2.0.

    --is_optimize_pi <type=int>
        Optimize π1 by maximum likelihood (0/1). Default is 1.

    --is_optimize_pi_average <type=int>
        Set π1 to the observed frequency of '1' in the MSA (0/1). Used only when --is_optimize_pi is 0.
        Default is 0.

    --is_optimize_alpha <type=int>
        Optimize α by maximum likelihood (0/1). Default is 1.

    --is_optimize_bl <type=int>
        Optimize the branch-length coefficient by maximum likelihood (0/1). Default is 1.

    --is_optimize_bl_per_branch <type=int>
        Optimize every branch length separately by maximum likelihood, instead of one coefficient (0/1).
        When set, it replaces --is_optimize_bl. Slower than the
        coefficient. Default is 0.
```

CoPAP parameters:

```text
    --is_do_not_use_copap <type=int>
        Skip the CoPAP analysis (0/1). Default is 0.

    --probability_lg <type=float>
        Minimum gain/loss probability for an event to count on a branch, between 0.01 and 0.99.
        Used to select the sites for the Pearson correlation table. Default is 0.5.

    --number_lg <type=int>
        Minimum number of such gain/loss events a site needs to be included in the Pearson
        correlation table, between 1 and 20. Default is 1.

    --number_datasets <type=int>
        Number of datasets simulated under the fitted model to build the null distribution
        for the coevolution p-values, between 1 and 1000. Default is 100.
```

Output files (each flag is 0/1 and turns one output file on or off; see [Output files](#output-files)):

```text
    --file_log_likelihood_tsv <type=int>                             Default is 1.
    --file_table_of_nodes_tsv <type=int>                             Default is 1.
    --file_table_of_branches_tsv <type=int>                          Default is 1.
    --file_branch_position_probabilities_tsv <type=int>              Default is 1.
    --file_table_of_coevolution_tsv <type=int>                       Default is 1.
    --file_table_of_parsimony_and_homoplasy_scores_tsv <type=int>    Default is 1.
    --file_table_of_posterior_rates_tsv <type=int>                   Default is 1.
    --file_table_of_pearson_correlation_tsv <type=int>               Default is 1.
    --file_table_of_attributes_tsv <type=int>                        Default is 1.
    --file_branch_length_models_tsv <type=int>                       Default is 1.
    --file_phylogenetic_tree_nwk <type=int>                          Default is 1.
    --file_all_nodes_fasta <type=int>                                Default is 1.
    --file_simulated_datasets_fastas <type=int>                      Default is 1.
    --file_barplot_of_correlation_svg <type=int>                     Default is 1.
    --file_plot_correlation_by_rate_bin_svg <type=int>               Default is 1.
    --file_plot_distribution_of_correlation_svg <type=int>           Default is 1.
    --file_phylogenetic_distance_matrix_svg <type=int>               Default is 1.
    --file_sequence_identity_matrix_svg <type=int>                   Default is 1.
    --file_binary_mapping_svg <type=int>                             Default is 1.
    --file_interactive_tree_html <type=int>                          Default is 0.
    --file_newick_tree_png <type=int>                                Default is 0.
```

## Output files

All tables are tab-separated. **Positions (`POS`) are 0-based**: `POS 0` is the first column of the MSA.
Branches are named after their child node, so "branch `N3`" means the branch leading from the parent of `N3` to `N3`.
Internal nodes are named `N1`, `N2`, … in the output tree.

The CoPAP files (coevolution, Pearson correlation, posterior rates, simulated datasets and correlation plots) are
created only when CoPAP is enabled and the MSA has more than one position. The posterior rates table needs more than
one rate category.

### Model and likelihood

| File                     | Contents                                                                                                                                                                                                                                       |
|--------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `TreeAttributes.tsv`     | Final model parameters after optimization: π1, gamma α, number of rate categories, branch-length coefficient, the rate of each gamma category, the alphabet and the total log-likelihood. With per-branch branch lengths the coefficient is 1. |
| `LogLikelihood.tsv`      | Log-likelihood (natural log) of each position, plus a `TOTAL` row with the log-likelihood of the whole dataset. Positions with very low values fit the model poorly.                                                                           |
| `PosteriorRates.tsv`     | `POS`, `rate`: posterior mean evolutionary rate of each position. Rates above 1 mean the character changes faster than average, rates near 0 mean it is nearly conserved.                                                                      |
| `PhylogeneticTree.nwk`   | The rooted tree used in the analysis, with internal node names and branch lengths after scaling by the coefficient (or the fitted branch lengths, with per-branch branch lengths).                                                             |
| `AllNodes.fasta`         | A comprehensive FASTA file containing sequences for all tree components, covering both internal ancestral nodes and terminal leaf nodes used in the study.                                                                                     |
| `BranchLengthModels.tsv` | Compares the single-coefficient fit with the per-branch fit, see below.                                                                                                                                                                        |

#### Per-branch branch lengths

By default, GLOOME keeps the relative branch lengths of the input tree and fits one coefficient that scales all of them.
With `--is_optimize_bl_per_branch 1` (web form: **optimize each branch length**) every branch length is fitted
separately, together with π1 and α. This is useful when the input branch lengths come from other data, for example
from sequences, and may not describe how the presence/absence characters evolve.

* Branch lengths are fitted by L-BFGS-B with an exact gradient, alternating with the π1 and α optimization, and are
  kept between 0.000001 and 50. The two branches below a bifurcating root cannot be told apart from their sum, so
  their ratio is kept as in the input tree.
* Different starting points can end in different local optima, so the fit runs from 5 starts: the input lengths, the
  single-coefficient fit and 3 random variations of it (with a fixed seed, so runs are reproducible). The best one is
  kept. Each start alternates at most 10 rounds of branch lengths and π1/α.
* All results (log-likelihood, gain/loss probabilities, ancestral states, CoPAP) then use the fitted branch lengths.
* It takes longer: seconds for the small examples, about an hour for the largest example (`patternMSA10`).

`BranchLengthModels.tsv` has three rows: `single coefficient`, `per-branch`, and their `difference`.

| Column                                                                            | Meaning                                                                                                                                                                                                                           |
|-----------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `log-likelihood`, `free parameters`, `AIC`, `BIC`                                 | Fit of each model. The per-branch model has one free parameter per branch instead of one coefficient. Lower AIC/BIC is better.                                                                                                    |
| `pi_1`, `alpha`, `coefficient of branch lengths`                                  | Fitted parameters of each model.                                                                                                                                                                                                  |
| `total tree length`                                                               | Sum of the branch lengths (after scaling).                                                                                                                                                                                        |
| `branches at lower bound`, `branches at upper bound`                              | Branches fitted to 0.000001 or to 50. A branch at the upper bound is saturated: the data cannot tell its length apart from a very long one.                                                                                       |
| `starts`, `starts log-likelihood range`, `starts reaching the best`, `best start` | How many starts ran, how far apart their results ended, how many reached the best log-likelihood (within 0.1) and which start gave it. If few starts reach the best, the likelihood surface has several optima.                   |
| `rounds`, `converged`                                                             | Rounds used by the best start, and whether it converged or stopped at the 10-round limit.                                                                                                                                         |
| `LRT statistic`, `LRT p-value`                                                    | (difference row) Likelihood-ratio test of the single coefficient against per-branch lengths. A small p-value means per-branch lengths fit significantly better. The p-value is conservative when branches are at the lower bound. |
| `preferred by AIC`, `preferred by BIC`                                            | (difference row) The model with the lower AIC/BIC.                                                                                                                                                                                |

### Gain and loss

| File                              | Contents                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
|-----------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `Branches.tsv`                    | One row per branch: `Parent node`, `Child node`, `Branch length`, then per-position lists: `Gain probability` P(0→1), `Loss probability` P(1→0), and `Branch probability vector`, which holds four probabilities per position in the order [absence maintained (0→0), loss (1→0), gain (0→1), presence maintained (1→1)]. The four values add up to 1.                                                                                                                                                                         |
| `BranchPositionProbabilities.tsv` | The same gain/loss probabilities in long format, one row per (position, branch, event): `G/L` (`gain` or `loss`), `POS`, `branch`, `branchLength`, `distance2root`, `distance2NearestOTU`, `numOfNodes2NearestOTU`, `probability`. Only rows with probability > 0.05 are written. Use this file to filter events, e.g. all gains with probability > 0.9, or to count the expected number of gains/losses per site or per branch by summing `probability`.                                                                      |
| `Nodes.tsv`                       | One row per node: `Name`, `Parent`, `Distance to parent`, `Children`, `Sequence` (reconstructed presence/absence pattern, most probable state at each position), `Probability coefficient` (posterior probability of that reconstructed state), `Ancestral comparison` (change from parent, see below), plus the technical likelihood vectors (`P matrix`, `Up vector`, `Down vector`, `Marginal vector`, `Vector of current conditional likelihood (subtree)`, `Vector of current conditional log-likelihood (ln, subtree)`). |

`Ancestral comparison` codes, per position, compare a node's reconstructed state with its parent's:

| Code | Meaning                     |
|------|-----------------------------|
| `A`  | absence maintained (0 → 0)  |
| `L`  | loss (1 → 0)                |
| `G`  | gain (0 → 1)                |
| `P`  | presence maintained (1 → 1) |

The codes come from the most probable states, so they give a single best reconstruction. For uncertain events, use
the probabilities in `Branches.tsv` or `BranchPositionProbabilities.tsv`.

### Co-evolution (CoPAP)

| File                            | Contents                                                                                                                                                                                                                                                                                                                               |
|---------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `Coevolution.tsv`               | Main CoPAP result, one row per pair of positions: `POS1`, `POS2`, `r` (Pearson correlation of the two positions' gain/loss probability profiles across all branches), `rate-bin` (pair of gamma rate categories of the two positions), `p-value`, `q-value`, `direction`. Sorted by q-value, so the most significant pairs come first. |
| `PearsonCorrelation.tsv`        | `POS1`, `POS2`, `correlation`: raw Pearson correlation of gain/loss profiles for pairs of positions that have at least `--number_lg` events with probability ≥ `--probability_lg`. No significance test; use `Coevolution.tsv` for that.                                                                                               |
| `SimulatedDatasets.fastas`      | The `--number_datasets` MSAs simulated on the same tree under the fitted model (each position keeps its posterior rate), separated by `iterations = i` headers. They form the null distribution for the p-values.                                                                                                                      |
| `DistributionOfCorrelation.svg` | Density (KDE) of `r` over all tested pairs, with the α and β of a Beta distribution fitted to it.                                                                                                                                                                                                                                      |
| `BarplotOfCorrelation.svg`      | Histogram of `r` over all tested pairs, with the same Beta fit.                                                                                                                                                                                                                                                                        |
| `CorrelationByRateBin.svg`      | `r` of every pair, grouped by rate-bin. Shows whether strong correlations concentrate in particular rate classes.                                                                                                                                                                                                                      |

How to read `Coevolution.tsv`:

* Only positions that vary and have at least one gain or loss with probability > 0.5 are tested.
* `r` > 0, `direction = co-occurrence`: the two characters tend to be gained and lost on the same branches.
  `r` < 0, `direction = avoidance`: when one is gained or lost, the other tends not to be.
* `p-value` is empirical: the fraction of simulated pairs **in the same rate-bin** with |r| at least as large as the
  observed one. Comparing within a rate-bin corrects for the fact that fast-evolving characters correlate more by
  chance. The smallest possible p-value is 1 / (number of null pairs in that bin + 1), so more simulated datasets
  give finer p-values.
* `q-value` is the Benjamini-Hochberg false discovery rate. A common cutoff is q < 0.05.

### Parsimony

| File                              | Contents                                                                                                                                                                                                                                                                                                                                                                                       |
|-----------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `ParsimonyAndHomoplasyScores.tsv` | Per position: `Minimum Possible Number Of Steps (M)` (number of states observed minus 1), `Parsimony Score (S)` (minimum number of changes on this tree, Fitch algorithm), `Homoplasy Score (H = S - M)` (extra changes caused by convergence or reversal), `Consistency Index (CI = M/S)` (1 means no homoplasy). A `TOTAL` row sums M, S and H over all positions and gives the ensemble CI. |

### Plots

These plots describe the input data (the tree and the presence/absence patterns of the leaves). They are on by
default and can be turned off one by one.

| File                             | Contents                                                                                                                                                                                                                                                                                                                                                         |
|----------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `PhylogeneticDistanceMatrix.svg` | Heatmap of the phylogenetic (patristic) distance between every pair of leaves: the sum of the branch lengths on the path that joins them through their most recent common ancestor. Darker cells are more distant pairs. Up to 100 leaves the value is printed in every cell (4 decimals).                                                                       |
| `SequenceIdentityMatrix.svg`     | Heatmap of the % identity between the presence/absence patterns of every pair of leaves: matching positions divided by compared positions × 100. Missing data (`?` or `-`) never counts as a match, and a position is left out only when it is missing in both leaves. Up to 100 leaves the value is printed in every cell (1 decimal).                          |
| `BinaryMapping.svg`              | The presence/absence matrix itself, one row per leaf and one column per position (numbered from 1 on the plot): `1` cells in salmon, `0` cells in white, missing data in grey. Up to 100 leaves each cell also shows its character, with a consensus row and a per-leaf count beside the matrix. Above 100 leaves the cells are coloured only (compact drawing). |

The matrices and the binary mapping list the leaves in the order of the MSA. For large datasets these plots are
simplified, see [Notes on capped outputs](#notes-on-capped-outputs).

### Notes on capped outputs

With large datasets some outputs would be too large to write or to open, so GLOOME caps them or draws them in a
simpler form. Every time this happens the run records a short note for that file:

* on the results page, hover over the file in **View/Download Results** to see its note;
* all notes of a run are also written to `notes.json` (file name → note).

| Output                                                         | When                             | What is done                                                                                                            |
|----------------------------------------------------------------|----------------------------------|-------------------------------------------------------------------------------------------------------------------------|
| `PhylogeneticDistanceMatrix.svg`, `SequenceIdentityMatrix.svg` | more than 100 leaves             | The values are not printed in the cells (the colour scale gives them) and the figure is scaled to fit.                  |
| `BinaryMapping.svg`                                            | more than 1,000 positions        | Only positions 1-1,000 are drawn (width limit).                                                                         |
| `BinaryMapping.svg`                                            | more than 100 leaves             | Compact drawing: cells coloured by state, without the character in each cell or the consensus / count rows.             |
| `Coevolution.tsv`                                              | more than 2,000,000 tested pairs | Only the 2,000,000 most significant pairs (lowest q-value) are written. The q-values are still computed over all pairs. |
| `PearsonCorrelation.tsv`                                       | more than 2,000,000 pairs        | Only the 2,000,000 pairs with the strongest correlation (largest \|r\|) are written.                                    |
| `DistributionOfCorrelation.svg`, `BarplotOfCorrelation.svg`    | more than 200,000 tested pairs   | Drawn from a random sample of 200,000 pairs; the α / β of the Beta fit use the same sample.                             |
| `CorrelationByRateBin.svg`                                     | more than 20,000 tested pairs    | Shows a random sample of 20,000 pairs.                                                                                  |

Each note gives the actual numbers of the run, for example: "Showing the 2,000,000 most significant pairs (lowest
q-value) out of N: cut due to the table size limit of 2,000,000 rows.", where N is the number of pairs tested in
that run.

### Other files

| File                   | Contents                                                                                                                                                     |
|------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `InteractiveTree.html` | Standalone interactive tree that opens in a browser (off by default).                                                                                        |
| `VisualTree.png`       | Static picture of the tree (off by default).                                                                                                                 |
| `notes.json`           | Notes for the outputs that were capped or simplified, see [Notes on capped outputs](#notes-on-capped-outputs). Written only when there is at least one note. |                    
| `*.log`                | Log of the run, with parameters and timings.                                                                                                                 |
| `<process_id>.zip`     | Archive of all output files.                                                                                                                                 |

## Webserver

GLOOME is available as a webserver at [gloome.tau.ac.il](https://gloome.tau.ac.il).

### Running an analysis

1. Paste a phyletic pattern MSA (FASTA) and a Newick tree into the text boxes, or upload files. **Load an example**
   fills in an example dataset, **Clear** resets the form. Large inputs are compressed by the browser before they are
   sent, so files of several MB can be submitted.
2. Optionally adjust the model parameters (**optimize BL coefficient** and **optimize each branch length** are
   alternatives: checking one unchecks the other), the CoPAP parameters, the rooting method and the output files.
   These options match the [command-line parameters](#command-line-usage).
   * **Rooting.** Under the rooting options the page says whether the tree you entered is already rooted. A rooted
     tree is kept as it is, and the rooting options are locked. For an unrooted tree, choose a rooting method; for
     outgroup rooting, choose the leaf from the list, which fills in from the tree.
   * **Output files** include the [plots](#plots) **phylogenetic distance matrix**, **sequence identity matrix** and
     **binary mapping** (all on by default).
3. Optionally enter an e-mail address to get a notification when the job finishes.
4. Click **SUBMIT**. The page checks the job status every few seconds and shows the results when it finishes.
   Each run has its own results page at `/results/<process_id>`, which you can bookmark. If the job fails, the page
   shows the reason (for example, that the job ran out of memory) with the process ID and a link to the job log.

### Results page

The results page has four parts.

**Log-likelihood bar.** Shows the total log-likelihood of the tree. Click it to copy the value to the clipboard.

**Interactive tree.**

* Node colors: red = root, orange = internal node, green = leaf.
* **Hover over a node** to see a short summary of the node in a tooltip. The node grows and changes color.
* **Hover over a branch** to see a short summary of the branch in a tooltip. The branch turns dark red.
* **Click a node** to open the **Node information** table below the tree.
* **Click a branch** to open the **Branch information** table below the tree.
* Zoom with the mouse wheel or a two-finger trackpad pinch, and drag to move the tree.
* **show distance to parent** writes each branch length next to its node.
* **show radial tree** switches between a rectangular and a circular layout.
* **Position** shows a single position on the tree (see below). **all** returns to all positions.
* **Save as PNG** downloads the tree exactly as it is shown, see [Saving the tree as PNG](#saving-the-tree-as-png).

#### Single-position view

Enter a position in the **Position** field to see the evolution of that one character on the tree. Positions are
numbered from 0, as in the result tables (`POS` column and `Index` row); the field accepts 0 to (MSA length − 1).
Clear the field or click **all** to show all positions again.

* **Nodes** are coloured by their state at that position, with the same colours as `BinaryMapping.svg`: salmon = `1`
  (present), white = `0` (absent), grey = missing data. The state is written above each node; for internal nodes it is
  followed by the posterior probability of that state, for example `1 (0.97)`.
* **Branches** are coloured by the event on them, from the `Ancestral Comparison` of the node below: green = gain,
  red = loss, light salmon = presence kept, light grey = absence kept. Gains and losses are drawn thicker.
* **Branch labels** give the posterior probability of a gain (`G 0.83`) and/or a loss (`L 0.12`) on the branch,
  when it is at least 0.05 (the same cut-off as `BranchPositionProbabilities.tsv`). Branches with smaller
  probabilities have no label.
* A **legend** in the corner of the tree shows the position and the colours.
* The hover tooltips and the **Node information** / **Branch information** tables show only that position, with its
  number in the `Index` row.
* Zoom and pan are kept while you switch from one position to another. A new result or switching to/from the radial layout starts
  again from the default view.

Some uses: follow where a gene family was gained or lost, check how certain the reconstruction is at the internal
nodes, or look at a pair of positions from `Coevolution.tsv` one after the other.

#### Saving the tree as PNG

**Save as PNG** downloads the tree as it is shown at that moment: the layout (rectangular or radial), zoom and pan,
branch lengths if shown, and, in the single-position view, the colours, labels and legend. The image is saved at
3× the on-screen size on a white background, as `tree_view.png`, or `tree_view_POS_<position>.png` in the
single-position view. Zoom in before saving to get a close-up of part of a large tree.

**Node information table** (one column per position; the last row, `Index`, gives the 0-based position):

| Row                       | Meaning                                                                                                                                             |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------|
| `Name`, `Node type`       | Node name and type (root, node or leaf).                                                                                                            |
| `Distance to parent`      | Length of the branch above the node.                                                                                                                |
| `Sequence`                | Presence/absence at each position: observed for leaves, reconstructed for internal nodes.                                                           |
| `Probability coefficient` | Posterior probability of the shown state, colored on a scale from red (low) to violet (high). Values near 0.5 mean the reconstruction is uncertain. |
| `Ancestral Comparison`    | Change from the parent at each position: `A` absence maintained, `L` loss, `G` gain, `P` presence maintained (see the legend next to the tree).     |

Missing data (`?`) in a leaf is shown as `? (x)`, where `x` is the state GLOOME reconstructed for that position.

**Branch information table** (one column per position):

| Row                         | Meaning                                                                  |
|-----------------------------|--------------------------------------------------------------------------|
| `Parent node`, `Child node` | The two ends of the branch.                                              |
| `Branch length`             | Length of the branch.                                                    |
| `Gain probability`          | Posterior probability of a gain (0 → 1) on this branch at each position. |
| `Loss probability`          | Posterior probability of a loss (1 → 0) on this branch at each position. |

Probabilities are colored from red (near 0) to violet (near 1), so likely events stand out when you scan a row.
These rows contain the same values as `Branches.tsv`.

**View/Download Results.** Lists every output file described in [Output files](#output-files).
**view** opens a file in the browser, **download** saves it. The archive (zip) contains all files. When a file was
capped or simplified because of the size of the data, hover over it to read the note that explains what it shows
(see [Notes on capped outputs](#notes-on-capped-outputs)).

## Citing
If you use GLOOME for your research, please cite the following publication:

Cohen, O., Ashkenazy, H., Belinky, F., Huchon, D., and Pupko, T. 2010. GLOOME: gain loss mapping engine.
Bioinformatics 26(22):2914-2915. [pdf](https://www.tau.ac.il/~talp/publications/GLOOME.pdf) [abs](https://academic.oup.com/bioinformatics/article/26/22/2914/228050)

### BibTeX
Proper citation helps support the development and maintenance of this tool.

```bibtex
@article{cohen2010gloome,
  author = {Cohen, Ofir and Ashkenazy, Haim and Belinky, Frida and Huchon, Doroth{\'e}e and Pupko, Tal},
  title = {GLOOME: gain loss mapping engine},
  journal = {Bioinformatics},
  volume = {26},
  number = {22},
  pages = {2914--2915},
  year = {2010},
  publisher = {Oxford University Press}
}
```

## Contact
For questions, issues, or contributions, please open an issue on the repository or contact the maintainer directly.
