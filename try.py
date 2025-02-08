from rush import build_blocking_provider
client = build_blocking_provider(
    access_token="373691e6-433e-49c1-b063-079a5a506360"
    # for example, if your token is 00000000-dddd-cccc-0000-11111111,
    # then you should put access_token="00000000-dddd-cccc-0000-11111111"
    # (including the double quotes)
)


# benchmark = client.benchmark(name="OpenFF Protein-Ligand Binding Benchmark")

code = r'''

let
    quad_eq_pos = λ a b c →   ((b * b + 4 * a * c) - b) / (2 * a),
    quad_eq_neg = λ a b c → - ((b * b + 4 * a * c) + b) / (2 * a),
    a = 1,
    b = 0,
    c = -1
in
    (quad_eq_pos a b c, quad_eq_neg a b c)

'''

client.eval_rex((code), wait_for_result = True, name = "yessir")


# code = r'''
# let
#     auto3d = \smi -> map to_data (get 0 (auto3d_rex_s default_runspec_gpu { k = 1 } [smi])),
    
#     p2rank = \prot_conf -> p2rank_rex_s default_runspec {} prot_conf,

#     gnina = \prot_conf -> \bounding_box -> \smol_conf ->
#         get 0 (get 0 (gnina_rex_s default_runspec_gpu {} [prot_conf] [bounding_box] smol_conf [])),

# in
# \input ->
#     let
#         protein = load (id (get 0 input)) "ProteinConformer",
#         smol_id = id (get 1 input),
#         smiles = smi (load smol_id "Smol"),

#         structure = load (structure_id protein) "Structure",
#         trc = [
#             topology structure,
#             residues structure,
#             chains structure
#         ],

#         bounding_box = get 0 (get 0 (p2rank trc)),

#         smol_structure = auto3d smiles,

#         docked_structure = gnina trc bounding_box [smol_structure],

#         min_affinity = list_min (map (get "affinity") (get "scores" docked_structure)),

#         binding_affinity = BindingAffinity {
#             affinity = min_affinity,
#             affinity_metric = "kcal/mol",
#             protein_id = protein_id protein,
#             smol_id = smol_id,
#             metadata = Metadata {
#                 name = "binding affinity for smol and protein",
#                 description = none,
#                 tags = []
#             }
#         }
#     in
#         [BenchmarkArg {
#             entity = "BindingAffinity",
#             id = save binding_affinity
#         }]
# '''


# submission = client.run_benchmark(
#     benchmark.id, 
#     code, 
#     "simple submission", 
#     sample=0.01
# )