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
WRITER_STYLE = ROOT / "harness" / "framework" / "writer-style.md"
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
    final_hook: bool = True,
    marker_dense: bool = False,
) -> str:
    scene_one = _base_scene(1, "偏厅", "夜", "内", "偏厅")
    scene_two = _base_scene(2, "长廊", "夜", "外", "长廊")

    if not final_hook:
        scene_two[-1] = "△：两个人都沉默了。烛火稳下来，她把手垂在身侧，呼吸终于缓了一寸。"

    if marker_dense:
        scene_one.insert(-1, "【镜头】：摇到她收紧的下颌，烛光在眼底晃了一下")
        scene_one.insert(-1, "♪：风声忽紧")
        scene_two.insert(-1, "【镜头】：切向案角那一点冷光，随后再切回她的手")
        scene_two.insert(-1, "♪：帘角轻响")
        scene_two.insert(-1, "♪：更鼓再响一声")

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
        self.assertIn("第一人称原著默认改写成第三人称可拍视角", content)
        self.assertIn("单点被看见", content)
        self.assertIn("自然发生的关键节点", content)
        self.assertIn("即时动作钩子", content)
        self.assertIn("只听到名，不得主动补姓", content)

    def test_writer_style_contains_third_person_posture(self) -> None:
        content = WRITER_STYLE.read_text(encoding="utf-8")
        self.assertIn("第一人称原著进入剧本时，默认拆掉“我”叙述腔", content)

    def test_verify_contract_contains_core_gates(self) -> None:
        content = VERIFY_CONTRACT.read_text(encoding="utf-8")
        self.assertIn("draft 未通过 `_ops/episode-lint.py`", content)
        self.assertIn("回应句失去触发语义", content)
        self.assertIn("自然事件被无依据改成设计局", content)
        self.assertIn("概述性信息被擅自扩成具体事故", content)
        self.assertIn("即时动作钩子在相邻下一集第一场未兑现", content)
        self.assertIn("上一集尾部已完整演出的桥段", content)
        self.assertIn("第一人称原著的小说式“我”叙述腔未改成第三人称可拍视角", content)
        self.assertIn("单点关系稀释", content)
        self.assertIn("`os` 语义悬空", content)
        self.assertIn("角色知识边界检查", content)

    def test_line_count_warning_is_warn_not_fail(self) -> None:
        data = _run_lint(_build_episode())
        self.assertEqual(data["status"], "warn")
        self.assertIn("line_count", data["checks"]["warnings"])
        self.assertEqual(data["checks"]["episode_failures"], [])

    def test_hookless_final_scene_is_warn_not_fail(self) -> None:
        data = _run_lint(_build_episode(line_padding=40, final_hook=False))
        self.assertEqual(data["status"], "warn")
        self.assertIn("hookless_final_scene", data["checks"]["warnings"])
        self.assertEqual(data["checks"]["episode_failures"], [])

    def test_marker_dense_is_warn_not_fail(self) -> None:
        data = _run_lint(_build_episode(line_padding=40, marker_dense=True))
        self.assertEqual(data["status"], "warn")
        self.assertIn("marker_dense", data["checks"]["warnings"])
        self.assertEqual(data["checks"]["episode_failures"], [])

    def test_first_person_triangle_narration_fails(self) -> None:
        episode = _build_episode(line_padding=40).replace(
            "△：廊灯压着青砖，冷光落在地上。她抬手扶住门框，袖口轻轻一晃。",
            "△：我推开门，冷光一下子压到我肩上。我抬手扶住门框，袖口轻轻一晃。",
            1,
        )
        data = _run_lint(episode)
        self.assertEqual(data["status"], "fail")
        self.assertEqual(data["totals"]["first_person_narration_count"], 1)
        self.assertTrue(any("first_person_narration" in scene["failures"] for scene in data["checks"]["scene_failures"]))

    def test_first_person_os_narration_fails(self) -> None:
        episode = _build_episode(line_padding=40).replace(
            "甲（os）：今晚不能退",
            "甲（os）：我今晚不能退，我得先稳住他。",
            1,
        )
        data = _run_lint(episode)
        self.assertEqual(data["status"], "fail")
        self.assertEqual(data["totals"]["first_person_narration_count"], 1)
        self.assertTrue(any("first_person_narration" in scene["failures"] for scene in data["checks"]["scene_failures"]))

    def test_first_person_dialogue_does_not_trigger_narration_gate(self) -> None:
        episode = _build_episode(line_padding=40).replace(
            "甲：人到了吗",
            "甲：我知道人到了，你先别动。",
            1,
        )
        data = _run_lint(episode)
        self.assertNotIn("first_person_narration", data["checks"]["episode_failures"])
        self.assertFalse(any("first_person_narration" in scene["failures"] for scene in data["checks"]["scene_failures"]))

    def test_pure_dialogue_run_fails(self) -> None:
        episode = _build_episode(line_padding=40).replace(
            "\n".join(
                [
                    "甲：人到了吗",
                    "△：她没有立刻答，先把手从门框上收回来。指尖擦过木纹时，动作稳得没有一丝抖。",
                    "乙：到了",
                    "甲：外头干净吗",
                    "【镜头】：特写她压下去的眼尾，目光冷得发亮",
                    "乙：干净",
                    "甲（os）：今晚不能退",
                ]
            ),
            "\n".join(
                [
                    "甲：人到了吗",
                    "乙：到了",
                    "甲：外头干净吗",
                    "乙：干净",
                    "甲：等我点头",
                    "乙：知道了",
                ]
            ),
            1,
        )
        data = _run_lint(episode)
        self.assertEqual(data["status"], "fail")
        self.assertTrue(any("pure_dialogue_run" in scene["failures"] for scene in data["checks"]["scene_failures"]))

    def test_too_many_hookless_non_final_scenes_fail(self) -> None:
        episode = "\n".join(
            [
                "第1集：测试",
                "",
                "场1-1：偏厅",
                "夜/日：夜",
                "外/内：内",
                "场景：偏厅",
                "△：冷光压在门边。她扶住门框，没动。",
                "△：窗缝钻进凉风，吹得袖口轻晃。",
                "△：案角一盏茶已经凉了。她指尖轻轻敲过杯沿。",
                "♪：风声贴窗。",
                "甲：人到了吗",
                "【镜头】：特写她垂下去的眼尾。",
                "△：她不出声，只把手垂回身侧。",
                "",
                "场1-2：长廊",
                "夜/日：夜",
                "外/内：外",
                "场景：长廊",
                "△：廊灯压低，影子贴着砖缝挪开。",
                "△：她站在栏杆边，肩线绷着，没有回头。",
                "△：另一只手还按着袖口，动作很慢。",
                "♪：脚步声停住。",
                "甲：外头干净吗",
                "【镜头】：推近她压住呼吸的侧脸。",
                "△：风停了，她也不动。",
                "",
                "场1-3：门边",
                "夜/日：夜",
                "外/内：内",
                "场景：门边",
                "△：门栓轻响，她立刻偏过脸。",
                "△：案角茶盏还在晃，影子却先压到门下。",
                "△：她把呼吸压低，指尖一下收紧。下一刻，门外脚步声停在门边？",
                "♪：门外风声忽紧。",
                "甲：开门。",
                "【镜头】：定住门缝下那一道细影。",
                "△：谁都没有再退。",
                "",
            ]
        ) + "\n"
        data = _run_lint(episode)
        self.assertEqual(data["status"], "fail")
        self.assertIn("too_many_hookless_scenes", data["checks"]["episode_failures"])

    def test_four_scene_function_driven_episode_is_not_scene_count_failure(self) -> None:
        episode = "\n".join(
            [
                "第1集：测试",
                "",
                "场1-1：街头",
                "日/夜：夜",
                "外/内：外",
                "场景：街口",
                "△：车灯切过路面，她刚迈出一步，就被人拦在霓虹底下。",
                "△：男人一把扣住她手腕，气息乱得像是追了一整夜。",
                "△：她猛地抽手，另一只手先把怀里的文件夹压紧。",
                "♪：风声卷过广告牌。",
                "【镜头】：推近男人发红的眼底。",
                "男人：你终于回来了。",
                "△：她没应，只盯着他扣住自己的那只手。",
                "",
                "场1-2：车旁",
                "日/夜：夜",
                "外/内：外",
                "场景：黑车旁",
                "△：她肩背绷直，鞋跟重重抵住车门下沿。",
                "△：男人俯身去拉车门，另一只手仍稳稳压着她肩后。",
                "△：文件夹被挤得变了形，封口银扣在路灯下闪了一下。",
                "♪：车门咔地弹开。",
                "【镜头】：定住她指节压白的那一瞬。",
                "她：放手。",
                "△：他没有松手，反而侧身把她往车里逼近半步。",
                "",
                "场1-3：后座",
                "日/夜：夜",
                "外/内：内",
                "场景：车后座",
                "△：暖风压在车厢里，她坐得很直，怀里的文件夹始终没离手。",
                "△：他坐在对面，视线一寸寸锁在她脸上，喉结滚了一下。",
                "△：她抬眼看他，只在他袖扣上停了一瞬，又把视线落回文件夹封口。",
                "♪：轮胎碾过减速带。",
                "【镜头】：切向她压住封口的指尖。",
                "她：我不是你要找的人。",
                "△：他没接话，只抬手按下中控锁。",
                "",
                "场1-4：院门",
                "日/夜：夜",
                "外/内：内",
                "场景：驶入宅门前",
                "△：车锁落下的一声闷响，把她和门外风声一起关在车厢里。",
                "△：前挡风玻璃外，院门灯柱正一寸寸逼近。",
                "△：她按住文件夹，侧脸映在车窗上，没有再退。",
                "♪：铁门缓缓滑开。",
                "【镜头】：越过她肩侧，定住门楣上亮起的宅门字样。",
                "男人：到了。",
                "△：黑车没减速，径直驶进门后的灯火里。",
                "",
            ]
        ) + "\n"
        data = _run_lint(episode)
        self.assertNotIn("scene_count", data["checks"]["episode_failures"])

    def test_hook_window_recognizes_locked_in_progression(self) -> None:
        episode = "\n".join(
            [
                "第1集：测试",
                "",
                "场1-1：车后座",
                "日/夜：夜",
                "外/内：内",
                "场景：黑车后座",
                "△：车厢里暖风闷着，她坐得很直，呼吸压得很稳。",
                "△：他抬手按下中控锁，锁扣落下的一声闷响贴着她耳边砸下来。",
                "△：前挡风玻璃外，院门灯柱正一寸寸逼近。",
                "♪：铁门缓缓滑开。",
                "【镜头】：越过她肩侧，定住门楣上亮起的宅门字样。",
                "男人：到了。",
                "△：她没再挣，只把文件夹抱得更紧。",
                "",
            ]
        ) + "\n"
        data = _run_lint(episode)
        self.assertNotIn("hookless_final_scene", data["checks"]["warnings"])

    def test_triangle_sentence_overflow_warns_only_when_single_triangle_is_too_long(self) -> None:
        episode = _build_episode(line_padding=40).replace(
            "△：廊灯压着青砖，冷光落在地上。她抬手扶住门框，袖口轻轻一晃。",
            "△：廊灯压着青砖。冷光落在地上。她抬手扶住门框。袖口轻轻一晃。指节又收了一寸。",
            1,
        )
        episode = episode.replace(
            "△：窗缝里钻进一阵凉风，吹得烛火发颤。她偏过脸，先看了一眼门外的影子。",
            "△：窗缝里钻进一阵凉风。她先看了一眼门外的影子。",
            1,
        )

        data = _run_lint(episode)

        self.assertEqual(data["status"], "warn")
        self.assertIn("triangle_sentence_count", data["checks"]["warnings"])
        self.assertEqual(data["checks"]["episode_failures"], [])

    def test_uniform_triangle_rhythm_is_warn_not_fail(self) -> None:
        episode = "\n".join(
            [
                "第1集：测试",
                "",
                "场1-1：偏厅",
                "日/夜：夜",
                "内/外：内",
                "场景：偏厅",
                "△：她推门进去。冷光压在肩上。",
                "△：他抬手拦住。她立刻侧身。",
                "△：她把文件夹抱紧。脚步没有停。",
                "△：门外风声一紧。她先看向门口。",
                "♪：风声贴窗。",
                "甲：人到了吗",
                "【镜头】：推近她压下去的眼尾",
                "△：她没回答。只把呼吸压低。",
                "",
                "场1-2：长廊",
                "日/夜：夜",
                "内/外：外",
                "场景：长廊",
                "△：她走到廊下。灯影跟着晃动。",
                "△：他逼近半步。她没有后退。",
                "△：她手指一收。袖口轻轻擦过栏杆。",
                "△：脚步声停住。下一句问话就要压下来。",
                "♪：脚步顿住。",
                "乙：先别走",
                "【镜头】：定住她没有回头的侧脸",
                "△：她依旧不回头。肩背却更紧了一寸。",
                "",
            ]
        ) + "\n"

        data = _run_lint(episode)

        self.assertEqual(data["status"], "warn")
        self.assertIn("triangle_rhythm_uniform", data["checks"]["warnings"])
        self.assertNotIn("triangle_sentence_count", data["checks"]["warnings"])
        self.assertEqual(data["checks"]["episode_failures"], [])

    def test_compact_two_scene_seven_triangle_episode_is_warn_not_fail(self) -> None:
        episode_text = "\n".join(
            [
                "第7集：测试",
                "",
                "场7-1：舞台边",
                "日/夜：夜",
                "外/内：内",
                "场景：会所舞台下方",
                "△：人群往两边退开，追光灯压在地板上。傅斯年迈步上前，鞋跟声很稳。",
                "△：他走到舞台边，伸手把时鸢扶了下来。动作很轻，却没有给旁人插手的余地。",
                "△：四周一下静住，只剩高跟鞋落地的一声轻响。时鸢抬眼看他，呼吸压得很稳。",
                "♪：低呼声骤停。",
                "时鸢：傅先生，自重。",
                "△：傅斯年没有松手，只把她护在身侧半步。所有人的视线都压了过来。",
                "",
                "场7-2：宴厅中央",
                "日/夜：夜",
                "外/内：内",
                "场景：会所宴厅中央",
                "【镜头】：近景定住，傅斯年半侧过身，把时鸢挡在自己身后。",
                "【镜头】：切向刘美兰骤然发白的脸，唇角已经压不住发抖。",
                "△：他抬眼看向全场，声音低沉有力。宴厅里的灯光一瞬间都像压低了。",
                "傅斯年：介绍一下，这位时鸢小姐，不是外人。",
                "傅斯年：她是我傅斯年认准的人，从今天起，我正式追求她。",
                "傅斯年：谁敢为难她，就是与我傅斯年为敌。",
                "△：四周的低呼声压成一片，谁都没敢立刻接话。时鸢站在他身侧，目光冷得发亮。",
                "♪：宴厅里轰地炸开一阵低呼。",
                "△：苏家三人的脸色一齐变了。谁都没想到，他会把话说到这个地步。",
                "△：刘美兰猛地甩开苏雨柔的手，踩着高跟鞋冲了上来。眼底又惊又怒，连嘴唇都在发抖。",
                "刘美兰：傅斯年！你疯了！",
                "△：傅斯年冷冷回眸，眼神锋利如刀。刘美兰后半句话全卡在了喉咙里。",
                "",
            ]
        ) + "\n"

        data = _run_lint(episode_text)

        self.assertNotIn("triangle_count", data["checks"]["episode_failures"])

    def test_project_specific_failures_are_removed(self) -> None:
        episode_text = "\n".join(
            [
                "第2集：测试",
                "",
                "场2-1：偏厅",
                "日/夜：夜",
                "外/内：内",
                "场景：偏厅",
                "△：门边冷光压下来。她扶住门框，没退。",
                "△：另一人抬眼看她，指尖还扣在袖口上。",
                "△：风声贴着窗缝滑进来，桌角的茶纹轻轻一晃。",
                "♪：风声贴窗。",
                "裴砚舟：姐姐两个字，别急着叫。",
                "【镜头】：推近她一下绷紧的下颌。",
                "△：她先收回视线，再把呼吸压低。门外脚步声停在门边？",
                "",
                "场2-2：门口",
                "日/夜：夜",
                "外/内：内",
                "场景：门口",
                "△：她转身走到门边，灯影顺着肩线往下压。",
                "△：另一人还站在原处，眼神没松。",
                "△：她按住门把，下一刻就要开门。",
                "♪：门外风声忽紧。",
                "时鸢：今晚到此为止。",
                "【镜头】：定住门缝下那一道细影。",
                "△：她没再回头，呼吸却还稳着。",
                "",
            ]
        ) + "\n"

        data = _run_lint(episode_text)

        self.assertNotIn("premature_identity_reveal", data["checks"]["episode_failures"])
        self.assertNotIn("character_knowledge_name_leak", data["checks"]["episode_failures"])
        self.assertNotIn("premature_relation_label", data["checks"]["episode_failures"])
        self.assertNotIn("reply_trigger_mismatch", data["checks"]["episode_failures"])
        self.assertNotIn("source_absent_addition", data["checks"]["episode_failures"])
        self.assertEqual(data["knowledge_name_leaks"], [])
        self.assertEqual(data["relation_label_leaks"], [])
        self.assertEqual(data["reply_trigger_mismatches"], [])
        self.assertEqual(data["source_absent_suspicious_additions"], [])


if __name__ == "__main__":
    unittest.main()
