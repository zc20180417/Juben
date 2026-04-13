# Run Manifest

- source_file: 墨凰谋：庶女上位录.md
- total_episodes: 60
- batch_size: 5
- key_episodes: EP-20, EP-32, EP-49, EP-60
- adaptation_mode: novel_to_short_drama
- adaptation_strategy: original_fidelity
- dialogue_adaptation_intensity: light
- generation_execution_mode: orchestrated_subagents
- generation_reset_mode: clean_rebuild
- run_status: active
- active_batch: batch02_promoted
- source_authority: original novel manuscript + harness/project/source.map.json
- draft_lane: drafts/episodes
- publish_lane: episodes
- promotion_policy: controller_only_after_full_batch_verify

## Current Runtime
- framework entry: harness/framework/entry.md
- source map: harness/project/source.map.md
- current batch brief: harness/project/batch-briefs/batch02_EP06-10.md
- regression packs: optional under harness/project/regressions/
- state directory: harness/project/state/

## Defaults
- stale legacy v1 files are not runtime authority
- published episodes are read-only outputs for current run
- draft episodes are the only candidate lane for verify
