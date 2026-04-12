import json
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "_ops" / "episode-lint.py"
WRITE_CONTRACT = ROOT / "harness" / "framework" / "write-contract.md"
VERIFY_CONTRACT = ROOT / "harness" / "framework" / "verify-contract.md"


def _scene_header(scene_no: int, title: str, day: str, place_type: str, place: str) -> list[str]:
    return [
        f"场1-{scene_no}：{title}",
        f"夜/日：{day}",
        f"外/内：{place_type}",
        f"场景：{place}",
    ]


def _base_scene(scene_no: int, title: str, day: str, place_type: str, place: str) -> list[str]:
    return _scene_header(scene_no, title, day, place_type, place) + [
        "△：廊灯压着青砖，冷光落在地上。她抬手扶住门框，袖口轻轻一晃。",
        "△：窗缝里钻进一阵凉风，吹得烛火发颤。她偏过脸，先看了一眼门外的影子。",
        "△：案角摆着半盏温茶，热气已经淡了。她用指腹轻轻敲了敲杯沿，声响很轻。",
        "△：门栓微微一响，她肩线立刻收紧。下一刻，她把呼吸压得更低。",
        "♪：风声贴窗",
        "甲：人到了吗",
        "△：她没有立刻答，先把手从门框上收回来。指尖擦过木纹时，动作稳得没有一丝抖。",
        "乙：到了",
        "甲：外头干净吗",
        "【镜头】：特写她压下去的眼尾，目光冷得发亮",
        "乙：干净",
        "甲（os）：今晚不能退",
        "△：她往前半步，裙角擦过桌边。桌上的茶纹跟着轻轻一颤。",
        "乙：那就开门",
        "甲：等我点头",
        "【镜头】：推近门缝下那一道细影，影子停着没动",
        "△：两个人同时收声，连呼吸都压住。门外脚步声忽然停在门边？",
    ]


def _build_episode(
    *,
    line_padding: int = 0,
    psychological_comment: bool = False,
    scene_one_metaphors: int = 0,
    final_hook: bool = True,
) -> str:
    scene_one = _base_scene(1, "偏厅", "夜", "内", "偏厅")
    scene_two = _base_scene(2, "长廊", "夜", "外", "长廊")

    if psychological_comment:
        scene_two[4] = "△：她把手按在栏杆上，像是故意让人看见自己的镇定。栏杆上的潮气一点点沾上她的指腹。"

    if scene_one_metaphors:
        metaphor_lines = [
            "△：廊灯压着青砖，像一层霜。她抬手扶住门框，袖口轻轻一晃。",
            "△：窗缝里钻进一阵凉风，像细刀刮过脸。她偏过脸，先看了一眼门外的影子。",
            "△：门栓微微一响，墙上的影子像被水拉长。下一刻，她把呼吸压得更低。",
        ]
        scene_one[4] = metaphor_lines[0]
        scene_one[5] = metaphor_lines[1]
        scene_one[7] = metaphor_lines[2]

    if not final_hook:
        scene_two[-1] = "△：两个人都沉默了。烛火稳下来，她把手垂在身侧，呼吸终于缓了一寸。"

    lines = ["第1集：测试", ""] + scene_one + [""] + scene_two
    lines.extend([""] * line_padding)
    return "\n".join(lines) + "\n"


def _run_lint(text: str) -> dict:
    with tempfile.NamedTemporaryFile("w", suffix=".md", encoding="utf-8", delete=False) as handle:
        handle.write(textwrap.dedent(text))
        path = Path(handle.name)
    try:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(path)],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        return json.loads(result.stdout)
    finally:
        path.unlink(missing_ok=True)


class EpisodeLintTests(unittest.TestCase):
    def test_write_contract_contains_core_rules(self) -> None:
        content = WRITE_CONTRACT.read_text(encoding="utf-8")
        self.assertIn("完整气口优先于碎句节拍", content)
        self.assertIn("保留回应句时，必须保留上句触发语义", content)
        self.assertIn("`os` 必须一眼读清主语、对象和判断落点", content)
        self.assertIn("单点被看见", content)
        self.assertIn("自然发生的关键节点", content)
        self.assertIn("即时动作钩子", content)

    def test_verify_contract_contains_core_gates(self) -> None:
        content = VERIFY_CONTRACT.read_text(encoding="utf-8")
        self.assertIn("draft 未通过 `_ops/episode-lint.py`", content)
        self.assertIn("回应句失去触发语义", content)
        self.assertIn("自然事件被无依据改成设计局", content)
        self.assertIn("概述性信息被擅自扩成具体事故", content)
        self.assertIn("即时动作钩子在相邻下一集第一场未兑现", content)
        self.assertIn("单点关系稀释", content)
        self.assertIn("`os` 语义悬空", content)

    def test_line_count_warning_is_warn_not_fail(self) -> None:
        data = _run_lint(_build_episode())
        self.assertEqual(data["status"], "warn")
        self.assertIn("line_count", data["checks"]["warnings"])
        self.assertEqual(data["checks"]["episode_failures"], [])

    def test_single_psychological_comment_is_warn_not_fail(self) -> None:
        data = _run_lint(_build_episode(line_padding=40, psychological_comment=True))
        self.assertEqual(data["status"], "warn")
        self.assertIn("psychological_comment_count", data["checks"]["warnings"])
        self.assertNotIn("psychological_comment_count", data["checks"]["episode_failures"])

    def test_scene_metaphor_limit_fails_even_when_episode_total_is_within_limit(self) -> None:
        data = _run_lint(_build_episode(line_padding=40, scene_one_metaphors=3))
        self.assertEqual(data["status"], "fail")
        self.assertEqual(data["totals"]["metaphor_count"], 3)
        self.assertIn("metaphor_count", data["checks"]["scene_failures"][0]["failures"])

    def test_hookless_final_scene_is_warn_not_fail(self) -> None:
        data = _run_lint(_build_episode(line_padding=40, final_hook=False))
        self.assertEqual(data["status"], "warn")
        self.assertIn("hookless_final_scene", data["checks"]["warnings"])
        self.assertEqual(data["checks"]["episode_failures"], [])


if __name__ == "__main__":
    unittest.main()
