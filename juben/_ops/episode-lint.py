#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


SCENE_HEADER_RE = re.compile(r"^场(?P<ep>\d+)-(?P<scene>\d+)：(?P<title>.+)$")
DIALOGUE_RE = re.compile(r"^(?P<speaker>[^：:【△♪\s][^：:]{0,30})[：:](?P<content>.+)$")
TRIANGLE_RE = re.compile(r"^△[：:](?P<content>.+)$")
SFX_RE = re.compile(r"^(♪|音效[：:])")
QUOTED_TEXT_RE = re.compile(r"“[^”]*”|\"[^\"]*\"|「[^」]*」|『[^』]*』")
FIRST_PERSON_NARRATION_PATTERNS = [
    re.compile(r"(^|[，。！？；、：\s])我(?!们)(?=[的在把将正刚便就又也都只还仍已先没不想要会能敢得该心眼手脚身头脸嘴推抬转退走看听盯按扶攥咬收停觉得知道明白一下一阵])"),
    re.compile(r"(^|[，。！？；、：\s])我的(?=\S)"),
    re.compile(r"(^|[，。！？；、：\s])我们(?=[在把将正刚便就又也都只还仍已先没不想要会能敢得该心眼手脚身头脸嘴推抬转退走看听盯按扶攥咬收停觉得知道明白])"),
    re.compile(r"(^|[，。！？；、：\s])咱们(?=[在把将正刚便就又也都只还仍已先没不想要会能敢得该])"),
]
HOOK_PATTERNS = re.compile(
    r"(？|未完|忽然|突然|下一刻|就在这时|还没|先|别|再|谁|怎么|为何|要什么|"
    r"风声|门响|脚步|抬眼|转身|收回|停住|压下|"
    r"落锁|锁扣|锁舌|车锁|门锁|锁上|合上|关上|"
    r"驶进|驶向|开进|压进|带进|拖进|推上车|塞进|"
    r"逼近|压近|贴近|拦住|拦下|喝止|站住|不准走|"
    r"推门|开门|门开|门外|门内|铁门|院门|宅门|"
    r"结果|真相|鉴定|进去就知道|马上就知道|马上见分晓)"
)


@dataclass
class Scene:
    title: str
    lines: list[str]


