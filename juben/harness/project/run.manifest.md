# Run Manifest

- source_file: 首辅白月光回京后，我主动让位，他却只要我.md
- total_episodes: 15
- recommended_total_episodes: 15
- episode_count_source: model_recommended
- batch_size: 5
- target_episode_minutes: 2
- episode_minutes_min: 1
- episode_minutes_max: 3
- key_episodes: 
- adaptation_mode: novel_to_short_drama
- adaptation_strategy: original_fidelity
- dialogue_adaptation_intensity: light
- generation_execution_mode: orchestrated_subagents
- writer_parallelism: 3
- writer_command: "{python}" _ops/run_writer.py --batch {batch_id} --episodes {episodes_csv} --parallelism {parallelism} {syntax_first_flag}
- generation_reset_mode: clean_rebuild
- run_status: active
- active_batch: batch03_promoted
- source_authority: original novel manuscript + harness/project/book.blueprint.md + harness/project/source.map.md
- draft_lane: drafts/episodes
- publish_lane: episodes
- promotion_policy: controller_only_after_full_batch_verify

## Current Runtime
- framework entry: harness/framework/entry.md
- book blueprint: harness/project/book.blueprint.md
- source map: harness/project/source.map.md
- current batch brief: (none)
- regression packs: optional under harness/project/regressions/
- state directory: harness/project/state/

## Defaults
- stale legacy v1 files are not runtime authority
- published episodes are read-only outputs for current run
- draft episodes are the only candidate lane for verify
