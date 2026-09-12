#!/bin/zsh
# Regenerate every derived result from the drafts after an instrument
# change (quotecheck2). Stage 1 rescoring runs in parallel; stage 2 the
# statistics; stage 3 the macros, figures, and paper. Logs in results/rebuild/.
set -u
cd "$(dirname "$0")/.."
PY=/opt/anaconda3/bin/python3
L=results/rebuild; mkdir -p $L
run() { name=$1; shift; echo "$(date +%H:%M:%S) start $name"; "$@" > $L/$name.log 2>&1 || echo "FAILED $name"; echo "$(date +%H:%M:%S) done $name"; }
# stage 1: rescoring (independent, parallel)
run records_full $PY src/records_dump.py &
run records_para $PY src/records_dump.py --tag para &
run records_app  $PY src/records_dump.py --tag app &
run records_rag  $PY src/records_dump.py --tag rag &
run records_rep2 $PY src/records_dump.py --tag rep2 &
run records_rep3 $PY src/records_dump.py --tag rep3 &
run rescore_full $PY src/rescore_full.py &
run rescore_loops $PY src/rescore_loops.py &
run rescore_gloop $PY src/rescore_loops.py --prefix gloop &
run human_baseline $PY src/human_baseline.py &
run provenance_cap $PY src/provenance.py --corpus cap &
run decompose $PY src/decompose.py &
run decompose_rag $PY src/decompose.py --tag rag &
run pincites $PY src/pincites.py &
wait
run alteration_aware $PY src/alteration_aware.py &
run human_alt $PY src/human_alt.py &
run attribution_audit $PY src/attribution_audit.py &
run attribution_audit_grounded $PY src/attribution_audit.py --grounded &
run human_existence $PY src/human_existence.py &
run name_mismatch $PY src/name_mismatch.py &
run validate_q2 $PY src/validate_q2.py &
wait
# stage 2: statistics
run stats $PY src/stats.py
run gee $PY src/gee.py
run gee_lenient $PY src/gee.py --lenient --out stats_gee_lenient.json
run gee_para $PY src/gee.py --records records_para.jsonl --out stats_gee_para.json
run gee_pooled $PY src/gee.py --pooled --out stats_gee_pooled.json
run gee_alt $PY src/gee.py --records records_alt.jsonl --out stats_gee_alt.json
run gee_distinct $PY src/gee.py --distinct --out stats_gee_distinct.json
run gee_nm $PY src/gee.py --records records_nm.jsonl --out stats_gee_nm.json
run count_outcome $PY src/count_outcome.py
run count_outcome_para $PY src/count_outcome.py --records records_para.jsonl --out count_outcome_para.json
run cluster_bootstrap $PY src/cluster_bootstrap.py
run audit_sensitivity $PY src/audit_sensitivity.py
run gee_pooled_runs $PY src/gee_pooled_runs.py
run loop_transitions $PY src/loop_transitions.py
run gloop_transitions $PY src/loop_transitions.py --prefix gloop
run loop_citations $PY src/loop_citations.py
run revision_stats $PY src/revision_stats.py
run phrasing_stats $PY src/phrasing_stats.py
run grounded_stats $PY src/grounded_stats.py
run appellate_stats $PY src/appellate_stats.py
run replicate $PY src/replicate.py
run era_check $PY src/era_check.py
run contrast_matrix $PY src/contrast_matrix.py
run index_recall $PY src/index_recall.py
run era_strata $PY src/era_strata.py
run opinion_part $PY src/opinion_part.py
run rounds_control $PY src/rounds_control.py
# stage 3
run emit_macros $PY src/emit_macros.py
run figures $PY src/figures.py
cp docs/figures/fig1_pressure.pdf docs/figures/fig2_repair.pdf docs/jurix/
echo "$(date +%H:%M:%S) ALL DONE"
