# Run Manifest

- source_file: 被弃真千金：总裁不好惹.md
- total_episodes: 25
- recommended_total_episodes: pending_book_extraction
- episode_count_source: manual_override
- batch_size: 5
- target_total_minutes: 50
- target_episode_minutes: 2
- episode_minutes_min: 1
- episode_minutes_max: 3
- key_episodes:
- adaptation_mode: novel_to_short_drama
- adaptation_strategy: original_fidelity
- dialogue_adaptation_intensity: light
- generation_execution_mode: prompt_packet_external_agent
- writer_parallelism: 1
- generation_reset_mode: clean_rebuild
- run_status: complete
- active_batch: (none)
- source_authority: original novel manuscript + harness/project/book.blueprint.md + harness/project/source.map.md
- draft_lane: drafts/episodes
- publish_lane: episodes
- promotion_policy: controller_only_after_batch_verify_gate

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
