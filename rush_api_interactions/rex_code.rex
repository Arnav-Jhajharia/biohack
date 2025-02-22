let
    cust_runspec = RunSpec{
        target = 'Bullet',
        resources = Resources{
            storage = some 10,
            storage_units = some "MB",
            gpus = some 1
        }
    },
    prepare_protein = \protein_conformer_trc ->
        get 0 (
            prepare_protein_rex_s default_runspec { ph = some 7.4 , truncation_threshold= some 1, naming_scheme = none, capping_style = some "Never"} protein_conformer_trc
        ),
    auto3d = \smi -> map to_data (get 0 (auto3d_rex_s cust_runspec { k = 5, optimizing_engine= "AIMNET", window=2.5, max_confs=15, enumerate_isomer=true, opt_steps=4000, patience=750, threshold=0.6, convergence_threshold =0.002, verbose=true,capacity=30} [smi])),
    p2rank = \prot_conf -> p2rank_rex_s default_runspec {} prot_conf,
    gnina = \prot_conf -> \bounding_box -> \smol_conf ->
        get 0 (get 0 (gnina_rex_s default_runspec_gpu {exhaustiveness=32, num_modes=30, minimize=true} [prot_conf] [bounding_box] smol_conf []))
in
    \input ->
        let
            protein =   load (id (get 0 input)) "ProteinConformer",
            smol_id =  id (get 1 input),
            smiles = smi (load smol_id "Smol"),
            structure = load (structure_id protein) "Structure",
            pp_trc = [(topology structure, residues structure, chains structure)],
            trc =  [topology structure, residues structure, chains structure],
            bounding_box = get 0 (get 0 (p2rank trc)),
            smol_structure = auto3d smiles,
            prepared_protein = prepare_protein pp_trc,
            docked_structure = gnina prepared_protein bounding_box [smol_structure],
            min_affinity = list_min (map (get "affinity") (get "scores" docked_structure)),
            binding_affinity = BindingAffinity {
                affinity = min_affinity,
                affinity_metric = "kcal/mol",
                protein_id = protein_id protein,
                smol_id = smol_id,
                metadata = Metadata {
                    name = "Protein Binding Affinity",
                    description = none,
                    tags = []
                }
            }
        in
            [BenchmarkArg { entity = "BindingAffinity", id = save binding_affinity }]