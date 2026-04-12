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

METAPHOR_RE = re.compile(r"(仿佛|如同|好似|像)")
METAPHOR_EXCLUDE_RE = re.compile(r"(像不像|好像是|像是|就像是)")
REACTION_PATTERNS = {
    "指节发白": re.compile(r"(指节|关节)发白"),
    "睫毛颤": re.compile(r"睫毛.*颤"),
    "嘴角弯起": re.compile(r"嘴角.*(勾起|弯|扬起)"),
    "指甲掐掌心": re.compile(r"指甲.*(掐进|嵌进).*(掌心|手心)"),
}
IMAGERY_PATTERNS = {
    "刀": re.compile(r"刀"),
    "火": re.compile(r"火"),
    "水": re.compile(r"(水|雨|泪)"),
    "棋": re.compile(r"棋"),
}
ENVIRONMENT_PATTERNS = {
    "space": re.compile(r"(殿|宫|院|门|窗|廊|堂|屋|柴房|宫道|雪地|御前|榻|殿外|殿内|墙|帐|案|灯|帘)"),
    "light": re.compile(r"(灯|火光|烛|光|亮|暗|昏|阴影|月色|雪光)"),
    "temperature": re.compile(r"(冷|热|寒|冻|潮|湿|汗)"),
    "sound": re.compile(r"(雨声|风声|钟|鼓|脚步|呼吸|哭声|笑声|闷响|响|声)"),
}
VISIBLE_DETAIL_PATTERNS = re.compile(
    r"(看|抬|垂|转|站|坐|跪|扑|按|捏|攥|扇|笑|哭|咬|退|走|推|扶|抬眼|低头|抬手|落|滑|滴|渗|撞|颤|停|收|掀|压|弯|俯|仰)"
)
PHYSICAL_DETAIL_PATTERNS = re.compile(
    r"(血|雨|泪|汗|伤|痕|泥|水|灯|火|烛|影|雪|风|门|窗|墙|袖|衣|发|眼|唇|手|指|肩|背|膝|脸|骨|呼吸)"
)
HOOK_PATTERNS = re.compile(
    r"(？|未完|忽然|突然|下一刻|就在这时|还没|先|别|再|谁|怎么|为何|要什么|新威胁|风声|门响|脚步|抬眼|转身|收回|停住|压下)"
)
PSYCHOLOGICAL_COMMENT_PATTERNS = [
    re.compile(r"(说明|意味着|可怕之处|真正厉害|越是.+越|不是.+而是|这让|这说明|在于|你就会|观众|显得|像是故意)"),
]
OS_POLISHED_PATTERNS = [
    re.compile(r"越.+越"),
    re.compile(r"不是.+而是"),
    re.compile(r"既.+也"),
]


@dataclass
class Scene:
    title: str
    lines: list[str]


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


def count_metaphors(text: str) -> int:
    if METAPHOR_EXCLUDE_RE.search(text):
        cleaned = METAPHOR_EXCLUDE_RE.sub("", text)
    else:
        cleaned = text
    count = 0
    for match in METAPHOR_RE.finditer(cleaned):
        if match.group(1) == "像" and "画像" in cleaned[max(0, match.start()-1):match.end()+1]:
            continue
        count += 1
    return count


def has_environment_anchor(text: str) -> bool:
    return any(pattern.search(text) for pattern in ENVIRONMENT_PATTERNS.values())


def has_visible_detail(text: str) -> bool:
    return bool(VISIBLE_DETAIL_PATTERNS.search(text) or PHYSICAL_DETAIL_PATTERNS.search(text))


def has_hook(text: str) -> bool:
    return bool(HOOK_PATTERNS.search(text))


def has_psychological_comment(text: str) -> bool:
    return any(pattern.search(text) for pattern in PSYCHOLOGICAL_COMMENT_PATTERNS)


def polished_os(text: str) -> bool:
    return any(pattern.search(text) for pattern in OS_POLISHED_PATTERNS)


def collect_history_files(current: Path) -> list[Path]:
    match = re.search(r"EP-(\d+)\.md$", current.name)
    if not match:
        return []
    current_num = int(match.group(1))
    if current_num <= 1:
        return []
    directory = current.parent
    history: list[Path] = []
    for num in range(max(1, current_num - 4), current_num):
        candidate = directory / f"EP-{num:02d}.md"
        if candidate.exists():
            history.append(candidate)
    return history