def _emit_json(payload: dict) -> None:
    sys.stdout.buffer.write(json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"))
    sys.stdout.buffer.write(b"\n")


def normalize_line(line: str) -> str:
    return line.strip()


def is_triangle(line: str) -> bool:
    return bool(TRIANGLE_RE.match(line))


def is_camera(line: str) -> bool:
    return "【镜头】" in line


def is_sfx(line: str) -> bool:
    return bool(SFX_RE.match(line))


def parse_dialogue(line: str) -> tuple[str, str] | None:
    match = DIALOGUE_RE.match(line)
    if not match:
        return None
    return match.group("speaker"), match.group("content")


def split_scenes(lines: list[str]) -> list[Scene]:
    scenes: list[Scene] = []
    current_title = ""
    current_lines: list[str] = []

    for raw in lines:
        line = raw.rstrip()
        header = SCENE_HEADER_RE.match(line)
        if header:
            if current_lines:
                scenes.append(Scene(title=current_title, lines=current_lines))
            current_title = header.group("title")
            current_lines = [line]
        elif current_lines:
            current_lines.append(line)

    if current_lines:
        scenes.append(Scene(title=current_title, lines=current_lines))
    return scenes


def sentence_count(text: str) -> int:
    parts = [part.strip() for part in re.split(r"[。！？!?；;]+", text) if part.strip()]
    return len(parts)


def has_first_person_narration(text: str) -> bool:
    cleaned = QUOTED_TEXT_RE.sub("", text)
    return any(pattern.search(cleaned) for pattern in FIRST_PERSON_NARRATION_PATTERNS)


def has_hook(text: str) -> bool:
    return bool(HOOK_PATTERNS.search(text))


def build_ending_window(scene: Scene, window: int = 3) -> str:
    meaningful_lines: list[str] = []
    for raw in reversed(scene.lines[1:]):
        line = normalize_line(raw)
        if not line:
            continue
        meaningful_lines.append(line)
        if len(meaningful_lines) >= window:
            break
    return "\n".join(reversed(meaningful_lines))


def build_scene_metrics(scene: Scene) -> dict:
    triangle_lines: list[str] = []
    camera_count = 0
    sfx_count = 0
    os_count = 0
    vo_count = 0
    dialogue_rounds = 0
    pure_dialogue_run = 0
    longest_pure_dialogue_run = 0
    action_inserts = 0
    between_dialogues = False
    interrupted = True
    last_speaker: str | None = None
    first_person_narration_count = 0

    for raw in scene.lines[1:]:
        line = normalize_line(raw)
        if not line:
            continue

        triangle = TRIANGLE_RE.match(line)
        if triangle:
            content = triangle.group("content")
            triangle_lines.append(content)
            if has_first_person_narration(content):
                first_person_narration_count += 1
            if between_dialogues:
                action_inserts += 1
                between_dialogues = False
            interrupted = True
            pure_dialogue_run = 0
            continue

        if is_camera(line):
            camera_count += 1
            if between_dialogues:
                action_inserts += 1
                between_dialogues = False
            interrupted = True
            pure_dialogue_run = 0
            continue

        if is_sfx(line):
            sfx_count += 1
            interrupted = True
            pure_dialogue_run = 0
            continue

        dialogue = parse_dialogue(line)
        if dialogue:
            speaker, content = dialogue
            if "（os）" in speaker:
                os_count += 1
                if has_first_person_narration(content):
                    first_person_narration_count += 1
            if "（vo）" in speaker:
                vo_count += 1
                if has_first_person_narration(content):
                    first_person_narration_count += 1
            if interrupted or speaker != last_speaker:
                dialogue_rounds += 1
            last_speaker = speaker
            interrupted = False
            pure_dialogue_run += 1
            longest_pure_dialogue_run = max(longest_pure_dialogue_run, pure_dialogue_run)
            between_dialogues = True

    triangle_sentence_counts = [sentence_count(text) for text in triangle_lines]
    ending_text = build_ending_window(scene)

    return {
        "title": scene.title,
        "triangle_count": len(triangle_lines),
        "triangle_sentence_counts": triangle_sentence_counts,
        "triangle_sentence_overflow_count": sum(1 for count in triangle_sentence_counts if count > 4),
        "triangle_rhythm_uniform": len(triangle_sentence_counts) >= 4 and len(set(triangle_sentence_counts)) == 1,
        "camera_count": camera_count,
        "sfx_count": sfx_count,
        "os_count": os_count,
        "vo_count": vo_count,
        "dialogue_rounds": dialogue_rounds,
        "longest_pure_dialogue_run": longest_pure_dialogue_run,
        "action_inserts_between_dialogues": action_inserts,
        "first_person_narration_count": first_person_narration_count,
        "ending_has_hook": has_hook(ending_text),
        "line_count": len(scene.lines),
    }


def build_checks(scenes: list[dict], totals: dict) -> dict:
    scene_failures = []
    total_scenes = len(scenes)
    for idx, scene in enumerate(scenes, 1):
        failures = []
        if scene["triangle_count"] < 3:
            failures.append("triangle_count")
        if scene["longest_pure_dialogue_run"] > 4:
            failures.append("pure_dialogue_run")
        if scene["first_person_narration_count"] > 0:
            failures.append("first_person_narration")
        scene_failures.append({"scene": idx, "title": scene["title"], "failures": failures})

    episode_failures = []
    if totals["scene_count"] < 1 or totals["scene_count"] > 4:
        episode_failures.append("scene_count")
    triangle_count_warning_only = totals["triangle_count"] == 7
    if totals["triangle_count"] < 7:
        episode_failures.append("triangle_count")
    if totals["camera_count"] < 2:
        episode_failures.append("camera_count")
    if totals["first_person_narration_count"] > 0:
        episode_failures.append("first_person_narration")

    hookless_non_final = sum(
        1 for index, scene in enumerate(scenes, 1)
        if index < total_scenes and not scene["ending_has_hook"]
    )
    if hookless_non_final >= 2:
        episode_failures.append("too_many_hookless_scenes")

    warnings = []
    if total_scenes >= 1 and not scenes[-1]["ending_has_hook"]:
        warnings.append("hookless_final_scene")
    if hookless_non_final == 1:
        warnings.append("hookless_non_final_scene")
    if totals["line_count"] < 70:
        warnings.append("line_count")
    if triangle_count_warning_only:
        warnings.append("triangle_count")
    if any(scene["line_count"] < 18 for scene in scenes):
        warnings.append("scene_line_count")
    if any(scene["triangle_sentence_overflow_count"] > 0 for scene in scenes):
        warnings.append("triangle_sentence_count")
    if any(scene["triangle_rhythm_uniform"] for scene in scenes):
        warnings.append("triangle_rhythm_uniform")
    if any(scene["sfx_count"] < 1 for scene in scenes):
        warnings.append("sfx")
    if totals["sfx_count"] < totals["scene_count"]:
        warnings.append("sfx_total")
    if any(scene["camera_count"] > 2 for scene in scenes):
        warnings.append("camera_dense")
    if any(scene["sfx_count"] > 2 for scene in scenes):
        warnings.append("sfx_dense")
    if totals["camera_count"] + totals["sfx_count"] > total_scenes * 3:
        warnings.append("marker_dense")
    if len(set(warnings)) >= 3:
        warnings.append("warning_bundle")

    return {
        "scene_failures": scene_failures,
        "episode_failures": sorted(set(episode_failures)),
        "warnings": sorted(set(warnings)),
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: episode-lint.py <episode-file>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    scenes = split_scenes(lines)
    scene_metrics = [build_scene_metrics(scene) for scene in scenes]

    totals = {
        "file": str(path),
        "scene_count": len(scenes),
        "triangle_count": sum(scene["triangle_count"] for scene in scene_metrics),
        "os_count": sum(scene["os_count"] for scene in scene_metrics),
        "vo_count": sum(scene["vo_count"] for scene in scene_metrics),
        "camera_count": sum(scene["camera_count"] for scene in scene_metrics),
        "sfx_count": sum(scene["sfx_count"] for scene in scene_metrics),
        "first_person_narration_count": sum(scene["first_person_narration_count"] for scene in scene_metrics),
        "line_count": len(lines),
        "longest_pure_dialogue_run": max((scene["longest_pure_dialogue_run"] for scene in scene_metrics), default=0),
    }

    history = {
        "reactions": {},
        "imagery": {},
        "adjacent_overlap": None,
    }
    checks = build_checks(scene_metrics, totals)
    has_failures = any(item["failures"] for item in checks["scene_failures"]) or bool(checks["episode_failures"])
    has_warnings = bool(checks["warnings"])
    status = "fail" if has_failures else "warn" if has_warnings else "pass"

    result = {
        "file": str(path),
        "status": status,
        "totals": totals,
        "scenes": scene_metrics,
        "history": history,
        "checks": checks,
        "knowledge_name_leaks": [],
        "relation_label_leaks": [],
        "reply_trigger_mismatches": [],
        "source_absent_suspicious_additions": [],
    }
    _emit_json(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