def build_scene_metrics(scene: Scene) -> dict:
    triangle_lines: list[str] = []
    camera_count = 0
    sfx_count = 0
    os_count = 0
    vo_count = 0
    metaphor_count = 0
    psychological_comment_count = 0
    dialogue_rounds = 0
    pure_dialogue_run = 0
    longest_pure_dialogue_run = 0
    action_inserts = 0
    between_dialogues = False
    interrupted = True
    last_speaker: str | None = None
    polished_os_count = 0

    for raw in scene.lines[1:]:
        line = normalize_line(raw)
        if not line:
            continue

        triangle = TRIANGLE_RE.match(line)
        if triangle:
            content = triangle.group("content")
            triangle_lines.append(content)
            metaphor_count += count_metaphors(content)
            if has_psychological_comment(content):
                psychological_comment_count += 1
            if between_dialogues:
                action_inserts += 1
                between_dialogues = False
            interrupted = True
            pure_dialogue_run = 0
            continue

        if is_camera(line):
            camera_count += 1
            metaphor_count += count_metaphors(line)
            if between_dialogues:
                action_inserts += 1
                between_dialogues = False
            interrupted = True
            pure_dialogue_run = 0
            continue

        if is_sfx(line):
            sfx_count += 1
            metaphor_count += count_metaphors(line)
            interrupted = True
            pure_dialogue_run = 0
            continue

        dialogue = parse_dialogue(line)
        if dialogue:
            speaker, content = dialogue
            metaphor_count += count_metaphors(content)
            if "（os）" in speaker:
                os_count += 1
                if polished_os(content):
                    polished_os_count += 1
            if "（vo）" in speaker:
                vo_count += 1
            if interrupted or speaker != last_speaker:
                dialogue_rounds += 1
            last_speaker = speaker
            interrupted = False
            pure_dialogue_run += 1
            longest_pure_dialogue_run = max(longest_pure_dialogue_run, pure_dialogue_run)
            between_dialogues = True
            continue

    triangle_sentence_counts = [sentence_count(text) for text in triangle_lines]
    first_two_triangles = triangle_lines[:2]
    ending_text = ""
    for raw in reversed(scene.lines):
        line = normalize_line(raw)
        if line:
            ending_text = line
            break

    return {
        "title": scene.title,
        "triangle_count": len(triangle_lines),
        "triangle_sentence_counts": triangle_sentence_counts,
        "all_triangles_have_2_to_4_sentences": all(2 <= count <= 4 for count in triangle_sentence_counts),
        "all_triangles_have_visible_detail": all(has_visible_detail(text) for text in triangle_lines) if triangle_lines else False,
        "environment_anchor_in_first_two_triangles": any(has_environment_anchor(text) for text in first_two_triangles),
        "camera_count": camera_count,
        "sfx_count": sfx_count,
        "os_count": os_count,
        "vo_count": vo_count,
        "dialogue_rounds": dialogue_rounds,
        "action_scene_exemption": len(triangle_lines) >= 5 and (os_count + vo_count + dialogue_rounds) >= 3,
        "longest_pure_dialogue_run": longest_pure_dialogue_run,
        "action_inserts_between_dialogues": action_inserts,
        "metaphor_count": metaphor_count,
        "psychological_comment_count": psychological_comment_count,
        "polished_os_count": polished_os_count,
        "ending_has_hook": has_hook(ending_text),
        "line_count": len(scene.lines),
    }


def history_repetition(current_lines: list[str], history_files: list[Path]) -> dict:
    current_text = "\n".join(current_lines)
    reaction_hits = {}
    for label, pattern in REACTION_PATTERNS.items():
        current_hit = bool(pattern.search(current_text))
        previous_hits = 0
        for file in history_files:
            if pattern.search(file.read_text(encoding="utf-8", errors="ignore")):
                previous_hits += 1
        reaction_hits[label] = {
            "current_hit": current_hit,
            "hits_in_previous_4_episodes": previous_hits,
        }

    imagery_hits = {}
    for label, pattern in IMAGERY_PATTERNS.items():
        current_count = len(pattern.findall(current_text))
        previous_hit = 0
        for file in history_files[-2:]:
            if pattern.search(file.read_text(encoding="utf-8", errors="ignore")):
                previous_hit += 1
        imagery_hits[label] = {
            "current_count": current_count,
            "hits_in_previous_2_episodes": previous_hit,
        }
    return {"reactions": reaction_hits, "imagery": imagery_hits}


def build_checks(scenes: list[dict], totals: dict, history: dict) -> dict:
    scene_failures = []
    total_scenes = len(scenes)
    for idx, scene in enumerate(scenes, 1):
        failures = []
        if scene["triangle_count"] < 3:
            failures.append("triangle_count")
        if not scene["all_triangles_have_2_to_4_sentences"]:
            failures.append("triangle_sentence_count")
        if not scene["all_triangles_have_visible_detail"]:
            failures.append("triangle_visible_detail")
        if not scene["environment_anchor_in_first_two_triangles"]:
            failures.append("environment_anchor")
        if scene["dialogue_rounds"] < 6 and not scene["action_scene_exemption"]:
            failures.append("dialogue_rounds")
        if scene["longest_pure_dialogue_run"] > 4:
            failures.append("pure_dialogue_run")
        if scene["action_inserts_between_dialogues"] < 2:
            failures.append("action_inserts")
        if scene["sfx_count"] < 1:
            failures.append("sfx")
        if scene["metaphor_count"] > 2:
            failures.append("metaphor_count")
        scene_failures.append({"scene": idx, "title": scene["title"], "failures": failures})

    episode_failures = []
    if totals["scene_count"] < 1 or totals["scene_count"] > 3:
        episode_failures.append("scene_count")
    if totals["triangle_count"] < 8:
        episode_failures.append("triangle_count")
    if totals["os_count"] + totals["vo_count"] < 1:
        episode_failures.append("os_vo_count")
    if totals["camera_count"] < 2:
        episode_failures.append("camera_count")
    if totals["sfx_count"] < totals["scene_count"]:
        episode_failures.append("sfx_total")
    if totals["metaphor_count"] > 5:
        episode_failures.append("metaphor_count")
    if totals["psychological_comment_count"] >= 2:
        episode_failures.append("psychological_comment_count")

    # Non-final scenes without hooks: allow 1 for pacing, fail if ≥ 2
    hookless_non_final = sum(
        1 for i, scene in enumerate(scenes, 1)
        if i < total_scenes and not scene["ending_has_hook"]
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
    if any(scene["line_count"] < 18 for scene in scenes):
        warnings.append("scene_line_count")
    if totals["psychological_comment_count"] == 1:
        warnings.append("psychological_comment_count")
    if totals["all_os_polished"] and totals["os_count"] > 0:
        warnings.append("os_polished")
    if totals["scene_tail_melodrama_run"] >= 3:
        warnings.append("melodramatic_endings")
    for label, entry in history["reactions"].items():
        if entry["current_hit"] and entry["hits_in_previous_4_episodes"] >= 1:
            warnings.append(f"reaction_repeat:{label}")
    for label, entry in history["imagery"].items():
        if entry["current_count"] > 3:
            warnings.append(f"imagery_dense:{label}")
        if entry["current_count"] > 0 and entry["hits_in_previous_2_episodes"] >= 2:
            warnings.append(f"imagery_repeat:{label}")
    if len(set(warnings)) >= 3:
        warnings.append("warning_bundle")

    return {
        "scene_failures": scene_failures,
        "episode_failures": episode_failures,
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
    history_files = collect_history_files(path)

    scene_metrics = [build_scene_metrics(scene) for scene in scenes]
    all_os_polished = all(scene["polished_os_count"] >= scene["os_count"] for scene in scene_metrics if scene["os_count"] > 0)
    scene_tail_melodrama_run = sum(
        1 for scene in scene_metrics if scene["metaphor_count"] > 0 and scene["ending_has_hook"]
    )

    totals = {
        "file": str(path),
        "scene_count": len(scenes),
        "triangle_count": sum(scene["triangle_count"] for scene in scene_metrics),
        "os_count": sum(scene["os_count"] for scene in scene_metrics),
        "vo_count": sum(scene["vo_count"] for scene in scene_metrics),
        "camera_count": sum(scene["camera_count"] for scene in scene_metrics),
        "sfx_count": sum(scene["sfx_count"] for scene in scene_metrics),
        "metaphor_count": sum(scene["metaphor_count"] for scene in scene_metrics),
        "psychological_comment_count": sum(scene["psychological_comment_count"] for scene in scene_metrics),
        "line_count": len(lines),
        "all_os_polished": all_os_polished,
        "scene_tail_melodrama_run": scene_tail_melodrama_run,
        "longest_pure_dialogue_run": max((scene["longest_pure_dialogue_run"] for scene in scene_metrics), default=0),
    }

    history = history_repetition(lines, history_files)
    checks = build_checks(scene_metrics, totals, history)
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
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
